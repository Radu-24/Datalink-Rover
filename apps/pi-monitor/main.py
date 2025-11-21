import customtkinter as ctk
from ui.picard import PiCard
from ui.pip_window import PiPWindow
from utils import format_uptime, fake_pi_stats
from ui.animations import fade_in_window

# --- Global Theme ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class PiMonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("DataLink Rover – Pi Monitor")
        # Start big enough to comfortably fit 3 full cards with big dials
        self.geometry("800x500")
        # Do NOT allow smaller than this, or things will necessarily overlap / be cut
        self.minsize(650, 475)

        self.attributes("-alpha", 0)   # fade-in animation
        self.pip = None                # PiP window reference

        # ---------------- TOP BAR ----------------
        top = ctk.CTkFrame(self, height=60)
        top.pack(side="top", fill="x")

        title = ctk.CTkLabel(
            top, text="DataLink Rover – Pi Monitor",
            font=("Segoe UI", 28, "bold")
        )
        title.pack(side="left", padx=20, pady=10)

        pip_btn = ctk.CTkButton(
            top, text="PiP Mode", command=self.open_pip
        )
        pip_btn.pack(side="right", padx=20, pady=10)

        # ---------------- MAIN AREA ----------------
        self.main = ctk.CTkFrame(self)
        self.main.pack(fill="both", expand=True, padx=20, pady=20)

        # 3 equal columns, one row
        for col in range(3):
            self.main.grid_columnconfigure(col, weight=1)
        self.main.grid_rowconfigure(0, weight=1)

        # ---------------- CREATE 3 CARDS ----------------
        self.card_remote = PiCard(self.main, "rpiremote", "RPi 5 (Controller)", model="pi5")
        self.card_remote.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        self.card_car = PiCard(self.main, "rpicar", "Raspberry Pi 5 (Car)", model="pi5")
        self.card_car.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)

        self.card_dock = PiCard(self.main, "rpidock", "Raspberry Pi Zero 2W", model="zero2w")
        self.card_dock.grid(row=0, column=2, sticky="nsew", padx=15, pady=15)

        # Startup Animation
        self.after(50, lambda: fade_in_window(self))

        # Update loop
        self.ticks = 0
        self.after(1000, self.update_loop)

    # ---------------- UPDATE LOOP ----------------
    def update_loop(self):
        """Update each Pi card every second."""
        self.ticks += 1
        uptime_str = format_uptime(self.ticks)

        r_stats = fake_pi_stats("pi5")
        c_stats = fake_pi_stats("pi5")
        d_stats = fake_pi_stats("zero2w")

        self.card_remote.update_stats(r_stats, uptime_str)
        self.card_car.update_stats(c_stats, uptime_str)
        self.card_dock.update_stats(d_stats, uptime_str)

        # update PiP if open (for now using rpiremote stats)
        if self.pip is not None and self.pip.winfo_exists():
            self.pip.update_stats(r_stats, uptime_str)

        self.after(1000, self.update_loop)

    # ---------------- OPEN PIP WINDOW ----------------
    def open_pip(self):
        if self.pip is None or not self.pip.winfo_exists():
            self.pip = PiPWindow(self)
        else:
            self.pip.focus()


if __name__ == "__main__":
    app = PiMonitorApp()
    app.mainloop()
