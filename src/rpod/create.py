"""RunPod pod creation workflow."""

from typing import Any

from rich.console import Console
from rich.table import Table
from typer import Exit

from rpod.runpod_api import RunpodGraphQLClient, RunpodGraphQLError


def create_pod(
    console: Console,
    *,
    gpu_index: int | None,
    gpu: str | None,
    name: str,
    image: str,
    gpu_count: int,
    disk: int,
    volume: int,
    ports: str,
    cloud: str,
    interruptible: bool,
) -> None:
    """Create a RunPod pod by GPU index or GPU type ID."""
    try:
        client = RunpodGraphQLClient.from_env()
        gpu_id = resolve_gpu_id(client, gpu_index=gpu_index, gpu=gpu)
        payload = build_create_payload(
            gpu_id=gpu_id,
            name=name,
            image=image,
            gpu_count=gpu_count,
            disk=disk,
            volume=volume,
            ports=ports,
            cloud=cloud,
            interruptible=interruptible,
        )
        pod = client.create_pod(payload)
    except (RunpodGraphQLError, ValueError) as exc:
        console.print(f"[red]Create failed[/red]\n{exc}")
        raise Exit(1) from exc

    print_created_pod(console, pod)


def resolve_gpu_id(
    client: RunpodGraphQLClient,
    *,
    gpu_index: int | None,
    gpu: str | None,
) -> str:
    if gpu_index is not None and gpu is not None:
        raise ValueError("Use either --gpu-index or --gpu, not both.")
    if gpu_index is None and gpu is None:
        raise ValueError("Provide --gpu-index from 'rpod gpu list' or --gpu.")
    if gpu_index is not None:
        gpu_type = client.get_gpu_by_index(gpu_index)
        return str(gpu_type["id"])
    return str(gpu)


def build_create_payload(
    *,
    gpu_id: str,
    name: str,
    image: str,
    gpu_count: int,
    disk: int,
    volume: int,
    ports: str,
    cloud: str,
    interruptible: bool,
) -> dict[str, Any]:
    if gpu_count < 1:
        raise ValueError("--gpu-count must be at least 1.")
    if disk < 1:
        raise ValueError("--disk must be at least 1 GB.")
    if volume < 0:
        raise ValueError("--volume cannot be negative.")

    cloud_type = cloud.upper()
    if cloud_type not in {"SECURE", "COMMUNITY"}:
        raise ValueError("--cloud must be SECURE or COMMUNITY.")

    payload: dict[str, Any] = {
        "name": name,
        "imageName": image,
        "computeType": "GPU",
        "gpuTypeIds": [gpu_id],
        "gpuCount": gpu_count,
        "containerDiskInGb": disk,
        "volumeInGb": volume,
        "cloudType": cloud_type,
        "interruptible": interruptible,
        "ports": parse_ports(ports),
    }
    return payload


def parse_ports(ports: str) -> list[str]:
    return [port.strip() for port in ports.split(",") if port.strip()]


def print_created_pod(console: Console, pod: dict[str, Any]) -> None:
    table = Table(title="Created RunPod Pod")
    table.add_column("Field")
    table.add_column("Value")

    for field in ("id", "name", "desiredStatus", "imageName"):
        value = pod.get(field)
        if value is not None:
            table.add_row(field, str(value))

    if not table.rows:
        table.add_row("response", str(pod))

    console.print(table)
