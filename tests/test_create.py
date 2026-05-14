import pytest

from rpod.create import build_create_payload, parse_ports, resolve_gpu_id


class FakeClient:
    def get_gpu_by_index(self, index):
        return {"id": f"gpu-{index}"}


def test_resolve_gpu_id_from_index():
    assert resolve_gpu_id(FakeClient(), gpu_index=2, gpu=None) == "gpu-2"


def test_resolve_gpu_id_from_gpu_name():
    assert (
        resolve_gpu_id(FakeClient(), gpu_index=None, gpu="NVIDIA GeForce RTX 4090")
        == "NVIDIA GeForce RTX 4090"
    )


def test_resolve_gpu_id_rejects_both_options():
    with pytest.raises(ValueError):
        resolve_gpu_id(FakeClient(), gpu_index=1, gpu="NVIDIA GeForce RTX 4090")


def test_build_create_payload():
    payload = build_create_payload(
        gpu_id="NVIDIA GeForce RTX 4090",
        name="test-pod",
        image="runpod/pytorch:latest",
        gpu_count=1,
        disk=50,
        volume=50,
        ports="22/tcp",
        cloud="secure",
        interruptible=False,
    )

    assert payload["gpuTypeIds"] == ["NVIDIA GeForce RTX 4090"]
    assert payload["cloudType"] == "SECURE"
    assert payload["imageName"] == "runpod/pytorch:latest"
    assert payload["ports"] == ["22/tcp"]


def test_parse_ports():
    assert parse_ports("22/tcp,8888/http") == ["22/tcp", "8888/http"]
    assert parse_ports(" 22/tcp , 8888/http ") == ["22/tcp", "8888/http"]
