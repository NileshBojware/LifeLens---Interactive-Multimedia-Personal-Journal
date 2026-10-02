"""
LifeLens - Data Manager Module
Handles local JSON storage, sample data generation, analytics calculation,
and 5 dynamic personality color themes with persistence.
"""

import os
import json
import uuid
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
DATA_FILE = os.path.join(DATA_DIR, "journal_data.json")
PETS_DIR = os.path.join(DATA_DIR, "pets")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

# =====================================================================
# 5 Distinct Personality Color Themes
# =====================================================================
PERSONALITY_THEMES = {
    "Cyber Gamer": {
        "name": "Cyber Gamer",
        "emoji": "🎮",
        "tagline": "HIGH REFLEX // 8-BIT CYBERPUNK ARCADE",
        "bg_main": "#0f0f1b",
        "bg_card": "#1a192e",
        "bg_inner": "#252342",
        "bg_sidebar": "#121124",
        "accent_primary": "#00f0ff",      # Glitch Cyan
        "accent_secondary": "#ff007f",    # Arcade Magenta
        "accent_gold": "#ffd700",         # Coin Gold
        "accent_green": "#00ff66",        # 1-UP Green
        "text_main": "#f1f5f9",
        "text_muted": "#8e8db5",
        "border": "#3d3a68",
        "chart_colors": ["#00f0ff", "#ff007f", "#ffd700", "#00ff66", "#a855f7", "#ff3333", "#38bdf8"]
    },
    "Zen Sage": {
        "name": "Zen Sage",
        "emoji": "🌿",
        "tagline": "MINDFUL HARMONY // CALM FOREST GROVE",
        "bg_main": "#081c15",
        "bg_card": "#112b23",
        "bg_inner": "#1b4332",
        "bg_sidebar": "#0b2119",
        "accent_primary": "#52b788",      # Emerald Jade
        "accent_secondary": "#74c69d",    # Matcha Mint
        "accent_gold": "#d8f3dc",         # Pale Leaf
        "accent_green": "#40916c",        # Pine Green
        "text_main": "#f0fff4",
        "text_muted": "#80b996",
        "border": "#2d6a4f",
        "chart_colors": ["#52b788", "#74c69d", "#d8f3dc", "#95d5b2", "#b7e4c7", "#2d6a4f", "#1b4332"]
    },
    "Vibrant Artist": {
        "name": "Vibrant Artist",
        "emoji": "🎨",
        "tagline": "CREATIVE SPARK // SUNSET PASSION",
        "bg_main": "#1f1024",
        "bg_card": "#2d1b33",
        "bg_inner": "#3d2445",
        "bg_sidebar": "#190c1d",
        "accent_primary": "#f43f5e",      # Sunset Coral
        "accent_secondary": "#a855f7",    # Electric Violet
        "accent_gold": "#fbbf24",         # Amber Glow
        "accent_green": "#34d399",        # Aqua Paint
        "text_main": "#fdf4ff",
        "text_muted": "#b582be",
        "border": "#582963",
        "chart_colors": ["#f43f5e", "#a855f7", "#fbbf24", "#34d399", "#ec4899", "#f97316", "#818cf8"]
    },
    "Deep Scholar": {
        "name": "Deep Scholar",
        "emoji": "🌌",
        "tagline": "ANALYTICAL MIND // CELESTIAL INTELLECT",
        "bg_main": "#0a0f1d",
        "bg_card": "#131c33",
        "bg_inner": "#1c2b4d",
        "bg_sidebar": "#0e1529",
        "accent_primary": "#38bdf8",      # Celestial Blue
        "accent_secondary": "#818cf8",    # Indigo Starlight
        "accent_gold": "#facc15",         # Stellar Gold
        "accent_green": "#2dd4bf",        # Prism Teal
        "text_main": "#f0f9ff",
        "text_muted": "#8197be",
        "border": "#2b3f6c",
        "chart_colors": ["#38bdf8", "#818cf8", "#facc15", "#2dd4bf", "#60a5fa", "#c084fc", "#4ade80"]
    },
    "Cozy Nomad": {
        "name": "Cozy Nomad",
        "emoji": "☕",
        "tagline": "WARM NOSTALGIA // CARAMEL FIRESIDE",
        "bg_main": "#1c120c",
        "bg_card": "#2c1d14",
        "bg_inner": "#3d291d",
        "bg_sidebar": "#170e0a",
        "accent_primary": "#fb923c",      # Warm Amber
        "accent_secondary": "#f87171",    # Terracotta
        "accent_gold": "#fde047",         # Honey Cream
        "accent_green": "#a3e635",        # Olive Leaf
        "text_main": "#fffbeb",
        "text_muted": "#b8957c",
        "border": "#573a28",
        "chart_colors": ["#fb923c", "#f87171", "#fde047", "#a3e635", "#d97706", "#ea580c", "#ca8a04"]
    },
    "Eternal Cosmos": {
        "name": "Eternal Cosmos",
        "emoji": "🚀",
        "tagline": "RETRO SPACE ODYSSEY // PITCH BLACK STARFIELD",
        "bg_main": "#030308",
        "bg_card": "#090914",
        "bg_inner": "#111122",
        "bg_sidebar": "#05050d",
        "accent_primary": "#00f0ff",      # Supernova Cyan
        "accent_secondary": "#bd00ff",    # Nebula Neon Violet
        "accent_gold": "#ffe600",         # Pulsar Star Gold
        "accent_green": "#00ff9d",        # Warp Drive Emerald
        "text_main": "#ffffff",           # Pure Star White
        "text_muted": "#7e84a3",          # Cosmic Dust Grey
        "border": "#1e1e38",              # Horizon Line
        "chart_colors": ["#00f0ff", "#bd00ff", "#ffe600", "#00ff9d", "#ff007f", "#7928ca", "#38bdf8"]
    }
}

DEFAULT_PERSONALITY = "Eternal Cosmos"


def get_active_personality():
    """Load the user's selected personality theme, or return default."""
    ensure_data_directories()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                theme_name = cfg.get("personality", DEFAULT_PERSONALITY)
                if theme_name in PERSONALITY_THEMES:
                    return theme_name
        except Exception:
            pass
    return DEFAULT_PERSONALITY


def set_active_personality(theme_name):
    """Save the user's selected personality theme."""
    ensure_data_directories()
    if theme_name not in PERSONALITY_THEMES:
        theme_name = DEFAULT_PERSONALITY
    try:
        cfg = {}
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except Exception:
                cfg = {}
        cfg["personality"] = theme_name
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False


def get_audio_settings():
    """Retrieve saved audio volume and track settings for App BGM and Quote Narration BGM."""
    ensure_data_directories()
    defaults = {
        "app_bgm_vol": 0.35,
        "quote_bgm_vol": 0.30,
        "quote_bgm_track": "golden-brown.mp3",
        "app_bgm_track": "interstellar_stay.mp3"
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return {
                    "app_bgm_vol": float(cfg.get("app_bgm_vol", 0.35)),
                    "quote_bgm_vol": float(cfg.get("quote_bgm_vol", 0.30)),
                    "quote_bgm_track": cfg.get("quote_bgm_track", "golden-brown.mp3"),
                    "app_bgm_track": cfg.get("app_bgm_track", "interstellar_stay.mp3")
                }
        except Exception:
            pass
    return defaults


def set_audio_settings(app_bgm_vol=None, quote_bgm_vol=None, quote_bgm_track=None, app_bgm_track=None):
    """Persist audio volume and track settings."""
    ensure_data_directories()
    try:
        cfg = {}
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except Exception:
                cfg = {}
        if app_bgm_vol is not None:
            cfg["app_bgm_vol"] = round(float(app_bgm_vol), 2)
        if quote_bgm_vol is not None:
            cfg["quote_bgm_vol"] = round(float(quote_bgm_vol), 2)
        if quote_bgm_track is not None:
            cfg["quote_bgm_track"] = str(quote_bgm_track)
        if app_bgm_track is not None:
            cfg["app_bgm_track"] = str(app_bgm_track)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving audio settings: {e}")
        return False


def get_pet_settings():
    """Retrieve saved pet settings: sleep state, pet type, custom GIF path, speed."""
    ensure_data_directories()
    defaults = {
        "pet_sleeping": False,
        "pet_type": "Pixel Cyber Cat",
        "pet_custom_path": "",
        "pet_speed": 3
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return {
                    "pet_sleeping": bool(cfg.get("pet_sleeping", False)),
                    "pet_type": cfg.get("pet_type", "Pixel Cyber Cat"),
                    "pet_custom_path": cfg.get("pet_custom_path", ""),
                    "pet_speed": int(cfg.get("pet_speed", 3))
                }
        except Exception:
            pass
    return defaults


def set_pet_settings(pet_sleeping=None, pet_type=None, pet_custom_path=None, pet_speed=None):
    """Persist pet settings in settings.json."""
    ensure_data_directories()
    try:
        cfg = {}
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except Exception:
                cfg = {}
        if pet_sleeping is not None:
            cfg["pet_sleeping"] = bool(pet_sleeping)
        if pet_type is not None:
            cfg["pet_type"] = str(pet_type)
        if pet_custom_path is not None:
            cfg["pet_custom_path"] = str(pet_custom_path)
        if pet_speed is not None:
            cfg["pet_speed"] = max(1, min(12, int(pet_speed)))
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving pet settings: {e}")
        return False


# Moods and their associated emojis and theme colors
MOOD_MAP = {
    "Happy": {"emoji": "😊", "color": "#F59E0B", "energy_avg": 8},
    "Calm": {"emoji": "😌", "color": "#10B981", "energy_avg": 6},
    "Good": {"emoji": "🙂", "color": "#3B82F6", "energy_avg": 7},
    "Neutral": {"emoji": "😐", "color": "#6B7280", "energy_avg": 5},
    "Sad": {"emoji": "😔", "color": "#6366F1", "energy_avg": 3},
    "Tired": {"emoji": "😫", "color": "#8B5CF6", "energy_avg": 2},
    "Stressed": {"emoji": "😤", "color": "#EF4444", "energy_avg": 4},
}

ACTIVITIES = [
    "Work",
    "Coding",
    "Exercise",
    "Family",
    "Reading",
    "Travel",
    "Creative",
    "Relaxation",
    "Other"
]


def ensure_data_directories():
    """Ensure data/, data/images/, and data/pets/ directories exist."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(IMAGES_DIR, exist_ok=True)
        os.makedirs(PETS_DIR, exist_ok=True)
    except Exception as e:
        print(f"Error creating directories: {e}")


def get_default_sample_entries():
    """Generate realistic initial sample entries with varied dates and metrics."""
    today = datetime.now()
    d0 = today.strftime("%Y-%m-%d")
    d1 = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    d2 = (today - timedelta(days=2)).strftime("%Y-%m-%d")
    d3 = (today - timedelta(days=4)).strftime("%Y-%m-%d")
    d4 = (today - timedelta(days=6)).strftime("%Y-%m-%d")

    sample_entries = [
        {
            "id": str(uuid.uuid4()),
            "date": d0,
            "mood": "Happy",
            "energy": 9,
            "activity": "Coding",
            "text": "Finished building and styling the LifeLens multimedia journal desktop application. Everything connects together smoothly with beautiful UI cards, charts, and voice tools!",
            "image": "data/images/sample_coding.png",
            "is_sample": True
        },
        {
            "id": str(uuid.uuid4()),
            "date": d1,
            "mood": "Calm",
            "energy": 7,
            "activity": "Reading",
            "text": "Spent a peaceful afternoon reading by the park. Practiced mindfulness and enjoyed a warm cup of herbal tea while listening to gentle ambient rain sounds.",
            "image": "data/images/sample_reading.png",
            "is_sample": True
        },
        {
            "id": str(uuid.uuid4()),
            "date": d2,
            "mood": "Good",
            "energy": 8,
            "activity": "Exercise",
            "text": "Went for a 5km morning run along the riverside trail. Felt energized and motivated for the day ahead.",
            "image": "data/images/sample_exercise.png",
            "is_sample": True
        },
        {
            "id": str(uuid.uuid4()),
            "date": d3,
            "mood": "Tired",
            "energy": 4,
            "activity": "Work",
            "text": "Long day of review meetings and document revisions. Need a good night's sleep to recharge my energy reserves.",
            "image": "",
            "is_sample": True
        },
        {
            "id": str(uuid.uuid4()),
            "date": d4,
            "mood": "Happy",
            "energy": 8,
            "activity": "Family",
            "text": "Had a lovely weekend dinner gathering with family and friends. Cooked homemade pasta and shared memorable stories.",
            "image": "data/images/sample_nature.png",
            "is_sample": True
        }
    ]
    return sample_entries


def load_entries():
    """
    Load journal entries from local JSON storage.
    If file doesn't exist or is empty/corrupt, auto-initializes with sample entries.
    """
    ensure_data_directories()
    
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        samples = get_default_sample_entries()
        save_entries(samples)
        return samples

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for entry in data:
                    if "id" not in entry:
                        entry["id"] = str(uuid.uuid4())
                    if "is_sample" not in entry:
                        entry["is_sample"] = False
                return data
            else:
                samples = get_default_sample_entries()
                save_entries(samples)
                return samples
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: Corrupt JSON ({e}). Falling back to sample entries.")
        samples = get_default_sample_entries()
        try:
            save_entries(samples)
        except Exception:
            pass
        return samples


def save_entries(entries):
    """Save list of journal entries to JSON file."""
    ensure_data_directories()
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving entries: {e}")
        return False


def add_entry(date_str, mood, energy, activity, text, image_rel_path="", is_sample=False):
    """Add a new journal entry to storage."""
    if not text or not text.strip():
        return False, "Journal entry text cannot be empty."
    
    if mood not in MOOD_MAP:
        mood = "Good"
        
    try:
        energy_val = int(energy)
        energy_val = max(1, min(10, energy_val))
    except (ValueError, TypeError):
        energy_val = 5

    new_entry = {
        "id": str(uuid.uuid4()),
        "date": date_str if date_str else datetime.now().strftime("%Y-%m-%d"),
        "mood": mood,
        "energy": energy_val,
        "activity": activity if activity else "Other",
        "text": text.strip(),
        "image": image_rel_path if image_rel_path else "",
        "is_sample": bool(is_sample)
    }

    entries = load_entries()
    entries.insert(0, new_entry)
    if save_entries(entries):
        return True, new_entry
    return False, "Failed to write entry to storage."


def delete_entry(entry_id):
    """Delete an entry by its ID."""
    entries = load_entries()
    original_len = len(entries)
    entries = [e for e in entries if e.get("id") != entry_id]
    if len(entries) != original_len:
        save_entries(entries)
        return True
    return False


def clear_sample_entries():
    """Remove all sample entries from the dataset."""
    entries = load_entries()
    filtered = [e for e in entries if not e.get("is_sample", False)]
    save_entries(filtered)
    return len(entries) - len(filtered)


def get_statistics():
    """Compute statistics for the dashboard and insights view."""
    entries = load_entries()
    total = len(entries)
    
    if total == 0:
        return {
            "total_entries": 0,
            "avg_energy": 0.0,
            "latest_mood": "None",
            "latest_mood_emoji": "✨",
            "top_mood": "None",
            "top_mood_emoji": "✨",
            "top_activity": "None",
            "mood_counts": {},
            "activity_counts": {},
            "energy_trend": [],
            "recent_entries": []
        }

    sorted_entries = sorted(entries, key=lambda x: x.get("date", ""), reverse=False)
    total_energy = sum(e.get("energy", 5) for e in entries)
    avg_energy = round(total_energy / total, 1)

    mood_counts = {m: 0 for m in MOOD_MAP.keys()}
    for e in entries:
        m = e.get("mood", "Good")
        mood_counts[m] = mood_counts.get(m, 0) + 1

    top_mood = max(mood_counts.items(), key=lambda x: x[1])[0] if entries else "Good"
    top_mood_emoji = MOOD_MAP.get(top_mood, {}).get("emoji", "😊")

    activity_counts = {}
    for e in entries:
        act = e.get("activity", "Other")
        activity_counts[act] = activity_counts.get(act, 0) + 1
    
    top_activity = max(activity_counts.items(), key=lambda x: x[1])[0] if activity_counts else "General"

    newest = sorted(entries, key=lambda x: x.get("date", ""), reverse=True)[0]
    latest_mood = newest.get("mood", "Good")
    latest_mood_emoji = MOOD_MAP.get(latest_mood, {}).get("emoji", "😊")

    date_energy_map = {}
    for e in sorted_entries:
        d = e.get("date", "")
        en = e.get("energy", 5)
        if d not in date_energy_map:
            date_energy_map[d] = []
        date_energy_map[d].append(en)
    
    energy_trend = []
    for d, en_list in date_energy_map.items():
        energy_trend.append((d, round(sum(en_list) / len(en_list), 1)))

    return {
        "total_entries": total,
        "avg_energy": avg_energy,
        "latest_mood": latest_mood,
        "latest_mood_emoji": latest_mood_emoji,
        "top_mood": top_mood,
        "top_mood_emoji": top_mood_emoji,
        "top_activity": top_activity,
        "mood_counts": mood_counts,
        "activity_counts": activity_counts,
        "energy_trend": energy_trend,
        "recent_entries": sorted(entries, key=lambda x: x.get("date", ""), reverse=True)[:4]
    }
