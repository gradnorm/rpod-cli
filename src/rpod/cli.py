from typing import Annotated

import typer
from rich.console import Console

from rpod import __version__, auth, config
from rpod import deploy as deploy_module
from rpod import fetch as fetch_module
from rpod import sync as sync_module

console = Console()

app = typer.Typer(
    name="rpod",
    help="Prepare and manage SSH-accessible RunPod experiment workspaces.",
    no_args_is_help=True,
)

auth_app = typer.Typer(help="Authentication helpers.")
target_app = typer.Typer(help="Manage saved pod targets.")

app.add_typer(auth_app, name="auth")
app.add_typer(target_app, name="target")


def version_callback(value: bool) -> None:
    if value:
        console.print(f"rpod {__version__}")
        raise typer.Exit


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", callback=version_callback, help="Show the rpod version."),
    ] = False,
) -> None:
    pass


@auth_app.command("hf")
@auth_app.command("huggingface")
def auth_huggingface() -> None:
    """Check Hugging Face authentication."""
    auth.check_huggingface(console)


@auth_app.command("runpod")
def auth_runpod() -> None:
    """Check RunPod API authentication."""
    auth.check_runpod(console)


@target_app.command("list")
def list_targets() -> None:
    """List configured pod targets."""
    cfg = config.load_config()
    config.print_targets(console, cfg)


@target_app.command("add")
def add_target(
    name: Annotated[str, typer.Argument(help="Target name, for example 'a100'.")],
    host: Annotated[str, typer.Option("--host", help="SSH hostname or IP address.")],
    user: Annotated[str, typer.Option("--user", help="SSH username.")] = "root",
    port: Annotated[int, typer.Option("--port", help="SSH port.")] = 22,
    ssh_key: Annotated[
        str | None,
        typer.Option("--ssh-key", help="Path to the private SSH key."),
    ] = None,
) -> None:
    """Save a reusable pod target."""
    cfg = config.load_config()
    cfg.targets[name] = config.Target(host=host, user=user, port=port, ssh_key=ssh_key)
    config.save_config(cfg)
    console.print(f"[green]Saved target[/green] {name}")


@app.command()
def deploy(
    repo: Annotated[str, typer.Option("--repo", help="Git repository URL.")],
    target: Annotated[
        str | None,
        typer.Option("--target", help="Saved target name from 'rpod target add'."),
    ] = None,
    host: Annotated[str | None, typer.Option("--host", help="SSH hostname or IP address.")] = None,
    user: Annotated[str, typer.Option("--user", help="SSH username.")] = "root",
    port: Annotated[int, typer.Option("--port", help="SSH port.")] = 22,
    ssh_key: Annotated[str | None, typer.Option("--ssh-key", help="Path to SSH key.")] = None,
    checkout: Annotated[str | None, typer.Option("--checkout", help="Branch, tag, or SHA.")] = None,
    remote_dir: Annotated[
        str,
        typer.Option("--remote-dir", help="Remote workspace directory."),
    ] = "/workspace",
    uv_extra: Annotated[
        list[str] | None,
        typer.Option("--uv-extra", help="Extra to pass to 'uv sync --extra'."),
    ] = None,
    bootstrap: Annotated[
        list[str] | None,
        typer.Option("--bootstrap", help="Command to run after checkout. Can be repeated."),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print commands without running."),
    ] = False,
) -> None:
    """Clone or update a repo on a pod and run setup commands."""
    deploy_module.run(
        console=console,
        repo=repo,
        target_name=target,
        host=host,
        user=user,
        port=port,
        ssh_key=ssh_key,
        checkout=checkout,
        remote_dir=remote_dir,
        uv_extra=uv_extra or [],
        bootstrap=bootstrap or [],
        dry_run=dry_run,
    )


@app.command("sync-env")
def sync_env(
    target: Annotated[str, typer.Option("--target", help="Saved target name.")],
    env_vars: Annotated[
        list[str],
        typer.Option("--var", "--vars", help="Environment variable to sync. Can be repeated."),
    ],
    remote_path: Annotated[
        str,
        typer.Option("--remote-path", help="Remote dotenv path to write."),
    ] = "/workspace/.env",
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print commands without running."),
    ] = False,
) -> None:
    """Sync selected local environment variables to a remote dotenv file."""
    sync_module.sync_env(console, target, env_vars, remote_path, dry_run=dry_run)


@app.command()
def fetch(
    target: Annotated[str, typer.Option("--target", help="Saved target name.")],
    remote_path: Annotated[str, typer.Option("--remote-path", help="Remote file or directory.")],
    local_path: Annotated[str, typer.Option("--local-path", help="Local destination path.")],
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print commands without running."),
    ] = False,
) -> None:
    """Fetch artifacts, logs, or checkpoints from a pod."""
    fetch_module.run(console, target, remote_path, local_path, dry_run=dry_run)


@app.command()
def doctor() -> None:
    """Show local configuration and dependency checks."""
    cfg = config.load_config()
    config.print_config_summary(console, cfg)
