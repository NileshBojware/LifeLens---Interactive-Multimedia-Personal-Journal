"""
LifeLens - Media Manager Module (Retro Pixel, Camera & Multi-Track Audio Edition)
Handles Pillow image processing, retro 8-bit filters, OpenCV camera snapshot capture,
and Pygame background music (Ambient App BGM + Spoken Quote Narration BGM with volume controls).
"""

import os
import math
import wave
import struct
import threading
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageEnhance, ImageFilter, ImageDraw

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from data_manager import get_audio_settings, set_audio_settings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
AMBIENT_FILE = os.path.join(DATA_DIR, "ambient_calm.wav")
QUOTE_BGM_FILE = os.path.join(DATA_DIR, "quote_bgm.wav")
GOLDEN_BROWN_FILE = os.path.join(DATA_DIR, "golden-brown.mp3")
INTERSTELLAR_FILE = os.path.join(DATA_DIR, "interstellar_stay.mp3")

AVAILABLE_FILTERS = [
    "Normal",
    "Pixel Art (8-Bit)",
    "Cyber Neon / High Contrast",
    "Retro Grayscale",
    "GameBoy Green",
    "CRT Scanline / Brighten"
]


# =====================================================================
# Pillow Image Processing (Retro & Pixel Art Effects)
# =====================================================================

def apply_image_filter(pil_img, filter_type="Normal"):
    """
    Apply retro and pixel processing filters to the given PIL Image.
    """
    if pil_img is None:
        return None

    img = pil_img.copy()
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    filter_type = filter_type.strip() if filter_type else "Normal"
    w, h = img.size

    if filter_type == "Pixel Art (8-Bit)":
        low_w = max(16, w // 10)
        low_h = max(16, h // 10)
        nearest_resample = getattr(Image, "Resampling", Image).NEAREST
        img_small = img.resize((low_w, low_h), nearest_resample)
        quantized = img_small.quantize(colors=16).convert("RGB")
        img = quantized.resize((w, h), nearest_resample)

    elif filter_type == "GameBoy Green":
        gray = img.convert("L")
        low_w = max(16, w // 8)
        low_h = max(16, h // 8)
        nearest_resample = getattr(Image, "Resampling", Image).NEAREST
        small_gray = gray.resize((low_w, low_h), nearest_resample)
        
        palette = [
            (15, 56, 15),
            (48, 98, 48),
            (139, 172, 15),
            (155, 188, 15)
        ]
        gb_img = Image.new("RGB", (low_w, low_h))
        pixels = small_gray.load()
        gb_pixels = gb_img.load()
        for y in range(low_h):
            for x in range(low_w):
                val = pixels[x, y]
                idx = min(3, int(val / 64))
                gb_pixels[x, y] = palette[idx]
        img = gb_img.resize((w, h), nearest_resample)

    elif filter_type == "Cyber Neon / High Contrast":
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.6)
        enhancer_c = ImageEnhance.Color(img)
        img = enhancer_c.enhance(1.8)

    elif filter_type == "Retro Grayscale":
        img = img.convert("L").convert("RGB")
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.3)

    elif filter_type == "CRT Scanline / Brighten":
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.35)

    return img


def resize_to_fit(pil_img, max_width, max_height, use_nearest=False):
    """Resize image preserving aspect ratio."""
    if pil_img is None:
        return None
    w, h = pil_img.size
    if w <= 0 or h <= 0:
        return pil_img

    ratio = min(max_width / w, max_height / h)
    new_w = max(1, int(w * ratio))
    new_h = max(1, int(h * ratio))
    
    if use_nearest:
        resample_mode = getattr(Image, "Resampling", Image).NEAREST
    else:
        resample_mode = getattr(Image, "Resampling", Image).LANCZOS
    return pil_img.resize((new_w, new_h), resample_mode)


def load_image_safe(relative_or_abs_path):
    """Safely loads a PIL Image from a file path."""
    if not relative_or_abs_path:
        return None
    
    if not os.path.isabs(relative_or_abs_path):
        target_path = os.path.join(BASE_DIR, relative_or_abs_path)
    else:
        target_path = relative_or_abs_path

    if not os.path.exists(target_path):
        return None

    try:
        img = Image.open(target_path)
        img.load()
        return img
    except Exception as e:
        print(f"Error loading image from {target_path}: {e}")
        return None


def save_processed_image(source_path, filter_type="Normal"):
    """Loads image, applies selected filter, and saves in data/images/."""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    img = load_image_safe(source_path)
    if img is None:
        return None

    img = apply_image_filter(img, filter_type)
    
    if img.width > 1200 or img.height > 1200:
        img = resize_to_fit(img, 1200, 1200)

    filename = f"pixel_entry_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
    save_dest = os.path.join(IMAGES_DIR, filename)
    
    try:
        img.save(save_dest, "PNG")
        return os.path.join("data", "images", filename).replace("\\", "/")
    except Exception as e:
        print(f"Error saving image: {e}")
        return None


def get_tk_image(pil_img, max_w, max_h, is_pixel_art=False):
    """Convert PIL Image to ImageTk.PhotoImage for Tkinter display."""
    if pil_img is None:
        return None
    scaled = resize_to_fit(pil_img, max_w, max_h, use_nearest=is_pixel_art)
    return ImageTk.PhotoImage(scaled)


# =====================================================================
# OpenCV Live Camera Capture Modal Dialog
# =====================================================================

class CameraCaptureDialog:
    """Live webcam snapshot capture window using OpenCV and Pillow."""

    def __init__(self, parent, on_photo_saved_callback):
        self.parent = parent
        self.on_photo_saved = on_photo_saved_callback
        self.cap = None
        self.is_running = False
        self.captured_image_path = None

        if not OPENCV_AVAILABLE:
            messagebox.showwarning(
                "Camera Module",
                "OpenCV library is not available for webcam capture."
            )
            return

        self._start_camera()

    def _start_camera(self):
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise RuntimeError("Cannot open video camera device.")
        except Exception as e:
            if self.cap:
                self.cap.release()
            messagebox.showwarning(
                "Webcam Error",
                f"Could not connect to camera: {e}\nPlease check your webcam permissions."
            )
            return

        self.modal = tk.Toplevel(self.parent)
        self.modal.title("★ RETRO WEBCAM SNAPSHOT ★")
        self.modal.geometry("540x480")
        self.modal.configure(bg="#0f0f1b")
        self.modal.grab_set()

        top_bar = tk.Frame(self.modal, bg="#1a192e", padx=12, pady=8)
        top_bar.pack(fill="x")
        tk.Label(
            top_bar,
            text="[ 📸 LIVE CAMERA STREAM // READY TO SNAP ]",
            font=("Consolas", 10, "bold"),
            fg="#00f0ff",
            bg="#1a192e"
        ).pack(side="left")

        self.view_frame = tk.Frame(self.modal, bg="#000000", bd=2, relief="sunken")
        self.view_frame.pack(fill="both", expand=True, padx=14, pady=10)

        self.stream_lbl = tk.Label(self.view_frame, bg="#000000")
        self.stream_lbl.pack(expand=True)

        ctrls = tk.Frame(self.modal, bg="#1a192e", padx=14, pady=10)
        ctrls.pack(fill="x")

        snap_btn = tk.Button(
            ctrls,
            text="[ 📸 SNAP PHOTO ]",
            font=("Consolas", 11, "bold"),
            bg="#00ff66",
            fg="#000000",
            activebackground="#00f0ff",
            relief="raised",
            bd=3,
            cursor="hand2",
            padx=16,
            pady=6,
            command=self._snap_photo
        )
        snap_btn.pack(side="left")

        cancel_btn = tk.Button(
            ctrls,
            text="[ CANCEL ]",
            font=("Consolas", 10),
            bg="#252342",
            fg="#f1f5f9",
            relief="raised",
            bd=2,
            cursor="hand2",
            padx=12,
            pady=6,
            command=self._close
        )
        cancel_btn.pack(side="right")

        self.is_running = True
        self.modal.protocol("WM_DELETE_WINDOW", self._close)
        self._update_stream()

    def _update_stream(self):
        if not self.is_running or not self.cap or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            self.last_frame = frame.copy()
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)
            scaled = resize_to_fit(pil_img, 480, 320)
            self.tk_live = ImageTk.PhotoImage(scaled)
            self.stream_lbl.config(image=self.tk_live)

        if self.modal.winfo_exists():
            self.modal.after(33, self._update_stream)

    def _snap_photo(self):
        if hasattr(self, "last_frame") and self.last_frame is not None:
            os.makedirs(IMAGES_DIR, exist_ok=True)
            filename = f"camera_snap_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
            dest_path = os.path.join(IMAGES_DIR, filename)
            cv2.imwrite(dest_path, self.last_frame)
            self._close()
            if self.on_photo_saved:
                self.on_photo_saved(dest_path)

    def _close(self):
        self.is_running = False
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        if hasattr(self, "modal") and self.modal.winfo_exists():
            self.modal.destroy()


def create_sample_visual_assets():
    """Creates sample graphics with Pillow."""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    samples = {
        "sample_coding.png": {
            "bg": "#0f0f1b",
            "accent": "#00f0ff",
            "border": "#ff007f",
            "title": ">> CODE QUEST // MISSION_COMPLETE",
            "subtitle": "[SYS: OK] 8-BIT PYTHON ENGINE"
        },
        "sample_reading.png": {
            "bg": "#0f231b",
            "accent": "#00ff66",
            "border": "#2ce8f5",
            "title": ">> TRANQUIL GROVE // LEVEL UP",
            "subtitle": "[MANA: +50] MINDFULNESS SCROLL"
        },
        "sample_exercise.png": {
            "bg": "#2b0f1b",
            "accent": "#ff007f",
            "border": "#ffd700",
            "title": ">> RUNNER 2000 // 5.0 KM",
            "subtitle": "[STAMINA: 100%] SPEED BOOST ACTIVE"
        },
        "sample_nature.png": {
            "bg": "#2b1f0f",
            "accent": "#ffd700",
            "border": "#ff77a8",
            "title": ">> GUILD BANQUET // FEAST",
            "subtitle": "[PARTY: 4/4] SHARED MEMORIES"
        }
    }

    for fname, conf in samples.items():
        fpath = os.path.join(IMAGES_DIR, fname)
        if not os.path.exists(fpath):
            try:
                img = Image.new("RGB", (600, 360), conf["bg"])
                draw = ImageDraw.Draw(img)
                for x in range(0, 600, 24):
                    draw.line([(x, 0), (x, 360)], fill="#1a1c2e", width=1)
                for y in range(0, 360, 24):
                    draw.line([(0, y), (600, y)], fill="#1a1c2e", width=1)
                draw.rectangle([12, 12, 588, 348], outline=conf["accent"], width=3)
                draw.rectangle([18, 18, 582, 342], outline=conf["border"], width=2)
                draw.rectangle([36, 36, 240, 68], fill=conf["accent"])
                draw.text((48, 44), "★ LIFELENS 8-BIT ★", fill="#000000")
                draw.text((44, 130), conf["title"], fill="#FFFFFF")
                draw.text((44, 175), conf["subtitle"], fill=conf["accent"])
                img.save(fpath, "PNG")
            except Exception as e:
                print(f"Error creating sample image {fname}: {e}")


# =====================================================================
# Offline Audio Synthesizers (App BGM + Spoken Quote Narration Pad)
# =====================================================================

def generate_offline_ambient_tone():
    """Generates soothing 8-bit chiptune loop."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(AMBIENT_FILE) and os.path.getsize(AMBIENT_FILE) > 1000:
        return

    sample_rate = 22050
    duration_secs = 4.0
    num_samples = int(sample_rate * duration_secs)
    notes = [261.63, 329.63, 392.00, 523.25, 392.00, 329.63]

    try:
        with wave.open(AMBIENT_FILE, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            frames = bytearray()
            for i in range(num_samples):
                t = float(i) / sample_rate
                note_idx = int(t * 4.0) % len(notes)
                freq = notes[note_idx]
                
                phase = (t * freq) % 1.0
                square = 0.3 if phase < 0.5 else -0.3
                triangle = (4.0 * abs(phase - 0.5) - 1.0) * 0.4
                
                bass_phase = (t * 130.81) % 1.0
                bass = 0.25 if bass_phase < 0.5 else -0.25
                
                loop_envelope = math.sin(math.pi * (i / num_samples))
                val = (square * 0.4 + triangle * 0.6 + bass * 0.3) * loop_envelope * 0.22
                val = max(-1.0, min(1.0, val))

                sample_int = int(val * 32767.0)
                frames.extend(struct.pack('<h', sample_int))

            wav_file.writeframes(frames)
    except Exception as e:
        print(f"Error generating ambient tone: {e}")


def generate_offline_quote_bgm():
    """
    Generates a gentle, cinematic ambient meditation pad (WAV)
    designed specifically to sit softly in the background while quotes/entries are read aloud.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(QUOTE_BGM_FILE) and os.path.getsize(QUOTE_BGM_FILE) > 1000:
        return

    sample_rate = 22050
    duration_secs = 6.0
    num_samples = int(sample_rate * duration_secs)

    # 432Hz harmonic soothing meditation chord frequencies (A=432Hz, C#=540Hz, E=648Hz)
    chords = [216.0, 270.0, 324.0, 432.0]

    try:
        with wave.open(QUOTE_BGM_FILE, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            frames = bytearray()
            for i in range(num_samples):
                t = float(i) / sample_rate
                loop_envelope = math.sin(math.pi * (i / num_samples))
                slow_lfo = 1.0 + 0.12 * math.sin(2 * math.pi * 0.3 * t)

                val = 0.0
                for f in chords:
                    val += math.sin(2.0 * math.pi * f * t) * 0.25

                val = val * loop_envelope * slow_lfo * 0.32
                val = max(-1.0, min(1.0, val))

                sample_int = int(val * 32767.0)
                frames.extend(struct.pack('<h', sample_int))

            wav_file.writeframes(frames)
    except Exception as e:
        print(f"Error generating quote BGM: {e}")


class AmbientAudioManager:
    """
    Dual-Track Audio Controller:
    - Track 1: General Retro App BGM (chiptune ambient loop)
    - Track 2: Quote / Voice Narration BGM (plays golden-brown.mp3 or custom track under speech until speech finishes)
    """

    def __init__(self):
        self.is_playing = False
        self.mixer_initialized = False
        self.quote_channel = None
        self.quote_sound = None
        self.is_quote_previewing = False
        
        # Load saved audio configuration
        audio_cfg = get_audio_settings()
        self.app_bgm_vol = float(audio_cfg.get("app_bgm_vol", 0.35))
        self.quote_bgm_vol = float(audio_cfg.get("quote_bgm_vol", 0.30))
        
        # Track file resolution
        self.quote_track_path = self._resolve_quote_track(audio_cfg.get("quote_bgm_track"))
        self.app_track_path = self._resolve_app_track(audio_cfg.get("app_bgm_track"))
        
        self._init_mixer()

    def _resolve_quote_track(self, saved_path=None):
        """Resolves the best path for quote background music, defaulting to golden-brown.mp3."""
        # 1. Check user configured path
        if saved_path:
            cand = os.path.abspath(saved_path) if os.path.isabs(saved_path) else os.path.join(DATA_DIR, saved_path)
            if os.path.exists(cand):
                return cand

        # 2. Check golden-brown.mp3 in DATA_DIR
        if os.path.exists(GOLDEN_BROWN_FILE):
            return GOLDEN_BROWN_FILE

        # 3. Check golden-brown.mp3 in workspace root
        root_cand = os.path.abspath(os.path.join(BASE_DIR, "..", "golden-brown.mp3"))
        if os.path.exists(root_cand):
            return root_cand

        # 4. Fallback to generated quote pad
        return QUOTE_BGM_FILE

    def _resolve_app_track(self, saved_path=None):
        """Resolves the best path for general ambient background music, defaulting to Interstellar S.T.A.Y."""
        # 1. Check user configured path
        if saved_path:
            cand = os.path.abspath(saved_path) if os.path.isabs(saved_path) else os.path.join(DATA_DIR, saved_path)
            if os.path.exists(cand):
                return cand

        # 2. Check interstellar_stay.mp3 in DATA_DIR
        if os.path.exists(INTERSTELLAR_FILE):
            return INTERSTELLAR_FILE

        # 3. Check long filename in workspace root
        for fname in os.listdir(os.path.join(BASE_DIR, "..")):
            if "Interstellar" in fname or "S.T.A.Y" in fname:
                full_p = os.path.abspath(os.path.join(BASE_DIR, "..", fname))
                if os.path.isfile(full_p):
                    return full_p

        # 4. Fallback to generated ambient tone
        return AMBIENT_FILE

    @property
    def quote_track_name(self):
        """Human-readable filename of currently selected quote music."""
        return os.path.basename(self.quote_track_path) if self.quote_track_path else "golden-brown.mp3"

    @property
    def app_track_name(self):
        """Human-readable filename of currently selected app ambient music."""
        return os.path.basename(self.app_track_path) if self.app_track_path else "ambient_calm.wav"

    def _init_mixer(self):
        if not PYGAME_AVAILABLE:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=4, buffer=1024)
            self.mixer_initialized = True
            
            # Ensure fallback generated audio exists
            generate_offline_ambient_tone()
            generate_offline_quote_bgm()
            
            # Setup dedicated quote channel (Channel 1)
            self.quote_channel = pygame.mixer.Channel(1)
            self._reload_quote_sound()
        except Exception as e:
            print(f"Pygame initialization note: {e}")
            self.mixer_initialized = False

    def _reload_quote_sound(self):
        """Loads or reloads the quote narration audio sound object."""
        if not PYGAME_AVAILABLE or not self.mixer_initialized:
            return False

        if self.quote_track_path and os.path.exists(self.quote_track_path):
            try:
                self.quote_sound = pygame.mixer.Sound(self.quote_track_path)
                return True
            except Exception as e:
                print(f"Error loading quote track {self.quote_track_path}: {e}")
        
        # Fallback to generated pad
        if os.path.exists(QUOTE_BGM_FILE):
            try:
                self.quote_sound = pygame.mixer.Sound(QUOTE_BGM_FILE)
                self.quote_track_path = QUOTE_BGM_FILE
                return True
            except Exception:
                pass
        return False

    # -------------------------------------------------------------
    # General App BGM Control
    # -------------------------------------------------------------
    def toggle(self):
        if not PYGAME_AVAILABLE or not self.mixer_initialized:
            return False, "Pygame is not initialized."

        active_file = self.app_track_path if os.path.exists(self.app_track_path) else AMBIENT_FILE
        if not os.path.exists(active_file):
            generate_offline_ambient_tone()
            active_file = AMBIENT_FILE

        if self.is_playing:
            try:
                pygame.mixer.music.stop()
                self.is_playing = False
                return False, "Audio Paused"
            except Exception:
                self.is_playing = False
                return False, "Error stopping audio"
        else:
            try:
                pygame.mixer.music.load(active_file)
                pygame.mixer.music.set_volume(self.app_bgm_vol)
                pygame.mixer.music.play(-1)
                self.is_playing = True
                return True, "Audio Playing"
            except Exception as e:
                self.is_playing = False
                return False, f"Error starting audio: {e}"

    def set_app_bgm_volume(self, vol):
        """Sets volume level for general background ambient music (0.0 to 1.0)."""
        self.app_bgm_vol = max(0.0, min(1.0, float(vol)))
        if self.mixer_initialized:
            try:
                pygame.mixer.music.set_volume(self.app_bgm_vol)
            except Exception:
                pass
        set_audio_settings(app_bgm_vol=self.app_bgm_vol)

    def set_app_track(self, file_path):
        """Sets and persists a custom track for general app ambient BGM."""
        if file_path and os.path.exists(file_path):
            self.app_track_path = file_path
            set_audio_settings(app_bgm_track=file_path)
            if self.is_playing:
                try:
                    pygame.mixer.music.load(file_path)
                    pygame.mixer.music.set_volume(self.app_bgm_vol)
                    pygame.mixer.music.play(-1)
                except Exception as e:
                    print(f"Error switching app BGM track: {e}")
            return True
        return False

    # -------------------------------------------------------------
    # Quote & Speech Narration BGM Control (Golden Brown & Custom Tracks)
    # -------------------------------------------------------------
    def set_quote_bgm_volume(self, vol):
        """Sets volume level for background music playing during quote narration (0.0 to 1.0)."""
        self.quote_bgm_vol = max(0.0, min(1.0, float(vol)))
        if self.quote_channel:
            try:
                self.quote_channel.set_volume(self.quote_bgm_vol)
            except Exception:
                pass
        set_audio_settings(quote_bgm_vol=self.quote_bgm_vol)

    def set_quote_track(self, file_path):
        """Sets and persists custom background music for quote reading."""
        if file_path and os.path.exists(file_path):
            self.quote_track_path = file_path
            set_audio_settings(quote_bgm_track=file_path)
            self._reload_quote_sound()
            return True
        return False

    def start_quote_narration_music(self):
        """Starts background music (golden-brown.mp3) under quote speech narration."""
        if not PYGAME_AVAILABLE or not self.mixer_initialized:
            return

        if not self.quote_sound:
            self._reload_quote_sound()

        if self.quote_sound and self.quote_channel:
            try:
                # Duck main app BGM slightly for voice clarity
                if self.is_playing:
                    pygame.mixer.music.set_volume(self.app_bgm_vol * 0.35)
                
                self.quote_channel.set_volume(self.quote_bgm_vol)
                self.quote_channel.play(self.quote_sound, loops=-1, fade_ms=300)
            except Exception as e:
                print(f"Error starting quote BGM: {e}")

    def stop_quote_narration_music(self):
        """Smoothly stops background music when quote speech narration finishes."""
        if not PYGAME_AVAILABLE or not self.mixer_initialized:
            return

        if self.quote_channel:
            try:
                self.quote_channel.fadeout(800)
            except Exception:
                try:
                    self.quote_channel.stop()
                except Exception:
                    pass

        # Restore main app BGM volume
        if self.is_playing:
            try:
                pygame.mixer.music.set_volume(self.app_bgm_vol)
            except Exception:
                pass

    def preview_quote_bgm(self):
        """Toggle preview of quote background music directly from Settings/About."""
        if not PYGAME_AVAILABLE or not self.mixer_initialized:
            return False, "Audio engine not ready."

        if not self.quote_sound:
            self._reload_quote_sound()

        if not self.quote_sound or not self.quote_channel:
            return False, "Quote music file not loaded."

        if self.is_quote_previewing:
            self.stop_quote_preview()
            return False, "Preview Stopped"
        else:
            try:
                self.quote_channel.set_volume(self.quote_bgm_vol)
                self.quote_channel.play(self.quote_sound, loops=-1, fade_ms=200)
                self.is_quote_previewing = True
                return True, "Playing Quote BGM Preview"
            except Exception as e:
                self.is_quote_previewing = False
                return False, f"Preview Error: {e}"

    def stop_quote_preview(self):
        """Stops quote preview playback."""
        if self.quote_channel:
            try:
                self.quote_channel.fadeout(400)
            except Exception:
                try:
                    self.quote_channel.stop()
                except Exception:
                    pass
        self.is_quote_previewing = False

    def stop(self):
        if self.mixer_initialized:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            if self.quote_channel:
                try:
                    self.quote_channel.stop()
                except Exception:
                    pass
            self.is_playing = False
            self.is_quote_previewing = False
