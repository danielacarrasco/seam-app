import json
import os
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status


SYSTEM_PROMPT = """You are an editorial sewing design assistant for a personal atelier app.

The user may provide dreams, thoughts, memories, moods, or vague inspiration. Your job is to translate that material into practical but poetic garment project ideas.

Prioritise:
- garment type
- silhouette
- fabric qualities
- colour palette
- construction direction
- emotional / visual rationale

Do not over-explain psychology. Do not diagnose. Do not make claims about the user. Treat the entry as creative inspiration only.

Return valid JSON only."""


SCHEMA_HINT = """{
  "mood": ["string"],
  "palette": ["string"],
  "imagery": ["string"],
  "garment_cues": ["string"],
  "fabric_cues": ["string"],
  "project_suggestions": [
    {
      "title": "string",
      "garment_type": "string",
      "silhouette": "string",
      "mood": ["string"],
      "palette": ["string"],
      "fabric_ideas": ["string"],
      "pattern_features": ["string"],
      "construction_notes": ["string"],
      "sketch_prompt": "string",
      "rationale": "string"
    }
  ]
}"""


def is_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _build_user_prompt(
    entry_type: Optional[str],
    title: Optional[str],
    tags: Optional[List[str]],
    body: str,
) -> str:
    return (
        f"Journal entry type: {entry_type or 'thought'}\n"
        f"Title: {title or '(untitled)'}\n"
        f"Tags: {', '.join(tags or []) or '(none)'}\n\n"
        f"Entry:\n{body}\n\n"
        "Generate 3 sewing project suggestions inspired by this entry.\n\n"
        "Each suggestion's sketch_prompt must be a complete editorial fashion-illustration "
        "prompt: garment type, silhouette, colour, fabric qualities, mood, with 'no text' and "
        "a neutral background. Keep it under 80 words.\n\n"
        f"Return JSON in this exact schema:\n\n{SCHEMA_HINT}"
    )


def generate_project_suggestions(
    *,
    entry_type: Optional[str],
    title: Optional[str],
    tags: Optional[List[str]],
    body: str,
) -> Dict[str, Any]:
    """Call OpenAI with structured JSON output. One repair pass on parse failure."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI suggestions are not configured for this deployment.",
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
    user_prompt = _build_user_prompt(entry_type, title, tags, body)

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
            {"role": "user", "content": user_prompt},
        ]
    )
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # one repair pass
        raw = _call(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
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

    if not isinstance(parsed, dict) or not isinstance(
        parsed.get("project_suggestions"), list
    ):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI response did not match the expected schema.",
        )

    parsed["_raw"] = raw
    return parsed
