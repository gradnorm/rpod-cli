import shlex
from pathlib import PurePosixPath

from rich.console import Console

from rpod import config, ssh
from rpod.github import repo_name_from_url


def run(
    *,
    console: Console,
    repo: str,
    target_name: str | None,
    host: str | None,
    user: str,
    port: int,
    ssh_key: str | None,
    checkout: str | None,
    remote_dir: str,
    uv_extra: list[str],
    bootstrap: list[str],
    dry_run: bool,
) -> None:
    target = _target_from_options(target_name, host, user, port, ssh_key)
    repo_name = repo_name_from_url(repo)
    repo_path = str(PurePosixPath(remote_dir) / repo_name)

    commands = [
        f"mkdir -p {shlex.quote(remote_dir)}",
        (
            f"test -d {shlex.quote(repo_path)}/.git "
            f"&& git -C {shlex.quote(repo_path)} pull --ff-only "
            f"|| git clone {shlex.quote(repo)} {shlex.quote(repo_path)}"
        ),
    ]

    if checkout:
        commands.append(f"git -C {shlex.quote(repo_path)} checkout {shlex.quote(checkout)}")

    if uv_extra:
        extras = " ".join(f"--extra {shlex.quote(extra)}" for extra in uv_extra)
        commands.append(f"cd {shlex.quote(repo_path)} && uv sync {extras}")

    commands.extend(f"cd {shlex.quote(repo_path)} && {command}" for command in bootstrap)

    for command in commands:
        console.print(f"[cyan]remote$[/cyan] {command}")
        ssh.run_remote(target, command, dry_run=dry_run)

    console.print(f"[green]Deployed[/green] {repo_name} to {ssh.remote_spec(target)}:{repo_path}")


def _target_from_options(
    target_name: str | None,
    host: str | None,
    user: str,
    port: int,
    ssh_key: str | None,
) -> config.Target:
    if target_name:
        return config.resolve_target(target_name)
    if not host:
        raise ValueError("Provide --target or --host.")
    return config.Target(host=host, user=user, port=port, ssh_key=ssh_key)
