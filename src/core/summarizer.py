import ollama

MODEL = "llama3.1:8b"

_DETAIL_CONFIGS: dict[str, dict[str, str]] = {
    "brief": {
        "points": "3–4",
        "depth_note": "Be concise: one sentence per point.",
    },
    "standard": {
        "points": "5–7",
        "depth_note": "Balance breadth and depth.",
    },
    "detailed": {
        "points": "8–12",
        "depth_note": "Be thorough: include sub-points and nuance where relevant.",
    },
}

_PROMPT = """\
You are a precise note-taking assistant. Read the following text and produce structured markdown notes.

Use exactly this format and nothing else:

### Summary
One concise paragraph covering the main idea.

### Key Points
Cover {points} key points. {depth_note}
- **Point**: brief explanation
  > "Short direct quote from the source that supports this point."

### Key Terms
- **Term**: brief definition

Rules:
- Every key point must include a supporting blockquote pulled verbatim from the source text.
- Only include Key Terms if the text contains domain-specific vocabulary worth defining. \
If there are no such terms, omit that section entirely.
- Do not add any text outside of these sections.

Text:
{text}
"""


def summarize(text: str, detail_level: str = "standard") -> str:
    config = _DETAIL_CONFIGS.get(detail_level, _DETAIL_CONFIGS["standard"])
    prompt = _PROMPT.format(text=text, **config)
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"].strip()
