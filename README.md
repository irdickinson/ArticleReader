# ML_ArticleReader_V1

A desktop application that extracts content from URLs and HTML files, then generates structured markdown notes using a local AI model.

## Project Status

| Stage | Description | Status |
|-------|-------------|--------|
| 1 | PyQt6 GUI shell | In progress |
| 2 | Text extraction + Ollama summarization | Planned |
| 3 | YouTube link support | Planned |

## Running the App

```bash
pip install -r requirements.txt
python src/main.py
```

## Development

This project follows [GitHub Flow](https://guides.github.com/introduction/flow/):
- All work on feature branches (`feat/`, `fix/`, `docs/`, etc.)
- PRs into `main`
- Conventional commit messages

```bash
# Code quality
black src/
flake8 src/
pytest
```
