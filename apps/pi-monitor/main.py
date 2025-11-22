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


# ---------- ADMIN ELEVATION ----------
def ensure_admin():
    """If not running as administrator, relaunch this program with admin rights."""
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        is_admin = False

    if is_admin:
        return

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

        self.attributes("-alpha", 0)
        self.pip = None
        self.rover_link_enabled = False

        self.monitor_running = False

        # initial fake stats (before rover link)
        self.stats_remote = fake_pi_stats("pi5")
        self.stats_remote["uptime"] = "demo"

        self.stats_car = fake_pi_stats("pi5")
        self.stats_car["uptime"] = "demo"

        self.stats_dock = fake_pi_stats("zero2w")
        self.stats_dock["uptime"] = "demo"

        self.monitor_thread = None

        # ----- TOP BAR -----
        top = ctk.CTkFrame(self, height=60)
        top.pack(side="top", fill="x")

        title = ctk.CTkLabel(
            top,
            text="DataLink Rover – Pi Monitor",
            font=("Segoe UI", 28, "bold")
        )
        title.pack(side="left", padx=20, pady=10)

        self.rover_btn = ctk.CTkButton(
            top,
            text="Start rover link",
            command=self.toggle_rover_link
        )
        self.rover_btn.pack(side="right", padx=20, pady=10)

        pip_btn = ctk.CTkButton(
            top,
            text="PIP",
            width=60,
            command=self.open_pip
        )
        pip_btn.pack(side="right", padx=10, pady=10)

        # ----- MAIN AREA -----
        self.main = ctk.CTkFrame(self)
        self.main.pack(fill="both", expand=True, padx=20, pady=20)

        for col in range(3):
            self.main.grid_columnconfigure(col, weight=1)
        self.main.grid_rowconfigure(0, weight=1)

        self.card_remote = PiCard(
            self.main, "rpiremote", "RPi 5 (Controller)", model="pi5"
        )
        self.card_remote.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        self.card_car = PiCard(
            self.main, "rpicar", "Raspberry Pi 5 (Car)", model="pi5"
        )
        self.card_car.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)

        self.card_dock = PiCard(
            self.main, "rpidock", "Raspberry Pi Zero 2W", model="zero2w"
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
            self.stats_remote = get_pi_stats_via_ssh(remote_host, "pi5")
            self.stats_dock = get_pi_stats_via_ssh(dock_host, "zero2w")

            # car still demo
            self.stats_car = fake_pi_stats("pi5")
            self.stats_car["uptime"] = "demo"

            time.sleep(2)

        print("[WORKER] stopped")

    # ----- UI UPDATE LOOP -----
    def update_loop(self):
        remote_uptime = self.stats_remote.get("uptime", "N/A")
        car_uptime = self.stats_car.get("uptime", remote_uptime)
        dock_uptime = self.stats_dock.get("uptime", remote_uptime)

        self.card_remote.update_stats(self.stats_remote, remote_uptime)
        self.card_car.update_stats(self.stats_car, car_uptime)
        self.card_dock.update_stats(self.stats_dock, dock_uptime)

        if self.pip is not None and self.pip.winfo_exists():
            self.pip.update_stats(self.stats_remote, remote_uptime)

        self.after(500, self.update_loop)

    # ----- START/STOP ROVER LINK -----
    def toggle_rover_link(self):
        try:
            if not self.rover_link_enabled:
                enable_rover_link()
                self.rover_link_enabled = True
                self.monitor_running = True
                self.rover_btn.configure(text="Stop rover link")

                if self.monitor_thread is None or not self.monitor_thread.is_alive():
                    self.monitor_thread = threading.Thread(
                        target=self.monitor_worker, daemon=True
                    )
                    self.monitor_thread.start()
            else:
                disable_rover_link()
                self.rover_link_enabled = False
                self.monitor_running = False
                self.rover_btn.configure(text="Start rover link")
        except Exception as e:
            messagebox.showerror("Network error", str(e))
            self.rover_link_enabled = False
            self.monitor_running = False
            self.rover_btn.configure(text="Start rover link")

    # ----- PIP -----
    def open_pip(self):
        if self.pip is None or not self.pip.winfo_exists():
            self.pip = PiPWindow(self)
        else:
            self.pip.focus()


if __name__ == "__main__":
    ensure_admin()
    app = PiMonitorApp()
    app.mainloop()
