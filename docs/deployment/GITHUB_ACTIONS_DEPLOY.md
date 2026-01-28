# GitHub Actions Deployment

DocsAI can be deployed to EC2 via **GitHub Actions** on push to `main` or manually.

---

## Overview

- **Workflow**: [`.github/workflows/deploy.yml`](../../.github/workflows/deploy.yml)
- **Triggers**: `push` to `main`, or **manual** (`workflow_dispatch`)
- **Target**: EC2 at `EC2_HOST` (e.g. `34.201.10.84`), app in `/var/www/docsai`
- **Steps**: SSH → `git fetch` / `git reset` → `deploy/remote-deploy.sh` (pip, migrate, collectstatic, restart Gunicorn) → optional health check

---

## Required secrets

Configure in **Settings → Secrets and variables → Actions**:

| Secret | Description | Example |
|--------|-------------|--------|
| `EC2_SSH_PRIVATE_KEY` | Full PEM private key for `ubuntu@EC2_HOST` | Contents of `your-key.pem` |
| `EC2_HOST` | EC2 public IP or hostname | `34.201.10.84` |
| `EC2_USER` | SSH user on EC2 | `ubuntu` |

---

## One-time EC2 setup

Before the workflow can deploy:

1. **App already deployed** at `/var/www/docsai` (clone, venv, `.env.prod`, systemd, Nginx). Follow [DEPLOY_EC2_34.201.10.84.md](./DEPLOY_EC2_34.201.10.84.md).
2. **SSH key**: Use the same key you use for manual SSH, or create a deploy-only key. The `EC2_USER` (e.g. `ubuntu`) must have:
   - Access to `/var/www/docsai` and `git`
   - Passwordless `sudo systemctl restart gunicorn`
3. **Git**: Remote `origin` must be the GitHub repo (or a mirror the workflow pushes to). Branch deployed is `main` (or the one you set in manual trigger).

---

## Triggers

### Push to `main`

Pushing to `main` runs the deploy job. Ensure branch protection requires CI to pass if you want “deploy only after tests pass”.

### Manual run

1. **Actions** → **Deploy to EC2** → **Run workflow**
2. Optionally set **Branch to deploy** (default `main`).
3. **Run workflow**.

---

## What the workflow does

1. **Setup SSH**: Writes `EC2_SSH_PRIVATE_KEY` to `~/.ssh/deploy_key`, runs `ssh-keyscan` for `EC2_HOST`.
2. **Deploy on EC2**: SSHs as `EC2_USER@EC2_HOST` and runs:
   - `cd /var/www/docsai`
   - `git fetch origin` && `git reset --hard origin/<branch>`
   - `bash deploy/remote-deploy.sh`
3. **remote-deploy.sh** (run on server):
   - `source venv/bin/activate`
   - `pip install -r requirements.txt`
   - `python manage.py migrate --noinput`
   - `python manage.py collectstatic --noinput`
   - `sudo systemctl restart gunicorn`
4. **Verify**: After a short sleep, `curl` the health endpoint `http://$EC2_HOST/api/v1/health/` (soft check).

---

## Optional: Deploy only after CI passes

**Option A – Branch protection**  
Require status checks (e.g. `lint`, `test`) to pass before merging to `main`. Pushes to `main` then imply CI has passed.

**Option B – `workflow_run`**  
Trigger deploy when `CI` workflow completes successfully on `main`:

```yaml
on:
  workflow_run:
    workflows: [CI]
    types: [completed]
    branches: [main]
```

Then add `if: github.event.workflow_run.conclusion == 'success'` to the deploy job. This runs deploy in a separate workflow run after CI.

---

## Troubleshooting

| Issue | Check |
|-------|--------|
| **Permission denied (publickey)** | `EC2_SSH_PRIVATE_KEY` is the full PEM, correct `EC2_USER` / `EC2_HOST`. Key added to `ubuntu`’s `authorized_keys` on EC2. |
| **Deploy fails at `git reset`** | Repo on EC2 has `origin` pointing at the GitHub repo; `main` exists. |
| **Deploy fails at `migrate` or `collectstatic`** | `.env.prod` present and valid; DB reachable; `DJANGO_ENV=production`. |
| **`sudo systemctl restart gunicorn` fails** | `ubuntu` has passwordless sudo for `systemctl`; Gunicorn unit is `gunicorn.service`. |
| **Health check fails** | App and Nginx running; security group allows HTTP 80 from GitHub IPs (or 0.0.0.0/0). Health check is soft (`|| true`); deploy can still succeed. |

---

## Related

- [DEPLOY_EC2_34.201.10.84.md](./DEPLOY_EC2_34.201.10.84.md) – EC2 setup and manual deploy
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) – Full deployment guide
- [deploy/remote-deploy.sh](../../deploy/remote-deploy.sh) – Script executed on EC2 during deploy
