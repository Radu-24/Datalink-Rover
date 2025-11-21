import customtkinter as ctk
from ui.colors import cpu_color, gpu_color, temp_color, storage_color, voltage_color


class PiPWindow(ctk.CTkToplevel):
    """
    Floating Picture-in-Picture window.
    Shows minimal stats for the selected Pi.
    Auto-resizes its content based on window width.
    """

    def __init__(self, master):
        super().__init__(master)

        self.title("PiP – Pi Monitor")
        self.geometry("420x260")
        self.minsize(200, 80)
        self.attributes("-topmost", True)

        self.scale = 1.0

        # Current stats snapshot
        self.current_stats = None
        self.current_uptime = "--"

        # --- Layout Containers ---
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header.pack(fill="x")

        self.name_label = ctk.CTkLabel(
            self.header, text="rpiremote (PiP)", font=("Segoe UI", 15, "bold")
        )
        self.name_label.pack(side="left")

        self.mode_label = ctk.CTkLabel(
            self.header, text="Mode: Large", font=("Segoe UI", 11)
        )
        self.mode_label.pack(side="right")

        # Containers for different modes
        self.large_frame = ctk.CTkFrame(self.main_frame)
        self.medium_frame = ctk.CTkFrame(self.main_frame)
        self.small_frame = ctk.CTkFrame(self.main_frame)

        # --- LARGE MODE WIDGETS (sliders & text) ---
        self.l_cpu = ctk.CTkProgressBar(self.large_frame, width=280, height=16)
        self.l_cpu.pack(pady=(8, 2))
        self.l_cpu_label = ctk.CTkLabel(self.large_frame, text="CPU: -- %")
        self.l_cpu_label.pack()

        self.l_gpu = ctk.CTkProgressBar(self.large_frame, width=280, height=16)
        self.l_gpu.pack(pady=(8, 2))
        self.l_gpu_label = ctk.CTkLabel(self.large_frame, text="GPU: -- % / N/A")
        self.l_gpu_label.pack()

        self.l_temp = ctk.CTkProgressBar(self.large_frame, width=280, height=16)
        self.l_temp.pack(pady=(8, 2))
        self.l_temp_label = ctk.CTkLabel(self.large_frame, text="Temp: -- °C")
        self.l_temp_label.pack()

        self.l_storage = ctk.CTkProgressBar(self.large_frame, width=280, height=16)
        self.l_storage.pack(pady=(8, 2))
        self.l_storage_label = ctk.CTkLabel(self.large_frame, text="Storage: --")
        self.l_storage_label.pack()

        self.l_voltage_label = ctk.CTkLabel(self.large_frame, text="Voltage: -- V")
        self.l_voltage_label.pack(pady=(8, 2))

        self.l_uptime_label = ctk.CTkLabel(self.large_frame, text="Uptime: --")
        self.l_uptime_label.pack(pady=(0, 4))

        # --- MEDIUM MODE WIDGETS (text only) ---
        self.m_cpu = ctk.CTkLabel(self.medium_frame, text="CPU: -- %")
        self.m_cpu.pack(pady=(4, 0))
        self.m_gpu = ctk.CTkLabel(self.medium_frame, text="GPU: -- % / N/A")
        self.m_gpu.pack()
        self.m_temp = ctk.CTkLabel(self.medium_frame, text="Temp: -- °C")
        self.m_temp.pack()
        self.m_storage = ctk.CTkLabel(self.medium_frame, text="Storage: --")
        self.m_storage.pack()
        self.m_voltage = ctk.CTkLabel(self.medium_frame, text="Voltage: -- V")
        self.m_voltage.pack()
        self.m_uptime = ctk.CTkLabel(self.medium_frame, text="Uptime: --")
        self.m_uptime.pack(pady=(0, 4))

        # --- SMALL MODE WIDGET (single line) ---
        self.s_compact = ctk.CTkLabel(self.small_frame, text="CPU --% | -- °C")
        self.s_compact.pack(pady=10)

        # Start in large mode by default
        self.current_mode = None
        self._show_large_mode()

        # React to resize
        self.bind("<Configure>", self.on_resize)

    # ---------- MODE SWITCHING ----------
    def _clear_modes(self):
        for f in (self.large_frame, self.medium_frame, self.small_frame):
            f.pack_forget()

    def _show_large_mode(self):
        self._clear_modes()
        self.large_frame.pack(fill="both", expand=True)
        self.current_mode = "large"
        self.mode_label.configure(text="Mode: Large")

    def _show_medium_mode(self):
        self._clear_modes()
        self.medium_frame.pack(fill="both", expand=True)
        self.current_mode = "medium"
        self.mode_label.configure(text="Mode: Medium")

    def _show_small_mode(self):
        self._clear_modes()
        self.small_frame.pack(fill="both", expand=True)
        self.current_mode = "small"
        self.mode_label.configure(text="Mode: Compact")

    # ---------- RESIZE HANDLER ----------
    def on_resize(self, event):
        width = event.width

        if width >= 380:
            if self.current_mode != "large":
                self._show_large_mode()
        elif width >= 240:
            if self.current_mode != "medium":
                self._show_medium_mode()
        else:
            if self.current_mode != "small":
                self._show_small_mode()

    # ---------- PUBLIC API ----------
    def update_stats(self, stats: dict, uptime: str):
        """
        Update PiP contents with the same stats used by the cards.
        stats keys: cpu, gpu, temp, storage_used, storage_total, voltage
        """
        self.current_stats = stats
        self.current_uptime = uptime

        cpu = stats["cpu"]
        gpu = stats["gpu"]
        temp = stats["temp"]
        used = stats["storage_used"]
        total = stats["storage_total"]
        voltage = stats["voltage"]

        # STORAGE %
        percent = int((used / total) * 100) if total > 0 else 0

        # --- LARGE MODE values ---
        self.l_cpu.set(cpu / 100)
        self.l_cpu.configure(progress_color=cpu_color(cpu))
        self.l_cpu_label.configure(text=f"CPU: {cpu}%")

        if gpu is None:
            self.l_gpu.set(0)
            self.l_gpu.configure(progress_color="#777777")
            self.l_gpu_label.configure(text="GPU: N/A")
        else:
            self.l_gpu.set(gpu / 100)
            self.l_gpu.configure(progress_color=gpu_color(gpu))
            self.l_gpu_label.configure(text=f"GPU: {gpu}%")

        self.l_temp.set(min(temp / 100, 1))
        self.l_temp.configure(progress_color=temp_color("pi5", temp))
        self.l_temp_label.configure(text=f"Temp: {temp} °C")

        self.l_storage.set(percent / 100)
        self.l_storage.configure(progress_color=storage_color(percent))
        self.l_storage_label.configure(text=f"Storage: {used}/{total} GB ({percent}%)")

        self.l_voltage_label.configure(text=f"Voltage: {voltage} V", text_color=voltage_color(voltage))
        self.l_uptime_label.configure(text=f"Uptime: {uptime}")

        # --- MEDIUM MODE values ---
        self.m_cpu.configure(text=f"CPU: {cpu}%")
        self.m_gpu.configure(text="GPU: N/A" if gpu is None else f"GPU: {gpu}%")
        self.m_temp.configure(text=f"Temp: {temp} °C")
        self.m_storage.configure(text=f"Storage: {used}/{total} GB ({percent}%)")
        self.m_voltage.configure(text=f"Voltage: {voltage} V", text_color=voltage_color(voltage))
        self.m_uptime.configure(text=f"Uptime: {uptime}")

        # --- SMALL MODE compact line ---
        self.s_compact.configure(text=f"CPU {cpu}% | {temp} °C")

    def set_name(self, name: str):
        self.name_label.configure(text=f"{name} (PiP)")

    def set_scale(self, scale: float):
        """Optionally adjust fonts based on global scaling."""
        self.scale = scale
        base = max(9, int(13 * scale))
        big = max(11, int(15 * scale))

        self.name_label.configure(font=("Segoe UI", big, "bold"))
        self.mode_label.configure(font=("Segoe UI", max(9, int(11 * scale))))

        # Large mode fonts
        self.l_cpu_label.configure(font=("Segoe UI", base))
        self.l_gpu_label.configure(font=("Segoe UI", base))
        self.l_temp_label.configure(font=("Segoe UI", base))
        self.l_storage_label.configure(font=("Segoe UI", base))
        self.l_voltage_label.configure(font=("Segoe UI", base))
        self.l_uptime_label.configure(font=("Segoe UI", base))

        # Medium mode fonts
        self.m_cpu.configure(font=("Segoe UI", base))
        self.m_gpu.configure(font=("Segoe UI", base))
        self.m_temp.configure(font=("Segoe UI", base))
        self.m_storage.configure(font=("Segoe UI", base))
        self.m_voltage.configure(font=("Segoe UI", base))
        self.m_uptime.configure(font=("Segoe UI", base))

        # Small mode font
        self.s_compact.configure(font=("Segoe UI", base))
