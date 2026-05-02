import os

from huggingface_hub import HfApi
from huggingface_hub.errors import HfHubHTTPError
from rich.console import Console


def check_huggingface(console: Console) -> None:
    token = os.environ.get("HF_TOKEN")
    try:
        user = HfApi(token=token).whoami()
    except HfHubHTTPError as exc:
        console.print(f"[red]Hugging Face auth failed:[/red] {exc}")
        raise

    name = user.get("name") or user.get("fullname") or "authenticated user"
    console.print(f"[green]Hugging Face authenticated[/green] as {name}")


def check_runpod(console: Console) -> None:
    if os.environ.get("RUNPOD_API_KEY"):
        console.print("[green]RUNPOD_API_KEY is set[/green]")
        return

    console.print("[yellow]RUNPOD_API_KEY is not set[/yellow]")
