import customtkinter as ctk


class Dial(ctk.CTkFrame):
    """
    Grey donut dial with smooth animation, matching CustomTkinter theme.

    Public API:
      - Dial(parent, "CPU")
      - set_value(percent: float)
      - self.label -> bottom caption ("CPU", "GPU").
    """

    def __init__(self, master, title: str = "CPU", **kwargs):
        super().__init__(master, **kwargs)

        self.current_value = 0.0
        self.target_value = 0.0
        self.animating = False

        self.size = 120
        self.thickness = 16
        pad = self.thickness / 2 + 4

        # ---- Resolve a SINGLE dark background color for canvas ----
        fg_raw = self.cget("fg_color")

        # fg_raw can be:
        #   - ("gray90", "gray13")
        #   - "gray90 gray13"
        #   - single string
        if isinstance(fg_raw, tuple):
            light, dark = fg_raw
        elif isinstance(fg_raw, str):
            parts = fg_raw.split()
            if len(parts) >= 2:
                light, dark = parts[0], parts[1]
            else:
                light = dark = fg_raw
        else:
            light = dark = "#212121"

        mode = ctk.get_appearance_mode()  # "Light" or "Dark"
        bg_color = dark if mode == "Dark" else light

        # Canvas for the donut ring, with theme-matching bg
        self.canvas = ctk.CTkCanvas(
            self,
            width=self.size,
            height=self.size,
            highlightthickness=0,
            bg=bg_color,   # <- ALWAYS a single, valid Tk color
        )
        self.canvas.grid(row=0, column=0, padx=0, pady=(0, 4))

        # Percentage text
        self.value_label = ctk.CTkLabel(
            self,
            text="0%",
            font=("Segoe UI", 18, "bold"),
        )
        self.value_label.grid(row=1, column=0)

        # Caption ("CPU", "GPU")
        self.label = ctk.CTkLabel(
            self,
            text=title,
            font=("Segoe UI", 12),
        )
        self.label.grid(row=2, column=0, pady=(2, 0))

        # Background donut (slightly lighter than card)
        self.bg_oval = self.canvas.create_oval(
            pad,
            pad,
            self.size - pad,
            self.size - pad,
            outline="#333333",
            width=self.thickness,
        )

        # Foreground arc – animated value, grey
        self.fg_arc = self.canvas.create_arc(
            pad,
            pad,
            self.size - pad,
            self.size - pad,
            start=135,         # 135° → 405° (270° sweep)
            extent=0,
            style="arc",
            outline="#888888",
            width=self.thickness,
        )

        self._redraw(0.0)

    # ---------- public API ----------
    def set_value(self, value: float):
        """
        Smoothly animate dial to new value (0..100).
        """
        self.target_value = max(0.0, min(100.0, float(value)))
        if not self.animating:
            self.animating = True
            self._animate_step()

    # ---------- internal helpers ----------
    def _grey_for_value(self, v: float) -> str:
        """
        Keep it grey but slightly brighter with higher value.
        """
        # 0% -> 0x70, 100% -> 0xb0
        base = 0x70 + int(0x40 * (v / 100.0))
        base = max(0x40, min(0xC0, base))
        return f"#{base:02x}{base:02x}{base:02x}"

    def _redraw(self, value: float):
        extent = 270 * (value / 100.0)

        # Update arc sweep and grey shade
        self.canvas.itemconfigure(self.fg_arc, extent=extent)
        self.canvas.itemconfigure(self.fg_arc, outline=self._grey_for_value(value))

        # Text
        self.value_label.configure(text=f"{int(round(value))}%")

    def _animate_step(self):
        diff = self.target_value - self.current_value
        if abs(diff) < 0.3:
            self.current_value = self.target_value
            self._redraw(self.current_value)
            self.animating = False
            return

        self.current_value += diff * 0.3
        self._redraw(self.current_value)
        self.after(30, self._animate_step)  # ~33 fps
