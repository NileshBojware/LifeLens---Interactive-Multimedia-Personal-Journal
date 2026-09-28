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

from data_manager import (
    PERSONALITY_THEMES,
    get_active_personality,
    set_active_personality,
    load_entries,
    ensure_data_directories,
)
from media_manager import create_sample_visual_assets, AmbientAudioManager
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

        self._configure_styles()

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_area()

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
