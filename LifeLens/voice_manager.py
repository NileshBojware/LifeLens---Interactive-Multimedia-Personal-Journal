"""
LifeLens - Voice Manager Module
Handles Speech-to-Text (SpeechRecognition) and Text-to-Speech (pyttsx3)
with asynchronous background threading and comprehensive error handling.
"""

import threading
import tkinter.messagebox as messagebox

try:
    import speech_recognition as sr
    SPEECH_REC_AVAILABLE = True
except ImportError:
    sr = None
    SPEECH_REC_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    pyttsx3 = None
    PYTTSX3_AVAILABLE = False


class VoiceInputManager:
    """Manages microphone recording and speech-to-text recognition."""

    def __init__(self):
        self.is_listening = False
        self._lock = threading.Lock()

    @staticmethod
    def is_supported():
        return SPEECH_REC_AVAILABLE

    def record_and_transcribe(self, on_success, on_error, on_status_update=None):
        """
        Runs speech recognition asynchronously in a background thread
        to prevent blocking the Tkinter event loop.
        """
        if not SPEECH_REC_AVAILABLE:
            if on_error:
                on_error("SpeechRecognition library is not installed.\nYou can type your journal entry directly.")
            return

        with self._lock:
            if self.is_listening:
                if on_status_update:
                    on_status_update("Already listening...")
                return
            self.is_listening = True

        def _worker():
            try:
                if on_status_update:
                    on_status_update("🎙️ Preparing microphone...")

                recognizer = sr.Recognizer()
                recognizer.energy_threshold = 300
                recognizer.dynamic_energy_threshold = True

                try:
                    with sr.Microphone() as source:
                        if on_status_update:
                            on_status_update("🎙️ Listening... Please speak now.")
                        recognizer.adjust_for_ambient_noise(source, duration=0.6)
                        audio = recognizer.listen(source, timeout=6, phrase_time_limit=14)
                except (AttributeError, OSError) as mic_err:
                    raise RuntimeError(
                        f"Microphone device not accessible or PyAudio not configured: {mic_err}.\n"
                        "Please ensure a microphone is connected, or type directly."
                    )

                if on_status_update:
                    on_status_update("⏳ Transcribing speech...")

                # Transcribe speech
                try:
                    # Uses standard recognition
                    text = recognizer.recognize_google(audio)
                    if text and text.strip():
                        if on_success:
                            on_success(text.strip())
                    else:
                        if on_error:
                            on_error("No speech was detected. Please try speaking again.")
                except sr.UnknownValueError:
                    if on_error:
                        on_error("Could not understand the audio. Please try again with clear speech.")
                except sr.RequestError as req_err:
                    if on_error:
                        on_error(f"Speech recognition service unavailable ({req_err}). Please type your entry.")

            except Exception as ex:
                if on_error:
                    on_error(str(ex))
            finally:
                with self._lock:
                    self.is_listening = False
                if on_status_update:
                    on_status_update("Ready")

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()


class TextToSpeechManager:
    """Manages text-to-speech synthesis with pyttsx3."""

    def __init__(self):
        self._is_speaking = False
        self._lock = threading.Lock()

    @staticmethod
    def is_supported():
        return PYTTSX3_AVAILABLE

    def is_speaking(self):
        return self._is_speaking

    def read_aloud_async(self, text, rate=125, on_start=None, on_word=None, on_finish=None, on_error=None):
        """
        Reads the provided text aloud in a background thread at 0.75x calm speed.
        Provides real-time on_word(name, location, length) event callbacks for word-by-word UI highlighting.
        Gracefully handles missing audio drivers or pyttsx3 errors.
        """
        if not text or not text.strip():
            if on_error:
                on_error("No text to read aloud.")
            return

        if not PYTTSX3_AVAILABLE:
            if on_error:
                on_error("pyttsx3 library is not available for Text-to-Speech.")
            return

        with self._lock:
            if self._is_speaking:
                return
            self._is_speaking = True

        def _tts_worker():
            try:
                if on_start:
                    on_start()

                # Reinitialize engine in worker thread for Windows COM apartment safety
                engine = pyttsx3.init()
                # 0.75x speed setting (approx 125 words per minute for relaxed, clear narration)
                speech_rate = rate if rate else 125
                engine.setProperty('rate', speech_rate)
                engine.setProperty('volume', 0.95)
                
                try:
                    voices = engine.getProperty('voices')
                    if voices and len(voices) > 1:
                        engine.setProperty('voice', voices[0].id)
                except Exception:
                    pass

                # Connect word callback for real-time karaoke / word-by-word visual highlight
                if on_word:
                    def _word_handler(name, location, length):
                        try:
                            on_word(name, location, length)
                        except Exception as w_err:
                            pass
                    engine.connect('started-word', _word_handler)

                engine.say(text)
                engine.runAndWait()
                engine.stop()

            except Exception as e:
                print(f"TTS Error: {e}")
                if on_error:
                    on_error(f"Text-to-Speech encounter: {e}")
            finally:
                with self._lock:
                    self._is_speaking = False
                if on_finish:
                    on_finish()

        thread = threading.Thread(target=_tts_worker, daemon=True)
        thread.start()
