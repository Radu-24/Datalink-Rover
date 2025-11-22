import random


# ---------- UPTIME FORMATTER ----------
def format_uptime(seconds: int) -> str:
    """Convert uptime in seconds to human-readable text."""
    if seconds < 60:
        return f"{seconds}s"

    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"

    hours = minutes // 60
    if hours < 24:
        return f"{hours}h {minutes % 60}m"

    days = hours // 24
    return f"{days}d {hours % 24}h"


# ---------- FAKE STATS (DEMO / OFFLINE) ----------
def fake_pi_stats(model: str):
    """
    Generate fake data to test the UI.
    """
    if model == "pi5":
        gpu_clock = random.randint(300, 900)  # MHz
    else:
        gpu_clock = 0

    return {
        "online": random.choice([True, True, True, False]),  # mostly online
        "cpu": random.randint(1, 100),
        "temp": random.randint(40, 85),
        "ram_percent": random.randint(10, 95),
        "storage_used": random.randint(4, 25),  # GB used
        "storage_total": 32,
        "voltage": round(random.uniform(4.6, 5.2), 2),
        "gpu_clock_mhz": gpu_clock,
    }
