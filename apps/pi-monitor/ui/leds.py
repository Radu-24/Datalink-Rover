# apps/pi-monitor/ui/leds.py

import customtkinter as ctk


class StatusLED(ctk.CTkCanvas):
    """
    Small circular LED with support for:
    - online / offline state
    - severity levels: "ok", "warn", "error"
    - fast blinking for offline/error
    """

    def __init__(self, master, size: int = 18, fast_blink: bool = True, **kwargs):
        # IMPORTANT: do NOT use bg="transparent" here, Tk doesn't support it.
        super().__init__(
            master,
            width=size,
            height=size,
            highlightthickness=0,
            bd=0,
            **kwargs,
        )

        self.size = size
        self.radius = size // 2 - 1

        # State flags
        self.online = False
        self.fast_blink = fast_blink  # used for offline/error blinking
        self._blink_state = False
        self.current_alpha = 1.0

        # Base colors
        self._color_ok = "#00ff66"     # green
        self._color_warn = "#ffb03b"   # orange
        self._color_error = "#ff3b3b"  # red

        self._current_color = self._color_error  # default: red offline

        # Draw once and keep item id
        self.led_circle = self.create_oval(
            1,
            1,
            self.size - 1,
            self.size - 1,
            fill=self._current_color,
            outline="",
        )

        # Start animation loop
        self.animate()

    # ---------- Public API ----------

    def set_status(self, online: bool, level: str = "ok"):
        """
        Unified method that most callers can use.

        level: "ok", "warn", "error"
        """
        self.online = bool(online)

        if level == "warn":
            self._current_color = self._color_warn
        elif level == "error":
            self._current_color = self._color_error
        else:
            self._current_color = self._color_ok

        # When online, keep LED fully bright and solid.
        # When offline, blinking logic in animate() will handle brightness.
        if self.online:
            self.current_alpha = 1.0
        self._redraw()

    def set_online(self, online: bool):
        """
        Convenience method if caller only knows online/offline.
        """
        # If going offline and no level set, treat as error (red).
        if not online:
            self.set_status(False, "error")
        else:
            self.set_status(True, "ok")

    def set_color(self, hex_color: str):
        """
        Optional: directly set a color (bypasses level mapping).
        """
        self._current_color = hex_color
        self._redraw()

    # ---------- Internal drawing ----------

    def _apply_alpha(self, hex_color: str, alpha: float) -> str:
        """
        Fake alpha by mixing towards black. Tk doesn't support real alpha on fills.
        """
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            return "#" + hex_color

        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
        except ValueError:
            return "#" + hex_color

        r = int(r * alpha)
        g = int(g * alpha)
        b = int(b * alpha)

        return f"#{r:02x}{g:02x}{b:02x}"

    def _redraw(self):
        color = self._apply_alpha(self._current_color, self.current_alpha)
        self.itemconfigure(self.led_circle, fill=color)

    # ---------- Blink animation loop ----------

    def animate(self):
        """
        Blink logic:
        - When online: LED is solid (no blink).
        - When offline (online == False): blink.
          If fast_blink is True, blink faster (used for red error state).
        """
        if not self.online:
            # toggle visible state
            self._blink_state = not self._blink_state

            if self._blink_state:
                # full brightness
                self.current_alpha = 1.0
            else:
                # dimmed
                self.current_alpha = 0.3

            self._redraw()
        else:
            # online -> ensure full brightness
            self.current_alpha = 1.0
            self._redraw()

        # timing: normal blink = 250 ms, fast blink (red offline) = 90 ms
        delay = 250 if not self.fast_blink else 90
        self.after(delay, self.animate)
