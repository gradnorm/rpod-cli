"""Minimal RunPod GraphQL client used by pod-related commands."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests

RUNPOD_GRAPHQL_URL = "https://api.runpod.io/graphql"
RUNPOD_REST_URL = "https://rest.runpod.io/v1"


class RunpodGraphQLError(RuntimeError):
    pass


@dataclass
class RunpodGraphQLClient:
    """Client class that stores api_key, endpoint url and provides reusable API methods"""

    api_key: str
    url: str = RUNPOD_GRAPHQL_URL
    timeout_s: int = 30

    @classmethod
    def from_env(cls) -> RunpodGraphQLClient:
        api_key = os.getenv("RUNPOD_API_KEY")
        if not api_key:
            raise RunpodGraphQLError(
                "Missing RUNPOD_API_KEY. export RUNPOD_API_KEY='...'\n"
            )
        return cls(api_key=api_key)

    def execute(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Core GraphQL engine"""

        # Builds header
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload: dict[str, Any] = {"query": query}
        if variables is not None:
            payload["variables"] = variables

        # Send post request
        try:
            resp = requests.post(
                self.url, json=payload, headers=headers, timeout=self.timeout_s
            )
        except requests.RequestException as e:
            raise RunpodGraphQLError(
                f"Network error calling RunPod GraphQL: {e}"
            ) from e

        # Non-2xx is still useful to print
        try:
            data = resp.json()
        except ValueError as exc:
            raise RunpodGraphQLError(
                f"Non-JSON response (HTTP {resp.status_code}): {resp.text[:500]}"
            ) from exc

        if resp.status_code >= 400:
            raise RunpodGraphQLError(f"HTTP {resp.status_code}: {data}")

        if "errors" in data and data["errors"]:
            raise RunpodGraphQLError(f"GraphQL errors: {data['errors']}")

        if "data" not in data:
            raise RunpodGraphQLError(f"Malformed GraphQL response: {data}")

        return data["data"]

    def list_pods(self) -> list[dict[str, Any]]:
        """Returns a list of pods list[dict[str, Any]]"""
        query = """
        query ListMyPods {
        myself {
            pods {
            id
            name
            desiredStatus
            gpuCount
            runtime {
                ports {
                ip
                isIpPublic
                privatePort
                publicPort
                type
                }
            }
            }
        }
        }
        """
        data = self.execute(query)
        pods = (data.get("myself") or {}).get("pods") or []
        return sorted(
            pods, key=lambda pod: (pod.get("name") or "", pod.get("id") or "")
        )

    def get_pod_by_index(self, index: int) -> dict[str, Any]:
        """Returns a pod from list_pods based on index"""
        pods = self.list_pods()
        if index < 1 or index > len(pods):
            raise RunpodGraphQLError(f"Invalid pod index {index}. Run 'rpod list'.")
        return pods[index - 1]

    def list_gpus(self) -> list[dict[str, Any]]:
        query = """
        query ListGpuTypes {
        gpuTypes {
            id
            displayName
            memoryInGb
            lowestPrice(input: { gpuCount: 1 }) {
                stockStatus
                availableGpuCounts
                minimumBidPrice
            }
        }
        }
        """
        data = self.execute(query)
        return data.get("gpuTypes") or []

    def get_gpu_by_index(self, index: int) -> dict[str, Any]:
        gpus = self.list_gpus()
        if index < 1 or index > len(gpus):
            raise RunpodGraphQLError(f"Invalid GPU index {index}.")
        return gpus[index - 1]

    def create_pod(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a pod using the RunPod REST API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(
                f"{RUNPOD_REST_URL}/pods",
                json=payload,
                headers=headers,
                timeout=self.timeout_s,
            )
        except requests.RequestException as exc:
            raise RunpodGraphQLError(f"Network error creating RunPod pod: {exc}") from exc

        try:
            data = resp.json()
        except ValueError as exc:
            raise RunpodGraphQLError(
                f"Non-JSON response (HTTP {resp.status_code}): {resp.text[:500]}"
            ) from exc

        if resp.status_code >= 400:
            raise RunpodGraphQLError(f"HTTP {resp.status_code}: {data}")

        return data

    def stop_pod(self, pod_id: str) -> dict[str, Any]:
        """Stop a pod using the RunPod REST API."""
        return self._pod_action("post", f"/pods/{pod_id}/stop")

    def terminate_pod(self, pod_id: str) -> None:
        """Terminate a pod using the RunPod REST API."""
        self._pod_action("delete", f"/pods/{pod_id}", success_codes={200, 202, 204})

    def _pod_action(
        self,
        method: str,
        path: str,
        *,
        success_codes: set[int] | None = None,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{RUNPOD_REST_URL}{path}"
        try:
            resp = requests.request(
                method,
                url,
                headers=headers,
                timeout=self.timeout_s,
            )
        except requests.RequestException as exc:
            raise RunpodGraphQLError(f"Network error calling RunPod REST API: {exc}") from exc

        success_codes = success_codes or {200}
        data: dict[str, Any] = {}
        if resp.text:
            try:
                data = resp.json()
            except ValueError as exc:
                if resp.status_code not in success_codes:
                    raise RunpodGraphQLError(
                        f"Non-JSON response (HTTP {resp.status_code}): {resp.text[:500]}"
                    ) from exc

        if resp.status_code not in success_codes:
            raise RunpodGraphQLError(f"HTTP {resp.status_code}: {data or resp.text}")

        return data
