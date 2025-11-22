import customtkinter as ctk
import paramiko
import threading
import re
import time

# ------------------- THEME SETTINGS -------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


# ------------------- SSH DATA FUNCTION -------------------
def get_pi_stats_via_ssh(host, user="radu", password="raduboss2004", timeout=3):
    stats = {
        "online": False,
        "cpu": 0,
        "ram": 0,
        "temp": 0,
        "storage": 0,
        "uptime": "N/A"
    }

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=timeout)

        stats["online"] = True

        # --- TEMP ---
        stdin, stdout, _ = client.exec_command("vcgencmd measure_temp")
        out = stdout.read().decode().strip()
        m = re.search(r"temp=([0-9.]+)", out)
        if m:
            stats["temp"] = float(m.group(1))

        # --- CPU LOAD ---
        stdin, stdout, _ = client.exec_command("top -bn1 | grep load")
        load_str = stdout.read().decode().strip()
        m = re.search(r"load average: ([0-9.]+)", load_str)
        if m:
            stats["cpu"] = int(float(m.group(1)) * 25)  # approx → convert load to %

        # --- RAM ---
        stdin, stdout, _ = client.exec_command("free -m")
        lines = stdout.read().decode().splitlines()
        if len(lines) >= 2:
            parts = lines[1].split()
            total_ram = int(parts[1])
            used_ram = int(parts[2])
            stats["ram"] = int((used_ram / total_ram) * 100)

        # --- STORAGE ---
        stdin, stdout, _ = client.exec_command("df -h / | tail -1")
        parts = stdout.read().decode().split()
        if len(parts) >= 5:
            used = parts[2]
            total = parts[1]
            percent = parts[4].replace("%", "")
            stats["storage"] = int(percent)

        # --- UPTIME ---
        stdin, stdout, _ = client.exec_command("uptime -p")
        stats["uptime"] = stdout.read().decode().strip()

        client.close()

    except:
        pass

    return stats


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

        self.grid_rowconfigure(8, weight=1)
        self.grid_columnconfigure(0, weight=1)

    # Update card
    def update_status(self, stats):
        if stats["online"]:
            self.label_online.configure(text="Status: ONLINE", text_color="green")
        else:
            self.label_online.configure(text="Status: OFFLINE", text_color="red")

        self.label_cpu.configure(text=f"CPU: {stats['cpu']} %")
        self.label_ram.configure(text=f"RAM: {stats['ram']} %")
        self.label_temp.configure(text=f"Temp: {stats['temp']} °C")
        self.label_storage.configure(text=f"Storage: {stats['storage']} %")
        self.label_uptime.configure(text=f"Uptime: {stats['uptime']}")


# ------------------- MAIN APP WINDOW --------------------
class PiMonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

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

        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(1, weight=1)
        self.main_area.grid_columnconfigure(2, weight=1)

        # Pi cards
        self.card_remote = PiCard(self.main_area, "rpiremote", "Remote / Controller")
        self.card_remote.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.card_car = PiCard(self.main_area, "rpicar", "Car")
        self.card_car.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.card_dock = PiCard(self.main_area, "rpidock", "Docking Station")
        self.card_dock.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)

        # Start threaded update loop
        self.after(1000, self.threaded_update)

    def on_config(self):
        print("Rover Network button clicked")

    # ------------------- THREADED REFRESH -------------------
    def threaded_update(self):
        threading.Thread(target=self.update_loop, daemon=True).start()
        self.after(2000, self.threaded_update)  # refresh every 2 sec

    # ------------------- UPDATE LOOP -------------------
    def update_loop(self):

        # Real stats:
        rpiremote_stats = get_pi_stats_via_ssh("10.0.0.1")
        rpidock_stats   = get_pi_stats_via_ssh("10.0.1.5")

        # Car stats (not implemented yet → offline)
        rpicar_stats = {
            "online": False,
            "cpu": 0,
            "ram": 0,
            "temp": 0,
            "storage": 0,
            "uptime": "N/A"
        }

        self.card_remote.update_status(rpiremote_stats)
        self.card_dock.update_status(rpidock_stats)
        self.card_car.update_status(rpicar_stats)


# ------------------- RUN APP -------------------
if __name__ == "__main__":
    app = PiMonitorApp()
    app.mainloop()
