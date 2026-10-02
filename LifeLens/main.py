"""
LifeLens - Interactive Multimedia Personal Journal (Retro + 5 Personality Themes)
Main Application Controller
"""

import sys
import os
import tkinter as tk
from tkinter import ttk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import time
from data_manager import (
    PERSONALITY_THEMES,
    get_active_personality,
    set_active_personality,
    load_entries,
    ensure_data_directories,
)
from media_manager import (
    create_sample_visual_assets,
    AmbientAudioManager,
    PetCompanionManager,
)
from dashboard import (
    DashboardScreen,
    NewEntryScreen,
    TimelineScreen,
    InsightsScreen,
    AboutScreen,
    FONT_MONO,
)


class LifeLensApp(tk.Tk):
    """LifeLens Application Controller with 5 Dynamic Personality Themes."""

    def __init__(self):
        super().__init__()
        
        # Load Personality Theme
        self.active_personality = get_active_personality()
        
        self.title(f"LifeLens ★ {self.theme['name']} 8-Bit Journal")
        self.geometry("1140x750")
        self.minsize(980, 640)
        self.configure(bg=self.theme["bg_main"])
        self._center_window(1140, 750)

        # Initialize Storage & Assets
        ensure_data_directories()
        create_sample_visual_assets()
        load_entries()
        self.ambient_manager = AmbientAudioManager()
        self.pet_manager = PetCompanionManager(target_height=36)

        self._configure_styles()

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        self._build_sidebar()
        self._build_content_area()
        self._build_pet_runner()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.navigate_to("dashboard")

    @property
    def theme(self):
        return PERSONALITY_THEMES.get(self.active_personality, PERSONALITY_THEMES["Cyber Gamer"])

    def _center_window(self, width, height):
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, int((screen_w - width) / 2))
        y = max(0, int((screen_h - height) / 2) - 20)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _configure_styles(self):
        t = self.theme
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("Retro.TFrame", background=t["bg_main"])
        
        style.configure(
            "TCombobox",
            fieldbackground=t["bg_inner"],
            background=t["bg_card"],
            foreground=t["text_main"],
            arrowcolor=t["accent_primary"],
            padding=4
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", t["bg_inner"])],
            foreground=[("readonly", t["text_main"])]
        )

        style.configure(
            "Vertical.TScrollbar",
            background=t["bg_card"],
            troughcolor=t["bg_main"],
            borderwidth=1,
            relief="solid",
            arrowsize=11
        )

        style.configure(
            "Horizontal.TScale",
            troughcolor=t["bg_inner"],
            background=t["accent_primary"]
        )

    def _build_sidebar(self):
        t = self.theme
        self.sidebar = tk.Frame(self, bg=t["bg_sidebar"], width=230, bd=2, relief="ridge")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.pack_propagate(False)

        # Branding
        self.brand_frame = tk.Frame(self.sidebar, bg=t["bg_sidebar"], padx=14, pady=18)
        self.brand_frame.pack(fill="x")

        self.logo_lbl = tk.Label(
            self.brand_frame,
            text=f"★ LIFELENS ★",
            font=(FONT_MONO, 14, "bold"),
            fg=t["accent_primary"],
            bg=t["bg_sidebar"]
        )
        self.logo_lbl.pack(anchor="w")

        self.archetype_lbl = tk.Label(
            self.brand_frame,
            text=f"{t['emoji']} {t['name'].upper()}",
            font=(FONT_MONO, 8, "bold"),
            fg=t["accent_gold"],
            bg=t["bg_sidebar"]
        )
        self.archetype_lbl.pack(anchor="w", pady=(2, 0))

        # Divider
        self.div = tk.Frame(self.sidebar, bg=t["border"], height=2)
        self.div.pack(fill="x", padx=10, pady=(0, 12))

        # Nav Buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "▶ DASHBOARD"),
            ("new_entry", "▶ NEW ENTRY"),
            ("timeline", "▶ TIMELINE"),
            ("insights", "▶ INSIGHTS"),
            ("about", "▶ SPECS / THEMES")
        ]

        self.nav_frame = tk.Frame(self.sidebar, bg=t["bg_sidebar"])
        self.nav_frame.pack(fill="x", padx=8)

        for screen_key, label_text in nav_items:
            btn = tk.Button(
                self.nav_frame,
                text=label_text,
                font=(FONT_MONO, 9, "bold"),
                bg=t["bg_sidebar"],
                fg=t["text_muted"],
                activebackground=t["bg_inner"],
                activeforeground=t["accent_primary"],
                relief="flat",
                bd=0,
                padx=10,
                pady=8,
                anchor="w",
                cursor="hand2",
                command=lambda k=screen_key: self.navigate_to(k)
            )
            btn.pack(fill="x", pady=2)
            self._add_hover_effect(btn, screen_key)
            self.nav_buttons[screen_key] = btn

        # Sidebar Personality Theme Selector Box
        self.pers_sidebar_frame = tk.Frame(self.sidebar, bg=t["bg_sidebar"], padx=8, pady=10)
        self.pers_sidebar_frame.pack(fill="x", pady=(10, 0))

        self.pers_side_lbl = tk.Label(
            self.pers_sidebar_frame,
            text="// SWITCH PERSONALITY:",
            font=(FONT_MONO, 7, "bold"),
            fg=t["accent_gold"],
            bg=t["bg_sidebar"]
        )
        self.pers_side_lbl.pack(anchor="w", pady=(0, 2))

        self.sidebar_pers_combo = ttk.Combobox(
            self.pers_sidebar_frame,
            values=[f"{p['emoji']} {p['name']}" for p in PERSONALITY_THEMES.values()],
            state="readonly",
            font=(FONT_MONO, 8),
            width=20
        )
        self.sidebar_pers_combo.set(f"{t['emoji']} {t['name']}")
        self.sidebar_pers_combo.pack(fill="x")
        self.sidebar_pers_combo.bind("<<ComboboxSelected>>", self._on_sidebar_personality_change)

        # Bottom Cartridge Info Badge
        self.bottom_frame = tk.Frame(self.sidebar, bg=t["bg_sidebar"], padx=10, pady=14)
        self.bottom_frame.pack(side="bottom", fill="x")

        # Pet Companion Quick Sleep/Wake Button
        is_sleeping = self.pet_manager.is_sleeping
        self.pet_toggle_btn = tk.Button(
            self.bottom_frame,
            text="[ 🐾 PET: ACTIVE ]" if not is_sleeping else "[ 💤 PET: SLEEPING ]",
            font=(FONT_MONO, 7, "bold"),
            bg=t["bg_inner"],
            fg=t["accent_primary"] if not is_sleeping else t["text_muted"],
            activebackground=t["bg_card"],
            activeforeground=t["accent_gold"],
            relief="ridge",
            bd=1,
            cursor="hand2",
            pady=3,
            command=self.toggle_pet_sleep
        )
        self.pet_toggle_btn.pack(fill="x", pady=(0, 6))

        self.status_box = tk.Frame(self.bottom_frame, bg=t["bg_inner"], bd=1, relief="solid", padx=6, pady=6)
        self.status_box.pack(fill="x")

        self.status_lbl = tk.Label(
            self.status_box,
            text="[ CARTRIDGE: ACTIVE ]",
            font=(FONT_MONO, 7, "bold"),
            fg=t["accent_green"],
            bg=t["bg_inner"]
        )
        self.status_lbl.pack(anchor="w")

        self.mode_lbl = tk.Label(
            self.status_box,
            text="100% OFFLINE + WEBCAM",
            font=(FONT_MONO, 7),
            fg=t["text_muted"],
            bg=t["bg_inner"]
        )
        self.mode_lbl.pack(anchor="w", pady=(2, 0))

    def _on_sidebar_personality_change(self, event):
        val = self.sidebar_pers_combo.get()
        for k, v in PERSONALITY_THEMES.items():
            if v["name"] in val:
                self.apply_personality_theme(k)
                break

    def _add_hover_effect(self, button, screen_key):
        def _on_enter(e):
            if self.current_screen_name != screen_key:
                button.config(bg=self.theme["bg_inner"], fg=self.theme["text_main"])

        def _on_leave(e):
            if self.current_screen_name != screen_key:
                button.config(bg=self.theme["bg_sidebar"], fg=self.theme["text_muted"])

        button.bind("<Enter>", _on_enter)
        button.bind("<Leave>", _on_leave)

    def _build_content_area(self):
        t = self.theme
        self.content_container = tk.Frame(self, bg=t["bg_main"])
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.columnconfigure(0, weight=1)
        self.content_container.rowconfigure(0, weight=1)

        self.screens = {
            "dashboard": DashboardScreen(self.content_container, self),
            "new_entry": NewEntryScreen(self.content_container, self),
            "timeline": TimelineScreen(self.content_container, self),
            "insights": InsightsScreen(self.content_container, self),
            "about": AboutScreen(self.content_container, self)
        }

        for screen in self.screens.values():
            screen.grid(row=0, column=0, sticky="nsew")

        self.current_screen_name = None

    def _build_pet_runner(self):
        """
        Builds a native in-window retro arcade pet companion footer track.
        Zero multi-window conflicts, zero Win32 DWM CPU load, 100% stable & smooth!
        """
        t = self.theme
        self.pet_track_frame = tk.Frame(self, bg=t["bg_sidebar"], height=38, bd=1, relief="ridge")
        self.pet_track_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.pet_track_frame.columnconfigure(1, weight=1)

        # Left Pet Badge
        self.pet_badge_frame = tk.Frame(self.pet_track_frame, bg=t["bg_sidebar"], padx=8, pady=3)
        self.pet_badge_frame.grid(row=0, column=0, sticky="w")

        self.pet_badge_lbl = tk.Label(
            self.pet_badge_frame,
            text="🐾 COMPANION:",
            font=(FONT_MONO, 7, "bold"),
            fg=t["accent_gold"],
            bg=t["bg_sidebar"]
        )
        self.pet_badge_lbl.pack(side="left")

        # Center Running Canvas
        self.pet_canvas = tk.Canvas(
            self.pet_track_frame,
            bg=t["bg_inner"],
            height=32,
            highlightthickness=1,
            highlightbackground=t["border"],
            bd=0,
            cursor="hand2"
        )
        self.pet_canvas.grid(row=0, column=1, sticky="ew", padx=6, pady=2)

        # Allow clicking directly on the canvas to pet the companion or wake/sleep
        self.pet_canvas.bind("<Button-1>", self._on_pet_canvas_click)

        # Right Controls
        self.pet_ctrl_frame = tk.Frame(self.pet_track_frame, bg=t["bg_sidebar"], padx=8, pady=2)
        self.pet_ctrl_frame.grid(row=0, column=2, sticky="e")

        self.pet_quick_toggle = tk.Button(
            self.pet_ctrl_frame,
            text="[ 💤 SLEEP ]" if not self.pet_manager.is_sleeping else "[ 🐾 WAKE ]",
            font=(FONT_MONO, 7, "bold"),
            bg=t["bg_inner"],
            fg=t["accent_primary"] if not self.pet_manager.is_sleeping else t["accent_gold"],
            relief="raised",
            bd=1,
            cursor="hand2",
            padx=6,
            pady=1,
            command=self.toggle_pet_sleep
        )
        self.pet_quick_toggle.pack(side="right")

        self.pet_x = -40.0
        self.pet_frame_idx = 0
        self.pet_last_frame_time = time.time()
        self.pet_toast_timer = 0
        self.pet_toast_text = ""

        self._animate_pet()

    def _on_pet_canvas_click(self, event):
        if self.pet_manager.is_sleeping:
            self.toggle_pet_sleep()
        else:
            import random
            quotes = ["💖 Purr~", "⭐ Happy!", "✨ Quest On!", "🐾 Level Up!", "🌟 Woof!", "💫 Good day!"]
            self.pet_toast_text = random.choice(quotes)
            self.pet_toast_timer = 45

    def _animate_pet(self):
        """Animates pet walking smoothly across the arcade footer track."""
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        t = self.theme
        is_sleeping = self.pet_manager.is_sleeping
        num_frames = self.pet_manager.media.get_num_frames()

        canvas_w = self.pet_canvas.winfo_width()
        if canvas_w < 100:
            canvas_w = 900

        if is_sleeping or num_frames == 0:
            self.pet_canvas.delete("all")
            self.pet_canvas.create_text(
                canvas_w // 2,
                16,
                text="[ 💤 PET IS SLEEPING PEACEFULLY — CLICK TO WAKE ]",
                font=(FONT_MONO, 7, "bold"),
                fill=t["text_muted"],
                tags="sleeping_text"
            )
            self.after(250, self._animate_pet)
            return

        pet_w = self.pet_manager.media.width or 36

        # Move across canvas
        self.pet_x += self.pet_manager.speed
        if self.pet_x > canvas_w + 30:
            self.pet_x = -float(pet_w) - 20.0

        # Advance frame
        now = time.time()
        dur_ms = self.pet_manager.media.get_duration(self.pet_frame_idx) or 110
        if now - self.pet_last_frame_time >= (dur_ms / 1000.0):
            self.pet_frame_idx = (self.pet_frame_idx + 1) % num_frames
            self.pet_last_frame_time = now

        current_frame = self.pet_manager.media.get_frame(self.pet_frame_idx)
        self.pet_canvas.delete("all")

        if current_frame:
            self.pet_canvas.create_image(
                int(self.pet_x),
                16,
                image=current_frame,
                anchor="center",
                tags="pet_sprite"
            )

        # Floating speech bubble / toast
        if self.pet_toast_timer > 0:
            self.pet_toast_timer -= 1
            if self.pet_toast_text:
                self.pet_canvas.create_text(
                    int(self.pet_x) + 38,
                    12,
                    text=self.pet_toast_text,
                    font=(FONT_MONO, 7, "bold"),
                    fill=t.get("accent_gold", "#ffd700"),
                    tags="pet_toast"
                )

        self.after(35, self._animate_pet)

    def toggle_pet_sleep(self):
        """Toggles sleep state across all pets (making pet sleep/disappear or wake)."""
        is_sleeping, msg = self.pet_manager.toggle_sleep()
        t = self.theme
        if hasattr(self, "pet_toggle_btn"):
            self.pet_toggle_btn.config(
                text="[ 💤 PET: SLEEPING ]" if is_sleeping else "[ 🐾 PET: ACTIVE ]",
                fg=t["text_muted"] if is_sleeping else t["accent_primary"]
            )
        if hasattr(self, "pet_quick_toggle"):
            self.pet_quick_toggle.config(
                text="[ 🐾 WAKE ]" if is_sleeping else "[ 💤 SLEEP ]",
                fg=t["accent_gold"] if is_sleeping else t["accent_primary"]
            )

        self.pet_toast_text = "💤 Zzz..." if is_sleeping else "🐾 Walking..."
        self.pet_toast_timer = 40

        # Update Settings screen if open
        if hasattr(self, "screens") and "about" in self.screens:
            try:
                self.screens["about"].refresh_pet_ui()
            except Exception:
                pass

    def apply_personality_theme(self, theme_name):
        """Applies a new personality theme dynamically across all UI components."""
        if theme_name not in PERSONALITY_THEMES:
            return
        
        self.active_personality = theme_name
        set_active_personality(theme_name)
        t = self.theme

        self.title(f"LifeLens ★ {t['name']} 8-Bit Journal")
        self.configure(bg=t["bg_main"])
        self._configure_styles()

        # Update Sidebar
        self.sidebar.configure(bg=t["bg_sidebar"])
        self.brand_frame.configure(bg=t["bg_sidebar"])
        self.logo_lbl.configure(fg=t["accent_primary"], bg=t["bg_sidebar"])
        self.archetype_lbl.configure(text=f"{t['emoji']} {t['name'].upper()}", fg=t["accent_gold"], bg=t["bg_sidebar"])
        self.div.configure(bg=t["border"])
        self.nav_frame.configure(bg=t["bg_sidebar"])
        self.pers_sidebar_frame.configure(bg=t["bg_sidebar"])
        self.pers_side_lbl.configure(fg=t["accent_gold"], bg=t["bg_sidebar"])
        self.sidebar_pers_combo.set(f"{t['emoji']} {t['name']}")
        self.bottom_frame.configure(bg=t["bg_sidebar"])
        self.status_box.configure(bg=t["bg_inner"])
        self.status_lbl.configure(fg=t["accent_green"], bg=t["bg_inner"])
        self.mode_lbl.configure(fg=t["text_muted"], bg=t["bg_inner"])

        if hasattr(self, "pet_toggle_btn"):
            is_sleeping = self.pet_manager.is_sleeping
            self.pet_toggle_btn.configure(
                bg=t["bg_inner"],
                fg=t["text_muted"] if is_sleeping else t["accent_primary"]
            )

        if hasattr(self, "pet_track_frame"):
            self.pet_track_frame.configure(bg=t["bg_sidebar"])
            self.pet_badge_frame.configure(bg=t["bg_sidebar"])
            self.pet_badge_lbl.configure(fg=t["accent_gold"], bg=t["bg_sidebar"])
            self.pet_canvas.configure(bg=t["bg_inner"], highlightbackground=t["border"])
            self.pet_ctrl_frame.configure(bg=t["bg_sidebar"])
            is_sleeping = self.pet_manager.is_sleeping
            self.pet_quick_toggle.configure(
                bg=t["bg_inner"],
                fg=t["accent_gold"] if is_sleeping else t["accent_primary"]
            )

        # Update Nav Buttons
        for k, btn in self.nav_buttons.items():
            if k == self.current_screen_name:
                btn.config(bg=t["accent_primary"], fg="#000000", relief="raised", bd=2)
            else:
                btn.config(bg=t["bg_sidebar"], fg=t["text_muted"], relief="flat", bd=0)

        # Update Content Container and Screens
        self.content_container.configure(bg=t["bg_main"])
        for screen in self.screens.values():
            screen.apply_theme()

        # Refresh Current Screen
        if self.current_screen_name:
            self.navigate_to(self.current_screen_name)

    def navigate_to(self, screen_name):
        if screen_name not in self.screens:
            return

        t = self.theme
        for key, btn in self.nav_buttons.items():
            if key == screen_name:
                btn.config(bg=t["accent_primary"], fg="#000000", relief="raised", bd=2)
            else:
                btn.config(bg=t["bg_sidebar"], fg=t["text_muted"], relief="flat", bd=0)

        self.current_screen_name = screen_name
        target_screen = self.screens[screen_name]
        target_screen.tkraise()
        target_screen.on_show()

    def _on_close(self):
        try:
            self.ambient_manager.stop()
        except Exception:
            pass
        self.destroy()


def main():
    app = LifeLensApp()
    app.mainloop()


if __name__ == "__main__":
    main()

