"""Typer command-line interface and command registration for rpod."""

from typing import Annotated

import typer
from rich.console import Console

from rpod import __version__, auth
from rpod import create as create_module
from rpod import deploy as deploy_module
from rpod import fetch as fetch_module
from rpod import gpu as gpu_module
from rpod import pod as pod_module
from rpod import ssh as ssh_module
from rpod.runpod_api import RunpodGraphQLClient

console = Console()

app = typer.Typer(
    name="rpod",
    help="Prepare and manage SSH-accessible RunPod experiment workspaces.",
    no_args_is_help=True,
    add_completion=False,
)

auth_app = typer.Typer(help="Authentication helpers.")
app.add_typer(auth_app, name="auth")

gpu_app = typer.Typer(help="List RunPod GPUs.")
app.add_typer(gpu_app, name="gpu")


def version_callback(value: bool) -> None:
    if value:
        console.print(f"rpod {__version__}")
        raise typer.Exit


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version", callback=version_callback, help="Show the rpod version."
        ),
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


@app.command("list")
def list_pods() -> None:
    """List RunPod pods"""
    pod_module.list_pods(console)


@app.command("ssh")
def ssh_pod(
    index: Annotated[int, typer.Option("--index", help="Pod index from rpod list.")],
    user: Annotated[str, typer.Option("--user", help="SSH username.")] = "root",
    ssh_key: Annotated[
        str | None, typer.Option("--ssh-key", help="Path to ssh key.")
    ] = None,
):
    """SSH into a runpod by index"""
    client = RunpodGraphQLClient.from_env()
    pod = client.get_pod_by_index(index)
    endpoint = pod_module.ssh_endpoint(pod)
    if not endpoint:
        raise typer.BadParameter(f"No public SSH endpoint found for pod index {index}.")
    host, port = endpoint
    ssh_module.run_interactive_ssh(host=host, port=port, user=user, ssh_key=ssh_key)


@app.command("stop")
def stop_pod(
    index: Annotated[int, typer.Option("--index", help="Pod index from rpod list.")],
) -> None:
    """Stop a RunPod pod by index."""
    typer.confirm(f"Stop pod at index {index}?", abort=True)
    pod_module.stop_pod_by_index(console, index)


@app.command("terminate")
def terminate_pod(
    index: Annotated[int, typer.Option("--index", help="Pod index from rpod list.")],
) -> None:
    """Terminate a RunPod pod by index."""
    typer.confirm(
        f"Terminate pod at index {index}? This can permanently delete pod data.",
        abort=True,
    )
    pod_module.terminate_pod_by_index(console, index)


@app.command()
def deploy(
    repo: Annotated[str, typer.Option("--repo", help="Git repository URL.")],
    index: Annotated[
        int | None,
        typer.Option("--index", help="Pod index from 'rpod list'."),
    ] = None,
    target: Annotated[
        str | None,
        typer.Option("--target", help="Saved target name from 'rpod target add'."),
    ] = None,
    host: Annotated[
        str | None, typer.Option("--host", help="SSH hostname or IP address.")
    ] = None,
    user: Annotated[str, typer.Option("--user", help="SSH username.")] = "root",
    port: Annotated[int, typer.Option("--port", help="SSH port.")] = 22,
    ssh_key: Annotated[
        str | None, typer.Option("--ssh-key", help="Path to SSH key.")
    ] = None,
    checkout: Annotated[
        str | None, typer.Option("--checkout", help="Branch, tag, or SHA.")
    ] = None,
    remote_dir: Annotated[
        str,
        typer.Option("--remote-dir", help="Remote workspace directory."),
    ] = "/workspace",
    install_uv: Annotated[
        bool,
        typer.Option("--install-uv", help="Install uv on the remote pod if missing."),
    ] = False,
    uv_sync: Annotated[
        bool,
        typer.Option("--uv-sync", help="Run 'uv sync' after clone/pull."),
    ] = False,
    uv_extra: Annotated[
        list[str] | None,
        typer.Option(
            "--uv-extra",
            help="Extra to pass to 'uv sync --extra'. Implies --uv-sync.",
        ),
    ] = None,
    bootstrap: Annotated[
        list[str] | None,
        typer.Option(
            "--bootstrap", help="Command to run after checkout. Can be repeated."
        ),
    ] = None,
    github_deploy_key: Annotated[
        str | None,
        typer.Option("--github-deploy-key", help="Local GitHub deploy key path."),
    ] = None,
    github_deploy_key_remote: Annotated[
        str,
        typer.Option(
            "--github-deploy-key-remote",
            help="Remote path where the GitHub deploy key will be written.",
        ),
    ] = "~/.ssh/rpod_github_deploy_key",
    stdin_upload: Annotated[
        bool,
        typer.Option(
            "--stdin-upload",
            help="Upload the deploy key through SSH stdin instead of scp.",
        ),
    ] = False,
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
        index=index,
        user=user,
        port=port,
        ssh_key=ssh_key,
        checkout=checkout,
        remote_dir=remote_dir,
        install_uv=install_uv,
        uv_sync=uv_sync,
        uv_extra=uv_extra or [],
        bootstrap=bootstrap or [],
        github_deploy_key=github_deploy_key,
        github_deploy_key_remote=github_deploy_key_remote,
        stdin_upload=stdin_upload,
        dry_run=dry_run,
    )


@app.command("create")
def create_pod(
    name: Annotated[str, typer.Option("--name", help="Pod name.")],
    image: Annotated[str, typer.Option("--image", help="Docker image name.")],
    gpu_index: Annotated[
        int | None,
        typer.Option("--gpu-index", help="GPU index from 'rpod gpu list'."),
    ] = None,
    gpu: Annotated[
        str | None,
        typer.Option("--gpu", help="RunPod GPU type ID, for example 'NVIDIA RTX A6000'."),
    ] = None,
    gpu_count: Annotated[
        int,
        typer.Option("--gpu-count", help="Number of GPUs."),
    ] = 1,
    disk: Annotated[
        int,
        typer.Option("--disk", help="Container disk size in GB."),
    ] = 50,
    volume: Annotated[
        int,
        typer.Option("--volume", help="Persistent volume size in GB."),
    ] = 50,
    ports: Annotated[
        str,
        typer.Option("--ports", help="Ports to expose, for example '22/tcp,8888/http'."),
    ] = "22/tcp",
    cloud: Annotated[
        str,
        typer.Option("--cloud", help="SECURE or COMMUNITY."),
    ] = "SECURE",
    interruptible: Annotated[
        bool,
        typer.Option("--interruptible", help="Create a spot/interruptible pod."),
    ] = False,
) -> None:
    """Create a RunPod pod."""
    create_module.create_pod(
        console,
        gpu_index=gpu_index,
        gpu=gpu,
        name=name,
        image=image,
        gpu_count=gpu_count,
        disk=disk,
        volume=volume,
        ports=ports,
        cloud=cloud,
        interruptible=interruptible,
    )


@app.command()
def fetch(
    index: Annotated[int, typer.Option("--index", help="Pod index from rpod list.")],
    remote_path: Annotated[
        str, typer.Option("--remote-path", help="Remote file or directory.")
    ],
    user: Annotated[str, typer.Option("--user", help="SSH username.")] = "root",
    ssh_key: Annotated[
        str | None, typer.Option("--ssh-key", help="Path to SSH key.")
    ] = None,
    local_path: Annotated[
        str | None,
        typer.Option(
            "--local-path",
            help="Local destination path. Defaults to the remote basename.",
        ),
    ] = None,
    archive: Annotated[
        bool,
        typer.Option(
            "--archive", help="Archive remote path as .tar.gz before fetching."
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print commands without running."),
    ] = False,
) -> None:
    """Fetch artifacts, logs, or checkpoints from a pod."""
    fetch_module.run(
        console,
        index=index,
        user=user,
        ssh_key=ssh_key,
        remote_path=remote_path,
        local_path=local_path,
        archive=archive,
        dry_run=dry_run,
    )


@gpu_app.command("list")
def list_gpus() -> None:
    """List RunPod GPU types available for pod creation."""
    gpu_module.list_gpus(console)
