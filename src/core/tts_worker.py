import asyncio
import os
import re
import tempfile
import threading

import miniaudio
import numpy as np
import sounddevice as sd
from PyQt6.QtCore import QThread, pyqtSignal

import edge_tts


class TTSWorker(QThread):
    status = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(
        self,
        text: str,
        voice: str = "en-US-AriaNeural",
        rate: str = "+0%",
    ) -> None:
        super().__init__()
        self._text = text
        self._voice = voice
        self._rate = rate
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()
        sd.stop()

    def run(self) -> None:
        try:
            clean = _strip_markdown(self._text)
            # Split on blank lines to synthesize paragraph by paragraph
            # so Stop is responsive and we don't wait for a full synthesis
            paragraphs = [p.strip() for p in re.split(r"\n{2,}", clean) if p.strip()]
            if not paragraphs:
                return

            self.status.emit("Speaking…")

            for para in paragraphs:
                if self._stop_event.is_set():
                    break
                self._speak_paragraph(para)

        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()

    def _speak_paragraph(self, text: str) -> None:
        tmp = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp = f.name

            asyncio.run(_synthesize(text, self._voice, self._rate, tmp))

            if self._stop_event.is_set():
                return

            decoded = miniaudio.decode_file(tmp, output_format=miniaudio.SampleFormat.SIGNED16)
            samples = np.frombuffer(decoded.samples, dtype=np.int16)
            if decoded.nchannels > 1:
                samples = samples.reshape(-1, decoded.nchannels)

            sd.play(samples, decoded.sample_rate)
            sd.wait()
        finally:
            if tmp and os.path.exists(tmp):
                os.unlink(tmp)


async def _synthesize(text: str, voice: str, rate: str, output_path: str) -> None:
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)


# Display name → edge-tts SSML rate string
SPEEDS: dict[str, str] = {
    "0.5×":  "-50%",
    "0.75×": "-25%",
    "1×":    "+0%",
    "1.25×": "+25%",
    "1.5×":  "+50%",
    "1.75×": "+75%",
    "2×":    "+100%",
}

# Display name → edge-tts voice ID
VOICES: dict[str, str] = {
    # US English
    "Aria    (US ♀)":  "en-US-AriaNeural",
    "Jenny   (US ♀)":  "en-US-JennyNeural",
    "Sara    (US ♀)":  "en-US-SaraNeural",
    "Guy     (US ♂)":  "en-US-GuyNeural",
    "Tony    (US ♂)":  "en-US-TonyNeural",
    "Davis   (US ♂)":  "en-US-DavisNeural",
    # UK English
    "Sonia   (UK ♀)":  "en-GB-SoniaNeural",
    "Libby   (UK ♀)":  "en-GB-LibbyNeural",
    "Ryan    (UK ♂)":  "en-GB-RyanNeural",
    "Thomas  (UK ♂)":  "en-GB-ThomasNeural",
}


def _strip_markdown(text: str) -> str:
    text = re.sub(r"#{1,6}\s*", "", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`(.*?)`", r"\1", text)
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
