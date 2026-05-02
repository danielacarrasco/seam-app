import json
import os
from typing import Any, Dict, Iterable, List, Optional

from fastapi import HTTPException, status


SYSTEM_PROMPT = """You are an editorial sewing design assistant for a personal atelier app.

The user provides one or more inspiration entries: dreams, thoughts, memories, moods, notes, fabric ideas, silhouettes, or images. Your task is to translate the selected inspiration into one cohesive sewing project idea.

The output should be poetic but practical.

Prioritise:
- garment type
- silhouette
- fabric qualities
- colour palette
- construction direction
- fit or pattern considerations
- why the selected inspirations belong together

Do not diagnose the user. Do not interpret dreams psychologically. Treat everything as creative inspiration only.

Return valid JSON only."""


SCHEMA_HINT = """{
  "title": "string",
  "garment_type": "string",
  "silhouette": "string",
  "mood": ["string"],
  "palette": ["string"],
  "imagery": ["string"],
  "fabric_ideas": ["string"],
  "pattern_features": ["string"],
  "construction_notes": ["string"],
  "fit_considerations": ["string"],
  "sketch_prompt": "string",
  "rationale": "string"
}"""


def is_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _format_entry_text(entry: Dict[str, Any]) -> str:
    tags = entry.get("tags") or []
    return (
        f"Entry ID: {entry['id']}\n"
        f"Title: {entry.get('title') or '(untitled)'}\n"
        f"Type: {entry.get('entry_type') or 'note'}\n"
        f"Tags: {', '.join(tags) if tags else '(none)'}\n"
        f"Text: {entry.get('body') or '(no text)'}\n"
        f"Image: {entry.get('image_url') or '(none)'}"
    )


def generate_project_suggestion(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Call OpenAI with structured JSON output. Multimodal when image URLs are absolute."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI project suggestions are not configured for this deployment.",
        )

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The openai package is not installed on the server.",
        ) from exc

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")

    text_block = (
        "Selected inspiration entries:\n\n"
        + "\n\n".join(_format_entry_text(e) for e in entries)
        + "\n\nCreate ONE cohesive sewing project suggestion inspired by these entries.\n\n"
        "The sketch_prompt must be a complete editorial fashion-illustration prompt: "
        "garment type, silhouette, colour, fabric qualities, mood, with 'no text' and a "
        "neutral background. Keep it under 80 words.\n\n"
        f"Return JSON in this exact schema:\n\n{SCHEMA_HINT}"
    )

    user_content: List[Dict[str, Any]] = [{"type": "text", "text": text_block}]
    for entry in entries:
        url = entry.get("image_url") or ""
        if url.startswith(("http://", "https://")):
            user_content.append({"type": "image_url", "image_url": {"url": url}})

    def _call(messages):
        try:
            response = client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                temperature=0.85,
                messages=messages,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI request failed: {exc}",
            ) from exc
        return response.choices[0].message.content or ""

    raw = _call(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
    )
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # one repair pass
        raw = _call(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": "Your previous response was not valid JSON. Return the same content as a strict JSON object matching the schema. Do not include any commentary outside the JSON.",
                },
            ]
        )
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI returned malformed JSON.",
            ) from exc

    if not isinstance(parsed, dict) or not parsed.get("title"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI response did not match the expected schema.",
        )

    parsed["_raw"] = raw
    return parsed
