import customtkinter as ctk
from ui.colors import cpu_color, gpu_color


class Dial(ctk.CTkFrame):
    """
    Premium circular dial used for CPU/GPU.
    Auto-resizes and redraws on scale changes.
    """

    def __init__(self, parent, label_text):
        super().__init__(parent, corner_radius=12)

        self.label_text = label_text
        self.value = 0
        self.size = 150  # will scale dynamically

        # Canvas for drawing dial
        self.canvas = ctk.CTkCanvas(
            self, width=self.size, height=self.size,
            bg="#000000",
            highlightthickness=0
        )
        self.canvas.pack(pady=5)

        # Label under dial
        self.label = ctk.CTkLabel(self, text=label_text, font=("Segoe UI", 14))
        self.label.pack()

        self.draw()

    # ---------- VALUE SETTER ----------
    def set_value(self, val):
        """Set CPU/GPU percent and redraw dial."""
        self.value = max(0, min(100, int(val)))
        self.draw()

    # ---------- DRAWING ----------
    def draw(self):
        """Draw the neon circular dial."""
        self.canvas.delete("all")

        radius = self.size - 10
        cx = cy = self.size / 2

        # Background arc (dark gray)
        self.canvas.create_oval(
            5, 5, radius, radius,
            outline="#333333",
            width=int(10 * (self.size / 150))
        )

        # Determine color (CPU/GPU logic handled here)
        if self.label_text.lower() == "gpu" and self.value == 0:
            # GPU might be unavailable (Zero 2 W)
            arc_color = "#777777"
        else:
            arc_color = gpu_color(self.value) if self.label_text.lower() == "gpu" else cpu_color(self.value)

        # Actual arc extent
        extent = (self.value / 100) * 360

        # Neon arc
        self.canvas.create_arc(
            5, 5, radius, radius,
            start=90,
            extent=-extent,
            outline=arc_color,
            width=int(10 * (self.size / 150)),
            style="arc"
        )

        # Percentage text
        self.canvas.create_text(
            cx, cy,
            text=f"{self.value}%",
            fill="white",
            font=("Segoe UI", int(18 * (self.size / 150)), "bold")
        )

    # ---------- SCALING ----------
    def set_scale(self, scale):
        """Resize dial smoothly according to scale factor."""
        new_size = max(100, int(150 * scale))
        if new_size != self.size:
            self.size = new_size
            self.canvas.config(width=self.size, height=self.size)
            self.draw()
