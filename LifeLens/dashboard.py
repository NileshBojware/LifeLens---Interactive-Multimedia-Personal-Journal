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

        title_box = tk.Frame(self.header, bg=self.theme["bg_main"])
        title_box.grid(row=0, column=0, sticky="w")

        self.title_lbl = tk.Label(
            title_box,
            text=f"★ LIFELENS // {self.theme['name'].upper()} STATION ★",
            font=("Consolas", 15, "bold"),
            fg=self.theme["accent_primary"],
            bg=self.theme["bg_main"]
        )
        self.title_lbl.pack(anchor="w")

        self.subtitle_lbl = tk.Label(
            title_box,
            text=f">> {self.theme['tagline']}",
            font=FONT_RETRO_SMALL,
            fg=self.theme["text_muted"],
            bg=self.theme["bg_main"]
        )
        self.subtitle_lbl.pack(anchor="w", pady=(2, 0))

        # Right Header: Date + Personality Selector Dropdown
        right_header = tk.Frame(self.header, bg=self.theme["bg_main"])
        right_header.grid(row=0, column=1, sticky="e")

        today_str = datetime.now().strftime("%Y.%m.%d").upper()
        self.date_badge = tk.Label(
            right_header,
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

        pers_box = tk.Frame(right_header, bg=self.theme["bg_main"])
        pers_box.pack(side="right")
        tk.Label(pers_box, text="THEME:", font=FONT_RETRO_SMALL, fg=self.theme["accent_primary"], bg=self.theme["bg_main"]).pack(side="left", padx=4)
        
        self.pers_combo = ttk.Combobox(
            pers_box,
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

        quote_top = tk.Frame(self.quote_card, bg=self.theme["bg_card"])
        quote_top.grid(row=0, column=0, sticky="ew")
        quote_top.columnconfigure(0, weight=1)

        self.quote_badge_lbl = tk.Label(
            quote_top,
            text=f"[ 💡 DAILY PSYCHOLOGICAL REFLECTION // DAY {day_num} OF 365 ]",
            font=FONT_RETRO_SMALL,
            fg=self.theme["accent_gold"],
            bg=self.theme["bg_card"]
        )
        self.quote_badge_lbl.pack(side="left")

        # Quote Actions
        quote_actions = tk.Frame(quote_top, bg=self.theme["bg_card"])
        quote_actions.pack(side="right")

        self.shuffle_quote_btn = tk.Button(
            quote_actions,
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
            quote_actions,
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
            foreground="#000000",
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
            fg="#000000",
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
        self.title_lbl.configure(text=f"★ LIFELENS // {t['name'].upper()} STATION ★", fg=t["accent_primary"], bg=t["bg_main"])
        self.subtitle_lbl.configure(text=f">> {t['tagline']}", fg=t["text_muted"], bg=t["bg_main"])
        self.date_badge.configure(fg=t["accent_gold"], bg=t["bg_card"])
        self.quote_card.configure(bg=t["bg_card"])
        self.quote_badge_lbl.configure(fg=t["accent_gold"], bg=t["bg_card"])
        
        self.quote_text_box.configure(bg=t["bg_card"], fg=t["text_main"])
        self.quote_text_box.tag_configure("quote_body", foreground=t["text_main"])
        self.quote_text_box.tag_configure(
            "word_highlight",
            background=t["accent_primary"],
            foreground="#000000",
            font=("Consolas", 10, "bold")
        )
        self.quote_author_lbl.configure(fg=t["accent_primary"], bg=t["bg_card"])
        self.shuffle_quote_btn.configure(bg=t["bg_inner"], fg=t["accent_primary"])
        self.speak_quote_btn.configure(bg=t["bg_inner"], fg=t["accent_secondary"])
        self.kpi_container.configure(bg=t["bg_main"])
        self.actions_bar.configure(bg=t["bg_main"])
        self.new_btn.configure(bg=t["accent_primary"], activebackground=t["accent_secondary"])
        self.ambient_btn.configure(bg=t["bg_card"], fg=t["accent_gold"], activebackground=t["bg_inner"])
        self.audio_settings_btn.configure(bg=t["bg_card"], fg=t["accent_primary"], activebackground=t["bg_inner"])
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
        
        tk.Label(
            item_frame,
            text=f"{mood_info['emoji']}",
            font=("Consolas", 14),
            bg=t["bg_inner"],
            padx=6,
            pady=2
        ).grid(row=0, column=0, rowspan=2, sticky="ns")

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
        canvas = tk.Canvas(self, bg=t["bg_main"], highlightthickness=0)
        v_scroll = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        form_frame = tk.Frame(canvas, bg=t["bg_main"])

        form_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=form_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        canvas.configure(yscrollcommand=v_scroll.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        form_frame.columnconfigure(0, weight=1)

        self.card = tk.Frame(form_frame, bg=t["bg_card"], bd=2, relief="ridge")
        self.card.grid(row=0, column=0, sticky="ew", padx=24, pady=16)
        self.card.columnconfigure(0, weight=1)

        # Title
        title_box = tk.Frame(self.card, bg=t["bg_card"])
        title_box.pack(fill="x", padx=18, pady=(12, 8))
        
        self.form_title = tk.Label(
            title_box,
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

        prompt_top = tk.Frame(self.prompt_box, bg=t["bg_inner"])
        prompt_top.pack(fill="x")

        self.prompt_badge_lbl = tk.Label(
            prompt_top,
            text="[ 💭 MINDFUL REFLECTION PROMPT ]",
            font=FONT_RETRO_SMALL,
            fg=t["accent_gold"],
            bg=t["bg_inner"]
        )
        self.prompt_badge_lbl.pack(side="left")

        self.prompt_shuffle_btn = tk.Button(
            prompt_top,
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
        row1 = tk.Frame(self.card, bg=t["bg_card"])
        row1.pack(fill="x", padx=18, pady=(0, 10))
        row1.columnconfigure(0, weight=1)
        row1.columnconfigure(1, weight=1)

        date_box = tk.Frame(row1, bg=t["bg_card"])
        date_box.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.date_lbl = tk.Label(date_box, text="// DATE [YYYY-MM-DD]:", font=FONT_RETRO_HEADER, fg=t["accent_gold"], bg=t["bg_card"])
        self.date_lbl.pack(anchor="w", pady=(0, 2))
        
        date_sub = tk.Frame(date_box, bg=t["bg_card"])
        date_sub.pack(fill="x")
        self.date_entry = tk.Entry(date_sub, font=FONT_RETRO_BODY, bg=t["bg_inner"], fg=t["text_main"], insertbackground=t["accent_primary"], bd=2, relief="sunken")
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.pack(side="left", fill="x", expand=True)

        self.today_btn = tk.Button(
            date_sub,
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

        act_box = tk.Frame(row1, bg=t["bg_card"])
        act_box.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self.act_lbl = tk.Label(act_box, text="// ACTIVITY / FOCUS:", font=FONT_RETRO_HEADER, fg=t["accent_gold"], bg=t["bg_card"])
        self.act_lbl.pack(anchor="w", pady=(0, 2))
        self.act_combo = ttk.Combobox(act_box, values=ACTIVITIES, textvariable=self.activity_val, state="readonly", font=FONT_RETRO_BODY)
        self.act_combo.pack(fill="x")

        # Row 2: Mood Selection
        mood_box = tk.Frame(self.card, bg=t["bg_card"])
        mood_box.pack(fill="x", padx=18, pady=(0, 10))
        self.mood_title = tk.Label(mood_box, text="// EMOTIONAL STATE:", font=FONT_RETRO_HEADER, fg=t["accent_gold"], bg=t["bg_card"])
        self.mood_title.pack(anchor="w", pady=(0, 3))

        self.mood_buttons_frame = tk.Frame(mood_box, bg=t["bg_card"])
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
        energy_box = tk.Frame(self.card, bg=t["bg_card"])
        energy_box.pack(fill="x", padx=18, pady=(0, 10))

        energy_header = tk.Frame(energy_box, bg=t["bg_card"])
        energy_header.pack(fill="x")
        self.energy_title = tk.Label(energy_header, text="// ENERGY & STAMINA METER:", font=FONT_RETRO_HEADER, fg=t["accent_gold"], bg=t["bg_card"])
        self.energy_title.pack(side="left")
        
        self.energy_display_lbl = tk.Label(
            energy_header,
            text=make_pixel_bar(8, 10, width=10) + " [HIGH]",
            font=FONT_RETRO_HEADER,
            fg=t["accent_green"],
            bg=t["bg_card"]
        )
        self.energy_display_lbl.pack(side="right")

        self.energy_slider = ttk.Scale(
            energy_box,
            from_=1,
            to=10,
            orient="horizontal",
            variable=self.energy_val,
            command=self._on_energy_slider_change
        )
        self.energy_slider.pack(fill="x", pady=(3, 0))

        # Row 4: Journal Text & Voice Button
        text_box_frame = tk.Frame(self.card, bg=t["bg_card"])
        text_box_frame.pack(fill="x", padx=18, pady=(0, 10))
        
        text_header = tk.Frame(text_box_frame, bg=t["bg_card"])
        text_header.pack(fill="x", pady=(0, 3))
        self.reflect_lbl = tk.Label(text_header, text="// REFLECTION / LOG TEXT:", font=FONT_RETRO_HEADER, fg=t["accent_gold"], bg=t["bg_card"])
        self.reflect_lbl.pack(side="left")

        self.voice_btn = tk.Button(
            text_header,
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

        self.voice_status_lbl = tk.Label(text_header, text="", font=FONT_RETRO_SMALL, fg=t["accent_primary"], bg=t["bg_card"])
        self.voice_status_lbl.pack(side="right", padx=6)

        self.text_area = tk.Text(
            text_box_frame,
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

        img_body = tk.Frame(self.img_section, bg=t["bg_inner"], padx=8, pady=8)
        img_body.pack(fill="x")
        img_body.columnconfigure(0, weight=1)
        img_body.columnconfigure(1, weight=1)

        img_controls = tk.Frame(img_body, bg=t["bg_inner"])
        img_controls.grid(row=0, column=0, sticky="nw")

        btn_row = tk.Frame(img_controls, bg=t["bg_inner"])
        btn_row.pack(anchor="w", pady=(0, 5))

        self.upload_btn = tk.Button(
            btn_row,
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
            btn_row,
            text="[📸 WEBCAM SNAP]",
            font=FONT_RETRO_SMALL,
            bg=t["accent_green"],
            fg="#000000",
            relief="raised",
            bd=2,
            cursor="hand2",
            padx=6,
            pady=2,
            command=self._open_camera
        )
        self.camera_btn.pack(side="left")

        self.filter_lbl = tk.Label(img_controls, text="// 8-BIT EFFECT FILTER:", font=FONT_RETRO_SMALL, fg=t["text_muted"], bg=t["bg_inner"])
        self.filter_lbl.pack(anchor="w")
        self.filter_combo = ttk.Combobox(
            img_controls,
            values=AVAILABLE_FILTERS,
            textvariable=self.filter_val,
            state="readonly",
            font=FONT_RETRO_SMALL,
            width=22
        )
        self.filter_combo.pack(anchor="w", pady=(2, 5))
        self.filter_combo.bind("<<ComboboxSelected>>", lambda e: self._update_image_preview())

        self.remove_img_btn = tk.Button(
            img_controls,
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

        self.preview_container = tk.Frame(img_body, bg="#101018", width=220, height=120, bd=2, relief="sunken")
        self.preview_container.grid(row=0, column=1, sticky="ne")
        self.preview_container.pack_propagate(False)

        self.preview_lbl = tk.Label(
            self.preview_container,
            text="[ NO PHOTO ATTACHED ]\n(FILE OR CAMERA)",
            font=FONT_RETRO_SMALL,
            fg=t["text_muted"],
            bg="#101018"
        )
        self.preview_lbl.pack(expand=True)

        # Bottom Actions
        action_row = tk.Frame(self.card, bg=t["bg_card"])
        action_row.pack(fill="x", padx=18, pady=(0, 16))

        self.save_btn = tk.Button(
            action_row,
            text="[★ SAVE QUEST LOG ★]",
            font=FONT_RETRO_HEADER,
            bg=t["accent_primary"],
            fg="#000000",
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
            action_row,
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
        self.card.configure(bg=t["bg_card"])
        self.form_title.configure(text=f"[ ■ LOG CREATION TERMINAL // {t['name'].upper()} ■ ]", fg=t["accent_primary"], bg=t["bg_card"])
        self.prompt_box.configure(bg=t["bg_inner"])
        self.prompt_badge_lbl.configure(fg=t["accent_gold"], bg=t["bg_inner"])
        self.prompt_shuffle_btn.configure(bg=t["bg_card"], fg=t["accent_primary"])
        self.prompt_text_lbl.configure(fg=t["text_main"], bg=t["bg_inner"])
        self.date_lbl.configure(fg=t["accent_gold"], bg=t["bg_card"])
        self.today_btn.configure(bg=t["bg_inner"], fg=t["accent_primary"])
        self.act_lbl.configure(fg=t["accent_gold"], bg=t["bg_card"])
        self.mood_title.configure(fg=t["accent_gold"], bg=t["bg_card"])
        self.energy_title.configure(fg=t["accent_gold"], bg=t["bg_card"])
        self.reflect_lbl.configure(fg=t["accent_gold"], bg=t["bg_card"])
        self.voice_btn.configure(bg=t["accent_secondary"])
        self.voice_status_lbl.configure(fg=t["accent_primary"], bg=t["bg_card"])
        self.text_area.configure(bg=t["bg_inner"], fg=t["text_main"], insertbackground=t["accent_primary"])
        self.img_section.configure(bg=t["bg_inner"])
        self.img_sec_header.configure(bg=t["bg_card"])
        self.photo_sec_lbl.configure(fg=t["accent_primary"], bg=t["bg_card"])
        self.upload_btn.configure(bg=t["bg_card"], fg=t["accent_primary"])
        self.camera_btn.configure(bg=t["accent_green"])
        self.filter_lbl.configure(fg=t["text_muted"], bg=t["bg_inner"])
        self.save_btn.configure(bg=t["accent_primary"], activebackground=t["accent_secondary"])
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
        
        inner_filter = tk.Frame(self.filter_bar, bg=t["bg_card"], padx=10, pady=6)
        inner_filter.pack(fill="x")

        self.lbl_s = tk.Label(inner_filter, text="SEARCH:", font=FONT_RETRO_HEADER, fg=t["accent_primary"], bg=t["bg_card"])
        self.lbl_s.pack(side="left", padx=(0, 4))
        self.search_entry = tk.Entry(inner_filter, textvariable=self.search_query, width=15, font=FONT_RETRO_BODY, bg=t["bg_inner"], fg=t["text_main"], insertbackground=t["accent_primary"], bd=2, relief="sunken")
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_query.trace_add("write", lambda *args: self.refresh_timeline())

        self.lbl_m = tk.Label(inner_filter, text="MOOD:", font=FONT_RETRO_HEADER, fg=t["accent_gold"], bg=t["bg_card"])
        self.lbl_m.pack(side="left", padx=(0, 4))
        mood_opts = ["All Moods"] + list(MOOD_MAP.keys())
        self.mood_combo = ttk.Combobox(inner_filter, values=mood_opts, textvariable=self.mood_filter, state="readonly", width=11, font=FONT_RETRO_BODY)
        self.mood_combo.pack(side="left", padx=(0, 10))
        self.mood_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_timeline())

        self.lbl_a = tk.Label(inner_filter, text="ACTIVITY:", font=FONT_RETRO_HEADER, fg=t["accent_secondary"], bg=t["bg_card"])
        self.lbl_a.pack(side="left", padx=(0, 4))
        act_opts = ["All Activities"] + ACTIVITIES
        self.act_combo = ttk.Combobox(inner_filter, values=act_opts, textvariable=self.act_filter, state="readonly", width=13, font=FONT_RETRO_BODY)
        self.act_combo.pack(side="left", padx=(0, 10))
        self.act_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_timeline())

        self.clear_btn = tk.Button(
            inner_filter,
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

        self.count_lbl = tk.Label(inner_filter, text="", font=FONT_RETRO_HEADER, fg=t["accent_green"], bg=t["bg_card"])
        self.count_lbl.pack(side="right")

        canvas_frame = tk.Frame(self, bg=t["bg_main"])
        canvas_frame.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 16))
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_frame, bg=t["bg_main"], highlightthickness=0)
        self.v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        
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
        self.filter_bar.configure(bg=t["bg_card"])
        self.lbl_s.configure(fg=t["accent_primary"], bg=t["bg_card"])
        self.lbl_m.configure(fg=t["accent_gold"], bg=t["bg_card"])
        self.lbl_a.configure(fg=t["accent_secondary"], bg=t["bg_card"])
        self.clear_btn.configure(bg=t["bg_inner"], fg=t["text_muted"])
        self.count_lbl.configure(fg=t["accent_green"], bg=t["bg_card"])
        self.canvas.configure(bg=t["bg_main"])
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
        ax3.set_facecolor(t["bg_card"])
        ax3.set_title("ENERGY LEVEL OSCILLATION WAVEFORM", fontfamily=FONT_MONO, fontsize=9, fontweight="bold", color=t["accent_green"], pad=8)

        trend = stats.get("energy_trend", [])
        if trend and len(trend) > 1:
            dates = [tr[0] for tr in trend]
            energies = [tr[1] for tr in trend]
            
            ax3.step(dates, energies, where='mid', color=t["accent_primary"], linewidth=2.5)
            ax3.plot(dates, energies, 'o', color=t["accent_gold"], markersize=6)
            ax3.fill_between(dates, energies, step='mid', color=t["accent_primary"], alpha=0.15)
            ax3.set_ylim(0, 11)
            ax3.set_ylabel("ENERGY", fontfamily=FONT_MONO, fontsize=7, color=t["text_muted"])
            ax3.grid(True, linestyle=":", alpha=0.3, color=t["border"])
            ax3.spines['top'].set_visible(False)
            ax3.spines['right'].set_visible(False)
            ax3.spines['left'].set_color(t["border"])
            ax3.spines['bottom'].set_color(t["border"])
            ax3.tick_params(colors=t["text_main"], labelsize=7)
            fig.autofmt_xdate()
        elif trend and len(trend) == 1:
            ax3.plot([trend[0][0]], [trend[0][1]], marker='o', color=t["accent_primary"], markersize=8)
            ax3.set_ylim(0, 11)
            ax3.set_ylabel("ENERGY", fontfamily=FONT_MONO, fontsize=7, color=t["text_muted"])
            ax3.grid(True, linestyle=":", alpha=0.3, color=t["border"])
        else:
            ax3.text(0.5, 0.5, "LOG ENTRIES TO VISUALIZE OSCILLATION", ha="center", va="center", color=t["text_muted"], fontfamily=FONT_MONO)
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

        tk.Label(
            self.card,
            text=">> DUAL-TRACK AUDIO MIXER // 365 REFLECTIONS // 6 PERSONALITY THEMES",
            font=FONT_RETRO_SMALL,
            fg=t["text_muted"],
            bg=t["bg_card"]
        ).pack(anchor="w", pady=(0, 12))

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

        # Personalities List
        self.pers_title = tk.Label(
            self.card,
            text="[ ■ 6 PERSONALITY THEMES INCLUDED ■ ]",
            font=FONT_RETRO_HEADER,
            fg=t["accent_gold"],
            bg=t["bg_card"]
        )
        self.pers_title.pack(anchor="w", pady=(4, 6))

        self.pers_frame = tk.Frame(self.card, bg=t["bg_inner"], bd=1, relief="solid", padx=10, pady=8)
        self.pers_frame.pack(fill="x", pady=(0, 12))

        for p_name, p_meta in PERSONALITY_THEMES.items():
            p_row = tk.Frame(self.pers_frame, bg=t["bg_inner"])
            p_row.pack(fill="x", pady=1)
            tk.Label(p_row, text=f"{p_meta['emoji']} {p_meta['name'].upper()}", font=FONT_RETRO_SMALL, fg=p_meta["accent_primary"], bg=t["bg_inner"]).pack(side="left")
            tk.Label(p_row, text=f":: {p_meta['tagline']}", font=FONT_RETRO_SMALL, fg=t["text_muted"], bg=t["bg_inner"]).pack(side="left", padx=6)

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

        h0 = tk.Label(self.tech_table, text="LIBRARY", font=FONT_RETRO_HEADER, bg=t["bg_inner"], fg=t["accent_primary"], padx=8, pady=4, anchor="w")
        h0.grid(row=0, column=0, sticky="ew")
        h1 = tk.Label(self.tech_table, text="ROLE / PURPOSE", font=FONT_RETRO_HEADER, bg=t["bg_inner"], fg=t["accent_primary"], padx=8, pady=4, anchor="w")
        h1.grid(row=0, column=1, sticky="ew")
        h2 = tk.Label(self.tech_table, text="WHERE USED IN APP", font=FONT_RETRO_HEADER, bg=t["bg_inner"], fg=t["accent_primary"], padx=8, pady=4, anchor="w")
        h2.grid(row=0, column=2, sticky="ew")

        rows = [
            ("Tkinter", "GUI and navigation", "Dynamic 5-personality theme windows"),
            ("Pillow", "Image processing", "8-Bit pixel filters & thumbnails"),
            ("OpenCV (cv2)", "Camera capture", "Live webcam snapshot upload"),
            ("SpeechRecognition", "Voice input", "Voice Entry (Speech-to-Text)"),
            ("pyttsx3", "Text-to-speech", "Read Aloud entries & 365 quotes (0.75x)"),
            ("Pygame", "Dual-Track Audio", "App BGM + golden-brown.mp3 Quote Narration Music"),
            ("Matplotlib", "Charts and analytics", "Personality-themed Insights radar"),
            ("JSON / Quotes DB", "Local data storage", "365+ quotes & data/journal_data.json")
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

        self.pers_title.configure(fg=t["accent_gold"], bg=t["bg_card"])
        self.pers_frame.configure(bg=t["bg_inner"])
        self.tech_title.configure(fg=t["accent_gold"], bg=t["bg_card"])
