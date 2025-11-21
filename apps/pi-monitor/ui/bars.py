import customtkinter as ctk
from ui.colors import temp_color, storage_color


class TempBar(ctk.CTkFrame):
    """
    Premium temperature bar.
    Uses a CTkProgressBar + label + dynamic colors.
    """

    def __init__(self, parent, model: str):
        super().__init__(parent, corner_radius=12)
        self.model = model
        self.scale = 1.0

        self.progress = ctk.CTkProgressBar(self, width=260, height=18)
        self.progress.pack(padx=10, pady=(8, 4))
        self.progress.set(0)

        self.label = ctk.CTkLabel(self, text="Temp: -- °C", font=("Segoe UI", 13))
        self.label.pack(pady=(0, 6))

    def update_temp(self, temp: int):
        self.label.configure(text=f"Temp: {temp} °C")
        color = temp_color(self.model, temp)
        self.progress.configure(progress_color=color)
        self.progress.set(min(temp / 100, 1))

    def set_scale(self, scale: float):
        self.scale = scale
        width = max(180, int(260 * scale))
        height = max(12, int(18 * scale))
        self.progress.configure(width=width, height=height)
        self.label.configure(font=("Segoe UI", max(10, int(13 * scale))))


class StorageBar(ctk.CTkFrame):
    """
    Storage "used" bar with text.
    Shows used/total and percentage, color-coded.
    """

    def __init__(self, parent):
        super().__init__(parent, corner_radius=12)
        self.scale = 1.0

        self.progress = ctk.CTkProgressBar(self, width=260, height=18)
        self.progress.pack(padx=10, pady=(8, 4))
        self.progress.set(0)

        self.label = ctk.CTkLabel(self, text="Storage: --", font=("Segoe UI", 13))
        self.label.pack(pady=(0, 6))

    def update_storage(self, used_gb: int, total_gb: int):
        if total_gb <= 0:
            self.progress.set(0)
            self.label.configure(text="Storage: N/A")
            return

        percent = int((used_gb / total_gb) * 100)
        color = storage_color(percent)
        self.progress.configure(progress_color=color)
        self.progress.set(percent / 100)

        self.label.configure(
            text=f"Storage: {used_gb} / {total_gb} GB ({percent}%)"
        )

    def set_scale(self, scale: float):
        self.scale = scale
        width = max(180, int(260 * scale))
        height = max(12, int(18 * scale))
        self.progress.configure(width=width, height=height)
        self.label.configure(font=("Segoe UI", max(10, int(13 * scale))))
