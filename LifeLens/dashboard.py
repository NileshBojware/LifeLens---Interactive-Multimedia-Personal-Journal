"""
LifeLens - Dashboard & UI Screens Module (Retro Pixel + 5 Personality Themes + 365 Quotes + Dual Audio Mixer)
Features:
- Spoken Quote background music playback with automatic fade out when speech finishes
- Dual-Track Audio Mixer (App Ambient BGM Volume + Quote Narration BGM Volume)
- 365 Curated Psychological Quotes with daily rotation, instant shuffle & TTS reading
- Dynamic 5-Personality Color Themes (Cyber Gamer, Zen Sage, Vibrant Artist, Deep Scholar, Cozy Nomad)
- Camera & Webcam live snapshot integration
- 8-Bit Pixel filters & retro charts
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from data_manager import (
    PERSONALITY_THEMES,
    get_active_personality,
    set_active_personality,
    get_audio_settings,
    set_audio_settings,
    MOOD_MAP,
    ACTIVITIES,
    load_entries,
    add_entry,
    delete_entry,
    clear_sample_entries,
    get_statistics,
)
from report_manager import (
    generate_report_data,
    generate_html_report,
    generate_plain_text_report,
    print_report,
    export_report_file,
    REPORTS_DIR,
)
from quotes_data import get_daily_quote, get_random_quote
from media_manager import (
    AVAILABLE_FILTERS,
    apply_image_filter,
    load_image_safe,
    save_processed_image,
    get_tk_image,
    CameraCaptureDialog,
    OPENCV_AVAILABLE,
    AmbientAudioManager,
)
from voice_manager import (
    VoiceInputManager,
    TextToSpeechManager,
    SPEECH_REC_AVAILABLE,
    PYTTSX3_AVAILABLE,
)

FONT_MONO = "Consolas"
FONT_RETRO_TITLE = ("Consolas", 15, "bold")
FONT_RETRO_HEADER = ("Consolas", 10, "bold")
FONT_RETRO_BODY = ("Consolas", 9)
FONT_RETRO_SMALL = ("Consolas", 8)


def make_pixel_bar(value, max_val=10, width=10):
    try:
        v = int(value)
    except (ValueError, TypeError):
        v = 5
    v = max(0, min(max_val, v))
    filled = int((v / max_val) * width)
    unfilled = width - filled
    return f"[{'█' * filled}{'░' * unfilled}] {v}/{max_val}"


class BaseScreen(tk.Frame):
    """Base class for theme-aware retro screens."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg=controller.theme["bg_main"])
        self.controller = controller

    @property
    def theme(self):
        return self.controller.theme

    def on_show(self):
        pass

    def apply_theme(self):
        pass


# =====================================================================
# 1. RETRO DASHBOARD SCREEN WITH 365 PSYCHOLOGICAL REFLECTIONS
# =====================================================================

class DashboardScreen(BaseScreen):
    """Retro Arcade Dashboard Home Screen with 365 Psychological Quotes & Dynamic Personality Themes."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.chart_canvas = None
        self.current_quote = get_daily_quote()
        self.tts_mgr = TextToSpeechManager()
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        # Header Title Banner & Personality Switcher
        self.header = tk.Frame(self, bg=self.theme["bg_main"])
        self.header.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 8))
        self.header.columnconfigure(0, weight=1)

        self.title_box = tk.Frame(self.header, bg=self.theme["bg_main"])
        self.title_box.grid(row=0, column=0, sticky="w")

        self.title_lbl = tk.Label(
            self.title_box,
            text=f"★ LIFELENS // {self.theme['name'].upper()} STATION ★",
            font=("Consolas", 15, "bold"),
            fg=self.theme["accent_primary"],
            bg=self.theme["bg_main"]
        )
        self.title_lbl.pack(anchor="w")

        self.subtitle_lbl = tk.Label(
            self.title_box,
            text=f">> {self.theme['tagline']}",
            font=FONT_RETRO_SMALL,
            fg=self.theme["text_muted"],
            bg=self.theme["bg_main"]
        )
        self.subtitle_lbl.pack(anchor="w", pady=(2, 0))

        # Right Header: Date + Personality Selector Dropdown
        self.right_header = tk.Frame(self.header, bg=self.theme["bg_main"])
        self.right_header.grid(row=0, column=1, sticky="e")

        today_str = datetime.now().strftime("%Y.%m.%d").upper()
        self.date_badge = tk.Label(
            self.right_header,
            text=f"[ 📅 {today_str} ]",
            font=FONT_RETRO_SMALL,
            fg=self.theme["accent_gold"],
            bg=self.theme["bg_card"],
            bd=2,
            relief="ridge",
            padx=8,
            pady=3
        )
        self.date_badge.pack(side="right", padx=(8, 0))

        self.pers_box = tk.Frame(self.right_header, bg=self.theme["bg_main"])
        self.pers_box.pack(side="right")
        self.pers_lbl = tk.Label(self.pers_box, text="THEME:", font=FONT_RETRO_SMALL, fg=self.theme["accent_primary"], bg=self.theme["bg_main"])
        self.pers_lbl.pack(side="left", padx=4)
        
        self.pers_combo = ttk.Combobox(
            self.pers_box,
            values=[f"{t['emoji']} {t['name']}" for t in PERSONALITY_THEMES.values()],
            state="readonly",
            font=FONT_RETRO_SMALL,
            width=18
        )
        curr_obj = PERSONALITY_THEMES.get(self.controller.active_personality, {})
        self.pers_combo.set(f"{curr_obj.get('emoji', '🎮')} {self.controller.active_personality}")
        self.pers_combo.pack(side="left")
        self.pers_combo.bind("<<ComboboxSelected>>", self._on_personality_selected)

        # -------------------------------------------------------------
        # 365 PSYCHOLOGICAL REFLECTION CARTRIDGE BANNER
        # -------------------------------------------------------------
        day_num = datetime.now().timetuple().tm_yday
        self.quote_card = tk.Frame(self, bg=self.theme["bg_card"], bd=2, relief="ridge", padx=14, pady=8)
        self.quote_card.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))
        self.quote_card.columnconfigure(0, weight=1)

        self.quote_top = tk.Frame(self.quote_card, bg=self.theme["bg_card"])
        self.quote_top.grid(row=0, column=0, sticky="ew")
        self.quote_top.columnconfigure(0, weight=1)

        self.quote_badge_lbl = tk.Label(
            self.quote_top,
            text=f"[ 💡 DAILY PSYCHOLOGICAL REFLECTION // DAY {day_num} OF 365 ]",
            font=FONT_RETRO_SMALL,
            fg=self.theme["accent_gold"],
            bg=self.theme["bg_card"]
        )
        self.quote_badge_lbl.pack(side="left")

        # Quote Actions
        self.quote_actions = tk.Frame(self.quote_top, bg=self.theme["bg_card"])
        self.quote_actions.pack(side="right")

        self.shuffle_quote_btn = tk.Button(
            self.quote_actions,
            text="[ 🎲 RANDOM INSIGHT ]",
            font=("Consolas", 7, "bold"),
            bg=self.theme["bg_inner"],
            fg=self.theme["accent_primary"],
            relief="raised",
            bd=2,
            cursor="hand2",
            padx=6,
            pady=1,
            command=self._shuffle_quote
        )
        self.shuffle_quote_btn.pack(side="left", padx=(0, 6))

        self.speak_quote_btn = tk.Button(
            self.quote_actions,
            text="[ 🔊 READ ALOUD + BGM ]",
            font=("Consolas", 7, "bold"),
            bg=self.theme["bg_inner"],
            fg=self.theme["accent_secondary"],
            relief="raised",
            bd=2,
            cursor="hand2",
            padx=6,
            pady=1,
            command=self._speak_current_quote
        )
        self.speak_quote_btn.pack(side="left")

        # Quote Text & Author (supports real-time word-by-word opaque color highlight)
        self.quote_text_box = tk.Text(
            self.quote_card,
            font=("Consolas", 10, "italic"),
            fg=self.theme["text_main"],
            bg=self.theme["bg_card"],
            height=2,
            wrap="word",
            bd=0,
            relief="flat",
            highlightthickness=0,
            padx=2,
            pady=2,
            cursor="arrow"
        )
        self.quote_text_box.grid(row=1, column=0, sticky="ew", pady=(3, 1))
        self.quote_text_box.tag_config("quote_body", font=("Consolas", 10, "italic"), foreground=self.theme["text_main"])
        self.quote_text_box.tag_config(
            "word_highlight",
            background=self.theme["accent_primary"],
            foreground=self.theme.get("accent_text", "#000000"),
            font=("Consolas", 10, "bold")
        )
        self.quote_text_box.bind("<Key>", lambda e: "break")
        self._render_current_quote()

        self.quote_author_lbl = tk.Label(
            self.quote_card,
            text=f"— {self.current_quote['author']}",
            font=FONT_RETRO_SMALL,
            fg=self.theme["accent_primary"],
            bg=self.theme["bg_card"]
        )
        self.quote_author_lbl.grid(row=2, column=0, sticky="e")

        # Top Arcade KPI Cartridges
        self.kpi_container = tk.Frame(self, bg=self.theme["bg_main"])
        self.kpi_container.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 10))
        for col in range(4):
            self.kpi_container.columnconfigure(col, weight=1)

        self._build_kpi_cartridges()

        # Action Buttons Row
        self.actions_bar = tk.Frame(self, bg=self.theme["bg_main"])
        self.actions_bar.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 10))

        self.new_btn = tk.Button(
            self.actions_bar,
            text="[+] WRITE NEW ENTRY",
            font=FONT_RETRO_HEADER,
            bg=self.theme["accent_primary"],
            fg=self.theme.get("accent_text", "#000000"),
            activebackground=self.theme["accent_secondary"],
            activeforeground="#FFFFFF",
            relief="raised",
            bd=3,
            cursor="hand2",
            padx=14,
            pady=5,
            command=lambda: self.controller.navigate_to("new_entry")
        )
        self.new_btn.pack(side="left", padx=(0, 10))

        self.ambient_btn = tk.Button(
            self.actions_bar,
            text="[♫ CHIPTUNE AUDIO: OFF]",
            font=FONT_RETRO_BODY,
            bg=self.theme["bg_card"],
            fg=self.theme["accent_gold"],
            activebackground=self.theme["bg_inner"],
            relief="raised",
            bd=3,
            cursor="hand2",
            padx=10,
            pady=5,
            command=self._toggle_ambient
        )
        self.ambient_btn.pack(side="left", padx=(0, 10))

        self.audio_settings_btn = tk.Button(
            self.actions_bar,
            text="[⚙ AUDIO MIXER]",
            font=FONT_RETRO_SMALL,
            bg=self.theme["bg_card"],
            fg=self.theme["accent_primary"],
            activebackground=self.theme["bg_inner"],
            relief="raised",
            bd=2,
            cursor="hand2",
            padx=8,
            pady=5,
            command=lambda: self.controller.navigate_to("about")
        )
        self.audio_settings_btn.pack(side="left", padx=(0, 10))

        self.reports_btn = tk.Button(
            self.actions_bar,
            text="[ 🖨️ REPORTS & CONCLUSION ]",
            font=FONT_RETRO_SMALL,
            bg=self.theme["bg_card"],
            fg=self.theme["accent_gold"],
            activebackground=self.theme["bg_inner"],
            relief="raised",
            bd=2,
            cursor="hand2",
            padx=8,
            pady=5,
            command=lambda: self.controller.navigate_to("reports")
        )
        self.reports_btn.pack(side="left", padx=(0, 10))

        self.clear_sample_btn = tk.Button(
            self.actions_bar,
            text="[x] CLEAR SAMPLES",
            font=FONT_RETRO_SMALL,
            bg=self.theme["bg_card"],
            fg=self.theme["text_muted"],
            activebackground=self.theme["bg_inner"],
            relief="raised",
            bd=2,
            cursor="hand2",
            padx=8,
            pady=5,
            command=self._clear_samples
        )
        self.clear_sample_btn.pack(side="right")

        # Split Content (Left: Recent Entries, Right: Radar Chart)
        self.split_frame = tk.Frame(self, bg=self.theme["bg_main"])
        self.split_frame.grid(row=4, column=0, sticky="nsew", padx=24, pady=(0, 16))
        self.split_frame.columnconfigure(0, weight=3)
        self.split_frame.columnconfigure(1, weight=2)
        self.split_frame.rowconfigure(0, weight=1)

        # Left Card: Recent Entries
        self.left_card = tk.Frame(self.split_frame, bg=self.theme["bg_card"], bd=2, relief="ridge")
        self.left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.left_card.columnconfigure(0, weight=1)
        self.left_card.rowconfigure(1, weight=1)

        self.left_header = tk.Frame(self.left_card, bg=self.theme["bg_card"])
        self.left_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 3))
        self.left_header.columnconfigure(0, weight=1)

        self.recent_title_lbl = tk.Label(
            self.left_header,
            text="[ ■ RECENT QUEST LOGS ■ ]",
            font=FONT_RETRO_HEADER,
            fg=self.theme["accent_primary"],
            bg=self.theme["bg_card"]
        )
        self.recent_title_lbl.grid(row=0, column=0, sticky="w")

        self.timeline_link = tk.Button(
            self.left_header,
            text=">> VIEW TIMELINE",
            font=FONT_RETRO_SMALL,
            fg=self.theme["accent_gold"],
            bg=self.theme["bg_card"],
            bd=0,
            cursor="hand2",
            command=lambda: self.controller.navigate_to("timeline")
        )
        self.timeline_link.grid(row=0, column=1, sticky="e")

        self.recent_list_frame = tk.Frame(self.left_card, bg=self.theme["bg_card"])
        self.recent_list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))
        self.recent_list_frame.columnconfigure(0, weight=1)

        # Right Card: Radar Chart
        self.right_card = tk.Frame(self.split_frame, bg=self.theme["bg_card"], bd=2, relief="ridge")
        self.right_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.right_card.columnconfigure(0, weight=1)
        self.right_card.rowconfigure(1, weight=1)

        self.radar_title_lbl = tk.Label(
            self.right_card,
            text="[ ■ MOOD SPECTRUM RADAR ■ ]",
            font=FONT_RETRO_HEADER,
            fg=self.theme["accent_secondary"],
            bg=self.theme["bg_card"]
        )
        self.radar_title_lbl.grid(row=0, column=0, sticky="w", padx=12, pady=(8, 2))

        self.chart_container = tk.Frame(self.right_card, bg=self.theme["bg_card"])
        self.chart_container.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))
        self.chart_container.columnconfigure(0, weight=1)
        self.chart_container.rowconfigure(0, weight=1)

    def _render_current_quote(self):
        quote_text = f'"{self.current_quote["quote"]}"'
        self.quote_text_box.config(state="normal")
        self.quote_text_box.delete("1.0", "end")
        self.quote_text_box.insert("1.0", quote_text, "quote_body")
        self.quote_text_box.config(state="disabled")
        if hasattr(self, "quote_author_lbl"):
            self.quote_author_lbl.config(text=f"— {self.current_quote['author']}")

    def _shuffle_quote(self):
        self.current_quote = get_random_quote()
        self._render_current_quote()
        self.quote_badge_lbl.config(text="[ 💡 RANDOM PSYCHOLOGICAL INSIGHT // 365 COLLECTION ]")

    def _speak_current_quote(self):
        if not PYTTSX3_AVAILABLE:
            messagebox.showinfo("Text-to-Speech", "pyttsx3 is not installed.")
            return

        text_to_speak = f"{self.current_quote['quote']} ... Quote by, {self.current_quote['author']}."
        self.speak_quote_btn.config(text="[ 🔊 SPEAKING... ]")

        # Reads aloud at 0.75x speed with synchronized BGM and real-time word-by-word highlight!
        self.tts_mgr.read_aloud_async(
            text=text_to_speak,
            rate=120,
            on_start=self.controller.ambient_manager.start_quote_narration_music,
            on_word=self._on_quote_word_spoken,
            on_finish=self._on_quote_speech_finish,
            on_error=lambda err: [
                self.controller.ambient_manager.stop_quote_narration_music(),
                self._on_quote_speech_finish(),
                messagebox.showwarning("Speech Error", f"{err}")
            ]
        )

    def _on_quote_word_spoken(self, name, location, length):
        if not hasattr(self, "quote_text_box") or not self.quote_text_box.winfo_exists():
            return
        self.after(0, lambda: self._apply_word_highlight(location, length))

    def _apply_word_highlight(self, location, length):
        try:
            if not hasattr(self, "quote_text_box") or not self.quote_text_box.winfo_exists():
                return
            self.quote_text_box.tag_remove("word_highlight", "1.0", "end")
            if location is not None and length and length > 0:
                quote_body = self.current_quote.get("quote", "")
                if location < len(quote_body):
                    start_idx = f"1.0 + {location + 1} chars"  # +1 for opening quote mark '“'
                    end_idx = f"1.0 + {location + 1 + length} chars"
                    self.quote_text_box.tag_add("word_highlight", start_idx, end_idx)
                    self.quote_text_box.see(start_idx)
        except Exception:
            pass

    def _on_quote_speech_finish(self):
        self.controller.ambient_manager.stop_quote_narration_music()
        self.after(0, self._cleanup_quote_speech_ui)

    def _cleanup_quote_speech_ui(self):
        try:
            if hasattr(self, "quote_text_box") and self.quote_text_box.winfo_exists():
                self.quote_text_box.tag_remove("word_highlight", "1.0", "end")
            if hasattr(self, "speak_quote_btn") and self.speak_quote_btn.winfo_exists():
                self.speak_quote_btn.config(text="[ 🔊 READ ALOUD + BGM ]")
        except Exception:
            pass

    def _on_personality_selected(self, event):
        val = self.pers_combo.get()
        for k, v in PERSONALITY_THEMES.items():
            if v["name"] in val:
                self.controller.apply_personality_theme(k)
                break

    def apply_theme(self):
        t = self.theme
        self.configure(bg=t["bg_main"])
        self.header.configure(bg=t["bg_main"])
        if hasattr(self, "title_box"):
            self.title_box.configure(bg=t["bg_main"])
        self.title_lbl.configure(text=f"★ LIFELENS // {t['name'].upper()} STATION ★", fg=t["accent_primary"], bg=t["bg_main"])
        self.subtitle_lbl.configure(text=f">> {t['tagline']}", fg=t["text_muted"], bg=t["bg_main"])
        if hasattr(self, "right_header"):
            self.right_header.configure(bg=t["bg_main"])
        self.date_badge.configure(fg=t["accent_gold"], bg=t["bg_card"])
        if hasattr(self, "pers_box"):
            self.pers_box.configure(bg=t["bg_main"])
        if hasattr(self, "pers_lbl"):
            self.pers_lbl.configure(fg=t["accent_primary"], bg=t["bg_main"])
        self.quote_card.configure(bg=t["bg_card"])
        if hasattr(self, "quote_top"):
            self.quote_top.configure(bg=t["bg_card"])
        self.quote_badge_lbl.configure(fg=t["accent_gold"], bg=t["bg_card"])
        if hasattr(self, "quote_actions"):
            self.quote_actions.configure(bg=t["bg_card"])
        
        self.quote_text_box.configure(bg=t["bg_card"], fg=t["text_main"])
        self.quote_text_box.tag_configure("quote_body", foreground=t["text_main"])
        self.quote_text_box.tag_configure(
            "word_highlight",
            background=t["accent_primary"],
            foreground=t.get("accent_text", "#000000"),
            font=("Consolas", 10, "bold")
        )
        self.quote_author_lbl.configure(fg=t["accent_primary"], bg=t["bg_card"])
        self.shuffle_quote_btn.configure(bg=t["bg_inner"], fg=t["accent_primary"])
        self.speak_quote_btn.configure(bg=t["bg_inner"], fg=t["accent_secondary"])
        self.kpi_container.configure(bg=t["bg_main"])
        self.actions_bar.configure(bg=t["bg_main"])
        self.new_btn.configure(bg=t["accent_primary"], fg=t.get("accent_text", "#000000"), activebackground=t["accent_secondary"])
        self.ambient_btn.configure(bg=t["bg_card"], fg=t["accent_gold"], activebackground=t["bg_inner"])
        self.audio_settings_btn.configure(bg=t["bg_card"], fg=t["accent_primary"], activebackground=t["bg_inner"])
        if hasattr(self, "reports_btn"):
            self.reports_btn.configure(bg=t["bg_card"], fg=t["accent_gold"], activebackground=t["bg_inner"])
        self.clear_sample_btn.configure(bg=t["bg_card"], fg=t["text_muted"], activebackground=t["bg_inner"])
        self.split_frame.configure(bg=t["bg_main"])
        self.left_card.configure(bg=t["bg_card"])
        self.left_header.configure(bg=t["bg_card"])
        self.recent_title_lbl.configure(fg=t["accent_primary"], bg=t["bg_card"])
        self.timeline_link.configure(fg=t["accent_gold"], bg=t["bg_card"])
        self.recent_list_frame.configure(bg=t["bg_card"])
        self.right_card.configure(bg=t["bg_card"])
        self.radar_title_lbl.configure(fg=t["accent_secondary"], bg=t["bg_card"])
        self.chart_container.configure(bg=t["bg_card"])

        curr_obj = PERSONALITY_THEMES.get(self.controller.active_personality, {})
        self.pers_combo.configure(values=[f"{p['emoji']} {p['name']}" for p in PERSONALITY_THEMES.values()])
        self.pers_combo.set(f"{curr_obj.get('emoji', '🎮')} {self.controller.active_personality}")

        for child in self.kpi_container.winfo_children():
            child.destroy()
        self._build_kpi_cartridges()
        self.refresh_dashboard()

    def _build_kpi_cartridges(self):
        t = self.theme
        self.kpi_widgets = []
        configs = [
            ("TOTAL LOGS", "0", t["accent_primary"], "QUESTS SAVED"),
            ("LATEST MOOD", "NONE", t["accent_gold"], "EMOTION SYNC"),
            ("ENERGY VITALITY", "0.0/10", t["accent_green"], "STAMINA RATING"),
            ("MAIN FOCUS", "NONE", t["accent_secondary"], "TOP ACTIVITY")
        ]

        for i, (title, val, color, sub) in enumerate(configs):
            card = tk.Frame(self.kpi_container, bg=t["bg_card"], bd=2, relief="ridge")
            card.grid(row=0, column=i, sticky="ew", padx=4 if i > 0 else (0, 4))
            card.columnconfigure(0, weight=1)

            bar = tk.Frame(card, bg=color, height=3)
            bar.pack(fill="x", side="top")

            inner = tk.Frame(card, bg=t["bg_card"], padx=10, pady=8)
            inner.pack(fill="both", expand=True)

            tk.Label(inner, text=f"// {title}", font=FONT_RETRO_SMALL, fg=t["text_muted"], bg=t["bg_card"]).pack(anchor="w")
            lbl_val = tk.Label(inner, text=val, font=("Consolas", 12, "bold"), fg=color, bg=t["bg_card"])
            lbl_val.pack(anchor="w", pady=(2, 1))

            lbl_sub = tk.Label(inner, text=f"[{sub}]", font=("Consolas", 7), fg=t["text_muted"], bg=t["bg_card"])
            lbl_sub.pack(anchor="w")

            self.kpi_widgets.append(lbl_val)

    def on_show(self):
        self.refresh_dashboard()

    def refresh_dashboard(self):
        stats = get_statistics()
        if hasattr(self, "kpi_widgets") and len(self.kpi_widgets) >= 4:
            self.kpi_widgets[0].config(text=str(stats["total_entries"]))
            self.kpi_widgets[1].config(text=f"{stats['latest_mood_emoji']} {stats['latest_mood'].upper()}" if stats['total_entries'] > 0 else "NONE")
            self.kpi_widgets[2].config(text=f"{stats['avg_energy']}/10" if stats['total_entries'] > 0 else "0/10")
            self.kpi_widgets[3].config(text=stats['top_activity'].upper() if stats['total_entries'] > 0 else "NONE")

        for child in self.recent_list_frame.winfo_children():
            child.destroy()

        recent = stats.get("recent_entries", [])
        if not recent:
            tk.Label(
                self.recent_list_frame,
                text="[!] NO QUEST LOGS YET. CLICK [+] TO BEGIN.",
                font=FONT_RETRO_SMALL,
                fg=self.theme["accent_gold"],
                bg=self.theme["bg_card"],
                pady=20
            ).pack()
        else:
            for item in recent:
                self._render_recent_item(item)

        self._render_mini_chart(stats)

    def _render_recent_item(self, item):
        t = self.theme
        item_frame = tk.Frame(self.recent_list_frame, bg=t["bg_inner"], bd=1, relief="solid")
        item_frame.pack(fill="x", pady=2)
        item_frame.columnconfigure(1, weight=1)

        mood_info = MOOD_MAP.get(item.get("mood", "Good"), {"emoji": "😊", "color": t["accent_primary"]})
        
        # Mood avatar badge with crisp background and vibrant emoji coloring
        mood_badge = tk.Frame(item_frame, bg=t["bg_card"], bd=1, relief="ridge", width=36, height=36)
        mood_badge.grid(row=0, column=0, rowspan=2, padx=(5, 6), pady=3, sticky="ns")
        mood_badge.pack_propagate(False)

        tk.Label(
            mood_badge,
            text=f"{mood_info['emoji']}",
            font=("Segoe UI Emoji", 14),
            fg=mood_info.get("color", t["accent_gold"]),
            bg=t["bg_card"]
        ).pack(expand=True)

        top_row = tk.Frame(item_frame, bg=t["bg_inner"])
        top_row.grid(row=0, column=1, sticky="ew", padx=(0, 6), pady=(3, 1))

        tk.Label(top_row, text=f"[{item.get('date', '')}]", font=FONT_RETRO_SMALL, fg=t["accent_primary"], bg=t["bg_inner"]).pack(side="left")
        tk.Label(top_row, text=f"<{item.get('activity', '').upper()}>", font=FONT_RETRO_SMALL, fg=t["accent_gold"], bg=t["bg_inner"]).pack(side="left", padx=4)

        en_meter = make_pixel_bar(item.get("energy", 5), 10, width=4)
        tk.Label(top_row, text=en_meter, font=FONT_RETRO_SMALL, fg=t["accent_green"], bg=t["bg_inner"]).pack(side="left", padx=2)

        if item.get("is_sample"):
            tk.Label(top_row, text="[SAMPLE]", font=("Consolas", 7), fg=t["text_muted"], bg=t["bg_inner"]).pack(side="right")

        snippet = item.get("text", "")
        if len(snippet) > 70:
            snippet = snippet[:70] + "..."
        tk.Label(item_frame, text=snippet, font=FONT_RETRO_SMALL, fg=t["text_main"], bg=t["bg_inner"], anchor="w", justify="left").grid(row=1, column=1, sticky="w", padx=(0, 6), pady=(0, 3))

    def _render_mini_chart(self, stats):
        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()
            self.chart_canvas = None

        t = self.theme
        fig = Figure(figsize=(3.4, 2.6), dpi=95, facecolor=t["bg_card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(t["bg_card"])

        mood_counts = {k: v for k, v in stats.get("mood_counts", {}).items() if v > 0}
        
        if not mood_counts:
            ax.text(0.5, 0.5, "NO RADAR DATA", ha="center", va="center", color=t["text_muted"], fontfamily=FONT_MONO, fontsize=8)
            ax.axis("off")
        else:
            labels = [k.upper() for k in mood_counts.keys()]
            values = list(mood_counts.values())
            colors = t.get("chart_colors", [t["accent_primary"], t["accent_secondary"]])[:len(values)]

            wedges, texts, autotexts = ax.pie(
                values,
                labels=labels,
                colors=colors,
                autopct="%1.0f%%",
                startangle=140,
                pctdistance=0.75,
                wedgeprops=dict(width=0.45, edgecolor=t["bg_main"], linewidth=2)
            )
            for txt in texts:
                txt.set_fontsize(7)
                txt.set_color(t["text_main"])
                txt.set_fontfamily(FONT_MONO)
            for at in autotexts:
                at.set_fontsize(7)
                at.set_weight("bold")
                at.set_color("#000000")

        fig.tight_layout()
        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)

    def _toggle_ambient(self):
        is_playing, msg = self.controller.ambient_manager.toggle()
        if is_playing:
            self.ambient_btn.config(text="[♫ CHIPTUNE: ON]", bg=self.theme["accent_green"], fg="#000000")
        else:
            self.ambient_btn.config(text="[♫ CHIPTUNE: OFF]", bg=self.theme["bg_card"], fg=self.theme["accent_gold"])

    def _clear_samples(self):
        if messagebox.askyesno("Clear Samples", "Purge all fictional sample quest entries?"):
            removed = clear_sample_entries()
            messagebox.showinfo("Purged", f"Purged {removed} sample logs.")
            self.refresh_dashboard()


# =====================================================================
# 2. RETRO NEW ENTRY FORM
# =====================================================================

class NewEntryScreen(BaseScreen):
    """Retro Entry Form with File Upload, Webcam Snapshot & Psychological Reflection Prompts."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.selected_mood = tk.StringVar(value="Happy")
        self.energy_val = tk.IntVar(value=8)
        self.activity_val = tk.StringVar(value="Coding")
        self.filter_val = tk.StringVar(value="Pixel Art (8-Bit)")
        self.current_prompt = get_random_quote()
        self.current_image_path = None
        self.preview_tk_img = None
        
        self.voice_mgr = VoiceInputManager()
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        t = self.theme
        self.form_canvas = tk.Canvas(self, bg=t["bg_main"], highlightthickness=0)
        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.form_canvas.yview)
        self.form_frame = tk.Frame(self.form_canvas, bg=t["bg_main"])

        self.form_frame.bind("<Configure>", lambda e: self.form_canvas.configure(scrollregion=self.form_canvas.bbox("all")))
        canvas_window = self.form_canvas.create_window((0, 0), window=self.form_frame, anchor="nw")
        self.form_canvas.bind("<Configure>", lambda e: self.form_canvas.itemconfig(canvas_window, width=e.width))

        self.form_canvas.configure(yscrollcommand=v_scroll.set)
        self.form_canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        self.form_frame.columnconfigure(0, weight=1)

        self.card = tk.Frame(self.form_frame, bg=t["bg_card"], bd=2, relief="ridge")
        self.card.grid(row=0, column=0, sticky="ew", padx=24, pady=16)
        self.card.columnconfigure(0, weight=1)

        # Title
        self.title_box = tk.Frame(self.card, bg=t["bg_card"])
        self.title_box.pack(fill="x", padx=18, pady=(12, 8))
        
        self.form_title = tk.Label(
            self.title_box,
            text=f"[ ■ LOG CREATION TERMINAL // {t['name'].upper()} ■ ]",
            font=("Consolas", 12, "bold"),
            fg=t["accent_primary"],
            bg=t["bg_card"]
        )
        self.form_title.pack(side="left")

        # Mindful Prompt Banner
        self.prompt_box = tk.Frame(self.card, bg=t["bg_inner"], bd=1, relief="solid", padx=10, pady=6)
        self.prompt_box.pack(fill="x", padx=18, pady=(0, 10))
        self.prompt_box.columnconfigure(0, weight=1)

        self.prompt_top = tk.Frame(self.prompt_box, bg=t["bg_inner"])
        self.prompt_top.pack(fill="x")

        self.prompt_badge_lbl = tk.Label(
            self.prompt_top,
            text="[ 💭 MINDFUL REFLECTION PROMPT ]",
            font=FONT_RETRO_SMALL,
            fg=t["accent_gold"],
            bg=t["bg_inner"]
        )
        self.prompt_badge_lbl.pack(side="left")

        self.prompt_shuffle_btn = tk.Button(
            self.prompt_top,
            text="[ 🎲 SHUFFLE PROMPT ]",
            font=("Consolas", 7),
            bg=t["bg_card"],
            fg=t["accent_primary"],
            relief="raised",
            bd=2,
            cursor="hand2",
            padx=6,
            pady=1,
            command=self._shuffle_prompt
        )
        self.prompt_shuffle_btn.pack(side="right")

        self.prompt_text_lbl = tk.Label(
            self.prompt_box,
            text=f"“{self.current_prompt['quote']}” — {self.current_prompt['author']}",
            font=("Consolas", 8, "italic"),
            fg=t["text_main"],
            bg=t["bg_inner"],
            wraplength=900,
            justify="left",
            anchor="w"
        )
        self.prompt_text_lbl.pack(fill="x", pady=(2, 0))

        # Row 1: Date & Activity
        self.row1 = tk.Frame(self.card, bg=t["bg_card"])
        self.row1.pack(fill="x", padx=18, pady=(0, 10))
        self.row1.columnconfigure(0, weight=1)
        self.row1.columnconfigure(1, weight=1)

        self.date_box = tk.Frame(self.row1, bg=t["bg_card"])
        self.date_box.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.date_lbl = tk.Label(self.date_box, text="// DATE [YYYY-MM-DD]:", font=FONT_RETRO_HEADER, fg=t["accent_gold"], bg=t["bg_card"])
        self.date_lbl.pack(anchor="w", pady=(0, 2))
        
        self.date_sub = tk.Frame(self.date_box, bg=t["bg_card"])
        self.date_sub.pack(fill="x")
        self.date_entry = tk.Entry(self.date_sub, font=FONT_RETRO_BODY, bg=t["bg_inner"], fg=t["text_main"], insertbackground=t["accent_primary"], bd=2, relief="sunken")
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.pack(side="left", fill="x", expand=True)

        self.today_btn = tk.Button(
            self.date_sub,
            text="[TODAY]",
            font=FONT_RETRO_SMALL,
            bg=t["bg_inner"],
            fg=t["accent_primary"],
            relief="raised",
            bd=2,
            cursor="hand2",
            padx=6,
            command=lambda: [self.date_entry.delete(0, tk.END), self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))]
        )
        self.today_btn.pack(side="right", padx=(6, 0))

        self.act_box = tk.Frame(self.row1, bg=t["bg_card"])
        self.act_box.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self.act_lbl = tk.Label(self.act_box, text="// ACTIVITY / FOCUS:", font=FONT_RETRO_HEADER, fg=t["accent_gold"], bg=t["bg_card"])
        self.act_lbl.pack(anchor="w", pady=(0, 2))
        self.act_combo = ttk.Combobox(self.act_box, values=ACTIVITIES, textvariable=self.activity_val, state="readonly", font=FONT_RETRO_BODY)
        self.act_combo.pack(fill="x")

        # Row 2: Mood Selection
        self.mood_box = tk.Frame(self.card, bg=t["bg_card"])
        self.mood_box.pack(fill="x", padx=18, pady=(0, 10))
        self.mood_title = tk.Label(self.mood_box, text="// EMOTIONAL STATE:", font=FONT_RETRO_HEADER, fg=t["accent_gold"], bg=t["bg_card"])
        self.mood_title.pack(anchor="w", pady=(0, 3))

        self.mood_buttons_frame = tk.Frame(self.mood_box, bg=t["bg_card"])
        self.mood_buttons_frame.pack(fill="x")
        self.mood_btn_map = {}

        for mood_name, meta in MOOD_MAP.items():
            btn = tk.Button(
                self.mood_buttons_frame,
                text=f"{meta['emoji']} {mood_name.upper()}",
                font=FONT_RETRO_SMALL,
                bg=t["bg_inner"],
                fg=t["text_main"],
                relief="raised",
                bd=2,
                cursor="hand2",
                padx=3,
                pady=4,
                command=lambda m=mood_name: self._set_mood(m)
            )
            btn.pack(side="left", padx=2, expand=True, fill="x")
            self.mood_btn_map[mood_name] = btn

        self._set_mood("Happy")

        # Row 3: Energy Meter
        self.energy_box = tk.Frame(self.card, bg=t["bg_card"])
        self.energy_box.pack(fill="x", padx=18, pady=(0, 10))

        self.energy_header = tk.Frame(self.energy_box, bg=t["bg_card"])
        self.energy_header.pack(fill="x")
        self.energy_title = tk.Label(self.energy_header, text="// ENERGY & STAMINA METER:", font=FONT_RETRO_HEADER, fg=t["accent_gold"], bg=t["bg_card"])
        self.energy_title.pack(side="left")
        
        self.energy_display_lbl = tk.Label(
            self.energy_header,
            text=make_pixel_bar(8, 10, width=10) + " [HIGH]",
            font=FONT_RETRO_HEADER,
            fg=t["accent_green"],
            bg=t["bg_card"]
        )
        self.energy_display_lbl.pack(side="right")

        self.energy_slider = ttk.Scale(
            self.energy_box,
            from_=1,
            to=10,
            orient="horizontal",
            variable=self.energy_val,
            command=self._on_energy_slider_change
        )
        self.energy_slider.pack(fill="x", pady=(3, 0))

        # Row 4: Journal Text & Voice Button
        self.text_box_frame = tk.Frame(self.card, bg=t["bg_card"])
        self.text_box_frame.pack(fill="x", padx=18, pady=(0, 10))
        
        self.text_header = tk.Frame(self.text_box_frame, bg=t["bg_card"])
        self.text_header.pack(fill="x", pady=(0, 3))
        self.reflect_lbl = tk.Label(self.text_header, text="// REFLECTION / LOG TEXT:", font=FONT_RETRO_HEADER, fg=t["accent_gold"], bg=t["bg_card"])
        self.reflect_lbl.pack(side="left")

        self.voice_btn = tk.Button(
            self.text_header,
            text="[🎙️ RECORD VOICE]",
            font=FONT_RETRO_SMALL,
            bg=t["accent_secondary"],
            fg="#FFFFFF",
            relief="raised",
            bd=2,
            cursor="hand2",
            padx=8,
            pady=2,
            command=self._start_voice_entry
        )
        self.voice_btn.pack(side="right")

        self.voice_status_lbl = tk.Label(self.text_header, text="", font=FONT_RETRO_SMALL, fg=t["accent_primary"], bg=t["bg_card"])
        self.voice_status_lbl.pack(side="right", padx=6)

        self.text_area = tk.Text(
            self.text_box_frame,
            font=FONT_RETRO_BODY,
            height=5,
            wrap="word",
            bg=t["bg_inner"],
            fg=t["text_main"],
            insertbackground=t["accent_primary"],
            bd=2,
            relief="sunken",
            padx=8,
            pady=8
        )
        self.text_area.pack(fill="x")

        # Row 5: Photo Upload & WEBCAM Section
        self.img_section = tk.Frame(self.card, bg=t["bg_inner"], bd=1, relief="solid")
        self.img_section.pack(fill="x", padx=18, pady=(0, 12))
        
        self.img_sec_header = tk.Frame(self.img_section, bg=t["bg_card"], padx=8, pady=4)
        self.img_sec_header.pack(fill="x")
        
        self.photo_sec_lbl = tk.Label(
            self.img_sec_header,
            text="[ 📷 PHOTO ATTACHMENT // FILE OR WEBCAM SNAP ]",
            font=FONT_RETRO_SMALL,
            fg=t["accent_primary"],
            bg=t["bg_card"]
        )
        self.photo_sec_lbl.pack(side="left")

        self.img_body = tk.Frame(self.img_section, bg=t["bg_inner"], padx=8, pady=8)
        self.img_body.pack(fill="x")
        self.img_body.columnconfigure(0, weight=1)
        self.img_body.columnconfigure(1, weight=1)

        self.img_controls = tk.Frame(self.img_body, bg=t["bg_inner"])
        self.img_controls.grid(row=0, column=0, sticky="nw")

        self.btn_row = tk.Frame(self.img_controls, bg=t["bg_inner"])
        self.btn_row.pack(anchor="w", pady=(0, 5))

        self.upload_btn = tk.Button(
            self.btn_row,
            text="[📂 BROWSE FILE]",
            font=FONT_RETRO_SMALL,
            bg=t["bg_card"],
            fg=t["accent_primary"],
            relief="raised",
            bd=2,
            cursor="hand2",
            padx=6,
            pady=2,
            command=self._choose_image
        )
        self.upload_btn.pack(side="left", padx=(0, 6))

        self.camera_btn = tk.Button(
            self.btn_row,
            text="[📸 WEBCAM SNAP]",
            font=FONT_RETRO_SMALL,
            bg=t["accent_green"],
            fg=t.get("accent_text", "#000000"),
            relief="raised",
            bd=2,
            cursor="hand2",
            padx=6,
            pady=2,
            command=self._open_camera
        )
        self.camera_btn.pack(side="left")

        self.filter_lbl = tk.Label(self.img_controls, text="// 8-BIT EFFECT FILTER:", font=FONT_RETRO_SMALL, fg=t["text_muted"], bg=t["bg_inner"])
        self.filter_lbl.pack(anchor="w")
        self.filter_combo = ttk.Combobox(
            self.img_controls,
            values=AVAILABLE_FILTERS,
            textvariable=self.filter_val,
            state="readonly",
            font=FONT_RETRO_SMALL,
            width=22
        )
        self.filter_combo.pack(anchor="w", pady=(2, 5))
        self.filter_combo.bind("<<ComboboxSelected>>", lambda e: self._update_image_preview())

        self.remove_img_btn = tk.Button(
            self.img_controls,
            text="[x] EJECT IMAGE",
            font=FONT_RETRO_SMALL,
            bg=t["bg_inner"],
            fg="#ff4444",
            relief="flat",
            cursor="hand2",
            command=self._clear_image
        )
        self.remove_img_btn.pack(anchor="w")
        self.remove_img_btn.config(state="disabled")

        self.preview_container = tk.Frame(self.img_body, bg=t["bg_inner"], width=220, height=120, bd=2, relief="sunken")
        self.preview_container.grid(row=0, column=1, sticky="ne")
        self.preview_container.pack_propagate(False)

        self.preview_lbl = tk.Label(
            self.preview_container,
            text="[ NO PHOTO ATTACHED ]\n(FILE OR CAMERA)",
            font=FONT_RETRO_SMALL,
            fg=t["text_muted"],
            bg=t["bg_inner"]
        )
        self.preview_lbl.pack(expand=True)

        # Bottom Actions
        self.action_row = tk.Frame(self.card, bg=t["bg_card"])
        self.action_row.pack(fill="x", padx=18, pady=(0, 16))

        self.save_btn = tk.Button(
            self.action_row,
            text="[★ SAVE QUEST LOG ★]",
            font=FONT_RETRO_HEADER,
            bg=t["accent_primary"],
            fg=t.get("accent_text", "#000000"),
            activebackground=t["accent_secondary"],
            activeforeground="#FFFFFF",
            relief="raised",
            bd=3,
            cursor="hand2",
            padx=18,
            pady=6,
            command=self._save_entry
        )
        self.save_btn.pack(side="left")

        self.reset_btn = tk.Button(
            self.action_row,
            text="[RESET FORM]",
            font=FONT_RETRO_BODY,
            bg=t["bg_inner"],
            fg=t["text_muted"],
            relief="raised",
            bd=2,
            cursor="hand2",
            padx=10,
            pady=5,
            command=self._reset_form
        )
        self.reset_btn.pack(side="left", padx=8)

    def _shuffle_prompt(self):
        self.current_prompt = get_random_quote()
        self.prompt_text_lbl.config(text=f"“{self.current_prompt['quote']}” — {self.current_prompt['author']}")

    def apply_theme(self):
        t = self.theme
        self.configure(bg=t["bg_main"])
        if hasattr(self, "form_canvas"):
            self.form_canvas.configure(bg=t["bg_main"])
        if hasattr(self, "form_frame"):
            self.form_frame.configure(bg=t["bg_main"])
        self.card.configure(bg=t["bg_card"])
        if hasattr(self, "title_box"):
            self.title_box.configure(bg=t["bg_card"])
        self.form_title.configure(text=f"[ ■ LOG CREATION TERMINAL // {t['name'].upper()} ■ ]", fg=t["accent_primary"], bg=t["bg_card"])
        self.prompt_box.configure(bg=t["bg_inner"])
        if hasattr(self, "prompt_top"):
            self.prompt_top.configure(bg=t["bg_inner"])
        self.prompt_badge_lbl.configure(fg=t["accent_gold"], bg=t["bg_inner"])
        self.prompt_shuffle_btn.configure(bg=t["bg_card"], fg=t["accent_primary"])
        self.prompt_text_lbl.configure(fg=t["text_main"], bg=t["bg_inner"])
        if hasattr(self, "row1"):
            self.row1.configure(bg=t["bg_card"])
        if hasattr(self, "date_box"):
            self.date_box.configure(bg=t["bg_card"])
        if hasattr(self, "date_sub"):
            self.date_sub.configure(bg=t["bg_card"])
        self.date_lbl.configure(fg=t["accent_gold"], bg=t["bg_card"])
        self.date_entry.configure(bg=t["bg_inner"], fg=t["text_main"], insertbackground=t["accent_primary"])
        self.today_btn.configure(bg=t["bg_inner"], fg=t["accent_primary"])
        if hasattr(self, "act_box"):
            self.act_box.configure(bg=t["bg_card"])
        self.act_lbl.configure(fg=t["accent_gold"], bg=t["bg_card"])
        if hasattr(self, "mood_box"):
            self.mood_box.configure(bg=t["bg_card"])
        self.mood_title.configure(fg=t["accent_gold"], bg=t["bg_card"])
        self.mood_buttons_frame.configure(bg=t["bg_card"])
        if hasattr(self, "energy_box"):
            self.energy_box.configure(bg=t["bg_card"])
        if hasattr(self, "energy_header"):
            self.energy_header.configure(bg=t["bg_card"])
        self.energy_title.configure(fg=t["accent_gold"], bg=t["bg_card"])
        if hasattr(self, "text_box_frame"):
            self.text_box_frame.configure(bg=t["bg_card"])
        if hasattr(self, "text_header"):
            self.text_header.configure(bg=t["bg_card"])
        self.reflect_lbl.configure(fg=t["accent_gold"], bg=t["bg_card"])
        self.voice_btn.configure(bg=t["accent_secondary"])
        self.voice_status_lbl.configure(fg=t["accent_primary"], bg=t["bg_card"])
        self.text_area.configure(bg=t["bg_inner"], fg=t["text_main"], insertbackground=t["accent_primary"])
        self.img_section.configure(bg=t["bg_inner"])
        self.img_sec_header.configure(bg=t["bg_card"])
        self.photo_sec_lbl.configure(fg=t["accent_primary"], bg=t["bg_card"])
        if hasattr(self, "img_body"):
            self.img_body.configure(bg=t["bg_inner"])
        if hasattr(self, "img_controls"):
            self.img_controls.configure(bg=t["bg_inner"])
        if hasattr(self, "btn_row"):
            self.btn_row.configure(bg=t["bg_inner"])
        self.upload_btn.configure(bg=t["bg_card"], fg=t["accent_primary"])
        self.camera_btn.configure(bg=t["accent_green"], fg=t.get("accent_text", "#000000"))
        self.filter_lbl.configure(fg=t["text_muted"], bg=t["bg_inner"])
        self.remove_img_btn.configure(bg=t["bg_inner"])
        self.preview_container.configure(bg=t["bg_inner"])
        self.preview_lbl.configure(bg=t["bg_inner"], fg=t["text_muted"])
        if hasattr(self, "action_row"):
            self.action_row.configure(bg=t["bg_card"])
        self.save_btn.configure(bg=t["accent_primary"], fg=t.get("accent_text", "#000000"), activebackground=t["accent_secondary"])
        self.reset_btn.configure(bg=t["bg_inner"], fg=t["text_muted"])
        self._set_mood(self.selected_mood.get())
        self._on_energy_slider_change(self.energy_val.get())

    def _set_mood(self, mood_name):
        self.selected_mood.set(mood_name)
        t = self.theme
        for name, btn in self.mood_btn_map.items():
            if name == mood_name:
                btn.config(bg=t["accent_secondary"], fg="#FFFFFF", relief="sunken")
            else:
                btn.config(bg=t["bg_inner"], fg=t["text_main"], relief="raised")

    def _on_energy_slider_change(self, val):
        energy = int(float(val))
        t = self.theme
        desc = "LOW" if energy <= 3 else ("MODERATE" if energy <= 7 else "HIGH / VIBRANT")
        color = t["accent_green"] if energy >= 7 else (t["accent_gold"] if energy >= 4 else "#ff4444")
        self.energy_display_lbl.config(
            text=f"{make_pixel_bar(energy, 10, width=10)} [{desc}]",
            fg=color
        )

    def _choose_image(self):
        filetypes = [("Image files", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"), ("All files", "*.*")]
        chosen = filedialog.askopenfilename(title="Select Journal Photo", filetypes=filetypes)
        if chosen:
            self.current_image_path = chosen
            self.remove_img_btn.config(state="normal")
            self._update_image_preview()

    def _open_camera(self):
        def on_snapped(photo_path):
            self.current_image_path = photo_path
            self.remove_img_btn.config(state="normal")
            self._update_image_preview()
            messagebox.showinfo("Webcam Snapshot", "Photo captured from webcam successfully! 📸")

        CameraCaptureDialog(self, on_snapped)

    def _update_image_preview(self):
        if not self.current_image_path:
            return
        pil_img = load_image_safe(self.current_image_path)
        if pil_img:
            filtered = apply_image_filter(pil_img, self.filter_val.get())
            is_pixel = "Pixel" in self.filter_val.get() or "GameBoy" in self.filter_val.get()
            self.preview_tk_img = get_tk_image(filtered, 200, 115, is_pixel_art=is_pixel)
            self.preview_lbl.config(image=self.preview_tk_img, text="")
        else:
            self.preview_lbl.config(image="", text="[LOAD ERROR]")

    def _clear_image(self):
        self.current_image_path = None
        self.preview_tk_img = None
        self.preview_lbl.config(image="", text="[ NO PHOTO ATTACHED ]\n(FILE OR CAMERA)")
        self.remove_img_btn.config(state="disabled")

    def _start_voice_entry(self):
        if not SPEECH_REC_AVAILABLE:
            messagebox.showinfo("Voice Input", "SpeechRecognition is not installed. Type directly into terminal.")
            return

        self.voice_btn.config(state="disabled", text="[🎙️ LISTENING...]")

        def on_success(recognized_text):
            def _update():
                current = self.text_area.get("1.0", tk.END).strip()
                if current:
                    self.text_area.insert(tk.END, " " + recognized_text)
                else:
                    self.text_area.insert("1.0", recognized_text)
                self.voice_btn.config(state="normal", text="[🎙️ RECORD VOICE]")
                self.voice_status_lbl.config(text="[OK] TRANSCRIBED!")
            self.after(0, _update)

        def on_error(err_msg):
            def _update():
                self.voice_btn.config(state="normal", text="[🎙️ RECORD VOICE]")
                self.voice_status_lbl.config(text="")
                messagebox.showwarning("Voice Input", f"{err_msg}")
            self.after(0, _update)

        def on_status(status_str):
            self.after(0, lambda: self.voice_status_lbl.config(text=f"[{status_str}]"))

        self.voice_mgr.record_and_transcribe(on_success, on_error, on_status)

    def _save_entry(self):
        date_str = self.date_entry.get().strip()
        mood = self.selected_mood.get()
        energy = int(float(self.energy_val.get()))
        activity = self.activity_val.get()
        text_content = self.text_area.get("1.0", tk.END).strip()

        if not text_content:
            messagebox.showwarning("Missing Text", "Please enter reflection text before saving to cartridge.")
            return

        saved_img_rel_path = ""
        if self.current_image_path:
            saved_img_rel_path = save_processed_image(self.current_image_path, self.filter_val.get())

        success, res = add_entry(
            date_str=date_str,
            mood=mood,
            energy=energy,
            activity=activity,
            text=text_content,
            image_rel_path=saved_img_rel_path,
            is_sample=False
        )

        if success:
            messagebox.showinfo("Log Saved", "Journal entry committed to local cartridge! ★")
            self._reset_form()
            self.controller.navigate_to("timeline")
        else:
            messagebox.showerror("Save Error", f"Could not write log: {res}")

    def _reset_form(self):
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self._set_mood("Happy")
        self.energy_val.set(8)
        self.energy_slider.set(8)
        self._on_energy_slider_change(8)
        self.activity_val.set("Coding")
        self.filter_val.set("Pixel Art (8-Bit)")
        self.text_area.delete("1.0", tk.END)
        self.voice_status_lbl.config(text="")
        self._clear_image()
        self._shuffle_prompt()


# =====================================================================
# 3. RETRO TIMELINE SCREEN
# =====================================================================

class TimelineScreen(BaseScreen):
    """Theme-Aware Retro Journal Timeline."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.search_query = tk.StringVar()
        self.mood_filter = tk.StringVar(value="All Moods")
        self.act_filter = tk.StringVar(value="All Activities")
        
        self.tts_mgr = TextToSpeechManager()
        self.card_image_refs = []
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        t = self.theme
        self.filter_bar = tk.Frame(self, bg=t["bg_card"], bd=2, relief="ridge")
        self.filter_bar.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 8))
        
        self.inner_filter = tk.Frame(self.filter_bar, bg=t["bg_card"], padx=10, pady=6)
        self.inner_filter.pack(fill="x")

        self.lbl_s = tk.Label(self.inner_filter, text="SEARCH:", font=FONT_RETRO_HEADER, fg=t["accent_primary"], bg=t["bg_card"])
        self.lbl_s.pack(side="left", padx=(0, 4))
        self.search_entry = tk.Entry(self.inner_filter, textvariable=self.search_query, width=15, font=FONT_RETRO_BODY, bg=t["bg_inner"], fg=t["text_main"], insertbackground=t["accent_primary"], bd=2, relief="sunken")
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_query.trace_add("write", lambda *args: self.refresh_timeline())

        self.lbl_m = tk.Label(self.inner_filter, text="MOOD:", font=FONT_RETRO_HEADER, fg=t["accent_gold"], bg=t["bg_card"])
        self.lbl_m.pack(side="left", padx=(0, 4))
        mood_opts = ["All Moods"] + list(MOOD_MAP.keys())
        self.mood_combo = ttk.Combobox(self.inner_filter, values=mood_opts, textvariable=self.mood_filter, state="readonly", width=11, font=FONT_RETRO_BODY)
        self.mood_combo.pack(side="left", padx=(0, 10))
        self.mood_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_timeline())

        self.lbl_a = tk.Label(self.inner_filter, text="ACTIVITY:", font=FONT_RETRO_HEADER, fg=t["accent_secondary"], bg=t["bg_card"])
        self.lbl_a.pack(side="left", padx=(0, 4))
        act_opts = ["All Activities"] + ACTIVITIES
        self.act_combo = ttk.Combobox(self.inner_filter, values=act_opts, textvariable=self.act_filter, state="readonly", width=13, font=FONT_RETRO_BODY)
        self.act_combo.pack(side="left", padx=(0, 10))
        self.act_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_timeline())

        self.clear_btn = tk.Button(
            self.inner_filter,
            text="[CLEAR]",
            font=FONT_RETRO_SMALL,
            bg=t["bg_inner"],
            fg=t["text_muted"],
            relief="raised",
            bd=2,
            cursor="hand2",
            padx=6,
            command=self._clear_filters
        )
        self.clear_btn.pack(side="left")

        self.count_lbl = tk.Label(self.inner_filter, text="", font=FONT_RETRO_HEADER, fg=t["accent_green"], bg=t["bg_card"])
        self.count_lbl.pack(side="right")

        self.canvas_frame = tk.Frame(self, bg=t["bg_main"])
        self.canvas_frame.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 16))
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas_frame.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.canvas_frame, bg=t["bg_main"], highlightthickness=0)
        self.v_scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        
        self.cards_frame = tk.Frame(self.canvas, bg=t["bg_main"])
        self.cards_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_win = self.canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_win, width=e.width))
        
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        if self.canvas.winfo_exists():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _clear_filters(self):
        self.search_query.set("")
        self.mood_filter.set("All Moods")
        self.act_filter.set("All Activities")
        self.refresh_timeline()

    def apply_theme(self):
        t = self.theme
        self.configure(bg=t["bg_main"])
        if hasattr(self, "filter_bar"):
            self.filter_bar.configure(bg=t["bg_card"])
        if hasattr(self, "inner_filter"):
            self.inner_filter.configure(bg=t["bg_card"])
        if hasattr(self, "lbl_s"):
            self.lbl_s.configure(fg=t["accent_primary"], bg=t["bg_card"])
        if hasattr(self, "search_entry"):
            self.search_entry.configure(bg=t["bg_inner"], fg=t["text_main"], insertbackground=t["accent_primary"])
        if hasattr(self, "lbl_m"):
            self.lbl_m.configure(fg=t["accent_gold"], bg=t["bg_card"])
        if hasattr(self, "lbl_a"):
            self.lbl_a.configure(fg=t["accent_secondary"], bg=t["bg_card"])
        if hasattr(self, "clear_btn"):
            self.clear_btn.configure(bg=t["bg_inner"], fg=t["text_muted"])
        if hasattr(self, "count_lbl"):
            self.count_lbl.configure(fg=t["accent_green"], bg=t["bg_card"])
        if hasattr(self, "canvas_frame"):
            self.canvas_frame.configure(bg=t["bg_main"])
        if hasattr(self, "canvas"):
            self.canvas.configure(bg=t["bg_main"])
        if hasattr(self, "cards_frame"):
            self.cards_frame.configure(bg=t["bg_main"])
        self.refresh_timeline()

    def on_show(self):
        self.refresh_timeline()

    def refresh_timeline(self):
        self.card_image_refs.clear()
        for child in self.cards_frame.winfo_children():
            child.destroy()

        entries = load_entries()
        q = self.search_query.get().strip().lower()
        m_filt = self.mood_filter.get()
        a_filt = self.act_filter.get()

        filtered = []
        for e in entries:
            if q:
                combined = (e.get("text", "") + " " + e.get("activity", "") + " " + e.get("date", "")).lower()
                if q not in combined:
                    continue
            if m_filt != "All Moods" and e.get("mood") != m_filt:
                continue
            if a_filt != "All Activities" and e.get("activity") != a_filt:
                continue
            filtered.append(e)

        self.count_lbl.config(text=f"LOGS: {len(filtered)}/{len(entries)}")

        if not filtered:
            empty_box = tk.Frame(self.cards_frame, bg=self.theme["bg_card"], bd=2, relief="ridge")
            empty_box.pack(fill="x", pady=18)
            tk.Label(
                empty_box,
                text="[!] NO QUEST LOGS MATCH QUERY.",
                font=FONT_RETRO_HEADER,
                fg=self.theme["accent_gold"],
                bg=self.theme["bg_card"],
                pady=20
            ).pack()
            return

        for entry in filtered:
            self._render_timeline_card(entry)

    def _render_timeline_card(self, entry):
        t = self.theme
        entry_id = entry.get("id")
        card = tk.Frame(self.cards_frame, bg=t["bg_card"], bd=2, relief="ridge")
        card.pack(fill="x", pady=4)
        card.columnconfigure(0, weight=1)

        mood_name = entry.get("mood", "Good")
        mood_meta = MOOD_MAP.get(mood_name, {"emoji": "😊", "color": t["accent_primary"]})

        header = tk.Frame(card, bg=t["bg_card"])
        header.pack(fill="x", padx=12, pady=(8, 3))

        tk.Label(header, text=f"[ 📅 {entry.get('date', '')} ]", font=FONT_RETRO_HEADER, fg=t["accent_primary"], bg=t["bg_card"]).pack(side="left")
        tk.Label(header, text=f"{mood_meta['emoji']} {mood_name.upper()}", font=FONT_RETRO_SMALL, bg=t["accent_secondary"], fg="#FFFFFF", padx=5, pady=1).pack(side="left", padx=5)
        tk.Label(header, text=f"<{entry.get('activity', '').upper()}>", font=FONT_RETRO_SMALL, fg=t["accent_gold"], bg=t["bg_card"], padx=3).pack(side="left", padx=2)

        en = entry.get("energy", 5)
        tk.Label(header, text=make_pixel_bar(en, 10, width=5), font=FONT_RETRO_SMALL, fg=t["accent_green"], bg=t["bg_card"]).pack(side="left", padx=5)

        if entry.get("is_sample"):
            tk.Label(header, text="[SAMPLE]", font=("Consolas", 7), fg=t["text_muted"], bg=t["bg_card"]).pack(side="right")

        body = tk.Frame(card, bg=t["bg_card"])
        body.pack(fill="x", padx=12, pady=(3, 6))
        body.columnconfigure(0, weight=1)

        full_text = entry.get("text", "")
        display_text = full_text if len(full_text) <= 190 else full_text[:187] + "..."
        
        tk.Label(body, text=display_text, font=FONT_RETRO_BODY, fg=t["text_main"], bg=t["bg_card"], wraplength=560, justify="left", anchor="nw").grid(row=0, column=0, sticky="nw")

        img_path = entry.get("image", "")
        if img_path:
            pil_img = load_image_safe(img_path)
            if pil_img:
                tk_thumb = get_tk_image(pil_img, 120, 75, is_pixel_art=True)
                self.card_image_refs.append(tk_thumb)
                thumb_lbl = tk.Label(body, image=tk_thumb, bg=t["bg_card"], bd=1, relief="solid")
                thumb_lbl.grid(row=0, column=1, sticky="ne", padx=(8, 0))

        footer = tk.Frame(card, bg=t["bg_inner"], bd=1, relief="ridge")
        footer.pack(fill="x")

        tk.Button(footer, text="[👁 VIEW FULL ENTRY]", font=FONT_RETRO_SMALL, bg=t["bg_inner"], fg=t["accent_primary"], bd=0, cursor="hand2", padx=8, pady=3, command=lambda e=entry: self._show_detail_modal(e)).pack(side="left")
        tk.Button(footer, text="[🔊 READ ALOUD + BGM]", font=FONT_RETRO_SMALL, bg=t["bg_inner"], fg=t["accent_secondary"], bd=0, cursor="hand2", padx=8, pady=3, command=lambda e=entry: self._read_entry_aloud(e)).pack(side="left")
        tk.Button(footer, text="[🗑 DELETE]", font=FONT_RETRO_SMALL, bg=t["bg_inner"], fg="#ff4444", bd=0, cursor="hand2", padx=8, pady=3, command=lambda eid=entry_id: self._delete_entry(eid)).pack(side="right")

    def _show_detail_modal(self, entry):
        t = self.theme
        modal = tk.Toplevel(self)
        modal.title(f"Quest Log - {entry.get('date')}")
        modal.geometry("640x540")
        modal.configure(bg=t["bg_main"])
        modal.grab_set()

        inner = tk.Frame(modal, bg=t["bg_card"], bd=2, relief="ridge", padx=14, pady=14)
        inner.pack(fill="both", expand=True, padx=12, pady=12)

        top = tk.Frame(inner, bg=t["bg_card"])
        top.pack(fill="x", pady=(0, 8))

        mood_name = entry.get("mood", "Good")
        mood_meta = MOOD_MAP.get(mood_name, {"emoji": "😊", "color": t["accent_primary"]})

        tk.Label(top, text=f"[ 📅 {entry.get('date')} ]", font=FONT_RETRO_HEADER, fg=t["accent_primary"], bg=t["bg_card"]).pack(side="left")
        tk.Label(top, text=f"{mood_meta['emoji']} {mood_name.upper()}", font=FONT_RETRO_SMALL, bg=t["accent_secondary"], fg="#FFFFFF", padx=5, pady=1).pack(side="left", padx=6)
        tk.Label(top, text=make_pixel_bar(entry.get('energy', 5)), font=FONT_RETRO_SMALL, fg=t["accent_green"], bg=t["bg_card"]).pack(side="left")
        tk.Label(top, text=f"<{entry.get('activity', '').upper()}>", font=FONT_RETRO_SMALL, fg=t["accent_gold"], bg=t["bg_card"]).pack(side="left", padx=6)

        img_path = entry.get("image", "")
        if img_path:
            pil_img = load_image_safe(img_path)
            if pil_img:
                tk_full = get_tk_image(pil_img, 560, 200, is_pixel_art=True)
                img_lbl = tk.Label(inner, image=tk_full, bg=t["bg_card"], bd=1, relief="solid")
                img_lbl.image = tk_full
                img_lbl.pack(pady=(0, 8))

        txt = tk.Text(inner, font=FONT_RETRO_BODY, wrap="word", bg=t["bg_inner"], fg=t["text_main"], bd=2, relief="sunken", padx=8, pady=8)
        txt.insert("1.0", entry.get("text", ""))
        txt.config(state="disabled")
        txt.tag_config("word_highlight", background=t["accent_primary"], foreground="#000000", font=(FONT_RETRO_BODY[0], FONT_RETRO_BODY[1], "bold"))
        txt.pack(fill="both", expand=True, pady=(0, 10))

        bottom = tk.Frame(inner, bg=t["bg_card"])
        bottom.pack(fill="x")

        read_btn = tk.Button(bottom, text="[🔊 READ ALOUD + BGM]", font=FONT_RETRO_SMALL, bg=t["accent_secondary"], fg="#FFFFFF", relief="raised", bd=2, cursor="hand2", padx=10, pady=3)
        read_btn.config(command=lambda e=entry, tb=txt, b=read_btn: self._read_entry_aloud(e, tb, b))
        read_btn.pack(side="left")
        tk.Button(bottom, text="[CLOSE]", font=FONT_RETRO_SMALL, bg=t["bg_inner"], fg=t["text_main"], relief="raised", bd=2, cursor="hand2", padx=10, pady=3, command=modal.destroy).pack(side="right")

    def _read_entry_aloud(self, entry, text_widget=None, btn=None):
        if not PYTTSX3_AVAILABLE:
            messagebox.showinfo("Text-to-Speech", "pyttsx3 is not installed.")
            return

        text = entry.get("text", "")
        if btn and btn.winfo_exists():
            btn.config(text="[🔊 READING...]")

        def _on_word(name, location, length):
            if text_widget and text_widget.winfo_exists():
                self.after(0, lambda: self._highlight_entry_word(text_widget, location, length))

        def _on_finish():
            self.controller.ambient_manager.stop_quote_narration_music()
            if text_widget and text_widget.winfo_exists():
                self.after(0, lambda: text_widget.tag_remove("word_highlight", "1.0", "end"))
            if btn and btn.winfo_exists():
                self.after(0, lambda: btn.config(text="[🔊 READ ALOUD + BGM]"))

        self.tts_mgr.read_aloud_async(
            text=text,
            rate=125,
            on_start=self.controller.ambient_manager.start_quote_narration_music,
            on_word=_on_word,
            on_finish=_on_finish,
            on_error=lambda err: [
                _on_finish(),
                messagebox.showwarning("Speech Error", f"{err}")
            ]
        )

    def _highlight_entry_word(self, text_widget, location, length):
        try:
            if not text_widget or not text_widget.winfo_exists():
                return
            text_widget.tag_remove("word_highlight", "1.0", "end")
            if location is not None and length and length > 0:
                start_idx = f"1.0 + {location} chars"
                end_idx = f"1.0 + {location + length} chars"
                text_widget.tag_add("word_highlight", start_idx, end_idx)
                text_widget.see(start_idx)
        except Exception:
            pass

    def _delete_entry(self, entry_id):
        if messagebox.askyesno("Confirm Delete", "Permanently delete this quest log?"):
            delete_entry(entry_id)
            self.refresh_timeline()


# =====================================================================
# 4. RETRO INSIGHTS SCREEN
# =====================================================================

class InsightsScreen(BaseScreen):
    """Theme-Aware Retro Analytics Radar."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        t = self.theme
        self.header = tk.Frame(self, bg=t["bg_main"])
        self.header.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 8))
        
        self.radar_title = tk.Label(
            self.header,
            text="★ RETRO ANALYTICS & INSIGHTS RADAR ★",
            font=("Consolas", 14, "bold"),
            fg=t["accent_primary"],
            bg=t["bg_main"]
        )
        self.radar_title.pack(side="left")

        self.print_report_btn = tk.Button(
            self.header,
            text="[ 🖨️ REPORTS & CONCLUSION ]",
            font=FONT_RETRO_SMALL,
            bg=t["accent_primary"],
            fg=t.get("accent_text", "#000000"),
            activebackground=t["accent_secondary"],
            relief="raised",
            bd=2,
            cursor="hand2",
            padx=10,
            pady=4,
            command=lambda: self.controller.navigate_to("reports")
        )
        self.print_report_btn.pack(side="right")

        self.chart_scroll_canvas = tk.Canvas(self, bg=t["bg_main"], highlightthickness=0)
        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.chart_scroll_canvas.yview)
        
        self.charts_inner_frame = tk.Frame(self.chart_scroll_canvas, bg=t["bg_main"])
        self.charts_inner_frame.bind("<Configure>", lambda e: self.chart_scroll_canvas.configure(scrollregion=self.chart_scroll_canvas.bbox("all")))
        self.canvas_window = self.chart_scroll_canvas.create_window((0, 0), window=self.charts_inner_frame, anchor="nw")
        self.chart_scroll_canvas.bind("<Configure>", lambda e: self.chart_scroll_canvas.itemconfig(self.canvas_window, width=e.width))

        self.chart_scroll_canvas.configure(yscrollcommand=v_scroll.set)
        self.chart_scroll_canvas.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 16))
        v_scroll.grid(row=1, column=1, sticky="ns", pady=(0, 16))

        self.charts_inner_frame.columnconfigure(0, weight=1)

    def apply_theme(self):
        t = self.theme
        self.configure(bg=t["bg_main"])
        self.header.configure(bg=t["bg_main"])
        self.radar_title.configure(fg=t["accent_primary"], bg=t["bg_main"])
        if hasattr(self, "print_report_btn"):
            self.print_report_btn.configure(
                bg=t["accent_primary"],
                fg=t.get("accent_text", "#000000"),
                activebackground=t["accent_secondary"]
            )
        self.chart_scroll_canvas.configure(bg=t["bg_main"])
        self.charts_inner_frame.configure(bg=t["bg_main"])
        self.refresh_insights()

    def on_show(self):
        self.refresh_insights()

    def refresh_insights(self):
        t = self.theme
        for child in self.charts_inner_frame.winfo_children():
            child.destroy()

        stats = get_statistics()
        if stats["total_entries"] == 0:
            tk.Label(
                self.charts_inner_frame,
                text="[!] NO LOG DATA IN CARTRIDGE.",
                font=FONT_RETRO_HEADER,
                fg=t["accent_gold"],
                bg=t["bg_main"],
                pady=40
            ).pack()
            return

        banner = tk.Frame(self.charts_inner_frame, bg=t["bg_card"], bd=2, relief="ridge")
        banner.pack(fill="x", pady=(0, 12))
        for i in range(3):
            banner.columnconfigure(i, weight=1)

        self._stat_box(banner, 0, "TOTAL LOGS", str(stats["total_entries"]), t["accent_primary"])
        self._stat_box(banner, 1, "AVG STAMINA", f"{stats['avg_energy']}/10", t["accent_green"])
        self._stat_box(banner, 2, "TOP EMOTION", f"{stats['top_mood_emoji']} {stats['top_mood'].upper()}", t["accent_gold"])

        charts_card = tk.Frame(self.charts_inner_frame, bg=t["bg_card"], bd=2, relief="ridge", padx=10, pady=10)
        charts_card.pack(fill="both", expand=True)

        fig = Figure(figsize=(8.5, 7.5), dpi=95, facecolor=t["bg_card"])
        
        # Subplot 1: Mood Distribution
        ax1 = fig.add_subplot(221)
        ax1.set_facecolor(t["bg_card"])
        ax1.set_title("MOOD SPECTRUM", fontfamily=FONT_MONO, fontsize=9, fontweight="bold", color=t["accent_primary"], pad=8)
        
        active_moods = {k: v for k, v in stats.get("mood_counts", {}).items() if v > 0}
        if active_moods:
            labels = [k.upper() for k in active_moods.keys()]
            colors = t.get("chart_colors", [t["accent_primary"], t["accent_secondary"]])[:len(labels)]
            wedges, texts, autotexts = ax1.pie(
                list(active_moods.values()),
                labels=labels,
                colors=colors,
                autopct="%1.0f%%",
                startangle=140,
                pctdistance=0.75,
                wedgeprops=dict(width=0.45, edgecolor=t["bg_main"], linewidth=2)
            )
            for txt in texts:
                txt.set_fontsize(7)
                txt.set_fontfamily(FONT_MONO)
                txt.set_color(t["text_main"])
            for at in autotexts:
                at.set_fontsize(7)
                at.set_weight("bold")
                at.set_color("#000000")
        else:
            ax1.text(0.5, 0.5, "NO MOOD DATA", ha="center", va="center", color=t["text_muted"], fontfamily=FONT_MONO)
            ax1.axis("off")

        # Subplot 2: Activity Breakdown
        ax2 = fig.add_subplot(222)
        ax2.set_facecolor(t["bg_card"])
        ax2.set_title("ACTIVITY BREAKDOWN", fontfamily=FONT_MONO, fontsize=9, fontweight="bold", color=t["accent_gold"], pad=8)
        
        acts = stats.get("activity_counts", {})
        sorted_acts = sorted(acts.items(), key=lambda x: x[1], reverse=False)
        if sorted_acts:
            act_names = [a[0].upper() for a in sorted_acts]
            act_vals = [a[1] for a in sorted_acts]
            ax2.barh(act_names, act_vals, color=t["accent_secondary"], height=0.55, edgecolor=t["border"])
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['left'].set_color(t["border"])
            ax2.spines['bottom'].set_color(t["border"])
            ax2.tick_params(colors=t["text_main"], labelsize=7)
            ax2.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
        else:
            ax2.text(0.5, 0.5, "NO ACTIVITY DATA", ha="center", va="center", color=t["text_muted"], fontfamily=FONT_MONO)
            ax2.axis("off")

        # Subplot 3: Energy Waveform
        ax3 = fig.add_subplot(212)
        ax3.set_facecolor(t.get("bg_inner", "#111122"))
        ax3.set_title(">> ENERGY LEVEL OSCILLATION WAVEFORM", fontfamily=FONT_MONO, fontsize=9.5, fontweight="bold", color=t.get("accent_primary", "#00f0ff"), pad=8)

        trend = stats.get("energy_trend", [])
        waveform_color = t.get("accent_primary", "#00f0ff")
        gold_marker = t.get("accent_gold", "#ffd700")
        grid_color = t.get("accent_primary", "#00f0ff")
        border_color = t.get("border", "#3d3a68")

        if trend and len(trend) > 1:
            dates = [tr[0] for tr in trend]
            energies = [tr[1] for tr in trend]
            
            # Bright luminous waveform line and vivid fill area
            ax3.step(dates, energies, where='mid', color=waveform_color, linewidth=3, zorder=3)
            ax3.plot(dates, energies, 'o', color=gold_marker, markersize=7, markeredgecolor="#ffffff", markeredgewidth=1.5, zorder=4)
            ax3.fill_between(dates, energies, step='mid', color=waveform_color, alpha=0.35, zorder=2)
            
            # Value badges on each point for instant clarity
            for d, val in zip(dates, energies):
                ax3.text(d, val + 0.45, f"{int(val) if val == int(val) else val}", 
                         ha="center", va="bottom", fontsize=7.5, fontweight="bold", 
                         color=gold_marker, fontfamily=FONT_MONO, zorder=5)

            ax3.set_ylim(0, 11)
            ax3.set_ylabel("ENERGY (1-10)", fontfamily=FONT_MONO, fontsize=7.5, fontweight="bold", color=t["text_main"])
            ax3.grid(True, linestyle="--", alpha=0.35, color=grid_color)
            ax3.spines['top'].set_visible(False)
            ax3.spines['right'].set_visible(False)
            ax3.spines['left'].set_color(border_color)
            ax3.spines['left'].set_linewidth(1.2)
            ax3.spines['bottom'].set_color(border_color)
            ax3.spines['bottom'].set_linewidth(1.2)
            ax3.tick_params(axis='x', colors=t["text_main"], labelsize=7.5)
            ax3.tick_params(axis='y', colors=t["text_main"], labelsize=7.5)
            fig.autofmt_xdate()
        elif trend and len(trend) == 1:
            d_single, val_single = trend[0][0], trend[0][1]
            ax3.axhline(y=val_single, color=waveform_color, linestyle="--", linewidth=2.5, alpha=0.85, zorder=2)
            ax3.plot([d_single], [val_single], marker='o', color=gold_marker, markersize=10, markeredgecolor="#ffffff", markeredgewidth=2, zorder=4)
            ax3.text(d_single, val_single + 0.6, f"STAMINA: {val_single}/10", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=gold_marker, fontfamily=FONT_MONO, zorder=5)
            ax3.set_ylim(0, 11)
            ax3.set_ylabel("ENERGY (1-10)", fontfamily=FONT_MONO, fontsize=7.5, fontweight="bold", color=t["text_main"])
            ax3.grid(True, linestyle="--", alpha=0.35, color=grid_color)
            ax3.spines['top'].set_visible(False)
            ax3.spines['right'].set_visible(False)
            ax3.spines['left'].set_color(border_color)
            ax3.spines['left'].set_linewidth(1.2)
            ax3.spines['bottom'].set_color(border_color)
            ax3.spines['bottom'].set_linewidth(1.2)
            ax3.tick_params(axis='x', colors=t["text_main"], labelsize=7.5)
            ax3.tick_params(axis='y', colors=t["text_main"], labelsize=7.5)
        else:
            ax3.text(0.5, 0.5, "LOG ENTRIES TO VISUALIZE OSCILLATION", ha="center", va="center", color=gold_marker, fontfamily=FONT_MONO, fontweight="bold")
            ax3.axis("off")

        fig.tight_layout(pad=1.8)
        canvas = FigureCanvasTkAgg(fig, master=charts_card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _stat_box(self, parent, col, title, val, color):
        t = self.theme
        frame = tk.Frame(parent, bg=t["bg_card"], padx=10, pady=8)
        frame.grid(row=0, column=col, sticky="ew")
        
        tk.Label(frame, text=f"// {title}", font=FONT_RETRO_SMALL, fg=t["text_muted"], bg=t["bg_card"]).pack(anchor="w")
        tk.Label(frame, text=val, font=("Consolas", 12, "bold"), fg=color, bg=t["bg_card"]).pack(anchor="w", pady=(1, 0))


# =====================================================================
# 5. RETRO ABOUT & AUDIO MIXER SETTINGS SCREEN
# =====================================================================

class AboutScreen(BaseScreen):
    """Specification, Audio Level Mixer & Personality Cartridge Screen."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        t = self.theme
        self.canvas = tk.Canvas(self, bg=t["bg_main"], highlightthickness=0)
        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=t["bg_main"])

        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        canvas_win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(canvas_win, width=e.width))

        self.canvas.configure(yscrollcommand=v_scroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        self.inner.columnconfigure(0, weight=1)

        self.card = tk.Frame(self.inner, bg=t["bg_card"], bd=2, relief="ridge", padx=18, pady=14)
        self.card.grid(row=0, column=0, sticky="ew", padx=24, pady=18)
        self.card.columnconfigure(0, weight=1)

        self.title_lbl = tk.Label(
            self.card,
            text="★ LIFELENS – MULTIMEDIA RETRO SPECIFICATION & SETTINGS ★",
            font=("Consolas", 13, "bold"),
            fg=t["accent_primary"],
            bg=t["bg_card"]
        )
        self.title_lbl.pack(anchor="w", pady=(0, 4))

        self.subtitle_desc = tk.Label(
            self.card,
            text=f">> DUAL-TRACK AUDIO MIXER // 365 REFLECTIONS // {len(PERSONALITY_THEMES)} PERSONALITY THEMES",
            font=FONT_RETRO_SMALL,
            fg=t["text_muted"],
            bg=t["bg_card"]
        )
        self.subtitle_desc.pack(anchor="w", pady=(0, 12))

        # -------------------------------------------------------------
        # DUAL AUDIO MIXER & SOUNDTRACK SETTINGS CARTRIDGE
        # -------------------------------------------------------------
        self.audio_card = tk.Frame(self.card, bg=t["bg_inner"], bd=2, relief="ridge", padx=12, pady=10)
        self.audio_card.pack(fill="x", pady=(0, 14))

        self.mixer_title = tk.Label(
            self.audio_card,
            text="[ 🎚️ DUAL-TRACK AUDIO MIXER & SOUNDTRACK SETTINGS ]",
            font=FONT_RETRO_HEADER,
            fg=t["accent_gold"],
            bg=t["bg_inner"]
        )
        self.mixer_title.pack(anchor="w", pady=(0, 8))

        mixer_grid = tk.Frame(self.audio_card, bg=t["bg_inner"])
        mixer_grid.pack(fill="x")
        mixer_grid.columnconfigure(0, weight=1)
        mixer_grid.columnconfigure(1, weight=1)

        # Track 1: App Ambient BGM Volume & Track
        self.app_bgm_box = tk.Frame(mixer_grid, bg=t["bg_inner"], padx=6, pady=4)
        self.app_bgm_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        self.app_vol_lbl = tk.Label(
            self.app_bgm_box,
            text=f"🎵 APP AMBIENT BGM: {int(self.controller.ambient_manager.app_bgm_vol * 100)}%",
            font=FONT_RETRO_SMALL,
            fg=t["accent_primary"],
            bg=t["bg_inner"]
        )
        self.app_vol_lbl.pack(anchor="w", pady=(0, 2))

        self.app_vol_scale = ttk.Scale(
            self.app_bgm_box,
            from_=0,
            to=100,
            orient="horizontal",
            value=int(self.controller.ambient_manager.app_bgm_vol * 100),
            command=self._on_app_vol_change
        )
        self.app_vol_scale.pack(fill="x", pady=(0, 4))

        self.app_track_lbl = tk.Label(
            self.app_bgm_box,
            text=f">> FILE: {self.controller.ambient_manager.app_track_name}",
            font=FONT_RETRO_SMALL,
            fg=t["text_muted"],
            bg=t["bg_inner"]
        )
        self.app_track_lbl.pack(anchor="w", pady=(0, 4))

        app_btn_row = tk.Frame(self.app_bgm_box, bg=t["bg_inner"])
        app_btn_row.pack(fill="x")

        self.app_change_btn = tk.Button(
            app_btn_row,
            text="[ 📁 CHANGE BGM ]",
            font=FONT_RETRO_SMALL,
            bg=t["bg_card"],
            fg=t["accent_primary"],
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self._on_choose_app_track
        )
        self.app_change_btn.pack(side="left", padx=(0, 4))

        self.app_preview_btn = tk.Button(
            app_btn_row,
            text="[ ▶ TOGGLE BGM ]",
            font=FONT_RETRO_SMALL,
            bg=t["bg_card"],
            fg=t["accent_gold"],
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self._on_toggle_app_preview
        )
        self.app_preview_btn.pack(side="left")

        # Track 2: Quote Reading BGM Volume & Track (golden-brown.mp3)
        self.quote_bgm_box = tk.Frame(mixer_grid, bg=t["bg_inner"], padx=6, pady=4)
        self.quote_bgm_box.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self.quote_vol_lbl = tk.Label(
            self.quote_bgm_box,
            text=f"🎙️ QUOTE READING BGM: {int(self.controller.ambient_manager.quote_bgm_vol * 100)}%",
            font=FONT_RETRO_SMALL,
            fg=t["accent_secondary"],
            bg=t["bg_inner"]
        )
        self.quote_vol_lbl.pack(anchor="w", pady=(0, 2))

        self.quote_vol_scale = ttk.Scale(
            self.quote_bgm_box,
            from_=0,
            to=100,
            orient="horizontal",
            value=int(self.controller.ambient_manager.quote_bgm_vol * 100),
            command=self._on_quote_vol_change
        )
        self.quote_vol_scale.pack(fill="x", pady=(0, 4))

        self.quote_track_lbl = tk.Label(
            self.quote_bgm_box,
            text=f">> FILE: {self.controller.ambient_manager.quote_track_name}",
            font=FONT_RETRO_SMALL,
            fg=t["accent_gold"],
            bg=t["bg_inner"]
        )
        self.quote_track_lbl.pack(anchor="w", pady=(0, 4))

        quote_btn_row = tk.Frame(self.quote_bgm_box, bg=t["bg_inner"])
        quote_btn_row.pack(fill="x")

        self.quote_change_btn = tk.Button(
            quote_btn_row,
            text="[ 📁 CHANGE QUOTE MUSIC ]",
            font=FONT_RETRO_SMALL,
            bg=t["bg_card"],
            fg=t["accent_secondary"],
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self._on_choose_quote_track
        )
        self.quote_change_btn.pack(side="left", padx=(0, 4))

        self.quote_preview_btn = tk.Button(
            quote_btn_row,
            text="[ ▶ TEST QUOTE BGM ]",
            font=FONT_RETRO_SMALL,
            bg=t["bg_card"],
            fg=t["accent_gold"],
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self._on_toggle_quote_preview
        )
        self.quote_preview_btn.pack(side="left")

        # -------------------------------------------------------------
        # VIRTUAL COMPANION & SLIDING PET SETTINGS CARTRIDGE
        # -------------------------------------------------------------
        self.pet_card = tk.Frame(self.card, bg=t["bg_inner"], bd=2, relief="ridge", padx=12, pady=10)
        self.pet_card.pack(fill="x", pady=(0, 14))

        self.pet_title = tk.Label(
            self.pet_card,
            text="[ 🐾 VIRTUAL COMPANION & SLIDING PET CONTROLS ]",
            font=FONT_RETRO_HEADER,
            fg=t["accent_gold"],
            bg=t["bg_inner"]
        )
        self.pet_title.pack(anchor="w", pady=(0, 8))

        pet_grid = tk.Frame(self.pet_card, bg=t["bg_inner"])
        pet_grid.pack(fill="x")
        pet_grid.columnconfigure(0, weight=1)
        pet_grid.columnconfigure(1, weight=1)

        # Left Column: Pet Status, Model Picker, Sleep Toggle
        self.pet_left_box = tk.Frame(pet_grid, bg=t["bg_inner"], padx=6, pady=4)
        self.pet_left_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.pet_status_lbl = tk.Label(
            self.pet_left_box,
            text="STATUS: 🐾 ACTIVE (SLIDING ACROSS SCREEN)" if not self.controller.pet_manager.is_sleeping else "STATUS: 💤 SLEEPING (HIDDEN)",
            font=FONT_RETRO_SMALL,
            fg=t["accent_green"] if not self.controller.pet_manager.is_sleeping else t["text_muted"],
            bg=t["bg_inner"]
        )
        self.pet_status_lbl.pack(anchor="w", pady=(0, 4))

        pet_btn_row = tk.Frame(self.pet_left_box, bg=t["bg_inner"])
        pet_btn_row.pack(fill="x", pady=(0, 8))

        self.pet_sleep_btn = tk.Button(
            pet_btn_row,
            text="[ 💤 MAKE PET SLEEP ]" if not self.controller.pet_manager.is_sleeping else "[ 🐾 WAKE UP COMPANION ]",
            font=FONT_RETRO_SMALL,
            bg=t["bg_card"],
            fg=t["accent_gold"] if not self.controller.pet_manager.is_sleeping else t["accent_primary"],
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self._on_toggle_pet_sleep
        )
        self.pet_sleep_btn.pack(side="left", padx=(0, 6))

        self.pet_gif_btn = tk.Button(
            pet_btn_row,
            text="[ 📁 LOAD CUSTOM GIF ]",
            font=FONT_RETRO_SMALL,
            bg=t["bg_card"],
            fg=t["accent_primary"],
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self._on_choose_custom_pet_gif
        )
        self.pet_gif_btn.pack(side="left")

        # Pet Type Selector
        tk.Label(
            self.pet_left_box,
            text="// CHOOSE PET MODEL (OR CUSTOM GIF):",
            font=FONT_RETRO_SMALL,
            fg=t["text_muted"],
            bg=t["bg_inner"]
        ).pack(anchor="w", pady=(0, 2))

        self.pet_combo = ttk.Combobox(
            self.pet_left_box,
            values=["Pixel Cyber Cat", "8-Bit Space Dog", "Retro Dino", "Custom GIF"],
            state="readonly",
            font=(FONT_MONO, 8)
        )
        self.pet_combo.set(self.controller.pet_manager.pet_type)
        self.pet_combo.pack(fill="x")
        self.pet_combo.bind("<<ComboboxSelected>>", self._on_pet_type_change)

        # Right Column: Walk Speed & File Info
        self.pet_right_box = tk.Frame(pet_grid, bg=t["bg_inner"], padx=6, pady=4)
        self.pet_right_box.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self.pet_speed_lbl = tk.Label(
            self.pet_right_box,
            text=f"🏃 SLIDE SPEED: {self.controller.pet_manager.speed} PX / STEP",
            font=FONT_RETRO_SMALL,
            fg=t["accent_primary"],
            bg=t["bg_inner"]
        )
        self.pet_speed_lbl.pack(anchor="w", pady=(0, 2))

        self.pet_speed_scale = ttk.Scale(
            self.pet_right_box,
            from_=1,
            to=10,
            orient="horizontal",
            value=self.controller.pet_manager.speed,
            command=self._on_pet_speed_change
        )
        self.pet_speed_scale.pack(fill="x", pady=(0, 6))

        self.pet_file_lbl = tk.Label(
            self.pet_right_box,
            text=f">> ACTIVE MEDIA: {os.path.basename(self.controller.pet_manager.get_resolved_path() or 'default_pet.gif')}",
            font=FONT_RETRO_SMALL,
            fg=t["text_muted"],
            bg=t["bg_inner"]
        )
        self.pet_file_lbl.pack(anchor="w")

        # Personalities List
        self.pers_title = tk.Label(
            self.card,
            text=f"[ ■ {len(PERSONALITY_THEMES)} PERSONALITY THEMES INCLUDED ■ ]",
            font=FONT_RETRO_HEADER,
            fg=t["accent_gold"],
            bg=t["bg_card"]
        )
        self.pers_title.pack(anchor="w", pady=(4, 6))

        self.pers_frame = tk.Frame(self.card, bg=t["bg_inner"], bd=1, relief="solid", padx=10, pady=8)
        self.pers_frame.pack(fill="x", pady=(0, 12))

        self.tech_title = tk.Label(
            self.card,
            text="[ ■ TECHNOLOGY & LIBRARIES SPECIFICATION TABLE ■ ]",
            font=FONT_RETRO_HEADER,
            fg=t["accent_gold"],
            bg=t["bg_card"]
        )
        self.tech_title.pack(anchor="w", pady=(4, 6))

        self.tech_table = tk.Frame(self.card, bg=t["bg_card"], bd=1, relief="solid")
        self.tech_table.pack(fill="x", pady=(0, 12))
        self.tech_table.columnconfigure(0, weight=1)
        self.tech_table.columnconfigure(1, weight=2)
        self.tech_table.columnconfigure(2, weight=2)

        self._rebuild_pers_list()
        self._rebuild_tech_table()

    def _rebuild_pers_list(self):
        t = self.theme
        if hasattr(self, "pers_title"):
            self.pers_title.configure(text=f"[ ■ {len(PERSONALITY_THEMES)} PERSONALITY THEMES INCLUDED ■ ]", fg=t["accent_gold"], bg=t["bg_card"])
        if hasattr(self, "pers_frame"):
            self.pers_frame.configure(bg=t["bg_inner"])
            for child in self.pers_frame.winfo_children():
                child.destroy()
            for p_name, p_meta in PERSONALITY_THEMES.items():
                p_row = tk.Frame(self.pers_frame, bg=t["bg_inner"])
                p_row.pack(fill="x", pady=1)
                tk.Label(p_row, text=f"{p_meta['emoji']} {p_meta['name'].upper()}", font=FONT_RETRO_SMALL, fg=p_meta["accent_primary"], bg=t["bg_inner"]).pack(side="left")
                tk.Label(p_row, text=f":: {p_meta['tagline']}", font=FONT_RETRO_SMALL, fg=t["text_muted"], bg=t["bg_inner"]).pack(side="left", padx=6)

    def _rebuild_tech_table(self):
        t = self.theme
        if hasattr(self, "tech_title"):
            self.tech_title.configure(fg=t["accent_gold"], bg=t["bg_card"])
        if hasattr(self, "tech_table"):
            self.tech_table.configure(bg=t["bg_card"])
            for child in self.tech_table.winfo_children():
                child.destroy()

            h0 = tk.Label(self.tech_table, text="LIBRARY", font=FONT_RETRO_HEADER, bg=t["bg_inner"], fg=t["accent_primary"], padx=8, pady=4, anchor="w")
            h0.grid(row=0, column=0, sticky="ew")
            h1 = tk.Label(self.tech_table, text="ROLE / PURPOSE", font=FONT_RETRO_HEADER, bg=t["bg_inner"], fg=t["accent_primary"], padx=8, pady=4, anchor="w")
            h1.grid(row=0, column=1, sticky="ew")
            h2 = tk.Label(self.tech_table, text="WHERE USED IN APP", font=FONT_RETRO_HEADER, bg=t["bg_inner"], fg=t["accent_primary"], padx=8, pady=4, anchor="w")
            h2.grid(row=0, column=2, sticky="ew")

            rows = [
                ("Tkinter", "GUI and navigation", f"Dynamic {len(PERSONALITY_THEMES)}-personality theme windows & Sliding Pet"),
                ("Pillow", "Image processing & Animated GIFs", "8-Bit pixel filters & Pet GIF playback"),
                ("OpenCV (cv2)", "Camera capture", "Live webcam snapshot upload"),
                ("SpeechRecognition", "Voice input", "Voice Entry (Speech-to-Text)"),
                ("pyttsx3", "Text-to-speech", "Read Aloud entries & 365 quotes (0.75x)"),
                ("Pygame", "Dual-Track Audio", "App BGM + golden-brown.mp3 Quote Narration Music"),
                ("Matplotlib", "Charts and analytics", "Personality-themed Insights radar & Energy Waveform"),
                ("JSON / Quotes DB", "Local data storage", "365+ quotes, settings.json & pet storage")
            ]

            for i, (lib, purp, where) in enumerate(rows, start=1):
                bg_row = t["bg_card"] if i % 2 != 0 else t["bg_inner"]
                tk.Label(self.tech_table, text=lib, font=FONT_RETRO_SMALL, bg=bg_row, fg=t["accent_gold"], padx=8, pady=4, anchor="w").grid(row=i, column=0, sticky="ew")
                tk.Label(self.tech_table, text=purp, font=FONT_RETRO_SMALL, bg=bg_row, fg=t["text_muted"], padx=8, pady=4, anchor="w").grid(row=i, column=1, sticky="ew")
                tk.Label(self.tech_table, text=where, font=FONT_RETRO_SMALL, bg=bg_row, fg=t["text_main"], padx=8, pady=4, anchor="w").grid(row=i, column=2, sticky="ew")

    def _on_app_vol_change(self, val):
        pct = int(float(val))
        vol_float = pct / 100.0
        self.controller.ambient_manager.set_app_bgm_volume(vol_float)
        self.app_vol_lbl.config(text=f"🎵 APP AMBIENT BGM: {pct}%")

    def _on_quote_vol_change(self, val):
        pct = int(float(val))
        vol_float = pct / 100.0
        self.controller.ambient_manager.set_quote_bgm_volume(vol_float)
        self.quote_vol_lbl.config(text=f"🎙️ QUOTE READING BGM: {pct}%")

    def _on_choose_app_track(self):
        fpath = filedialog.askopenfilename(
            title="Select App Background Music (MP3/WAV/OGG)",
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.mid"), ("All Files", "*.*")]
        )
        if fpath:
            self.controller.ambient_manager.set_app_track(fpath)
            self.app_track_lbl.config(text=f">> FILE: {self.controller.ambient_manager.app_track_name}")
            messagebox.showinfo("Audio Updated", f"App BGM set to: {os.path.basename(fpath)}")

    def _on_choose_quote_track(self):
        fpath = filedialog.askopenfilename(
            title="Select Quote Narration Music (MP3/WAV/OGG)",
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.mid"), ("All Files", "*.*")]
        )
        if fpath:
            self.controller.ambient_manager.set_quote_track(fpath)
            self.quote_track_lbl.config(text=f">> FILE: {self.controller.ambient_manager.quote_track_name}")
            messagebox.showinfo("Audio Updated", f"Quote narration music set to: {os.path.basename(fpath)}")

    def _on_toggle_app_preview(self):
        playing, msg = self.controller.ambient_manager.toggle()
        if playing:
            self.app_preview_btn.config(text="[ ■ STOP BGM ]")
        else:
            self.app_preview_btn.config(text="[ ▶ TOGGLE BGM ]")

    def _on_toggle_quote_preview(self):
        playing, msg = self.controller.ambient_manager.preview_quote_bgm()
        if playing:
            self.quote_preview_btn.config(text="[ ■ STOP QUOTE BGM ]")
        else:
            self.quote_preview_btn.config(text="[ ▶ TEST QUOTE BGM ]")

    def _on_toggle_pet_sleep(self):
        self.controller.toggle_pet_sleep()
        self.refresh_pet_ui()

    def _on_pet_type_change(self, event=None):
        val = self.pet_combo.get()
        self.controller.pet_manager.set_pet_type(val)
        self.refresh_pet_ui()

    def _on_choose_custom_pet_gif(self):
        fpath = filedialog.askopenfilename(
            title="Select Pet Animation GIF (*.gif)",
            filetypes=[("GIF Animations", "*.gif"), ("All Files", "*.*")]
        )
        if fpath:
            ok, msg = self.controller.pet_manager.load_custom_gif(fpath)
            if ok:
                self.pet_combo.set("Custom GIF")
                self.refresh_pet_ui()
                messagebox.showinfo("Pet Updated", msg)
            else:
                messagebox.showerror("Invalid File", msg)

    def _on_pet_speed_change(self, val):
        spd = int(float(val))
        self.controller.pet_manager.set_speed(spd)
        self.pet_speed_lbl.config(text=f"🏃 SLIDE SPEED: {spd} PX / STEP")

    def refresh_pet_ui(self):
        t = self.theme
        is_sleeping = self.controller.pet_manager.is_sleeping
        if hasattr(self, "pet_status_lbl"):
            self.pet_status_lbl.config(
                text="STATUS: 🐾 ACTIVE (SLIDING ACROSS SCREEN)" if not is_sleeping else "STATUS: 💤 SLEEPING (HIDDEN)",
                fg=t["accent_green"] if not is_sleeping else t["text_muted"]
            )
        if hasattr(self, "pet_sleep_btn"):
            self.pet_sleep_btn.config(
                text="[ 💤 MAKE PET SLEEP ]" if not is_sleeping else "[ 🐾 WAKE UP COMPANION ]",
                fg=t["accent_gold"] if not is_sleeping else t["accent_primary"]
            )
        if hasattr(self, "pet_file_lbl"):
            path = self.controller.pet_manager.get_resolved_path() or "default_pet.gif"
            self.pet_file_lbl.config(text=f">> ACTIVE MEDIA: {os.path.basename(path)}")
        if hasattr(self, "pet_combo"):
            self.pet_combo.set(self.controller.pet_manager.pet_type)

    def apply_theme(self):
        t = self.theme
        self.configure(bg=t["bg_main"])
        self.canvas.configure(bg=t["bg_main"])
        self.inner.configure(bg=t["bg_main"])
        self.card.configure(bg=t["bg_card"])
        self.title_lbl.configure(fg=t["accent_primary"], bg=t["bg_card"])
        self.audio_card.configure(bg=t["bg_inner"])
        self.mixer_title.configure(fg=t["accent_gold"], bg=t["bg_inner"])
        
        self.app_bgm_box.configure(bg=t["bg_inner"])
        self.app_vol_lbl.configure(fg=t["accent_primary"], bg=t["bg_inner"])
        self.app_track_lbl.configure(fg=t["text_muted"], bg=t["bg_inner"])
        self.app_change_btn.configure(bg=t["bg_card"], fg=t["accent_primary"])
        self.app_preview_btn.configure(bg=t["bg_card"], fg=t["accent_gold"])

        self.quote_bgm_box.configure(bg=t["bg_inner"])
        self.quote_vol_lbl.configure(fg=t["accent_secondary"], bg=t["bg_inner"])
        self.quote_track_lbl.configure(fg=t["accent_gold"], bg=t["bg_inner"])
        self.quote_change_btn.configure(bg=t["bg_card"], fg=t["accent_secondary"])
        self.quote_preview_btn.configure(bg=t["bg_card"], fg=t["accent_gold"])

        if hasattr(self, "pet_card"):
            self.pet_card.configure(bg=t["bg_inner"])
            self.pet_title.configure(fg=t["accent_gold"], bg=t["bg_inner"])
            self.pet_left_box.configure(bg=t["bg_inner"])
            self.pet_right_box.configure(bg=t["bg_inner"])
            self.pet_sleep_btn.configure(bg=t["bg_card"])
            self.pet_gif_btn.configure(bg=t["bg_card"], fg=t["accent_primary"])
            self.refresh_pet_ui()

        if hasattr(self, "subtitle_desc"):
            self.subtitle_desc.configure(fg=t["text_muted"], bg=t["bg_card"], text=f">> DUAL-TRACK AUDIO MIXER // 365 REFLECTIONS // {len(PERSONALITY_THEMES)} PERSONALITY THEMES")

        self.pers_title.configure(fg=t["accent_gold"], bg=t["bg_card"])
        self.pers_frame.configure(bg=t["bg_inner"])
        self.tech_title.configure(fg=t["accent_gold"], bg=t["bg_card"])
        self._rebuild_pers_list()
        self._rebuild_tech_table()


# =====================================================================
# 6. RETRO EXECUTIVE REPORTS & CONCLUSION SCREEN
# =====================================================================

class ReportsScreen(BaseScreen):
    """
    Weekly & Monthly Executive Journal Reports & Conclusion Screen.
    Synthesizes clinical wellness evaluations, behavioral correlations,
    and lifestyle prescriptions with interactive in-app viewing and 1-click printing.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.current_period = "weekly"
        self.tts_manager = TextToSpeechManager()
        self.is_speaking_conclusion = False
        self.current_report_data = None
        self._toast_job = None
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        t = self.theme

        # 1. Header Frame
        self.header_frame = tk.Frame(self, bg=t["bg_main"])
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 4))
        self.header_frame.columnconfigure(0, weight=1)

        self.title_lbl = tk.Label(
            self.header_frame,
            text="★ EXECUTIVE JOURNAL REPORTS & CONCLUSION ★",
            font=("Consolas", 14, "bold"),
            fg=t["accent_primary"],
            bg=t["bg_main"]
        )
        self.title_lbl.pack(anchor="w")

        self.subtitle_lbl = tk.Label(
            self.header_frame,
            text="// Automated Behavioral Synthesis • Clinical Wellness Conclusions • Printable PDF Artifacts",
            font=FONT_RETRO_SMALL,
            fg=t["text_muted"],
            bg=t["bg_main"]
        )
        self.subtitle_lbl.pack(anchor="w", pady=(2, 0))

        # 2. Controls & Actions Toolbar
        self.controls_bar = tk.Frame(self, bg=t["bg_main"])
        self.controls_bar.grid(row=1, column=0, sticky="ew", padx=24, pady=(6, 4))
        self.controls_bar.columnconfigure(0, weight=1)
        self.controls_bar.columnconfigure(1, weight=1)

        # Left: Period Selector Tabs
        self.tabs_frame = tk.Frame(self.controls_bar, bg=t["bg_main"])
        self.tabs_frame.grid(row=0, column=0, sticky="w")

        self.tab_weekly = tk.Button(
            self.tabs_frame,
            text="[ 📅 WEEKLY (7 DAYS) ]",
            font=FONT_RETRO_SMALL,
            bg=t["accent_primary"],
            fg=t.get("accent_text", "#000000"),
            relief="raised",
            bd=2,
            cursor="hand2",
            padx=8,
            pady=4,
            command=lambda: self._select_period("weekly")
        )
        self.tab_weekly.pack(side="left", padx=(0, 6))

        self.tab_monthly = tk.Button(
            self.tabs_frame,
            text="[ 🗓️ MONTHLY (30 DAYS) ]",
            font=FONT_RETRO_SMALL,
            bg=t["bg_card"],
            fg=t["text_muted"],
            relief="flat",
            bd=1,
            cursor="hand2",
            padx=8,
            pady=4,
            command=lambda: self._select_period("monthly")
        )
        self.tab_monthly.pack(side="left", padx=(0, 6))

        self.tab_all = tk.Button(
            self.tabs_frame,
            text="[ 📚 ALL-TIME RECORD ]",
            font=FONT_RETRO_SMALL,
            bg=t["bg_card"],
            fg=t["text_muted"],
            relief="flat",
            bd=1,
            cursor="hand2",
            padx=8,
            pady=4,
            command=lambda: self._select_period("all")
        )
        self.tab_all.pack(side="left")

        # Right: Action Buttons
        self.actions_frame = tk.Frame(self.controls_bar, bg=t["bg_main"])
        self.actions_frame.grid(row=0, column=1, sticky="e")

        self.btn_print = tk.Button(
            self.actions_frame,
            text="[ 🖨️ PRINT REPORT ]",
            font=FONT_RETRO_SMALL,
            bg=t["accent_gold"],
            fg="#000000",
            activebackground=t["accent_primary"],
            relief="raised",
            bd=2,
            cursor="hand2",
            padx=8,
            pady=4,
            command=self._on_print
        )
        self.btn_print.pack(side="left", padx=(0, 6))

        self.btn_export = tk.Button(
            self.actions_frame,
            text="[ 📄 EXPORT FILE ]",
            font=FONT_RETRO_SMALL,
            bg=t["bg_card"],
            fg=t["accent_primary"],
            activebackground=t["bg_inner"],
            relief="raised",
            bd=1,
            cursor="hand2",
            padx=8,
            pady=4,
            command=self._on_export
        )
        self.btn_export.pack(side="left", padx=(0, 6))

        self.btn_copy = tk.Button(
            self.actions_frame,
            text="[ 📋 COPY CONCLUSION ]",
            font=FONT_RETRO_SMALL,
            bg=t["bg_card"],
            fg=t["text_main"],
            activebackground=t["bg_inner"],
            relief="raised",
            bd=1,
            cursor="hand2",
            padx=8,
            pady=4,
            command=self._on_copy_conclusion
        )
        self.btn_copy.pack(side="left", padx=(0, 6))

        self.btn_read = tk.Button(
            self.actions_frame,
            text="[ 🔊 READ ALOUD ]",
            font=FONT_RETRO_SMALL,
            bg=t["bg_card"],
            fg=t["accent_secondary"],
            activebackground=t["bg_inner"],
            relief="raised",
            bd=1,
            cursor="hand2",
            padx=8,
            pady=4,
            command=self._on_read_aloud
        )
        self.btn_read.pack(side="left")

        # Status / Feedback Toast Banner
        self.toast_frame = tk.Frame(self, bg=t["bg_main"])
        self.toast_frame.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 4))
        self.toast_lbl = tk.Label(
            self.toast_frame,
            text="",
            font=FONT_RETRO_SMALL,
            fg=t["accent_green"],
            bg=t["bg_main"]
        )
        self.toast_lbl.pack(anchor="w")

        # 3. Scrollable Report Area
        self.report_canvas = tk.Canvas(self, bg=t["bg_main"], highlightthickness=0)
        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.report_canvas.yview)

        self.report_inner = tk.Frame(self.report_canvas, bg=t["bg_main"])
        self.report_inner.bind(
            "<Configure>",
            lambda e: self.report_canvas.configure(scrollregion=self.report_canvas.bbox("all"))
        )
        self.canvas_window = self.report_canvas.create_window((0, 0), window=self.report_inner, anchor="nw")
        self.report_canvas.bind(
            "<Configure>",
            lambda e: self.report_canvas.itemconfig(self.canvas_window, width=e.width)
        )

        self.report_canvas.configure(yscrollcommand=v_scroll.set)
        self.report_canvas.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 16))
        v_scroll.grid(row=3, column=1, sticky="ns", pady=(0, 16))

        self.report_inner.columnconfigure(0, weight=1)
        self.report_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        if self.winfo_ismapped() and hasattr(self, "report_canvas"):
            self.report_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _show_toast(self, text, is_success=True):
        t = self.theme
        color = t["accent_green"] if is_success else t["accent_gold"]
        self.toast_lbl.config(text=text, fg=color)
        if self._toast_job:
            self.after_cancel(self._toast_job)
        self._toast_job = self.after(5000, lambda: self.toast_lbl.config(text=""))

    def _select_period(self, period):
        self.current_period = period
        t = self.theme
        tabs = [
            ("weekly", self.tab_weekly),
            ("monthly", self.tab_monthly),
            ("all", self.tab_all)
        ]
        for p_key, btn in tabs:
            if p_key == period:
                btn.config(bg=t["accent_primary"], fg=t.get("accent_text", "#000000"), relief="raised", bd=2)
            else:
                btn.config(bg=t["bg_card"], fg=t["text_muted"], relief="flat", bd=1)
        self.refresh_report()

    def _on_print(self):
        try:
            fpath = print_report(self.current_period, self.theme)
            self._show_toast("✓ Report generated and opened in browser! Press Ctrl+P to print or save as PDF.")
        except Exception as ex:
            self._show_toast(f"[!] Print preview error: {ex}", is_success=False)

    def _on_export(self):
        try:
            fpath = filedialog.asksaveasfilename(
                title=f"Export LifeLens {self.current_period.capitalize()} Report",
                defaultextension=".html",
                filetypes=[
                    ("HTML Printable Document (*.html)", "*.html"),
                    ("Plain Text Report (*.txt)", "*.txt"),
                    ("All Files (*.*)", "*.*")
                ],
                initialfile=f"lifelens_{self.current_period}_report.html"
            )
            if fpath:
                file_format = "txt" if fpath.lower().endswith(".txt") else "html"
                export_report_file(fpath, self.current_period, file_format, self.theme)
                self._show_toast(f"✓ Report successfully exported to: {os.path.basename(fpath)}")
        except Exception as ex:
            self._show_toast(f"[!] Export error: {ex}", is_success=False)

    def _on_copy_conclusion(self):
        if self.current_report_data:
            try:
                txt = generate_plain_text_report(self.current_report_data)
                self.clipboard_clear()
                self.clipboard_append(txt)
                self._show_toast("✓ Complete executive report copied to clipboard!")
            except Exception as ex:
                self._show_toast(f"[!] Clipboard error: {ex}", is_success=False)

    def _on_read_aloud(self):
        if not self.current_report_data:
            return

        text_to_speak = self.current_report_data.get("executive_conclusion", "")
        if not text_to_speak:
            self._show_toast("[!] No conclusion text available to read aloud.", is_success=False)
            return

        if self.is_speaking_conclusion:
            self.is_speaking_conclusion = False
            self.btn_read.config(text="[ 🔊 READ ALOUD ]", fg=self.theme["accent_secondary"])
            return

        self.is_speaking_conclusion = True
        self.btn_read.config(text="[ ■ READING... ]", fg=self.theme["accent_gold"])
        self._show_toast("🔊 Reading executive conclusion aloud...")

        def _on_finish():
            self.is_speaking_conclusion = False
            try:
                self.btn_read.config(text="[ 🔊 READ ALOUD ]", fg=self.theme["accent_secondary"])
            except Exception:
                pass

        def _on_error(err):
            self.is_speaking_conclusion = False
            try:
                self.btn_read.config(text="[ 🔊 READ ALOUD ]", fg=self.theme["accent_secondary"])
                self._show_toast(f"[!] TTS Notice: {err}", is_success=False)
            except Exception:
                pass

        self.tts_manager.read_aloud_async(
            text_to_speak,
            rate=128,
            on_finish=_on_finish,
            on_error=_on_error
        )

    def on_show(self):
        self.refresh_report()

    def apply_theme(self):
        t = self.theme
        self.configure(bg=t["bg_main"])
        self.header_frame.configure(bg=t["bg_main"])
        self.title_lbl.configure(fg=t["accent_primary"], bg=t["bg_main"])
        self.subtitle_lbl.configure(fg=t["text_muted"], bg=t["bg_main"])
        self.controls_bar.configure(bg=t["bg_main"])
        self.tabs_frame.configure(bg=t["bg_main"])
        self.actions_frame.configure(bg=t["bg_main"])
        self.toast_frame.configure(bg=t["bg_main"])
        self.toast_lbl.configure(bg=t["bg_main"])
        self.report_canvas.configure(bg=t["bg_main"])
        self.report_inner.configure(bg=t["bg_main"])

        # Update tabs
        self._select_period(self.current_period)

        self.btn_print.configure(bg=t["accent_gold"], fg="#000000")
        self.btn_export.configure(bg=t["bg_card"], fg=t["accent_primary"])
        self.btn_copy.configure(bg=t["bg_card"], fg=t["text_main"])
        self.btn_read.configure(bg=t["bg_card"], fg=t["accent_secondary"])

    def refresh_report(self):
        t = self.theme
        for child in self.report_inner.winfo_children():
            child.destroy()

        data = generate_report_data(self.current_period)
        self.current_report_data = data

        if not data.get("has_data", False):
            no_card = tk.Frame(self.report_inner, bg=t["bg_card"], bd=2, relief="ridge", padx=24, pady=32)
            no_card.pack(fill="x", pady=20)
            tk.Label(
                no_card,
                text="[!] INSUFFICIENT DATA FOR REPORT",
                font=FONT_RETRO_HEADER,
                fg=t["accent_gold"],
                bg=t["bg_card"]
            ).pack(anchor="w")
            tk.Label(
                no_card,
                text=data.get("executive_summary", "No journal entries found in this timeframe."),
                font=FONT_RETRO_BODY,
                fg=t["text_muted"],
                bg=t["bg_card"],
                pady=8
            ).pack(anchor="w")
            return

        # -------------------------------------------------------------
        # Section 1: Executive Conclusion & Verdict Callout Banner
        # -------------------------------------------------------------
        conclusion_card = tk.Frame(self.report_inner, bg=t["bg_card"], bd=2, relief="ridge", padx=16, pady=16)
        conclusion_card.pack(fill="x", pady=(0, 14))

        # Top Banner Row: Badges
        badge_row = tk.Frame(conclusion_card, bg=t["bg_card"])
        badge_row.pack(fill="x", pady=(0, 10))

        verdict_badge = tk.Label(
            badge_row,
            text=f" {data.get('verdict_emoji', '🌟')} {data.get('verdict', 'EVALUATED')} ",
            font=("Consolas", 10, "bold"),
            bg=data.get("badge_color", t["accent_primary"]),
            fg="#ffffff",
            padx=10,
            pady=4,
            relief="solid",
            bd=1
        )
        verdict_badge.pack(side="left", padx=(0, 8))

        wellness_badge = tk.Label(
            badge_row,
            text=f"WELLNESS VITALITY: {data.get('wellness_score', 0)}/100",
            font=("Consolas", 9, "bold"),
            bg=t["bg_inner"],
            fg=t["accent_primary"],
            padx=8,
            pady=4,
            relief="solid",
            bd=1
        )
        wellness_badge.pack(side="left", padx=(0, 8))

        horizon_badge = tk.Label(
            badge_row,
            text=f"// {data.get('period_label')}",
            font=FONT_RETRO_SMALL,
            bg=t["bg_card"],
            fg=t["text_muted"]
        )
        horizon_badge.pack(side="left")

        # Heading
        tk.Label(
            conclusion_card,
            text=">> EXECUTIVE CLINICAL & WELLNESS CONCLUSION:",
            font=("Consolas", 10, "bold"),
            fg=t["accent_gold"],
            bg=t["bg_card"]
        ).pack(anchor="w", pady=(0, 6))

        # Full Conclusion Text
        conc_lbl = tk.Label(
            conclusion_card,
            text=data.get("executive_conclusion", ""),
            font=("Consolas", 9),
            fg=t["text_main"],
            bg=t["bg_card"],
            justify="left",
            wraplength=820
        )
        conc_lbl.pack(anchor="w", fill="x")

        # Re-adjust wrap on inner frame configure
        conclusion_card.bind("<Configure>", lambda e: conc_lbl.config(wraplength=max(300, e.width - 32)))

        # Sub-status tags
        tags_row = tk.Frame(conclusion_card, bg=t["bg_card"])
        tags_row.pack(fill="x", pady=(10, 0))

        tk.Label(
            tags_row,
            text=f"[ TRAJECTORY: {data.get('trajectory_text', '')} ]",
            font=("Consolas", 8, "bold"),
            fg=t["accent_green"],
            bg=t["bg_card"]
        ).pack(side="left", padx=(0, 10))

        tk.Label(
            tags_row,
            text=f"[ STABILITY: {data.get('stability_text', '')} ]",
            font=("Consolas", 8, "bold"),
            fg=t["accent_secondary"],
            bg=t["bg_card"]
        ).pack(side="left")

        # -------------------------------------------------------------
        # Section 2: 4 Core Metric KPI Boxes
        # -------------------------------------------------------------
        kpi_row = tk.Frame(self.report_inner, bg=t["bg_main"])
        kpi_row.pack(fill="x", pady=(0, 14))
        for col_idx in range(4):
            kpi_row.columnconfigure(col_idx, weight=1)

        kpi_data = [
            ("TOTAL LOGS", f"{data['total_entries']} entries", t["accent_primary"], f"{data['start_date']} to {data['end_date']}"),
            ("AVG STAMINA", f"{data['avg_energy']}/10", t["accent_green"], f"StdDev: ±{data.get('energy_std_dev', 0)}"),
            ("DOMINANT EMOTION", f"{data['top_mood_emoji']} {data['top_mood'].upper()}", t["accent_gold"], "Primary Posture"),
            ("BURNOUT RISK", f"{data.get('burnout_ratio', 0)}%", data.get('burnout_color', t['accent_green']), data.get('burnout_level', 'LOW RISK'))
        ]

        for idx, (title, val, color, note) in enumerate(kpi_data):
            box = tk.Frame(kpi_row, bg=t["bg_card"], bd=2, relief="ridge", padx=10, pady=8)
            box.grid(row=0, column=idx, sticky="ew", padx=4 if idx > 0 else (0, 4))
            tk.Label(box, text=f"// {title}", font=FONT_RETRO_SMALL, fg=t["text_muted"], bg=t["bg_card"]).pack(anchor="w")
            tk.Label(box, text=val, font=("Consolas", 11, "bold"), fg=color, bg=t["bg_card"]).pack(anchor="w", pady=(2, 1))
            tk.Label(box, text=note, font=("Consolas", 7), fg=t["text_muted"], bg=t["bg_card"]).pack(anchor="w")

        # -------------------------------------------------------------
        # Section 3: Activity Impact & Correlation Analysis
        # -------------------------------------------------------------
        act_card = tk.Frame(self.report_inner, bg=t["bg_card"], bd=2, relief="ridge", padx=14, pady=12)
        act_card.pack(fill="x", pady=(0, 14))

        tk.Label(
            act_card,
            text="[ ⚡ ACTIVITY IMPACT & ENERGY CORRELATIONS ]",
            font=FONT_RETRO_HEADER,
            fg=t["accent_primary"],
            bg=t["bg_card"]
        ).pack(anchor="w", pady=(0, 8))

        act_grid = tk.Frame(act_card, bg=t["bg_card"])
        act_grid.pack(fill="x")

        impacts = data.get("activity_impacts", [])
        if impacts:
            num_cols = min(3, len(impacts))
            for i in range(num_cols):
                act_grid.columnconfigure(i, weight=1)

            for idx, act in enumerate(impacts):
                col = idx % num_cols
                r = idx // num_cols
                item_frame = tk.Frame(act_grid, bg=t["bg_inner"], bd=1, relief="solid", padx=10, pady=8)
                item_frame.grid(row=r, column=col, sticky="ew", padx=3, pady=3)

                d_val = act["energy_delta"]
                delta_str = f"+{d_val}" if d_val > 0 else f"{d_val}"
                delta_color = t["accent_green"] if d_val > 0 else (t["accent_gold"] if d_val == 0 else "#ef4444")

                tk.Label(
                    item_frame,
                    text=f"▶ {act['activity'].upper()} ({act['count']} logs)",
                    font=("Consolas", 9, "bold"),
                    fg=t["text_main"],
                    bg=t["bg_inner"]
                ).pack(anchor="w")

                tk.Label(
                    item_frame,
                    text=f"Stamina: {act['avg_energy']}/10  |  Δ {delta_str} vs Avg",
                    font=FONT_RETRO_SMALL,
                    fg=delta_color,
                    bg=t["bg_inner"]
                ).pack(anchor="w", pady=(2, 0))

                tk.Label(
                    item_frame,
                    text=f"Mood: {act['dominant_mood_emoji']} {act['dominant_mood']}",
                    font=("Consolas", 8),
                    fg=t["text_muted"],
                    bg=t["bg_inner"]
                ).pack(anchor="w")
        else:
            tk.Label(act_card, text="No activity data recorded in this period.", font=FONT_RETRO_SMALL, fg=t["text_muted"], bg=t["bg_card"]).pack(anchor="w")

        # -------------------------------------------------------------
        # Section 4: Actionable Lifestyle Prescriptions
        # -------------------------------------------------------------
        recs_card = tk.Frame(self.report_inner, bg=t["bg_card"], bd=2, relief="ridge", padx=14, pady=12)
        recs_card.pack(fill="x", pady=(0, 14))

        tk.Label(
            recs_card,
            text="[ 💡 ACTIONABLE LIFESTYLE & WELLNESS PRESCRIPTIONS ]",
            font=FONT_RETRO_HEADER,
            fg=t["accent_gold"],
            bg=t["bg_card"]
        ).pack(anchor="w", pady=(0, 8))

        for idx, rec in enumerate(data.get("recommendations", []), 1):
            rf = tk.Frame(recs_card, bg=t["bg_card"])
            rf.pack(fill="x", pady=2)
            tk.Label(rf, text=f"({idx})", font=("Consolas", 8, "bold"), fg=t["accent_primary"], bg=t["bg_card"]).pack(side="left", anchor="n", padx=(0, 6))
            rec_lbl = tk.Label(
                rf,
                text=rec,
                font=FONT_RETRO_SMALL,
                fg=t["text_main"],
                bg=t["bg_card"],
                justify="left",
                wraplength=800
            )
            rec_lbl.pack(side="left", fill="x", expand=True, anchor="w")
            recs_card.bind("<Configure>", lambda e, l=rec_lbl: l.config(wraplength=max(280, e.width - 50)))

        # -------------------------------------------------------------
        # Section 5: Period Evaluated Journal Entries
        # -------------------------------------------------------------
        entries_card = tk.Frame(self.report_inner, bg=t["bg_card"], bd=2, relief="ridge", padx=14, pady=12)
        entries_card.pack(fill="x", pady=(0, 14))

        tk.Label(
            entries_card,
            text=f"[ 📖 EVALUATED JOURNAL ENTRIES ({data['total_entries']}) ]",
            font=FONT_RETRO_HEADER,
            fg=t["accent_primary"],
            bg=t["bg_card"]
        ).pack(anchor="w", pady=(0, 8))

        entries_list = data.get("entries", [])
        for e in entries_list:
            ef = tk.Frame(entries_card, bg=t["bg_inner"], bd=1, relief="solid", padx=10, pady=8)
            ef.pack(fill="x", pady=4)

            top_row = tk.Frame(ef, bg=t["bg_inner"])
            top_row.pack(fill="x")

            d_str = e.get("date", "")
            m_str = e.get("mood", "Good")
            m_emoji = MOOD_MAP.get(m_str, {}).get("emoji", "😊")
            en_val = e.get("energy", 5)
            act_str = e.get("activity", "Other")

            tk.Label(top_row, text=f"📅 {d_str}", font=("Consolas", 8, "bold"), fg=t["accent_gold"], bg=t["bg_inner"]).pack(side="left", padx=(0, 10))
            tk.Label(top_row, text=f"{m_emoji} {m_str}", font=("Consolas", 8, "bold"), fg=t["accent_primary"], bg=t["bg_inner"]).pack(side="left", padx=(0, 10))
            tk.Label(top_row, text=f"⚡ {make_pixel_bar(en_val, 10, 8)}", font=("Consolas", 8), fg=t["accent_green"], bg=t["bg_inner"]).pack(side="left", padx=(0, 10))
            tk.Label(top_row, text=f"[{act_str.upper()}]", font=("Consolas", 8), fg=t["text_muted"], bg=t["bg_inner"]).pack(side="left")

            txt = e.get("text", "").strip()
            if txt:
                tk.Label(
                    ef,
                    text=txt,
                    font=("Consolas", 8),
                    fg=t["text_main"],
                    bg=t["bg_inner"],
                    justify="left",
                    wraplength=780
                ).pack(anchor="w", pady=(4, 0))

