from rpod.config import Target
from rpod.github import normalize_remote_ssh_path, repo_name_from_url


def test_repo_name_from_ssh_url():
    assert repo_name_from_url("git@github.com:gradnorm/allreduce.git") == "allreduce"


def test_repo_name_from_https_url():
    assert repo_name_from_url("https://github.com/gradnorm/allreduce.git") == "allreduce"


def test_normalize_remote_ssh_path_expands_root_home():
    target = Target(host="example.com", user="root")

    assert (
        normalize_remote_ssh_path(target, "~/.ssh/rpod_github_deploy_key")
        == "/root/.ssh/rpod_github_deploy_key"
    )
