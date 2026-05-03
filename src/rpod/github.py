"""GitHub repository and deploy-key helpers."""

import shlex
from pathlib import Path
from urllib.parse import urlparse

from rpod import ssh
from rpod.config import Target


def repo_name_from_url(repo_url: str) -> str:
    repo = repo_url.rstrip("/").removesuffix(".git")

    if repo.startswith("git@"):
        repo = repo.split(":", 1)[-1]
        return repo.rsplit("/", 1)[-1]

    parsed = urlparse(repo)
    if parsed.path:
        return parsed.path.rsplit("/", 1)[-1]

    return repo.rsplit("/", 1)[-1]


def upload_deploy_key(
    target: Target,
    local_key_path: str,
    remote_key_path: str,
    *,
    use_stdin: bool = False,
    dry_run: bool = False,
) -> None:
    """Upload a GitHub deploy key and lock down remote permissions."""
    local_key = Path(local_key_path).expanduser()
    remote_key_path = normalize_remote_ssh_path(target, remote_key_path)

    if not local_key.exists():
        raise FileNotFoundError(f"GitHub deploy key not found: {local_key}")

    # Make remote directory and set file permission
    ssh.run_remote_stream(
        target,
        f"mkdir -p {shlex.quote(remote_ssh_dir(target))} "
        f"&& chmod 700 {shlex.quote(remote_ssh_dir(target))}",
        dry_run=dry_run,
    )
    # Copy Github deployment key into remote
    if use_stdin:
        ssh.write_file_from_stdin(
            target, str(local_key), remote_key_path, dry_run=dry_run
        )
    else:
        ssh.copy_to(target, str(local_key), remote_key_path, dry_run=dry_run)

    ssh.run_remote_stream(
        target,
        f"chmod 600 {shlex.quote(remote_key_path)}",
        dry_run=dry_run,
    )


def configure_github_ssh(
    target: Target,
    remote_key_path: str,
    *,
    dry_run: bool = False,
) -> None:
    """Configure GitHub SSH without fully overwriting existing config."""
    remote_key_path = normalize_remote_ssh_path(target, remote_key_path)
    ssh_dir = remote_ssh_dir(target)
    config_path = f"{ssh_dir}/config"
    rpod_config_path = f"{ssh_dir}/config.rpod-github"
    known_hosts_path = f"{ssh_dir}/known_hosts"

    script = f"""
set -euo pipefail
mkdir -p {shlex.quote(ssh_dir)}
chmod 700 {shlex.quote(ssh_dir)}
touch {shlex.quote(known_hosts_path)}
ssh-keyscan github.com >> {shlex.quote(known_hosts_path)} 2>/dev/null || true
chmod 644 {shlex.quote(known_hosts_path)}

cat > {shlex.quote(rpod_config_path)} <<'EOF'
Host github.com
  HostName github.com
  User git
  IdentityFile {remote_key_path}
  IdentitiesOnly yes
EOF

grep -q 'Include {rpod_config_path}' {shlex.quote(config_path)} 2>/dev/null || \\
  printf '\\nInclude {rpod_config_path}\\n' >> {shlex.quote(config_path)}
chmod 600 {shlex.quote(config_path)} {shlex.quote(rpod_config_path)}
"""
    ssh.run_remote_stream(target, f"bash -lc {shlex.quote(script)}", dry_run=dry_run)


def normalize_remote_ssh_path(target: Target, path: str) -> str:
    """Expand supported remote SSH paths without relying on shell tilde expansion."""
    if path == "~":
        return remote_home(target)
    if path.startswith("~/"):
        return f"{remote_home(target)}/{path[2:]}"
    return path


def remote_ssh_dir(target: Target) -> str:
    return f"{remote_home(target)}/.ssh"


def remote_home(target: Target) -> str:
    if target.user == "root":
        return "/root"
    return f"/home/{target.user}"
