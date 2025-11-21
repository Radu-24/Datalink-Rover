import random
import customtkinter as ctk

# ------------------- THEME SETTINGS -------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


# ------------------- PiCard WIDGET --------------------
class PiCard(ctk.CTkFrame):
    """A visual tile/card that displays the status of one Raspberry Pi."""

    def __init__(self, parent, name: str, role: str):
        super().__init__(parent, corner_radius=12)

        self.name = name
        self.role = role

        # Pi name (big)
        self.label_name = ctk.CTkLabel(
            self,
            text=name,
            font=("Segoe UI", 18, "bold")
        )
        self.label_name.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))

        # Pi role (smaller)
        self.label_role = ctk.CTkLabel(
            self,
            text=role,
            font=("Segoe UI", 12)
        )
        self.label_role.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 10))

        # Online/Offline status
        self.label_online = ctk.CTkLabel(
            self,
            text="Status: OFFLINE",
            font=("Segoe UI", 12),
            text_color="red"
        )
        self.label_online.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 10))

        # Stat placeholders
        self.label_cpu = ctk.CTkLabel(self, text="CPU: -- %")
        self.label_cpu.grid(row=3, column=0, sticky="w", padx=10, pady=2)

        self.label_ram = ctk.CTkLabel(self, text="RAM: -- %")
        self.label_ram.grid(row=4, column=0, sticky="w", padx=10, pady=2)

        self.label_temp = ctk.CTkLabel(self, text="Temp: -- °C")
        self.label_temp.grid(row=5, column=0, sticky="w", padx=10, pady=2)

        self.label_storage = ctk.CTkLabel(self, text="Storage: -- %")
        self.label_storage.grid(row=6, column=0, sticky="w", padx=10, pady=2)

        self.label_uptime = ctk.CTkLabel(self, text="Uptime: --")
        self.label_uptime.grid(row=7, column=0, sticky="w", padx=10, pady=(2, 10))

        # Let card stretch nicely
        self.grid_rowconfigure(8, weight=1)
        self.grid_columnconfigure(0, weight=1)

    # ------ FUNCTION TO UPDATE ONE CARD ------
    def update_status(self, online: bool, cpu: int, ram: int, temp: int, storage: int, uptime: str):

        if online:
            self.label_online.configure(text="Status: ONLINE", text_color="green")
        else:
            self.label_online.configure(text="Status: OFFLINE", text_color="red")

        self.label_cpu.configure(text=f"CPU: {cpu} %")
        self.label_ram.configure(text=f"RAM: {ram} %")
        self.label_temp.configure(text=f"Temp: {temp} °C")
        self.label_storage.configure(text=f"Storage: {storage} %")
        self.label_uptime.configure(text=f"Uptime: {uptime}")


# ------------------- MAIN APP WINDOW --------------------
class PiMonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window
        self.title("DataLink Rover – Pi Monitor")
        self.geometry("1000x600")
        self.minsize(900, 500)

        # ------------------- TOP BAR -------------------
        self.top_bar = ctk.CTkFrame(self, height=60)
        self.top_bar.pack(side="top", fill="x")

        self.title_label = ctk.CTkLabel(
            self.top_bar,
            text="DataLink Rover – Pi Monitor",
            font=("Segoe UI", 22, "bold")
        )
        self.title_label.pack(side="left", padx=20, pady=10)

        self.net_button = ctk.CTkButton(
            self.top_bar,
            text="Rover Network",
            command=self.on_config
        )
        self.net_button.pack(side="right", padx=20, pady=10)

        # ------------------- MAIN AREA -------------------
        self.main_area = ctk.CTkFrame(self)
        self.main_area.pack(fill="both", expand=True, padx=20, pady=20)

        # 1 row, 3 columns
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(1, weight=1)
        self.main_area.grid_columnconfigure(2, weight=1)

        # Three Pi cards
        self.card_remote = PiCard(self.main_area, "rpiremote", "Remote / Controller")
        self.card_remote.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.card_car = PiCard(self.main_area, "rpicar", "Car")
        self.card_car.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.card_dock = PiCard(self.main_area, "rpidock", "Docking Station")
        self.card_dock.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)

        # Fake uptime counter
        self.ticks = 0

        # Start update loop (every 1 sec)
        self.after(1000, self.update_loop)

    def on_config(self):
        # Will become your slide-out animation menu later
        print("Rover Network button clicked")

    # ------------------- AUTO-REFRESH LOOP -------------------
    def update_loop(self):

        self.ticks += 1
        uptime_str = f"{self.ticks} s"

        def fake_stats():
            cpu = random.randint(1, 100)
            ram = random.randint(1, 100)
            temp = random.randint(35, 80)
            storage = random.randint(10, 90)
            online = random.choice([True, True, True, False])
            return online, cpu, ram, temp, storage

        # Update each card
        r_on, r_cpu, r_ram, r_temp, r_storage = fake_stats()
        self.card_remote.update_status(r_on, r_cpu, r_ram, r_temp, r_storage, uptime_str)

        c_on, c_cpu, c_ram, c_temp, c_storage = fake_stats()
        self.card_car.update_status(c_on, c_cpu, c_ram, c_temp, c_storage, uptime_str)

        d_on, d_cpu, d_ram, d_temp, d_storage = fake_stats()
        self.card_dock.update_status(d_on, d_cpu, d_ram, d_temp, d_storage, uptime_str)

        # Call this method again in 1 second
        self.after(1000, self.update_loop)


# ------------------- RUN APP -------------------
if __name__ == "__main__":
    app = PiMonitorApp()
    app.mainloop()
