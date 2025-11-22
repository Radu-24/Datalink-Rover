import customtkinter as ctk
from ui.colors import temp_color, cpu_color


class _SmoothBar(ctk.CTkFrame):
    """
    Base class: smooth animated bar from 0..100%.
    Subclasses should implement:
      - _apply_color(percent)
      - _format_label_value(percent)  -> string
    """

    def __init__(self, master, label: str, **kwargs):
        super().__init__(master, **kwargs)

        self.current_value = 0.0
        self.target_value = 0.0

        self.label_left = ctk.CTkLabel(self, text=label)
        self.label_left.pack(anchor="w")

        self.bar = ctk.CTkProgressBar(self)
        self.bar.set(0.0)
        self.bar.pack(fill="x", pady=(2, 0))

        self.label_right = ctk.CTkLabel(self, text="0")
        self.label_right.pack(anchor="e", pady=(2, 0))

        self.after(50, self._smooth_step)

    def _smooth_step(self):
        diff = self.target_value - self.current_value
        self.current_value += diff * 0.25
        if abs(diff) < 0.5:
            self.current_value = self.target_value

        clamped = max(0.0, min(100.0, self.current_value))
        self._apply_bar_value(clamped)

        self.after(50, self._smooth_step)

    def _apply_bar_value(self, percent: float):
        """Update progress + label using subclass logic."""
        # default: 0..100% bar
        self.bar.set(percent / 100.0)
        self._apply_color(percent)
        self.label_right.configure(text=self._format_label_value(percent))

    def _set_target(self, value: float):
        self.target_value = value

    # to be implemented by subclasses
    def _apply_color(self, percent: float):
        raise NotImplementedError

    def _format_label_value(self, percent: float) -> str:
        return f"{percent:.0f}%"


class TempBar(_SmoothBar):
    """
    Temperature bar. We pass real °C into update_temp(),
    and treat that °C value directly on the bar.
    """

    def __init__(self, master, model: str, **kwargs):
        super().__init__(master, label="Temp", **kwargs)
        self.model = model

    def _apply_bar_value(self, temp_c: float):
        # visual range 0..100°C
        clamped = max(0.0, min(100.0, temp_c))
        self.bar.set(clamped / 100.0)
        self._apply_color(clamped)
        self.label_right.configure(text=self._format_label_value(clamped))

    def _apply_color(self, temp_c: float):
        color = temp_color(self.model, temp_c)
        self.bar.configure(progress_color=color)

    def _format_label_value(self, temp_c: float) -> str:
        return f"{temp_c:.0f} °C"

    def update_temp(self, temp_c: float):
        self._set_target(temp_c)


class StorageBar(_SmoothBar):
    """
    Storage bar: shows % used, but we also keep used/total for logic.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, label="Storage", **kwargs)
        self.used = 0.0
        self.total = 1.0

    def _apply_color(self, percent: float):
        if percent < 70:
            color = "#00c853"
        elif percent < 90:
            color = "#ffd600"
        else:
            color = "#ff3d00"
        self.bar.configure(progress_color=color)

    def _format_label_value(self, percent: float) -> str:
        return f"{percent:.0f}%"

    def update_storage(self, used_gb: float, total_gb: float):
        self.used = used_gb
        self.total = max(total_gb, 0.1)
        percent = (self.used / self.total) * 100.0
        self._set_target(percent)


class RamBar(_SmoothBar):
    """
    RAM usage bar, based on percent used.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, label="RAM", **kwargs)

    def _apply_color(self, percent: float):
        color = cpu_color(percent)
        self.bar.configure(progress_color=color)

    def _format_label_value(self, percent: float) -> str:
        return f"{percent:.0f}%"

    def update_ram(self, percent: float):
        self._set_target(max(0.0, min(100.0, float(percent))))


class ClockBar(_SmoothBar):
    """
    GPU clock bar. Internally works with %, but label shows MHz.
    """

    def __init__(self, master, max_mhz: float = 1000.0, **kwargs):
        super().__init__(master, label="GPU clk", **kwargs)
        self.max_mhz = max_mhz

    def _apply_color(self, percent: float):
        # reuse CPU color thresholds (low/med/high)
        color = cpu_color(percent)
        self.bar.configure(progress_color=color)

    def _format_label_value(self, percent: float) -> str:
        mhz = (percent / 100.0) * self.max_mhz
        return f"{mhz:.0f} MHz"

    def update_clock(self, mhz: float):
        if self.max_mhz <= 0:
            percent = 0.0
        else:
            percent = max(0.0, min(100.0, (mhz / self.max_mhz) * 100.0))
        self._set_target(percent)
