import customtkinter as ctk


def fade_in_window(window: ctk.CTk, step: float = 0.05):
    """Simple fade-in animation for the main window."""
    try:
        alpha = window.attributes("-alpha")
    except Exception:
        return

    if alpha < 1.0:
        window.attributes("-alpha", min(1.0, alpha + step))
        window.after(20, lambda: fade_in_window(window, step))
