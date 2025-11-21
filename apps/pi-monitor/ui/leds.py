import customtkinter as ctk


class StatusLED(ctk.CTkFrame):
    """
    Neon status LED with pulsing / blinking behavior.
    Auto-resizes using set_scale().
    """

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        # Canvas for drawing LED
        self.canvas = ctk.CTkCanvas(
            self, width=22, height=22,
            bg="#000000",  # dark background
            highlightthickness=0
        )
        self.canvas.pack()

        self.color = "#00ff88"   # default neon green
        self.blinking = False
        self.fast_blink = False

        self.size = 22   # will scale dynamically

        self.draw()

    # ---------- DRAW LED ----------
    def draw(self):
        self.canvas.delete("all")

        # Glow shadow (outer circle)
        self.canvas.create_oval(
            2, 2, self.size, self.size,
            fill=self._dim_color(self.color, 0.25),
            outline=""
        )

        # Main LED circle
        self.canvas.create_oval(
            4, 4, self.size - 2, self.size - 2,
            fill=self.color,
            outline=""
        )

    # ---------- SET COLOR ----------
    def set_color(self, color, blink=False, fast=False):
        self.color = color
        self.blinking = blink
        self.fast_blink = fast
        self.draw()

    # ---------- BLINK ANIMATION ----------
    def animate(self):
        if self.blinking:
            # Toggle visibility by dimming LED
            if self.fast_blink:
                self.color = self._dim_color(self.color, 0.4)
            else:
                self.color = self._dim_color(self.color, 0.7)

            self.draw()

        # Schedule next frame
        self.after(250 if not self.fast_blink else 120, self.animate)

    # ---------- UTILITY: DIM COLOR ----------
    def _dim_color(self, hex_color, factor):
        """Fade a hex color by factor (0–1)."""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)

        return f"#{r:02x}{g:02x}{b:02x}"

    # ---------- SCALING ----------
    def set_scale(self, scale):
        new_size = max(14, int(22 * scale))
        if new_size != self.size:
            self.size = new_size
            self.canvas.config(width=self.size, height=self.size)
            self.draw()
