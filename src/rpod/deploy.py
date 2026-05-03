"""Remote repository deployment workflow for SSH-accessible pods."""

import shlex
from pathlib import PurePosixPath

from rich.console import Console

from rpod import config, github, pod, ssh
from rpod.github import repo_name_from_url


def run(
    *,
    console: Console,
    repo: str,
    target_name: str | None,
    host: str | None,
    index: int | None,
    user: str,
    port: int,
    ssh_key: str | None,
    checkout: str | None,
    remote_dir: str,
    install_uv: bool,
    uv_sync: bool,
    uv_extra: list[str],
    bootstrap: list[str],
    github_deploy_key: str | None,
    github_deploy_key_remote: str,
    stdin_upload: bool,
    dry_run: bool,
) -> None:
    target = _target_from_options(
        index=index,
        target_name=target_name,
        host=host,
        user=user,
        port=port,
        ssh_key=ssh_key,
    )
    repo_name = repo_name_from_url(repo)
    repo_path = str(PurePosixPath(remote_dir) / repo_name)

    quoted_repo_path = shlex.quote(repo_path)
    quoted_remote_dir = shlex.quote(remote_dir)

    clone_or_pull = f"""
set -euo pipefail
if [ -d {quoted_repo_path}/.git ]; then
  git -C {quoted_repo_path} fetch --all --prune
  git -C {quoted_repo_path} pull --ff-only
else
  git clone {shlex.quote(repo)} {quoted_repo_path}
fi
"""

    if github_deploy_key:
        github.upload_deploy_key(
            target,
            github_deploy_key,
            github_deploy_key_remote,
            use_stdin=stdin_upload,
            dry_run=dry_run,
        )
        github.configure_github_ssh(
            target,
            github_deploy_key_remote,
            dry_run=dry_run,
        )

    commands = [
        f"mkdir -p {quoted_remote_dir}",
        f"bash -lc {shlex.quote(clone_or_pull)}",
    ]

    if checkout:
        commands.append(f"git -C {quoted_repo_path} checkout {shlex.quote(checkout)}")

    if install_uv:
        commands.append(
            "command -v uv >/dev/null 2>&1 || "
            "(curl -LsSf https://astral.sh/uv/install.sh | sh)"
        )

    if uv_sync or uv_extra:
        extras = " ".join(f"--extra {shlex.quote(extra)}" for extra in uv_extra)
        uv_sync_command = f"uv sync {extras}".strip()
        commands.append(
            f"cd {quoted_repo_path} && "
            f'PATH="$HOME/.local/bin:$PATH" {uv_sync_command}'
        )

    commands.extend(f"cd {quoted_repo_path} && {command}" for command in bootstrap)

    for command in commands:
        console.print(f"[cyan]remote$[/cyan] {command}")
        ssh.run_remote_stream(target, command, dry_run=dry_run)

    console.print(
        f"[green]Deployed[/green] {repo_name} to {ssh.remote_spec(target)}:{repo_path}"
    )


def _target_from_options(
    *,
    index: int | None,
    target_name: str | None,
    host: str | None,
    user: str,
    port: int,
    ssh_key: str | None,
) -> config.Target:
    if index is not None:
        return pod.target_from_index(index=index, user=user, ssh_key=ssh_key)

    if target_name:
        return config.resolve_target(target_name)

    if host:
        return config.Target(host=host, user=user, port=port, ssh_key=ssh_key)

    raise ValueError("Provide --index, --target, or --host.")
