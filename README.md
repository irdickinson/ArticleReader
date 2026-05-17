# Article Reader

A local desktop application for automated note-taking. Give it URLs, HTML files, PDFs, or YouTube links and it produces structured, readable markdown notes — summarized and explained by a local AI model with no API costs or data leaving your machine.

## Features

- **URL scraping** — paste any article URL and extract the text automatically
- **PDF & HTML files** — upload local files directly
- **YouTube transcripts** — paste a YouTube link to summarize the video
- **AI summarization** — runs locally via [Ollama](https://ollama.com), no API key required
- **Source quotes** — key points include direct quotes from the source as evidence
- **Rendered markdown** — notes display as formatted output, not raw text
- **History** — tracks every source you've processed; re-queue past items in one click
- **File cache** — uploaded files are preserved locally so they're always re-accessible
- **Copy to clipboard** — one-click copy of raw markdown for pasting into Obsidian or any editor
- **Export** — save notes as `.md` files

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) installed and running locally with `llama3.1:8b` pulled

## Installation

```bash
git clone https://github.com/irdickinson/ML_ArticleReader_V1.git
cd ML_ArticleReader_V1
pip install -r requirements.txt
ollama pull llama3.1:8b
```

## Running

```bash
python src/main.py
```

Ollama must be running in the background (`ollama serve` or started via the Ollama app).

## Usage

1. **Add sources** — paste a URL or upload a file in the left panel, then click **Add**
2. **Process** — click **Process** to extract and summarize all queued sources
3. **Review notes** — rendered markdown appears in the right panel
4. **Save** — click **Save as Markdown** to export the notes as a `.md` file
5. **History** — switch to the **History** tab to re-queue any previously processed source

## Project Structure

```
src/
├── main.py                  # entry point
├── core/
│   ├── extractor.py         # text extraction (URL, HTML, PDF, YouTube)
│   ├── summarizer.py        # Ollama prompt and response handling
│   ├── worker.py            # background QThread for processing
│   ├── history.py           # persistent history store
│   └── paths.py             # project-relative path constants
└── ui/
    ├── main_window.py       # main window and signal wiring
    └── panels/
        ├── input_panel.py   # source input and history tabs
        └── output_panel.py  # rendered notes and save
uploads/                     # cached copies of uploaded files (gitignored)
```

## Building a standalone executable

Produces `dist/ArticleReader/ArticleReader.exe` — no Python installation required on the target machine.

```powershell
.\build.ps1
```

To distribute: copy the entire `dist/ArticleReader/` folder to the target machine. Create a shortcut to `ArticleReader.exe` for the desktop. The target machine still needs [Ollama](https://ollama.com) installed with `llama3.1:8b` pulled.

## Development

For contributors who want to modify the source code. Not needed to run or use the app.

```bash
black src/     # auto-format code
flake8 src/    # check for lint errors
pytest         # run tests
```

## License

[MIT](LICENSE)
