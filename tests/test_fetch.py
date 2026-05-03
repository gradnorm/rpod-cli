import pytest

from rpod.fetch import default_local_path


def test_default_local_path_uses_remote_basename():
    assert default_local_path("/workspace/allreduce/sim_out") == "sim_out"


def test_default_local_path_strips_trailing_slash():
    assert default_local_path("/workspace/allreduce/sim_out/") == "sim_out"


def test_default_local_path_adds_archive_suffix():
    assert (
        default_local_path("/workspace/allreduce/sim_out", archive=True)
        == "sim_out.tar.gz"
    )


def test_default_local_path_rejects_remote_root():
    with pytest.raises(ValueError):
        default_local_path("/")
