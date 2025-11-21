# DataLink Rover – Pi Monitor App (Code Walkthrough)

This document explains, in plain language, what every part of the Pi Monitor app does,
file by file. It is written so you can *learn* the patterns and then reproduce them
yourself for future projects.

The project layout:

- `main.py`
- `utils.py`
- `scale_engine.py`
- `ui/__init__.py`
- `ui/colors.py`
- `ui/leds.py`
- `ui/dials.py`
- `ui/bars.py`
- `ui/animations.py`
- `ui/pip_window.py`
- `ui/picard.py`


---

## 1. `main.py`

### High-level role

`main.py` is the **entry point** of the app:

- Creates the main window.
- Builds the 3 Pi cards (rpiremote, rpicar, rpidock).
- Starts the update loop that refreshes stats every second.
- Connects the ScaleEngine (for auto-resizing).
- Creates and manages the PiP window.

### Imports

```python
import customtkinter as ctk
from ui.picard import PiCard
from ui.pip_window import PiPWindow
from scale_engine import ScaleEngine
from utils import format_uptime, fake_pi_stats
from ui.animations import fade_in_window
```

- `customtkinter as ctk` – your main GUI toolkit.
- `PiCard` – the widget class that draws one Pi dashboard card.
- `PiPWindow` – the floating mini window with minimal stats.
- `ScaleEngine` – object that reacts to window resize and scales UI.
- `format_uptime` – converts seconds into “1h 23m” style string.
- `fake_pi_stats` – generates fake random stats (until you plug real Pis).
- `fade_in_window` – small helper to animate fade-in at startup.

### Theme

```python
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")
```

- Global theme config – tells CustomTkinter to use dark UI and its dark-blue accent theme.

### Class definition

```python
class PiMonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
```

- `PiMonitorApp` inherits from `ctk.CTk`, which is CustomTkinter’s main window class.
- `super().__init__()` calls the original CTk constructor to create the actual window.

### Window setup

```python
        self.title("DataLink Rover – Pi Monitor")
        self.geometry("1500x850")
        self.minsize(900, 650)
        self.attributes("-alpha", 0)   # fade-in animation
        self.pip = None                # PiP window reference
```

- Set window title.
- Start window at 1500×850.
- Do not allow smaller than 900×650.
- Set transparency (`-alpha`) to 0 so it starts invisible (for fade-in).
- `self.pip` will hold the PiPWindow instance when it exists.

### Scale engine

```python
        self.scale_engine = ScaleEngine(self)
```

- Create a `ScaleEngine` attached to this window.
- The scale engine will observe window size and adjust widget sizes.

### Top bar

```python
        top = ctk.CTkFrame(self, height=60)
        top.pack(side="top", fill="x")
```

- `top` is a frame used as a horizontal bar at the top of the window.
- `pack(side="top", fill="x")` – place it at the top and stretch horizontally.

```python
        title = ctk.CTkLabel(
            top, text="DataLink Rover – Pi Monitor",
            font=("Segoe UI", 28, "bold")
        )
        title.pack(side="left", padx=20, pady=10)
```

- Creates a label with the app title inside the top bar.
- Packs it to the left with some padding.

```python
        pip_btn = ctk.CTkButton(
            top, text="PiP Mode", command=self.open_pip
        )
        pip_btn.pack(side="right", padx=20, pady=10)
```

- A button on the right side to open the PiP window.
- When clicked, runs `self.open_pip`.

### Main content area

```python
        self.main = ctk.CTkFrame(self)
        self.main.pack(fill="both", expand=True, padx=20, pady=20)
```

- `self.main` is the central area holding the 3 cards.
- `fill="both", expand=True` – it grows to use all remaining space.

#### Grid setup

```python
        for col in range(3):
            self.main.grid_columnconfigure(col, weight=1)
        self.main.grid_rowconfigure(0, weight=1)
```

- This configures the internal grid layout:
  - 3 columns with equal weight → they share space evenly.
  - 1 row with weight → row also expands.

### Creating the 3 Pi cards

```python
        self.card_remote = PiCard(self.main, "rpiremote", "Raspberry Pi 5 (Controller)", model="pi5")
        self.card_remote.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
```

- Create PiCard for `rpiremote` with role text and model `"pi5"`.
- Place it at grid row 0, column 0.
- `sticky="nsew"` – make it stretch in all directions within its cell.
- `padx`/`pady` – outer margin.

Same pattern for `rpicar` and `rpidock`:

```python
        self.card_car = PiCard(self.main, "rpicar", "Raspberry Pi 5 (Car)", model="pi5")
        self.card_car.grid(... column=1 ...)

        self.card_dock = PiCard(self.main, "rpidock", "Raspberry Pi Zero 2W", model="zero2w")
        self.card_dock.grid(... column=2 ...)
```

### Startup animation

```python
        self.after(50, lambda: fade_in_window(self))
```

- Schedules `fade_in_window(self)` to run after 50 ms.
- `after` is Tkinter’s method to schedule work later (non-blocking).

### Update loop counter and scheduling

```python
        self.ticks = 0
        self.after(1000, self.update_loop)
```

- `self.ticks` = number of seconds passed (our fake uptime).
- `after(1000, self.update_loop)` – call `update_loop` in 1000 ms (1 second).

### Bind resize event for scaling

```python
        self.bind("<Configure>", self.scale_engine.on_resize)
```

- `<Configure>` fires when the window is resized.
- We pass that event into `scale_engine.on_resize`.

### The update loop

```python
    def update_loop(self):
        """Update each Pi card every second."""
        self.ticks += 1
        uptime_str = format_uptime(self.ticks)
```

- Add 1 second to our tick counter.
- Convert ticks to text (e.g. `"1m"`, `"2h 3m"`).

```python
        r_stats = fake_pi_stats("pi5")
        c_stats = fake_pi_stats("pi5")
        d_stats = fake_pi_stats("zero2w")
```

- Generate fake stats for each Pi model (just for UI testing).
- Later this will be replaced by real data fetch.

```python
        self.card_remote.update_stats(r_stats, uptime_str)
        self.card_car.update_stats(c_stats, uptime_str)
        self.card_dock.update_stats(d_stats, uptime_str)
```

- Push each stats dict into the corresponding `PiCard`.
- The card itself updates its dials, bars, labels, LED.

```python
        if self.pip is not None:
            self.pip.update_stats(r_stats, uptime_str)
```

- If PiP window exists, update it with the same stats (right now using remote stats as example).

```python
        self.after(1000, self.update_loop)
```

- Reschedule itself to run again after 1 second → infinite refresh loop.

### PiP handler

```python
    def open_pip(self):
        if self.pip is None or not self.pip.winfo_exists():
            self.pip = PiPWindow(self)
        else:
            self.pip.focus()
```

- If PiP does not exist (or was closed), create a new `PiPWindow`.
- If it exists, just bring it to front.

### App entry-point

```python
if __name__ == "__main__":
    app = PiMonitorApp()
    app.mainloop()
```

- Standard Python GUI boilerplate.
- Creates a `PiMonitorApp` instance and enters its event loop.

---

## 2. `utils.py`

### Purpose

- Keep small helper functions unrelated to UI layout.
- Currently has:
  - Uptime formatter.
  - Fake stats generator.

The logic of `format_uptime`:

1. If `<60` sec → `"Xs"`.
2. Else convert to minutes.
3. If `<60` min → `"Xm"`.
4. Else convert to hours.
5. If `<24` hours → `"Xh Ym"`.
6. Else show days and remaining hours.

`fake_pi_stats(model)`:

- Returns a dict with keys: `online`, `cpu`, `gpu`, `temp`, `storage_used`, `storage_total`, `voltage`.
- Uses `random` to simulate realistic ranges.
- For `"pi5"` it returns GPU usage; for `"zero2w"` GPU is `None`.

Meant for **UI testing** before wiring real SSH/HTTP.

---

## 3. `scale_engine.py`

Key ideas:

- Stores `base_width` and `base_height`.
- Computes `w_ratio` and `h_ratio` from current size vs base.
- Uses smaller of the two ratios as `raw_scale`. This keeps aspect ratio reasonable.
- Clamps to `[0.70, 1.30]` to avoid crazy scaling.
- Calls `.set_scale(self.scale)` on each `PiCard` and `PiPWindow`.

You don’t need to remember the exact math – just understand:
> “When the window gets bigger or smaller, we compute a scaling factor and tell each widget to adapt.”

---

## 4. `ui/colors.py`

All functions here return a color string like `"#00ff88"` based on thresholds.

Important idea:

- **Single source of truth** for visual thresholds.
- If you ever want to change “what is considered HOT CPU temperature”, you do it in one place instead of hunting through 10 files.

---

## 5. `ui/leds.py`, `ui/dials.py`, `ui/bars.py`, `ui/animations.py`, `ui/pip_window.py`, `ui/picard.py`

You already saw their roles while coding. The key patterns to learn are:

### a) Custom widget pattern

Every custom widget (LED, Dial, TempBar, StorageBar, PiCard, PiPWindow):

- Inherits from `ctk.CTkFrame` or `ctk.CTkToplevel`.
- Creates child widgets in `__init__`.
- Public methods:
  - `update_xxx(...)` – to refresh its state.
  - `set_scale(scale)` – to react to global scaling.
- Often has an internal `draw()` method for Canvas-based rendering.

### b) Composition

`PiCard` is composed from:

- `StatusLED`
- Two `Dial` widgets
- `TempBar`
- `StorageBar`
- Two labels

You didn’t hard-code CPU/GPU drawing in `PiCard` – you delegate to `Dial`.
This is “composition” and is the core of UI architecture.

### c) Adaptive layout

`PiPWindow` shows how to:

- Use multiple frames for different “modes”.
- Show/hide frames depending on window width.
- Reuse the same stats for all three modes (only layout changes).

This exact pattern can be reused to build responsive components in Tkinter.

---

# How to Learn This For Real (Plan)

Here is a concrete learning path you can follow:

## Step 1 — Re-read this doc with the project open

Have VS Code on the left, this doc on the right.
Jump file-by-file and match explanations to real code.

## Step 2 — Small exercises

1. Change colors in `ui/colors.py` and see instant effect.
2. Increase dial size in `ui/dials.py` by modifying `self.size` default.
3. Change the threshold in `temp_color` so red triggers earlier and see LED behavior change.

## Step 3 — Write your own mini-component

Example: a “NetworkSpeedBar”:

- A CTkFrame with:
  - CTkProgressBar.
  - Label “Net: 12 Mbps”.
- `update_speed(mbps)` method.
- `set_scale(scale)` method.

You can add it to `PiCard` under Storage.

## Step 4 — Rebuild one widget from scratch

Pick one of:

- `TempBar`
- `StorageBar`
- `Dial`

Delete it and try to re-implement it looking only at how it behaves in the app, not copying code.
Then compare with original and adjust.

## Step 5 — Apply patterns to a new project

Make a new repo `pc-monitor`:

- Similar layout: main.py, ui/ components.
- Use the same ideas but different metrics (local PC CPU, RAM, etc. via psutil).

Once you do that, this style of coding won’t look “new” anymore – it will be *your* pattern.

