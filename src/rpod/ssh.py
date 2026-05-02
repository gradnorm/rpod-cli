import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

from rpod.config import Target


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
    if completed.returncode != 0:
        raise subprocess.CalledProcessError(
            completed.returncode,
            args,
            output=completed.stdout,
            stderr=completed.stderr,
        )

    return CommandResult(
        args=args,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


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
