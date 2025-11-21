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


# ---------- SIMULATED PI STATS FOR DEBUG/UI DEVELOPMENT ----------
def fake_pi_stats(model: str):
    """
    Generate fake data to test the UI.
    Later this will be replaced by real HTTP requests
    to rpiremote, rpicar, and rpidock.
    """
    return {
        "online": random.choice([True, True, True, False]),  # mostly online
        "cpu": random.randint(1, 100),
        "gpu": random.randint(1, 100) if model == "pi5" else None,
        "temp": random.randint(40, 85),
        "storage_used": random.randint(4, 25),  # GB used
        "storage_total": 32,
        "voltage": round(random.uniform(4.6, 5.2), 2)
    }
