import ollama

MODEL = "llama3.1:8b"

_PROMPT = """\
You are a precise note-taking assistant. Read the following text and produce structured markdown notes.

Use exactly this format and nothing else:

### Summary
One concise paragraph covering the main idea.

### Key Points
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


def summarize(text: str) -> str:
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": _PROMPT.format(text=text)}],
    )
    return response["message"]["content"].strip()
