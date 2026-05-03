# rpod-cli

`rpod-cli` is a lightweight command-line tool for preparing and managing RunPod experiment workspaces. 

![rpod list screenshot](assets/rpod-screenshot.png)


It focuses on automating repetitive parts of remote ML training and experiments:

- Clone or update GitHub repo on a pod
- Check out a branch, tag or commit
- Run setup commands such as `uv sync`
- Sync .env / config files
- Fetch logs, checkpoints and artifacts back to local machine


The published package name is `rpod-cli`; the installed shell command is
`rpod`.

## Install

Install directly from GitHub:

```bash
pip install git+https://github.com/gradnorm/rpod-cli.git
```

Or clone the repo and install locally:

```bash
git clone https://github.com/gradnorm/rpod-cli.git
cd rpod-cli
pip install .
```

For development:

```bash
pip install -e ".[dev]"
```

After install, the CLI command is available as:

```bash
rpod --help
```

When published to PyPI, installation will be:

```bash
pip install rpod-cli
```

## Usage

List RunPod pods:

```bash
rpod list
```

Deploy a repo and run setup:

```bash
rpod deploy \
  --index 1 \
  --repo git@github.com:your-org/your-repo.git \
  --ssh-key ~/.ssh/runpod_ed25519 \
  --github-deploy-key ~/.ssh/github_deploy_key \
  --checkout main \
  --install-uv \
  --uv-sync
```

`--ssh-key` is the key used to connect from your machine to the pod.
`--github-deploy-key` is copied to the pod so it can clone a private GitHub repo.

SSH into a pod:

```bash
rpod ssh --index 1 --ssh-key ~/.ssh/runpod_ed25519
```

Fetch artifacts:

```bash
rpod fetch \
  --index 1 \
  --remote-path /workspace/your-repo/sim_out \
  --local-path ./downloads/sim_out \
  --ssh-key ~/.ssh/runpod_ed25519
```
