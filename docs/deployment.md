# Deployment

The app is one stdlib-only Python process (`python -m pvagent serve`). It reads `PORT` and `HOST`.

| Env var | Default | Purpose |
|---|---|---|
| `PORT` / `HOST` | 8000 / 127.0.0.1 | listen address (container sets HOST=0.0.0.0) |
| `REVIEWER_TOKEN` | unset | if set, approve/reject requires this token |
| `APPROVAL_TIMEOUT` | 900 | seconds before an unanswered review stays `pending` |
| `PV_OUT_DIR` | output/web | run artefacts (ephemeral on most free hosts) |

## Local
`make serve` → http://127.0.0.1:8000

## Docker
`docker build -t pv-triage . && docker run -p 8000:8000 -e REVIEWER_TOKEN=change-me pv-triage`

## Render (blueprint)
Push the repo to GitHub → Render → New → Blueprint → select the repo. `render.yaml` builds the Dockerfile,
generates a `REVIEWER_TOKEN` (see the service's Environment tab) and health-checks `/healthz`.
Railway/Heroku-style hosts can use the `Procfile`.

## Before exposing publicly
The app has no user authentication beyond the shared reviewer token, and processes only synthetic demo data.
Do not submit real patient data to a public instance.
