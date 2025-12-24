# apps/pi-monitor/ui/pip_window.py

import customtkinter as ctk


class _PiRow(ctk.CTkFrame):
    """
    Compact single-line row in the PiP window:
    [LED] name  |  CPU xx%  |  T xx°C  |  RAM xx%  |  Disk xx%
    """

    def __init__(self, master, name: str, role: str):
        super().__init__(master, fg_color="#151515", corner_radius=6)
        self.name = name

        self.grid_columnconfigure(2, weight=1)

        small_font = ctk.CTkFont(size=10)
        title_font = ctk.CTkFont(size=11, weight="bold")

        # LED
        self.led = ctk.CTkLabel(self, text="●", width=18, anchor="center")
        self.led.grid(row=0, column=0, padx=(6, 2), pady=3, sticky="w")

        # Name
        self.title_label = ctk.CTkLabel(
            self,
            text=f"{name} – {role}",
            font=title_font,
            anchor="w",
        )
        self.title_label.grid(row=0, column=1, sticky="w", padx=(2, 4), pady=3)

        # Metrics (all in one short line)
        self.metrics_label = ctk.CTkLabel(
            self,
            text="CPU 0% | T 0°C | RAM 0% | Disk 0%",
            font=small_font,
            anchor="w",
        )
        self.metrics_label.grid(row=0, column=2, sticky="ew", padx=(2, 6), pady=3)

        self._blink_phase = 0
        self._online = False
        self._start_blink()

    def _start_blink(self):
        """
        Simple blink only for OFFLINE (red). Online stays solid.
        Blink slightly faster for clearer “offline” feedback.
        """
        if not self._online:
            self._blink_phase = 1 - self._blink_phase
            if self._blink_phase:
                self.led.configure(text_color="#ff3b3b")   # bright red
            else:
                self.led.configure(text_color="#802020")   # dim red
        self.after(90, self._start_blink)  # small, fast blink

    def update_from_stats(self, stats: dict):
        """
        stats is the same dict used for PiCard.update_stats:
        online, cpu, temp, ram_percent, storage_used/total, voltage, uptime, gpu_clock_mhz
        """
        online = bool(stats.get("online", False))
        self._online = online

        cpu = int(stats.get("cpu", 0) or 0)
        temp = float(stats.get("temp", 0.0) or 0.0)
        ram = int(stats.get("ram_percent", 0) or 0)

        used = int(stats.get("storage_used", 0) or 0)
        total = int(stats.get("storage_total", 100) or 100)
        disk_pct = 0
        if total > 0:
            disk_pct = int(round(used * 100.0 / total))

        # LED color when online
        if online:
            if temp >= 75 or cpu >= 90:
                color = "#ffb03b"  # orange – hot
            else:
                color = "#00ff66"  # green – OK
            self.led.configure(text_color=color)
        else:
            # offline: blinking logic handles colors
            self.led.configure(text_color="#ff3b3b")

        # Update metrics line (short, fits on one line)
        self.metrics_label.configure(
            text=f"CPU {cpu}% | T {int(round(temp))}°C | RAM {ram}% | Disk {disk_pct}%"
        )


class PiPWindow(ctk.CTkToplevel):
    """
    Small always-on-top window showing a compact row per Pi.
    main.py calls:
        pip = PiPWindow(root)
        pip.update_stats(remote_stats, car_stats, dock_stats)
    """

    def __init__(self, master):
        super().__init__(master)
        self.title("Pi Monitor – PiP")
        # Smaller default size so the whole window fits nicely
        self.geometry("420x150")
        self.minsize(380, 130)
        self.attributes("-topmost", True)

        self.configure(fg_color="#0b0b0b")

        # Main container
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        wrapper = ctk.CTkFrame(self, fg_color="#101010", corner_radius=10)
        wrapper.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        wrapper.grid_columnconfigure(0, weight=1)

        # Each Pi in a single, thin row
        self.row_remote = _PiRow(wrapper, "rpiremote", "Controller")
        self.row_remote.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 2))

        self.row_car = _PiRow(wrapper, "rpicar", "Car")
        self.row_car.grid(row=1, column=0, sticky="ew", padx=4, pady=2)

        self.row_dock = _PiRow(wrapper, "rpidock", "Dock")
        self.row_dock.grid(row=2, column=0, sticky="ew", padx=4, pady=(2, 4))

    def update_stats(self, stats_remote: dict, stats_car: dict, stats_dock: dict):
        """
        Called periodically from main.update_loop().
        """
        self.row_remote.update_from_stats(stats_remote or {})
        self.row_car.update_from_stats(stats_car or {})
        self.row_dock.update_from_stats(stats_dock or {})
