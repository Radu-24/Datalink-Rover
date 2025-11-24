import sys
import os
import ctypes
import re
import time
import threading
import json

import customtkinter as ctk
from ui.picard import PiCard
from ui.pip_window import PiPWindow
from utils import fake_pi_stats
from ui.animations import fade_in_window
from tkinter import messagebox
from netconfig import enable_rover_link, disable_rover_link

import paramiko


# ---------- CONFIG LOADER ----------
def load_config():
    """
    Load config.json from:
      - folder of the .exe when frozen
      - folder of main.py when running from source
    """
    default = {
        "ssh_user": "radu",
        "ssh_password": "",
        "rpiremote_host": "10.0.0.1",
        "rpidock_host": "10.0.1.5",
        "rpicar_host": "10.0.1.3"
    }

    try:
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        cfg_path = os.path.join(base_dir, "config.json")

        print(f"[CONFIG] base_dir = {base_dir}")
        print(f"[CONFIG] looking for: {cfg_path}")

        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        default.update(data)
        print(
            f"[CONFIG] loaded: ssh_user={default['ssh_user']}, "
            f"pass_len={len(default['ssh_password'])}"
        )
    except Exception as e:
        print(f"[CONFIG] ERROR loading config.json: {e}", file=sys.stderr)
        print("[CONFIG] Using built-in defaults (NO password)", file=sys.stderr)

    return default


CONFIG = load_config()


# ---------- ELEVATION ----------
def is_admin() -> bool:
    """
    Check if we are running with administrative privileges.
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def ensure_admin():
    """
    Relaunch the script with admin rights if not already elevated.
    This is required for netsh calls in netconfig.py.
    """
    if is_admin():
        return

    print("[ADMIN] Not elevated, relaunching with admin rights...")

    if getattr(sys, "frozen", False):
        exe = sys.executable
        params = ""
        workdir = None
    else:
        python_exe = sys.executable
        scripts_dir = os.path.dirname(python_exe)
        pythonw_exe = os.path.join(scripts_dir, "pythonw.exe")
        if not os.path.exists(pythonw_exe):
            pythonw_exe = python_exe

        exe = pythonw_exe
        script_path = os.path.abspath(sys.argv[0])
        params = f"\"{script_path}\""
        workdir = None

    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", exe, params, workdir, 1
    )
    sys.exit()


# ---------- REAL SSH STATS ----------
def get_pi_stats_via_ssh(host: str, model: str, timeout: int = 3) -> dict:
    """
    Return a stats dict compatible with PiCard.update_stats:
      online, cpu, temp, ram_percent, storage_used, storage_total,
      voltage, uptime, gpu_clock_mhz
    """
    user = CONFIG.get("ssh_user", "radu")
    password = CONFIG.get("ssh_password", "")

    print(f"[SSH] trying host={host}, user={user}, pass_len={len(password)}")

    stats = {
        "online": False,
        "cpu": 0,
        "temp": 0.0,
        "ram_percent": 0,
        "storage_used": 0,
        "storage_total": 32,
        "voltage": 5.0,
        "uptime": "N/A",
        "gpu_clock_mhz": 0.0,
    }

    if not password:
        print(f"[SSH] password is EMPTY, skipping connect to {host}")
        return stats

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(host, username=user, password=password, timeout=timeout)
        print(f"[SSH] CONNECTED to {host}")

        stats["online"] = True

        # --- TEMP ---
        stdin, stdout, _ = client.exec_command("vcgencmd measure_temp")
        out = stdout.read().decode().strip()
        m = re.search(r"temp=([0-9.]+)", out)
        if m:
            stats["temp"] = float(m.group(1))

        # --- CPU LOAD (approx from idle %) ---
        stdin, stdout, _ = client.exec_command("top -bn1 | grep 'Cpu(s)'")
        cpu_line = stdout.read().decode()
        m = re.search(r"([0-9.]+)\s*id", cpu_line)
        if m:
            idle = float(m.group(1))
            cpu = max(0, min(100, int(100 - idle)))
            stats["cpu"] = cpu

        # --- RAM PERCENT ---
        stdin, stdout, _ = client.exec_command("free -m")
        lines = stdout.read().decode().splitlines()
        for line in lines:
            if line.lower().startswith("mem:"):
                parts = line.split()
                if len(parts) >= 3:
                    total = int(parts[1])
                    used = int(parts[2])
                    if total > 0:
                        stats["ram_percent"] = int((used / total) * 100)
                break

        # --- STORAGE (MB) ---
        stdin, stdout, _ = client.exec_command("df -m / | tail -1")
        parts = stdout.read().decode().split()
        if len(parts) >= 3:
            total_mb = int(parts[1])
            used_mb = int(parts[2])
            stats["storage_total"] = total_mb
            stats["storage_used"] = used_mb

        # --- VOLTAGE ---
        stdin, stdout, _ = client.exec_command("vcgencmd measure_volts")
        v_out = stdout.read().decode().strip()
        m = re.search(r"volt=([0-9.]+)V", v_out)
        if m:
            stats["voltage"] = float(m.group(1))

        # --- UPTIME (REAL, from Pi) ---
        stdin, stdout, _ = client.exec_command("uptime -p")
        stats["uptime"] = stdout.read().decode().strip()

        # --- GPU CLOCK (v3d) in MHz ---
        stdin, stdout, _ = client.exec_command("vcgencmd measure_clock v3d")
        c_out = stdout.read().decode().strip()
        m = re.search(r"=(\d+)", c_out)
        if m:
            hz = int(m.group(1))
            stats["gpu_clock_mhz"] = hz / 1_000_000.0

        client.close()

    except Exception as e:
        print(f"[SSH ERROR] host={host}: {e}", file=sys.stderr)

    return stats


# ---------- CHAINED STATS VIA RPIREMOTE ----------
def _default_stats_dict() -> dict:
    """Base stats structure compatible with PiCard.update_stats."""
    return {
        "online": False,
        "cpu": 0,
        "temp": 0.0,
        "ram_percent": 0,
        "storage_used": 0,
        "storage_total": 32,
        "voltage": 5.0,
        "uptime": "N/A",
        "gpu_clock_mhz": 0.0,
    }


def _get_stats_via_rpiremote_chain(kind: str, timeout: int = 5) -> dict:
    """Ask rpiremote to SSH into rpidock / rpicar and run the dlr_*_stats.py scripts.

    kind: "dock" or "car"
    """
    stats = _default_stats_dict()

    user = CONFIG.get("ssh_user", "radu")
    password = CONFIG.get("ssh_password", "")
    rpiremote_host = CONFIG.get("rpiremote_host", "10.0.0.1")

    if not password:
        print(f"[SSH-CHAIN] password is EMPTY, skipping {kind} via rpiremote")
        return stats

    if kind == "dock":
        remote_cmd = "ssh rpidock 'python3 ~/dlr_dock_stats.py'"
    elif kind == "car":
        remote_cmd = "ssh rpicar 'python3 ~/dlr_car_stats.py'"
    else:
        print(f"[SSH-CHAIN] unknown kind={kind}")
        return stats

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"[SSH-CHAIN] connecting to rpiremote={rpiremote_host} as {user}")
        client.connect(rpiremote_host, username=user, password=password, timeout=timeout)

        print(f"[SSH-CHAIN] exec: {remote_cmd}")
        stdin, stdout, stderr = client.exec_command(remote_cmd, timeout=timeout + 5)

        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()

        if err:
            print(f"[SSH-CHAIN] STDERR from rpiremote for {kind}: {err}", file=sys.stderr)

        client.close()

        if not out:
            print(f"[SSH-CHAIN] EMPTY stdout for {kind} stats", file=sys.stderr)
            return stats

        # Expect a single JSON line from dlr_*_stats.py
        try:
            data = json.loads(out)
        except Exception as e:
            print(f"[SSH-CHAIN] JSON parse error for {kind}: {e}; raw={out}", file=sys.stderr)
            return stats

        # ---- Core fields ----
        stats["online"] = bool(data.get("online", True))

        cpu_val = data.get("cpu")
        if cpu_val is not None:
            try:
                stats["cpu"] = int(round(float(cpu_val)))
            except Exception:
                pass

        temp_val = data.get("temp")
        if temp_val is not None:
            try:
                stats["temp"] = float(temp_val)
            except Exception:
                pass

        ram_val = data.get("ram") or data.get("ram_percent")
        if ram_val is not None:
            try:
                stats["ram_percent"] = int(round(float(ram_val)))
            except Exception:
                pass

        storage_pct = data.get("storage")
        if storage_pct is not None:
            try:
                pct = int(round(float(storage_pct)))
                pct = max(0, min(100, pct))
                stats["storage_total"] = 100
                stats["storage_used"] = pct
            except Exception:
                pass

        uptime_str = data.get("uptime")
        if isinstance(uptime_str, str) and uptime_str.strip():
            stats["uptime"] = uptime_str.strip()

        # ---- New: voltage & GPU clock ----
        volt_val = data.get("voltage")
        if volt_val is not None:
            try:
                stats["voltage"] = float(volt_val)
            except Exception:
                pass

        gclk_val = data.get("gpu_clock_mhz") or data.get("gpu_clock")
        if gclk_val is not None:
            try:
                stats["gpu_clock_mhz"] = float(gclk_val)
            except Exception:
                pass

    except Exception as e:
        print(f"[SSH-CHAIN ERROR] kind={kind}, rpiremote={rpiremote_host}: {e}", file=sys.stderr)

    return stats



def get_rpidock_stats_via_rpiremote() -> dict:
    """Public helper for the docking station card."""
    return _get_stats_via_rpiremote_chain("dock")


def get_rpicar_stats_via_rpiremote() -> dict:
    """Public helper for the car brain card."""
    return _get_stats_via_rpiremote_chain("car")


# --- Global Theme ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class PiMonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window
        self.title("DataLink Rover – Pi Monitor")
        self.geometry("800x500")
        self.minsize(650, 475)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # State
        self.stats_remote = fake_pi_stats("pi5")
        self.stats_car = fake_pi_stats("pi5")
        self.stats_dock = fake_pi_stats("zero2w")
        self.uptime_seconds = 0
        self.monitor_running = False
        self.worker_thread: threading.Thread | None = None
        self.pip: PiPWindow | None = None

        # Top bar
        top_bar = ctk.CTkFrame(self, corner_radius=0)
        top_bar.pack(side="top", fill="x")

        self.rover_btn = ctk.CTkButton(
            top_bar,
            text="Start rover link",
            command=self.toggle_rover_link
        )
        self.rover_btn.pack(side="left", padx=10, pady=6)

        self.pip_btn = ctk.CTkButton(
            top_bar,
            text="PiP Mode",
            command=self.open_pip
        )
        self.pip_btn.pack(side="right", padx=10, pady=6)

        # Main content
        main = ctk.CTkFrame(self, fg_color="#101010")
        main.pack(expand=True, fill="both", padx=10, pady=10)

        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)
        main.grid_columnconfigure(2, weight=1)
        main.grid_rowconfigure(0, weight=1)

        # Cards
        self.card_remote = PiCard(
            main, name="rpiremote", role="Controller (Pi 5)", model="pi5"
        )
        self.card_remote.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        self.card_car = PiCard(
            main, name="rpicar", role="Car brain (Pi 5)", model="pi5"
        )
        self.card_car.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)

        self.card_dock = PiCard(
            main, name="rpidock", role="Dock (Zero 2W)", model="zero2w"
        )
        self.card_dock.grid(row=0, column=2, sticky="nsew", padx=15, pady=15)

        self.after(10, lambda: fade_in_window(self))
        self.after(500, self.update_loop)

    # ----- BACKGROUND WORKER -----
    def monitor_worker(self):
        print("[WORKER] started")

        remote_host = CONFIG.get("rpiremote_host", "10.0.0.1")
        dock_host = CONFIG.get("rpidock_host", "10.0.1.5")

        while self.monitor_running:
            # rpiremote: direct SSH (unchanged)
            self.stats_remote = get_pi_stats_via_ssh(remote_host, "pi5")

            # rpidock & rpicar stats fetched via rpiremote SSH chain
            self.stats_dock = get_rpidock_stats_via_rpiremote()
            self.stats_car = get_rpicar_stats_via_rpiremote()

            time.sleep(2)

        print("[WORKER] stopped")

    # ----- UI UPDATE LOOP -----
    def update_loop(self):
        # Increase uptime counter every second (for demo when offline)
        self.uptime_seconds += 1
        demo_uptime = self.uptime_seconds

        # Update cards
        self.card_remote.update_stats(self.stats_remote, self.stats_remote.get("uptime", "N/A"))
        self.card_car.update_stats(self.stats_car, self.stats_car.get("uptime", f"{demo_uptime}s"))
        self.card_dock.update_stats(self.stats_dock, self.stats_dock.get("uptime", "N/A"))

        # Update PiP if open
        if self.pip is not None and self.pip.winfo_exists():
            self.pip.update_stats(self.stats_remote, self.stats_car, self.stats_dock)

        self.after(1000, self.update_loop)

    # ----- ROVER LINK TOGGLE -----
    def toggle_rover_link(self):
        if not self.monitor_running:
            # Start rover link (netsh to 10.0.0.10 etc.)
            try:
                enable_rover_link()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to enable rover link:\n{e}")
                return

            self.monitor_running = True
            self.worker_thread = threading.Thread(target=self.monitor_worker, daemon=True)
            self.worker_thread.start()
            self.rover_btn.configure(text="Stop rover link")
        else:
            # Stop rover link
            self.monitor_running = False
            try:
                disable_rover_link()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to disable rover link:\n{e}")

            self.rover_btn.configure(text="Start rover link")

    # ----- PIP -----
    def open_pip(self):
        if self.pip is None or not self.pip.winfo_exists():
            self.pip = PiPWindow(self)
        else:
            self.pip.focus()

    # ----- CLOSE -----
    def on_close(self):
        self.monitor_running = False
        self.destroy()


if __name__ == "__main__":
    ensure_admin()
    app = PiMonitorApp()
    app.mainloop()
