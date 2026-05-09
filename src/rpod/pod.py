"""RunPod pod listing, selection, and SSH endpoint helpers."""

from rich.console import Console
from rich.table import Table

from rpod import config, ssh
from rpod.runpod_api import RunpodGraphQLClient, RunpodGraphQLError


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
        endpoint = ssh_endpoint(pod)
        endpoint_format = ""
        if endpoint:
            host, port = endpoint
            endpoint_format = f"{host}:{port}"

        table.add_row(
            str(index),
            pod.get("name", ""),
            pod.get("id", ""),
            pod.get("desiredStatus", ""),
            str(pod.get("gpuCount", 0)),
            endpoint_format,
        )
    console.print(table)


def ssh_endpoint(pod: dict) -> tuple[str, int] | None:
    """Extracts the public SSH endpoint from a RunPod pod object"""
    ports = ((pod.get("runtime") or {}).get("ports")) or []
    for port in ports:
        if port.get("privatePort") == 22 and port.get("publicPort"):
            ip = port.get("ip")
            if ip:
                return str(ip), int(port.get("publicPort"))
    return None


def ssh_into_pod(index: int, user: str = "root", ssh_key: str | None = None):
    """Wrapper function to SSH into Runpod."""
    client = RunpodGraphQLClient.from_env()
    pod = client.get_pod_by_index(index)
    endpoint = ssh_endpoint(pod)

    if not endpoint:
        raise RunpodGraphQLError(f"No public SSH endpoint found for pod index {index}.")
    host, port = endpoint
    ssh.run_interactive_ssh(host=host, port=port, user=user, ssh_key=ssh_key)


def target_from_index(
    index: int, user: str = "root", ssh_key: str | None = None
) -> config.Target:
    client = RunpodGraphQLClient.from_env()
    pod = client.get_pod_by_index(index)
    endpoint = ssh_endpoint(pod)
    if not endpoint:
        raise RunpodGraphQLError(f"No public SSH endpoint found for pod index {index}.")
    host, port = endpoint
    return config.Target(host=host, port=int(port), user=user, ssh_key=ssh_key)


def stop_pod_by_index(console: Console, index: int) -> None:
    client = RunpodGraphQLClient.from_env()
    pod = client.get_pod_by_index(index)
    client.stop_pod(str(pod["id"]))
    console.print(f"[green]Stopped[/green] {pod_label(pod)}")


def terminate_pod_by_index(console: Console, index: int) -> None:
    client = RunpodGraphQLClient.from_env()
    pod = client.get_pod_by_index(index)
    client.terminate_pod(str(pod["id"]))
    console.print(f"[green]Terminated[/green] {pod_label(pod)}")


def pod_label(pod: dict) -> str:
    name = pod.get("name") or "unnamed"
    pod_id = pod.get("id") or "unknown-id"
    return f"{name} ({pod_id})"
