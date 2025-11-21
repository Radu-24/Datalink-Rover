import customtkinter as ctk
from ui.dials import Dial
from ui.bars import TempBar, StorageBar
from ui.leds import StatusLED
from ui.colors import voltage_color, temp_color, cpu_color, gpu_color


class PiCard(ctk.CTkFrame):
    """
    Main widget representing one Raspberry Pi.
    Contains:
      - header (name, role, status LED)
      - CPU & GPU dials (always visible)
      - temperature bar
      - storage bar
      - voltage label
      - uptime label
    """

    def __init__(self, parent, name: str, role: str, model: str):
        super().__init__(parent, corner_radius=18)

        self.model = model  # "pi5" or "zero2w"

        # -------- HEADER --------
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 4))

        self.name_label = ctk.CTkLabel(
            header,
            text=name,
            font=("Segoe UI", 18, "bold")
        )
        self.name_label.pack(side="left")

        self.role_label = ctk.CTkLabel(
            header,
            text=role,
            font=("Segoe UI", 12)
        )
        self.role_label.pack(side="left", padx=(8, 0))

        self.status_led = StatusLED(header)
        self.status_led.pack(side="right", padx=(0, 4))
        self.status_led.animate()

        # -------- DIAL ROW (CPU + GPU) --------
        dial_row = ctk.CTkFrame(self, fg_color="transparent")
        dial_row.pack(pady=(4, 0))

        self.cpu_dial = Dial(dial_row, "CPU")
        self.cpu_dial.pack(side="left", padx=6, pady=4)

        self.gpu_dial = Dial(dial_row, "GPU")
        self.gpu_dial.pack(side="left", padx=6, pady=4)

        # -------- TEMP + STORAGE --------
        self.temp_bar = TempBar(self, model=self.model)
        self.temp_bar.pack(pady=(6, 2))

        self.storage_bar = StorageBar(self)
        self.storage_bar.pack(pady=(6, 2))

        # -------- VOLTAGE & UPTIME --------
        self.voltage_label = ctk.CTkLabel(self, text="Voltage: -- V")
        self.voltage_label.pack(pady=(8, 2))

        self.uptime_label = ctk.CTkLabel(self, text="Uptime: --")
        self.uptime_label.pack(pady=(0, 8))

    # ---------- UPDATE FROM STATS ----------
    def update_stats(self, stats: dict, uptime: str):
        """
        Update all visual elements from a stats dict:
          stats = {
            "online": bool,
            "cpu": int,
            "gpu": int | None,
            "temp": int,
            "storage_used": int,
            "storage_total": int,
            "voltage": float
          }
        """

        online = stats["online"]
        cpu = stats["cpu"]
        gpu = stats["gpu"]
        temp = stats["temp"]
        used = stats["storage_used"]
        total = stats["storage_total"]
        voltage = stats["voltage"]

        # ------ STATUS LED ------
        if not online:
            self.status_led.set_color("#ff4444", blink=True, fast=False)
        else:
            # If overheated or very high CPU => yellow blinking
            if temp_color(self.model, temp) == "#ff4444" or cpu_color(cpu) == "#ff4444":
                self.status_led.set_color("#ffdd00", blink=True, fast=False)
            else:
                self.status_led.set_color("#00ff88", blink=False, fast=False)

        # ------ CPU / GPU DIALS ------
        self.cpu_dial.set_value(cpu)

        if gpu is None:
            self.gpu_dial.set_value(0)
            self.gpu_dial.label.configure(text="GPU (N/A)")
        else:
            self.gpu_dial.label.configure(text="GPU")
            self.gpu_dial.set_value(gpu)

        # ------ Temperature bar ------
        self.temp_bar.update_temp(temp)

        # ------ Storage bar ------
        self.storage_bar.update_storage(used, total)

        # ------ Voltage ------
        v_color = voltage_color(voltage)
        self.voltage_label.configure(text=f"Voltage: {voltage} V", text_color=v_color)

        # ------ Uptime ------
        self.uptime_label.configure(text=f"Uptime: {uptime}")

    # ---------- SCALING STUB ----------
    def set_scale(self, scale: float):
        """
        Stub kept only so existing calls won't crash
        if we ever reintroduce scaling.
        Currently does nothing to keep UI stable & fast.
        """
        return
