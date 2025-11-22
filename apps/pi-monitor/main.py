import sys
import os
import ctypes

import customtkinter as ctk
from ui.picard import PiCard
from ui.pip_window import PiPWindow
from utils import format_uptime, fake_pi_stats
from ui.animations import fade_in_window
from tkinter import messagebox
from netconfig import enable_rover_link, disable_rover_link


# ---------- ADMIN ELEVATION (works for both .py and PyInstaller .exe) ----------
def ensure_admin():
    """
    If not running as administrator, relaunch this program with admin rights.
    - When running from Python: uses pythonw.exe main.py (no console).
    - When frozen with PyInstaller: relaunches the .exe itself.
    """
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        is_admin = False

    if is_admin:
        return  # already elevated

    if getattr(sys, "frozen", False):
        # Running as PyInstaller EXE
        exe = sys.executable
        params = ""
        workdir = None
    else:
        # Running as plain Python script
        python_exe = sys.executable              # ...\venv\Scripts\python.exe
        scripts_dir = os.path.dirname(python_exe)
        pythonw_exe = os.path.join(scripts_dir, "pythonw.exe")
        if not os.path.exists(pythonw_exe):
            pythonw_exe = python_exe

        exe = pythonw_exe
        script_path = os.path.abspath(sys.argv[0])
        params = f"\"{script_path}\""
        workdir = None

    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",    # triggers UAC
        exe,
        params,
        workdir,
        1          # normal window
    )
    sys.exit()



# --- Global Theme ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class PiMonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("DataLink Rover – Pi Monitor")
        self.geometry("800x500")
        self.minsize(650, 475)

        self.attributes("-alpha", 0)   # fade-in animation
        self.pip = None                # PiP window reference
        self.rover_link_enabled = False
        self.monitor_running = False   # controls whether fake stats update

        # ---------------- TOP BAR ----------------
        top = ctk.CTkFrame(self, height=60)
        top.pack(side="top", fill="x")

        title = ctk.CTkLabel(
            top,
            text="DataLink Rover – Pi Monitor",
            font=("Segoe UI", 28, "bold")
        )
        title.pack(side="left", padx=20, pady=10)

        # Start/Stop rover link button
        self.rover_btn = ctk.CTkButton(
            top,
            text="Start rover link",
            command=self.toggle_rover_link
        )
        self.rover_btn.pack(side="right", padx=20, pady=10)

        # PiP button
        pip_btn = ctk.CTkButton(
            top,
            text="PiP Mode",
            command=self.open_pip
        )
        pip_btn.pack(side="right", padx=10, pady=10)

        # ---------------- MAIN AREA ----------------
        self.main = ctk.CTkFrame(self)
        self.main.pack(fill="both", expand=True, padx=20, pady=20)

        for col in range(3):
            self.main.grid_columnconfigure(col, weight=1)
        self.main.grid_rowconfigure(0, weight=1)

        # ---------------- CREATE 3 CARDS ----------------
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

        # Startup Animation
        self.after(50, lambda: fade_in_window(self))

        # Update loop – always ticks, only updates stats when monitor_running
        self.ticks = 0
        self.after(1000, self.update_loop)

    # ---------------- UPDATE LOOP ----------------
    def update_loop(self):
        """Update each Pi card every second (when enabled)."""
        self.ticks += 1
        uptime_str = format_uptime(self.ticks)

        if self.monitor_running:
            r_stats = fake_pi_stats("pi5")
            c_stats = fake_pi_stats("pi5")
            d_stats = fake_pi_stats("zero2w")

            self.card_remote.update_stats(r_stats, uptime_str)
            self.card_car.update_stats(c_stats, uptime_str)
            self.card_dock.update_stats(d_stats, uptime_str)

            if self.pip is not None and self.pip.winfo_exists():
                self.pip.update_stats(r_stats, uptime_str)

        self.after(1000, self.update_loop)

    # ---------------- START/STOP ROVER LINK ----------------
    def toggle_rover_link(self):
        try:
            if not self.rover_link_enabled:
                # set static IP + metric
                enable_rover_link()
                self.rover_link_enabled = True
                self.monitor_running = True
                self.rover_btn.configure(text="Stop rover link")
            else:
                # revert to DHCP + auto metric
                disable_rover_link()
                self.rover_link_enabled = False
                self.monitor_running = False
                self.rover_btn.configure(text="Start rover link")
        except Exception as e:
            messagebox.showerror("Network error", str(e))
            self.rover_link_enabled = False
            self.monitor_running = False
            self.rover_btn.configure(text="Start rover link")

    # ---------------- OPEN PIP WINDOW ----------------
    def open_pip(self):
        if self.pip is None or not self.pip.winfo_exists():
            self.pip = PiPWindow(self)
        else:
            self.pip.focus()


if __name__ == "__main__":
    # First thing: make sure we are elevated (UAC pops here, no console)
    ensure_admin()
    app = PiMonitorApp()
    app.mainloop()
