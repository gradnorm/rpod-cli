from rich.console import Console

from rpod import config, ssh


def run(
    console: Console,
    target_name: str,
    remote_path: str,
    local_path: str,
    *,
    dry_run: bool,
) -> None:
    target = config.resolve_target(target_name)
    console.print(f"[cyan]fetch[/cyan] {ssh.remote_spec(target)}:{remote_path} -> {local_path}")
    ssh.copy_from(target, remote_path, local_path, dry_run=dry_run)
    console.print(f"[green]Fetched[/green] {remote_path}")
