# ---------- COLOR CHOICES FOR ALL METRICS ----------
# These colors match the Armory Crate neon style.


def temp_color(model, temp):
    """Return neon green/yellow/red based on Pi model temperature thresholds."""

    if model == "pi5":
        if temp < 65:
            return "#00ff88"   # green neon
        if temp < 75:
            return "#ffdd00"   # yellow
        return "#ff4444"       # red

    else:  # pi zero 2 w
        if temp < 55:
            return "#00ff88"
        if temp < 65:
            return "#ffdd00"
        return "#ff4444"


def cpu_color(cpu):
    """CPU usage color."""
    if cpu < 60:
        return "#00ff88"
    if cpu < 85:
        return "#ffdd00"
    return "#ff4444"


def gpu_color(gpu):
    """GPU usage color (same threshold as CPU for now)."""
    if gpu is None:
        return "#888888"  # grey for zero 2w or no GPU
    return cpu_color(gpu)


def storage_color(p):
    """Storage % full."""
    if p < 70:
        return "#00ff88"
    if p < 90:
        return "#ffdd00"
    return "#ff4444"


def voltage_color(v):
    """Voltage threshold."""
    if v >= 4.90:
        return "#00ff88"
    if v >= 4.75:
        return "#ffdd00"
    return "#ff4444"
