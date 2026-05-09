"""Helper functions for listing RunPod GPUs."""

from typing import Any

from rich.console import Console
from rich.table import Table

from rpod.runpod_api import RunpodGraphQLClient


def list_gpus(console: Console) -> None:
    client = RunpodGraphQLClient.from_env()
    gpu_types = client.list_gpus()

    table = Table(title="RunPod GPUs")
    table.add_column("Index")
    table.add_column("Name")
    table.add_column("ID")
    table.add_column("Memory")
    table.add_column("Stock")
    table.add_column("Counts")
    table.add_column("Min bid")

    for idx, gpu in enumerate(gpu_types, start=1):
        lowest_price = gpu.get("lowestPrice") or {}
        table.add_row(
            str(idx),
            gpu.get("displayName", ""),
            gpu.get("id", ""),
            f"{gpu.get('memoryInGb', '')} GB",
            str(lowest_price.get("stockStatus") or ""),
            format_available_gpu_counts(lowest_price.get("availableGpuCounts")),
            format_price(lowest_price.get("minimumBidPrice")),
        )

    console.print(table)


def format_available_gpu_counts(counts: Any) -> str:
    if not counts:
        return ""
    return ", ".join(str(count) for count in counts)


def format_price(price: Any) -> str:
    if price is None:
        return ""
    return f"${float(price):.3f}/hr"
