import io
import re
from pathlib import Path

import pdfplumber
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ArticleReader/2.0)"}
_STRIP_TAGS = ["script", "style", "nav", "footer", "header", "aside", "noscript"]
_MAX_CHARS = 15_000
_YOUTUBE_RE = re.compile(
    r"(?:youtube\.com/watch\?(?:.*&)?v=|youtu\.be/)([A-Za-z0-9_-]{11})"
)


def extract(source: str) -> tuple[str, str]:
    """Return (title, text) for a URL or local file path."""
    if source.startswith("http://") or source.startswith("https://"):
        if _YOUTUBE_RE.search(source):
            return _from_youtube(source)
        return _from_url(source)
    path = Path(source)
    if path.suffix.lower() == ".pdf":
        return _from_pdf_file(path)
    return _from_html_file(path)


def is_youtube_url(url: str) -> bool:
    return bool(_YOUTUBE_RE.search(url))


def _from_youtube(url: str) -> tuple[str, str]:
    match = _YOUTUBE_RE.search(url)
    if not match:
        raise ValueError(f"Could not extract video ID from URL: {url}")
    video_id = match.group(1)

    # Fetch title from og:title — more reliable than <title> for YouTube
    try:
        response = requests.get(url, headers=_HEADERS, timeout=20)
        soup = BeautifulSoup(response.content, "html.parser")
        og_title = soup.find("meta", property="og:title")
        title = og_title["content"] if og_title else f"YouTube ({video_id})"
    except Exception:
        title = f"YouTube ({video_id})"

    api = YouTubeTranscriptApi()
    try:
        # Try English first; fall back to any available transcript
        try:
            fetched = api.fetch(video_id)
        except NoTranscriptFound:
            transcript_list = api.list(video_id)
            fetched = next(iter(transcript_list)).fetch()
    except TranscriptsDisabled:
        raise RuntimeError("This video has transcripts disabled.")
    except CouldNotRetrieveTranscript as exc:
        raise RuntimeError(f"Could not retrieve transcript: {exc}")

    text = " ".join(snippet.text for snippet in fetched)
    return title, text[:_MAX_CHARS]


def _from_url(url: str) -> tuple[str, str]:
    response = requests.get(url, timeout=20, headers=_HEADERS)
    response.raise_for_status()
    if "pdf" in response.headers.get("content-type", ""):
        return _from_pdf_bytes(response.content, url)
    return _parse_html(response.content, fallback_title=url)


def _from_html_file(path: Path) -> tuple[str, str]:
    content = path.read_bytes()
    return _parse_html(content, fallback_title=path.name)


def _from_pdf_file(path: Path) -> tuple[str, str]:
    return _from_pdf_bytes(path.read_bytes(), path.stem)


def _from_pdf_bytes(data: bytes, fallback_title: str) -> tuple[str, str]:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    text = "\n".join(pages).strip()
    return fallback_title, text[:_MAX_CHARS]


def _parse_html(content: bytes, fallback_title: str) -> tuple[str, str]:
    soup = BeautifulSoup(content, "html.parser")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else fallback_title
    for tag in soup(_STRIP_TAGS):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    return title, text[:_MAX_CHARS]
