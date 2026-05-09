"""Wrappers around local ssh and scp commands."""

import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

from rpod.config import Target


class RpodCommandError(RuntimeError):
    """Raised when a local ssh/scp command exits unsuccessfully."""

    def __init__(self, result: "CommandResult") -> None:
        self.result = result
        super().__init__(self.message)

    @property
    def message(self) -> str:
        command = shlex.join(self.result.args)
        stderr = self.result.stderr.strip()
        stdout = self.result.stdout.strip()
        details = stderr or stdout or "No output captured."
        return f"Command failed with exit code {self.result.returncode}: {command}\n{details}"


@dataclass(frozen=True)
class CommandResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str


def remote_spec(target: Target) -> str:
    return f"{target.user}@{target.host}"


def ssh_args(target: Target) -> list[str]:
    args = ["ssh", "-p", str(target.port)]
    if target.ssh_key:
        args.extend(["-i", str(Path(target.ssh_key).expanduser())])
    args.append(remote_spec(target))
    return args


def scp_args(target: Target) -> list[str]:
    args = ["scp", "-P", str(target.port)]
    if target.ssh_key:
        args.extend(["-i", str(Path(target.ssh_key).expanduser())])
    return args


def quote(command: str) -> str:
    return shlex.quote(command)


def run(args: list[str], dry_run: bool = False) -> CommandResult:
    if dry_run:
        return CommandResult(args=args, returncode=0, stdout="", stderr="")

    completed = subprocess.run(args, check=False, capture_output=True, text=True)
    result = CommandResult(
        args=args,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
    if completed.returncode != 0:
        raise RpodCommandError(result)

    return result


def run_remote(target: Target, command: str, dry_run: bool = False) -> CommandResult:
    return run([*ssh_args(target), command], dry_run=dry_run)


def copy_from(
    target: Target,
    remote_path: str,
    local_path: str,
    dry_run: bool = False,
) -> CommandResult:
    source = f"{remote_spec(target)}:{remote_path}"
    return run([*scp_args(target), "-r", source, local_path], dry_run=dry_run)


def copy_from_stream(
    target: Target,
    remote_path: str,
    local_path: str,
    dry_run: bool = False,
) -> CommandResult:
    """Copy files from remote while allowing scp to show progress."""
    source = f"{remote_spec(target)}:{remote_path}"
    args = [*scp_args(target), "-r", source, local_path]

    if dry_run:
        return CommandResult(args=args, returncode=0, stdout="", stderr="")

    completed = subprocess.run(args, check=False)
    result = CommandResult(
        args=args,
        returncode=completed.returncode,
        stdout="",
        stderr="",
    )

    if completed.returncode != 0:
        raise RpodCommandError(result)

    return result


def copy_to(
    target: Target,
    local_path: str,
    remote_path: str,
    dry_run: bool = False,
) -> CommandResult:
    """Copy local files to remote."""
    destination = f"{remote_spec(target)}:{remote_path}"
    return run([*scp_args(target), local_path, destination], dry_run=dry_run)


def run_interactive_ssh(
    host: str, port: int, user: str = "root", ssh_key: str | None = None
):
    args = ["ssh", "-p", str(port)]
    if ssh_key:
        args.extend(["-i", str(Path(ssh_key).expanduser())])
    args.append(f"{user}@{host}")
    subprocess.run(args, check=False)


def write_file_from_stdin(
    target: Target,
    local_path: str,
    remote_path: str,
    dry_run: bool = False,
) -> CommandResult:
    """Stream local files through ssh stdin."""
    command = f"cat > {shlex.quote(remote_path)}"
    args = [*ssh_args(target), f"bash -lc {shlex.quote(command)}"]

    if dry_run:
        return CommandResult(args=args, returncode=0, stdout="", stderr="")

    with Path(local_path).expanduser().open("rb") as f:
        completed = subprocess.run(args, stdin=f, check=False)

    if completed.returncode != 0:
        raise subprocess.CalledProcessError(completed.returncode, args)

    return CommandResult(
        args=args, returncode=completed.returncode, stdout="", stderr=""
    )


def run_remote_stream(
    target: Target, command: str, dry_run: bool = False
) -> CommandResult:
    """Run long commands with live outputs.

    Commands like `uv sync` can take time. Stream output so deploys do not
    look stuck.
    """
    args = [*ssh_args(target), command]

    if dry_run:
        return CommandResult(args=args, returncode=0, stdout="", stderr="")

    completed = subprocess.run(args, check=False)
    if completed.returncode != 0:
        raise subprocess.CalledProcessError(completed.returncode, args)

    return CommandResult(
        args=args, returncode=completed.returncode, stdout="", stderr=""
    )
