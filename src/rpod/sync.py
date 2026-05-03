"""Remote sync workflows for environment and configuration files."""

import os
import shlex

from rich.console import Console

from rpod import config, ssh


def sync_env(
    console: Console,
    target_name: str,
    vars: list[str],
    remote_path: str,
    *,
    dry_run: bool,
) -> None:
    target = config.resolve_target(target_name)
    lines = []

    for name in vars:
        value = os.environ.get(name)
        if value is None:
            console.print(f"[yellow]Skipping unset env var[/yellow] {name}")
            continue
        lines.append(f"{name}={shlex.quote(value)}")

    if not lines:
        console.print("[yellow]No environment variables to sync[/yellow]")
        return

    content = "\n".join(lines) + "\n"
    remote_dir = os.path.dirname(remote_path) or "."
    command = (
        f"mkdir -p {shlex.quote(remote_dir)} "
        f"&& cat > {shlex.quote(remote_path)} <<'EOF'\n"
        f"{content}"
        "EOF\n"
        f"chmod 600 {shlex.quote(remote_path)}"
    )
    console.print(f"[cyan]remote$[/cyan] write {remote_path}")
    ssh.run_remote(target, command, dry_run=dry_run)
    console.print(f"[green]Synced[/green] {len(lines)} env var(s) to {remote_path}")
