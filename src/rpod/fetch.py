"""Artifact retrieval workflow for copying files back from remote pods."""

from pathlib import PurePosixPath
from uuid import uuid4

from rich.console import Console
from typer import Exit

from rpod import pod, ssh


def run(
    console: Console,
    index: int,
    user: str,
    ssh_key: str | None,
    remote_path: str,
    local_path: str | None,
    *,
    archive: bool,
    dry_run: bool,
) -> None:
    target = pod.target_from_index(index=index, user=user, ssh_key=ssh_key)
    local_path = local_path or default_local_path(remote_path, archive=archive)
    console.print(
        f"[cyan]fetch[/cyan] {ssh.remote_spec(target)}:{remote_path} -> {local_path}"
    )
    try:
        if archive:
            remote_archive = create_remote_archive(target, remote_path, dry_run=dry_run)
            try:
                ssh.copy_from(target, remote_archive, local_path, dry_run=dry_run)
            finally:
                cleanup_remote_archive(target, remote_archive, dry_run=dry_run)
        else:
            ssh.copy_from(target, remote_path, local_path, dry_run=dry_run)
    except ssh.RpodCommandError as exc:
        console.print(f"[red]Fetch failed[/red]\n{exc}")
        raise Exit(1) from exc
    console.print(f"[green]Fetched[/green] {remote_path}")


def create_remote_archive(
    target: pod.config.Target,
    remote_path: str,
    *,
    dry_run: bool,
) -> str:
    remote = PurePosixPath(remote_path.rstrip("/"))
    archive_name = f"{remote.name}-{uuid4().hex}.tar.gz"
    remote_archive = f"/tmp/{archive_name}"
    script = f"""
set -euo pipefail
command -v tar >/dev/null 2>&1
command -v gzip >/dev/null 2>&1
tar -czf {ssh.quote(remote_archive)} -C {ssh.quote(str(remote.parent))} {ssh.quote(remote.name)}
"""
    ssh.run_remote_stream(target, f"bash -lc {ssh.quote(script)}", dry_run=dry_run)
    return remote_archive


def cleanup_remote_archive(
    target: pod.config.Target,
    remote_archive: str,
    *,
    dry_run: bool,
) -> None:
    ssh.run_remote(target, f"rm -f {ssh.quote(remote_archive)}", dry_run=dry_run)


def default_local_path(remote_path: str, *, archive: bool = False) -> str:
    name = PurePosixPath(remote_path.rstrip("/")).name
    if not name:
        raise ValueError("Cannot infer local path for remote root. Provide --local-path.")
    if archive:
        return f"{name}.tar.gz"
    return name
