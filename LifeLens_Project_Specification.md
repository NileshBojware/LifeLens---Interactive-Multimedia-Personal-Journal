# LifeLens – Interactive Multimedia Personal Journal

## Project Specification (for AI Coding Agent)

> **Note to coding agent:** This is a college mini-project. Keep the implementation simple, clean, and efficient. Do not over-engineer. Do not add extra features beyond this spec. Aim to build this using minimal iterations/credits — favor straightforward, working code over exhaustive polish passes.

---

## 1. Project Concept

LifeLens is a simple, modern, visually appealing **desktop personal journal application** built with **Python**.

The user can create daily journal entries containing:

- Date
- Journal text
- Mood
- Energy level
- Activity/category
- Optional image
- Voice input

The app displays entries in an attractive timeline and provides a simple analytics dashboard.

**Constraints:**
- Must work **fully offline** — no internet, no APIs, no cloud services, no database server, no external datasets.
- Must feel like a polished modern desktop app, but stay simple enough for a college mini-project.
- Do not expand scope beyond what is described in this document.

---

## 2. Main Features

### 2.1 Dashboard (Home Screen)

- LifeLens title/logo (text or emoji-based, no external images)
- Today's date
- Total journal entries count
- Latest mood
- Average energy
- Recent journal entries (short list/preview)
- Simple mood/energy chart (Matplotlib, embedded)
- "New Entry" button
- Navigation to Timeline and Insights
- "About / Libraries Used" section

Use attractive cards, spacing, emoji/icons, and subtle hover/visual effects.

### 2.2 New Journal Entry Form

Fields:
- Date (defaults to today, editable)
- Journal text area (multi-line)
- Mood selector — one of:
  - 😊 Happy
  - 😌 Calm
  - 🙂 Good
  - 😐 Neutral
  - 😔 Sad
  - 😫 Tired
  - 😤 Stressed
- Energy slider (1–10)
- Activity/category selector (e.g., Work, Coding, Exercise, Family, Reading, Travel, Other — simple dropdown)
- Image upload (optional, via file picker)
- 🎙 Voice Entry button (optional)
- Save button

Keep the form on a single simple screen.

### 2.3 Journal Timeline

- Displays past entries as scrollable cards, newest first.
- Each card shows: date, mood emoji, energy, activity, journal text (truncated if long), image thumbnail if present.
- Card actions:
  - 👁 View (full entry in a popup/detail view)
  - 🔊 Read Aloud
  - 🗑 Delete (with confirmation)

### 2.4 Insights (Analytics)

Simple analytics screen showing:
- Total entries
- Average energy
- Most selected mood
- Activity frequency (simple bar chart or counts)
- Mood distribution chart (Matplotlib)
- Energy trend chart (Matplotlib)

No prediction, no ML, no advanced statistics — just counts, averages, and basic charts.

---

## 3. Multimedia Features

### 3.1 Image Processing (Pillow)

- Load user-selected images
- Resize to fit UI
- Generate thumbnails for timeline cards
- Display in Tkinter via `ImageTk`
- Apply one simple filter/effect (e.g., grayscale, slight blur, or brightness enhance) as an optional demonstration of image processing

### 3.2 Voice Input (SpeechRecognition)

- "🎙 Voice Entry" button on the New Entry form
- Records from microphone, converts speech to text
- Recognized text is inserted into the journal text box
- If microphone/recognition is unavailable, show a friendly message box and allow normal typing — do not crash

### 3.3 Text-to-Speech (pyttsx3)

- "🔊 Read Aloud" button on timeline entries/detail view
- Reads the journal text of the selected entry aloud
- Handle unavailability gracefully with a message box

### 3.4 Audio (Pygame)

- Optional simple ambient/background sound toggle (e.g., a soft background tone or short looped ambient clip if a bundled sample audio file is generated/included)
- Keep minimal — a simple on/off toggle button; this is **not** a music player
- If no audio available/fails to load, fail silently or show a simple message; do not block the app

---

## 4. Visual Design Guidelines

- Soft, modern background color palette (e.g., soft neutral background with one accent color, like teal, indigo, or coral)
- Rounded-looking cards (simulate via Canvas-drawn rounded rectangles or padded frames with border colors, since raw Tkinter widgets aren't rounded)
- Consistent padding/spacing across screens
- Clear, readable typography (consistent font family/sizes across the app, e.g., "Segoe UI" or "Helvetica")
- Mood emojis used throughout for visual warmth
- Simple icon-like glyphs (emoji) instead of external icon files
- Subtle hover effects on buttons/cards (color change on hover)
- One consistent accent color used for buttons, highlights, and active nav items
- Clean top or side navigation bar between Dashboard / New Entry / Timeline / Insights / About

Avoid the default gray Tkinter look — use `ttk` styling, custom colors, and custom fonts throughout. No external decorative images; use Canvas/Pillow-generated shapes only.

---

## 5. Python Libraries & Their Roles

| Library | Purpose |
|---|---|
| Tkinter | GUI, windows, frames, buttons, forms, navigation, journal cards |
| Pillow | Image loading, resizing, thumbnails, basic image processing |
| SpeechRecognition | Voice input — converting spoken journal entries into text |
| pyttsx3 | Text-to-speech — reading journal entries aloud |
| Pygame | Simple ambient/background audio |
| Matplotlib | Mood charts, energy charts, analytics (embedded via `FigureCanvasTkAgg`) |
| json (built-in) | Local data storage for journal entries |

No database engine, no ORM, no external APIs.

---

## 6. "Technology & Libraries Used" Section (In-App)

Must be accessible from the app's About/Info screen. Include:

**Table:**

| Library | Purpose |
|---|---|
| Tkinter | GUI and navigation |
| Pillow | Image processing |
| SpeechRecognition | Voice input |
| pyttsx3 | Text-to-speech |
| Pygame | Audio |
| Matplotlib | Charts and analytics |
| JSON | Local data storage |

**Where Each Library Is Used:**

- Tkinter → Entire application interface
- Pillow → Image upload and thumbnails
- SpeechRecognition → Voice Entry
- pyttsx3 → Read Aloud
- Pygame → Ambient audio
- Matplotlib → Insights
- JSON → Journal storage

---

## 7. Local Data Storage

Store journal entries in a local JSON file (list of entry objects). Example entry:

```json
{
    "date": "2026-09-27",
    "mood": "Happy",
    "energy": 8,
    "activity": "Coding",
    "text": "Completed my project today.",
    "image": "data/images/example.jpg",
    "is_sample": false
}
```

Requirements:
- Auto-create `data/` and `data/images/` folders and `journal_data.json` file if missing.
- On first launch (no existing data file, or empty), populate with a few fictional **sample entries** to avoid an empty UI/charts.
- Sample entries must include `"is_sample": true` so they can be visually distinguished (e.g., a small "Sample" badge on the card) and optionally cleared by the user.

---

## 8. Project Structure

```text
LifeLens/
│
├── main.py              # App entry point, navigation between screens
├── data_manager.py      # JSON load/save, sample data generation
├── media_manager.py     # Pillow image handling, Pygame audio
├── voice_manager.py     # SpeechRecognition + pyttsx3 wrappers
├── dashboard.py         # Dashboard/Timeline/Insights/New Entry UI screens
│
├── data/
│   ├── journal_data.json
│   └── images/
│
└── README.md
```

If a simpler structure is more practical during implementation, it is acceptable to reduce/merge files (e.g., combine UI screens into fewer files), but keep logic organized and readable. Do not create excessive files or folders.

---

## 9. Error Handling Requirements

Handle gracefully with user-friendly `tkinter.messagebox` dialogs (never raw tracebacks):

- Empty journal entry (missing text) on save
- Invalid image file selected
- Missing image file (path no longer exists)
- Microphone unavailable / speech recognition failure
- Audio playback unavailable
- Missing `journal_data.json` (auto-create)
- Corrupted JSON file (fallback to empty/sample data with a warning message)
- Missing folders (auto-create)

---

## 10. No External Content Requirement

The app must be fully usable without the developer/user providing any datasets, images, videos, audio files, APIs, or external services.

- Images are optional user uploads only.
- All decorative visuals are generated via Tkinter Canvas / Pillow.
- Sample journal data is auto-generated on first run.
- If ambient audio is included, generate/bundle a minimal simple sound (or make the feature a no-op with a message if no audio file is available) — do not require the user to supply audio.

---

## 11. Explicitly Out of Scope

Do **NOT** implement:

- AI chatbot
- Machine learning
- Facial emotion detection
- Sentiment analysis
- Medical or mental-health diagnosis features
- Login/authentication or user accounts
- Cloud sync
- Social media features
- Complex databases (SQL/NoSQL servers)
- Maps
- Email
- Notifications
- Web scraping
- Any external API integrations

**Core focus only:** Journal + Multimedia + Voice + Visualization + Interactive GUI.

---

## 12. User Flow

```text
Open LifeLens
     ↓
View Dashboard
     ↓
Create Journal Entry
     ↓
Add Mood + Energy + Activity
     ↓
Optionally Add Image
     ↓
Optionally Use Voice Input
     ↓
Save Entry
     ↓
View Entry in Timeline
     ↓
Read Entry Aloud
     ↓
View Insights
     ↓
See Mood/Energy Charts
```

---

## 13. Expected Final Deliverable

A working Python desktop application with:

- Polished, modern Tkinter GUI with custom styling (not default look)
- Working navigation: Dashboard, New Entry, Timeline, Insights, About
- Journal entry creation with mood, energy, activity, optional image, optional voice input
- Scrollable journal timeline with View / Read Aloud / Delete actions
- Image thumbnails and basic image processing via Pillow
- Working voice-to-text (SpeechRecognition) with graceful fallback
- Working text-to-speech (pyttsx3)
- Simple optional ambient audio toggle (Pygame)
- Insights dashboard with Matplotlib charts (mood distribution, energy trend, activity frequency)
- Local JSON-based storage with auto-created folders/files and sample data on first run
- "Technology & Libraries Used" section in the About screen
- Friendly error handling throughout (no tracebacks shown to the user)
- A short README.md explaining how to install dependencies and run the app

**Build instruction:** Implement this efficiently in as few files/iterations as reasonably possible while meeting all requirements above. Avoid unnecessary complexity, abstraction layers, or extra features not listed in this specification.
