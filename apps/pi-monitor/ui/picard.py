import customtkinter as ctk
from ui.dials import Dial
from ui.bars import TempBar, StorageBar, RamBar, ClockBar
from ui.leds import StatusLED
from ui.colors import voltage_color, temp_color, cpu_color


class PiCard(ctk.CTkFrame):
    """
    Main widget representing one Raspberry Pi.
    Contains:
      - header (name, role, status LED)
      - CPU dial
      - right column: Temp + GPU clock bars (in place of old GPU dial)
      - RAM bar
      - Storage bar
      - Voltage label
      - Uptime label
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

        # -------- TOP ROW: CPU DIAL + TEMP/CLOCK BOX --------
        dial_row = ctk.CTkFrame(self, fg_color="transparent")
        dial_row.pack(fill="x", padx=6, pady=(4, 2))

        self.cpu_dial = Dial(dial_row, "CPU")
        self.cpu_dial.pack(side="left", padx=6, pady=4)

        right_box = ctk.CTkFrame(dial_row, fg_color="transparent")
        right_box.pack(side="left", fill="both", expand=True, padx=6, pady=4)

        self.temp_bar = TempBar(right_box, model=self.model)
        self.temp_bar.pack(fill="x", pady=(0, 4))

        self.clock_bar = ClockBar(right_box, max_mhz=1000.0)
        self.clock_bar.pack(fill="x", pady=(0, 0))

        # -------- RAM + STORAGE --------
        self.ram_bar = RamBar(self)
        self.ram_bar.pack(fill="x", padx=6, pady=(4, 2))

        self.storage_bar = StorageBar(self)
        self.storage_bar.pack(fill="x", padx=6, pady=(2, 4))

        # -------- VOLTAGE & UPTIME --------
        self.voltage_label = ctk.CTkLabel(self, text="Voltage: -- V")
        self.voltage_label.pack(pady=(6, 2))

        self.uptime_label = ctk.CTkLabel(self, text="Uptime: --")
        self.uptime_label.pack(pady=(0, 8))

    # ---------- UPDATE FROM STATS ----------
    def update_stats(self, stats: dict, uptime: str):
        """
        stats dict is expected to contain:
          online         -> bool
          cpu            -> int 0..100
          temp           -> float (°C)
          ram_percent    -> int 0..100
          storage_used   -> numeric (same unit as total)
          storage_total  -> numeric
          voltage        -> float (V)
          gpu_clock_mhz  -> float (MHz)
        """
        online = stats.get("online", False)
        cpu = stats.get("cpu", 0)
        temp = stats.get("temp", 0.0)
        ram_percent = stats.get("ram_percent", 0)
        used = stats.get("storage_used", 0)
        total = stats.get("storage_total", 32)
        voltage = stats.get("voltage", 5.0)
        gpu_clock_mhz = stats.get("gpu_clock_mhz", 0.0)

        # ------ Status LED logic ------
        if not online:
            self.status_led.set_color("#ff4444", blink=True, fast=True)
        else:
            if temp_color(self.model, temp) == "#ff4444" or cpu_color(cpu) == "#ff4444":
                self.status_led.set_color("#ffdd00", blink=True, fast=False)
            else:
                self.status_led.set_color("#00ff88", blink=False, fast=False)

        # ------ CPU DIAL ------
        self.cpu_dial.set_value(cpu)

        # ------ Temperature + Clock bars ------
        self.temp_bar.update_temp(temp)
        self.clock_bar.update_clock(gpu_clock_mhz)

        # ------ RAM + Storage ------
        self.ram_bar.update_ram(ram_percent)
        self.storage_bar.update_storage(used, total)

        # ------ Voltage ------
        v_color = voltage_color(voltage)
        self.voltage_label.configure(text=f"Voltage: {voltage} V", text_color=v_color)

        # ------ Uptime ------
        self.uptime_label.configure(text=f"Uptime: {uptime}")

    # kept for compatibility, does nothing right now
    def set_scale(self, scale: float):
        return
