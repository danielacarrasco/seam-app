import base64
import os
from typing import Optional

from fastapi import HTTPException, status


def generate_fashion_sketch(prompt: str) -> bytes:
    """Generate a fashion sketch PNG via OpenAI's image API.

    Requires OPENAI_API_KEY in the environment. Raises a 503 if the
    key is missing or the API call fails.
    """
    api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Image generation is not configured (OPENAI_API_KEY missing).",
        )

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The openai package is not installed on the server.",
        ) from exc

    model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
    size = os.getenv("OPENAI_IMAGE_SIZE", "1024x1024")

    framed = (
        "A clean editorial fashion illustration, front-facing flat sketch on a "
        f"plain off-white background. {prompt.strip()}"
    )

    try:
        client = OpenAI(api_key=api_key)
        response = client.images.generate(
            model=model,
            prompt=framed,
            size=size,
            n=1,
        )
    except Exception as exc:  # openai raises a variety of exception types
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Image generation failed: {exc}",
        ) from exc

    data = response.data[0]
    b64 = getattr(data, "b64_json", None)
    if b64:
        return base64.b64decode(b64)

    url = getattr(data, "url", None)
    if url:
        import urllib.request

        with urllib.request.urlopen(url) as resp:  # noqa: S310 - url from trusted provider
            return resp.read()

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Image generation returned no data.",
    )
