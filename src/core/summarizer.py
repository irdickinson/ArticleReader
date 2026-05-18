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

_DEFAULT_SECTIONS: dict[str, bool] = {
    "summary": True,
    "key_points": True,
    "key_takeaways": False,
    "key_terms": True,
    "questions": False,
}


def summarize(
    text: str,
    detail_level: str = "standard",
    sections: dict[str, bool] | None = None,
    model: str | None = None,
) -> str:
    active = {**_DEFAULT_SECTIONS, **(sections or {})}
    config = _DETAIL_CONFIGS.get(detail_level, _DETAIL_CONFIGS["standard"])
    prompt = _build_prompt(text, config, active)
    response = ollama.chat(
        model=model or MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"].strip()


def _build_prompt(
    text: str, config: dict[str, str], sections: dict[str, bool]
) -> str:
    parts: list[str] = [
        "You are a precise note-taking assistant. Read the following text and produce "
        "structured markdown notes.\n\n"
        "Include only the sections listed below, in exactly this format:\n",
    ]

    if sections.get("summary"):
        parts.append(
            "### Summary\n"
            "One concise paragraph covering the main idea.\n"
        )

    if sections.get("key_points"):
        parts.append(
            f"### Key Points\n"
            f"Cover {config['points']} key points. {config['depth_note']}\n"
            "- **Point**: brief explanation\n"
            '  > "Short direct quote from the source that supports this point."\n'
        )

    if sections.get("key_takeaways"):
        parts.append(
            "### Key Takeaways\n"
            "Practical conclusions or actionable insights the reader should walk away with.\n"
            "- **Takeaway**: what this means in practice\n"
        )

    if sections.get("key_terms"):
        parts.append(
            "### Key Terms\n"
            "- **Term**: brief definition\n"
            "(Only include this section if the text contains domain-specific vocabulary "
            "worth defining. If there are no such terms, omit this section entirely.)\n"
        )

    if sections.get("questions"):
        parts.append(
            "### Questions to Explore\n"
            "Thought-provoking questions raised by this content worth reflecting on.\n"
            "- Question?\n"
        )

    _SECTION_LABELS = {
        "summary":       "Summary",
        "key_points":    "Key Points",
        "key_takeaways": "Key Takeaways",
        "key_terms":     "Key Terms",
        "questions":     "Questions to Explore",
    }
    disabled = [_SECTION_LABELS[k] for k, v in sections.items() if not v and k in _SECTION_LABELS]
    exclusion_line = (
        f"CRITICAL: Do NOT include these sections under any circumstances: {', '.join(disabled)}.\n"
        if disabled else ""
    )

    parts.append(
        f"{exclusion_line}"
        "Rules:\n"
        "- Only output the sections listed above. Nothing else.\n"
        "- Key points must each include a blockquote pulled verbatim from the source.\n"
        "- Do not add any text, headers, or commentary outside the requested sections.\n\n"
        f"Text:\n{text}"
    )

    return "\n".join(parts)
