from urllib.parse import urlparse


def repo_name_from_url(repo_url: str) -> str:
    repo = repo_url.rstrip("/").removesuffix(".git")

    if repo.startswith("git@"):
        repo = repo.split(":", 1)[-1]
        return repo.rsplit("/", 1)[-1]

    parsed = urlparse(repo)
    if parsed.path:
        return parsed.path.rsplit("/", 1)[-1]

    return repo.rsplit("/", 1)[-1]
