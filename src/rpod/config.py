"""Local configuration models, paths, persistence, and display helpers."""

import json
import os
from pathlib import Path

from pydantic import BaseModel, Field
from rich.console import Console
from rich.table import Table

APP_NAME = "rpod"
CONFIG_ENV_VAR = "RPOD_CONFIG"


class Target(BaseModel):
    host: str
    user: str = "root"
    port: int = 22
    ssh_key: str | None = None


class Config(BaseModel):
    targets: dict[str, Target] = Field(default_factory=dict)


def config_dir() -> Path:
    if xdg_config_home := os.environ.get("XDG_CONFIG_HOME"):
        return Path(xdg_config_home) / APP_NAME
    return Path.home() / ".config" / APP_NAME


def config_path() -> Path:
    if override := os.environ.get(CONFIG_ENV_VAR):
        return Path(override).expanduser()
    return config_dir() / "config.json"


def load_config(path: Path | None = None) -> Config:
    path = path or config_path()
    if not path.exists():
        return Config()

    with path.open() as f:
        data = json.load(f)
    return Config.model_validate(data)


def save_config(cfg: Config, path: Path | None = None) -> None:
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(cfg.model_dump_json(indent=2) + "\n")
    path.chmod(0o600)


def resolve_target(name: str) -> Target:
    cfg = load_config()
    try:
        return cfg.targets[name]
    except KeyError as exc:
        raise ValueError(f"Unknown target '{name}'. Run 'rpod target list'.") from exc


def print_targets(console: Console, cfg: Config) -> None:
    if not cfg.targets:
        console.print("No targets configured. Add one with [bold]rpod target add[/bold].")
        return

    table = Table(title="rpod targets")
    table.add_column("Name")
    table.add_column("User")
    table.add_column("Host")
    table.add_column("Port")
    table.add_column("SSH key")

    for name, target in sorted(cfg.targets.items()):
        table.add_row(name, target.user, target.host, str(target.port), target.ssh_key or "")

    console.print(table)


def print_config_summary(console: Console, cfg: Config) -> None:
    console.print(f"Config: [bold]{config_path()}[/bold]")
    print_targets(console, cfg)
