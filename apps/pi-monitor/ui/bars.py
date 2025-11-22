import customtkinter as ctk
from ui.colors import temp_color  # we reuse your existing color logic if needed


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
        self.animating = False

        self.label_widget = ctk.CTkLabel(
            self,
            text=label,
            font=("Segoe UI", 11),
        )
        self.label_widget.grid(row=0, column=0, sticky="w")

        self.value_label = ctk.CTkLabel(
            self,
            text="--",
            font=("Segoe UI", 11),
        )
        self.value_label.grid(row=0, column=1, padx=(8, 0))

        self.bar = ctk.CTkProgressBar(
            self,
            height=12,
        )
        self.bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        self.columnconfigure(0, weight=1)
        self.bar.set(0.0)

    # ---------- animation ----------
    def _apply_color(self, percent: float):
        pass

    def _format_label_value(self, percent: float) -> str:
        return f"{percent:.0f}%"

    def _update_visuals(self, percent: float):
        self.bar.set(percent / 100.0)
        self._apply_color(percent)
        self.value_label.configure(text=self._format_label_value(percent))

    def _animate_step(self):
        diff = self.target_value - self.current_value
        if abs(diff) < 0.5:
            self.current_value = self.target_value
            self._update_visuals(self.current_value)
            self.animating = False
            return

        self.current_value += diff * 0.3
        self._update_visuals(self.current_value)
        self.after(30, self._animate_step)

    def _set_target(self, percent: float):
        self.target_value = max(0.0, min(100.0, float(percent)))
        if not self.animating:
            self.animating = True
            self._animate_step()


class TempBar(_SmoothBar):
    """
    Temperature bar.
    API expected by PiCard:
      - __init__(..., model="pi5"|"zero2w")
      - update_temp(temp_c: int)
    """

    def __init__(self, master, model: str, **kwargs):
        super().__init__(master, label="Temp", **kwargs)
        self.model = model

    def _apply_color(self, percent: float):
        # We assume percent ~= temp C (0..100). Use your existing temp_color.
        color = temp_color(self.model, percent)
        self.bar.configure(progress_color=color)

    def _format_label_value(self, percent: float) -> str:
        return f"{percent:.0f} °C"

    # public API used by PiCard
    def update_temp(self, temp_c: float):
        # we treat 0..100°C as 0..100%
        self._set_target(temp_c)


class StorageBar(_SmoothBar):
    """
    Storage bar.
    API expected by PiCard:
      - update_storage(used_gb: int, total_gb: int)
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, label="Storage", **kwargs)
        self.used = 0
        self.total = 1

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
