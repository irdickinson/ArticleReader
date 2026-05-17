import re
import threading
from typing import Any

import sounddevice as sd
from PyQt6.QtCore import QThread, pyqtSignal

# Cached per lang_code so the model only loads once per session
_pipelines: dict[str, Any] = {}


class TTSWorker(QThread):
    status = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, text: str, voice: str = "af_heart") -> None:
        super().__init__()
        self._text = text
        self._voice = voice
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()
        sd.stop()

    def run(self) -> None:
        try:
            lang_code = "b" if self._voice.startswith("b") else "a"

            if lang_code not in _pipelines:
                self.status.emit("Loading voice model…")
                from kokoro import KPipeline
                _pipelines[lang_code] = KPipeline(lang_code=lang_code)

            pipeline = _pipelines[lang_code]
            self.status.emit("Speaking…")

            clean = _strip_markdown(self._text)
            for _, _, audio in pipeline(clean, voice=self._voice):
                if self._stop_event.is_set():
                    break
                sd.play(audio, samplerate=24000)
                sd.wait()
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()


# Voices available in Kokoro, grouped by accent and gender.
# Keys are display names shown in the UI; values are Kokoro voice IDs.
VOICES: dict[str, str] = {
    # --- US English ---
    "Heart  (US ♀)":    "af_heart",
    "Bella  (US ♀)":    "af_bella",
    "Nicole (US ♀)":    "af_nicole",
    "Sky    (US ♀)":    "af_sky",
    "Adam   (US ♂)":    "am_adam",
    "Michael(US ♂)":    "am_michael",
    # --- UK English ---
    "Emma   (UK ♀)":    "bf_emma",
    "Isabella(UK ♀)":   "bf_isabella",
    "George (UK ♂)":    "bm_george",
    "Lewis  (UK ♂)":    "bm_lewis",
}


def _strip_markdown(text: str) -> str:
    text = re.sub(r"#{1,6}\s*", "", text)                        # headings
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)                 # bold
    text = re.sub(r"\*(.*?)\*", r"\1", text)                     # italic
    text = re.sub(r"`(.*?)`", r"\1", text)                       # inline code
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)        # blockquotes
    text = re.sub(r"^[-*+]\s+", "", text, flags=re.MULTILINE)    # bullets
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)        # links
    text = re.sub(r"\n{3,}", "\n\n", text)                       # excess blank lines
    return text.strip()
