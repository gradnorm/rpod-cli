from rich.console import Console
from rich.table import Table

from rpod.runpod_api import RunpodGraphQLClient


def list_pods(console: Console):
    client = RunpodGraphQLClient.from_env()
    pods = client.list_pods()

    table = Table(title="RunPod Pods")
    table.add_column("Index")
    table.add_column("Name")
    table.add_column("ID")
    table.add_column("Status")
    table.add_column("GPUs")
    table.add_column("SSH")

    for index, pod in enumerate(pods, start=1):
        ssh = _ssh_endpoint(pod)
        table.add_row(
            str(index),
            pod.get("name", ""),
            pod.get("id", ""),
            pod.get("desiredStatus", ""),
            str(pod.get("gpuCount", 0)),
            ssh or "",
        )
    console.print(table)


def _ssh_endpoint(pod: dict) -> str | None:
    """Extracts the public SSH endpoint from a RunPod pod object"""
    ports = pod.get("runtime", {}).get("ports", {})
    for port in ports:
        if port.get("privatePort") == 22 and port.get("publicPort"):
            return f"{port.get('ip')}:{port.get("publicPort")}"
    return None
