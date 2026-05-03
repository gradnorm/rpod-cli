"""Small Hugging Face API helpers."""

from huggingface_hub import HfApi


def whoami(token: str | None = None) -> dict:
    return HfApi(token=token).whoami()
