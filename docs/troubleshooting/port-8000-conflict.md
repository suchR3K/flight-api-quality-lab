# API container fails to start because port 8000 is occupied

## Classification

Local environment configuration issue.

## Environment

- Ubuntu VM in VirtualBox
- FastAPI and Uvicorn
- Docker Compose
- API published on 127.0.0.1:8000

## Preconditions

A local Uvicorn process is already listening on port 8000:

```bash
python -m uvicorn main:app --reload
```

Docker Compose is configured to publish the API container on the same
host address and port.

## Steps to reproduce

1. Start Uvicorn locally on port 8000.
2. Attempt to start the API container:

   ```bash
   docker compose up -d api
   ```

## Expected behavior

With port 8000 available, the API container starts and serves requests.

If the port is already occupied, the environment requires the local
server to be stopped or a different host port to be configured.

## Actual behavior

The API container failed to start.

Docker reported:

```text
failed to bind host port ... address already in use
```

PostgreSQL remained healthy.

## Diagnosis

Checked the process listening on port 8000:

```bash
sudo ss -ltnp 'sport = :8000'
```

Inspected the reported process IDs with:

```text
ps -p <PID>,<CHILD_PID> -o pid,ppid,args
```

The listener was a local Uvicorn process running with `--reload`
and its child process.

An HTTP 200 response from `/health` alone did not prove that the
containerized API was running: the local server could answer that request.

## Resolution

Stopped the identified local Uvicorn parent process with SIGTERM.

After confirming that port 8000 was free, started the API container:

```bash
docker compose up -d api
```

## Verification

- `docker compose ps` showed the API running and PostgreSQL healthy.
- `docker compose exec api id` showed UID 10001, user `appuser`.
- Creating a flight returned HTTP 201.
- Retrieving the created flight returned HTTP 200.
- The same flight remained available after recreating the API container.

## Prevention

- Stop local Uvicorn before starting the containerized API on port 8000.
- Check container status as well as HTTP responses.
- Inspect the listening process when Docker reports a port conflict.
- Do not hard-code process IDs in troubleshooting instructions.
