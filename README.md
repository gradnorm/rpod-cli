# rpod-cli

`rpod-cli` is a lightweight command-line tool for preparing and managing RunPod experiment workspaces. 

It focuses on automating repetitive parts of remote ML training and experiments:
- Clone or update GitHub repo on a pod
- Check out a branch, tag or commit
- Run setup commands such as `uv sync`
- Sync .env / config files
- Fetch logs, checkpoints and artifacts back to local machine


The published package name is `rpod-cli`; the installed shell command is
`rpod`.

## Install
```bash
pip install -e ".[dev]"
```

## Usage

Add a reusable SSH target:

```bash
rpod target add a100 \
  --host 1.2.3.4 \
  --user root \
  --port 22 \
  --ssh-key ~/.ssh/runpod_ed25519
```

Deploy a repo and run setup:

```bash
rpod deploy \
  --target a100 \
  --repo git@github.com:gradnorm/allreduce.git \
  --checkout train_grpo \
  --uv-extra faiss_gpu_cu12
```

Sync selected environment variables:

```bash
rpod sync-env --target a100 --var HF_TOKEN --var WANDB_API_KEY
```

Fetch artifacts:

```bash
rpod fetch \
  --target a100 \
  --remote-path /workspace/allreduce/sim_out \
  --local-path ./downloads/sim_out
```

## Scope

`rpod` is not a training framework, experiment tracker, or general
infrastructure platform. It is a small SSH-first workflow helper for making a
remote pod feel like a usable project workspace.
