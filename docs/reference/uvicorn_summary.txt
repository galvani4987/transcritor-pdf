# Uvicorn Summary Reference

This document summarizes key concepts, command-line options, programmatic usage, and configuration for Uvicorn, focusing on running FastAPI applications, especially in Docker environments.

## Official Documentation

* **Main Documentation:** [https://www.uvicorn.org/](https://www.uvicorn.org/)
* **Deployment Guide (including Docker):** [https://www.uvicorn.org/deployment/](https://www.uvicorn.org/deployment/)
* **Settings/Configuration:** [https://www.uvicorn.org/settings/](https://www.uvicorn.org/settings/)
* **GitHub Repository:** [https://www.github.com/encode/uvicorn](https://www.github.com/encode/uvicorn)

## Key Concepts

*   **ASGI Server:** Uvicorn is an ASGI (Asynchronous Server Gateway Interface) web server implementation for Python. ASGI allows for async frameworks and features like WebSockets, which WSGI (Web Server Gateway Interface) doesn't handle well.
*   **Compatibility:** Uvicorn supports HTTP/1.1 and WebSockets. It can run various ASGI frameworks like Starlette, FastAPI, Django Channels, Quart, etc.
*   **Performance:** Uvicorn aims for high performance, offering options to use `uvloop` (a fast asyncio event loop replacement) and `httptools` (for HTTP protocol handling).

## Command-Line Usage

The basic command to run a Uvicorn server is:

```bash
uvicorn main:app [OPTIONS]
```

Where `main:app` refers to the Python module (`main.py`) and the ASGI application instance (`app`) within that module. For FastAPI, `app` is typically your `FastAPI()` instance.

### Important CLI Options:

*   `--host TEXT`: Bind socket to this host. Default: `127.0.0.1`. For Docker, often set to `0.0.0.0` to be accessible from outside the container.
    *   Example: `uvicorn main:app --host 0.0.0.0`
*   `--port INTEGER`: Bind socket to this port. Default: `8000`.
    *   Example: `uvicorn main:app --port 8080`
*   `--workers INTEGER`: Number of worker processes. Defaults to `$WEB_CONCURRENCY` or 1. Not valid with `--reload`. For production, this is typically set to a number like `(2 * CPU_CORES) + 1`.
    *   Example: `uvicorn main:app --workers 4`
*   `--reload`: Enable auto-reload for development. Uvicorn will watch for file changes and restart the server. Do not use in production.
    *   Example: `uvicorn main:app --reload`
*   `--reload-dir PATH`: Specify directories to watch for changes if not the current working directory.
*   `--log-level [critical|error|warning|info|debug|trace]`: Set the logging level. Default: `info`.
    *   Example: `uvicorn main:app --log-level debug`
*   `--app-dir TEXT`: Directory to search for the APP module.
*   `--factory`: Treat APP as an application factory (a function that returns an ASGI app).
    *   Example: `uvicorn --factory main:create_app` (if `create_app` is a function in `main.py` that returns your FastAPI app)

## Programmatic Usage

Uvicorn can be run programmatically from within your Python code.

### Using `uvicorn.run()`:

This is a direct programmatic equivalent of the CLI.

```python
# main.py
import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
    # Or, to run the app instance directly (less common for FastAPI where 'app' is defined globally):
    # uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
```

### Using `Config` and `Server` instances:

This provides more control over the server lifecycle.

```python
# main.py
import uvicorn
import asyncio
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

async def main():
    config = uvicorn.Config("main:app", host="0.0.0.0", port=8000, log_level="info")
    # For FastAPI, it's often cleaner to pass the app instance directly:
    # config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

*   **Environment Variables:** Many CLI options can be set via environment variables (e.g., `WEB_CONCURRENCY` for workers, `FORWARDED_ALLOW_IPS`).
*   `--env-file PATH`: Load environment variables from a `.env` file. Requires `python-dotenv` to be installed (`pip install 'uvicorn[standard]'`).
*   `--log-config PATH`: Path to a logging configuration file (INI, JSON, YAML). Requires `PyYAML` for YAML files.

### Development Configuration:

Typically involves:
*   `--reload` for automatic restarts on code changes.
*   `--host 0.0.0.0` if running in a VM or container and need external access.
*   `--port` as needed.
*   `log_level="debug"` for more verbose output.

Example:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

### Production Configuration:

*   **No `--reload`**: Reloading is not suitable for production.
*   **Workers**: Use the `--workers` option (e.g., `uvicorn main:app --workers 4 --host 0.0.0.0 --port 80`).
*   **Gunicorn as Process Manager**: For robust production deployments, Uvicorn recommends using Gunicorn with the `uvicorn.workers.UvicornWorker` class. This provides better process management (restarting workers, scaling, zero-downtime upgrades).
    *   Install `gunicorn` and `uvicorn-worker`: `pip install gunicorn uvicorn-worker`
    *   Run: `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:80`
    *   The `uvicorn.workers` module is deprecated; use the `uvicorn-worker` package instead.
*   **Proxy Headers**: If behind a proxy (like Nginx or Traefik), use `--proxy-headers` and configure `--forwarded-allow-ips`.
*   **SSL/TLS**: Uvicorn can handle SSL directly (`--ssl-keyfile`, `--ssl-certfile`), but it's often handled by a reverse proxy in production.

## Docker Integration

Uvicorn is well-suited for Docker. The [official Uvicorn documentation](https://www.uvicorn.org/deployment/docker/) provides a Docker image.

Key considerations for Docker:

1.  **Base Image**: Start with an official Python base image.
2.  **Install Dependencies**: Copy your `requirements.txt` and install packages.
3.  **Copy Application Code**: Copy your application files into the container.
4.  **Expose Port**: Use the `EXPOSE` instruction in your Dockerfile to document the port your application will listen on (e.g., `EXPOSE 80`).
5.  **CMD Instruction**: Use `CMD` to run Uvicorn.
    *   Set `--host 0.0.0.0` so the application is accessible from outside the container.
    *   Specify the number of workers for production.

**Example Dockerfile snippet for a FastAPI app:**

```dockerfile
# Start with an official Python base image
FROM python:3.9-slim

WORKDIR /app

# Install Uvicorn (and FastAPI, etc.)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY . .

# Expose the port Uvicorn will run on
EXPOSE 80

# Command to run Uvicorn
# For development:
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
# For production (without Gunicorn, directly using Uvicorn workers):
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--workers", "4"]
# For production (with Gunicorn):
# CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:80"]
```

**Running the Docker container:**

```bash
docker build -t my-fastapi-app .
docker run -d -p 8080:80 --name my-app-container my-fastapi-app
```
This maps port 8080 on the host to port 80 in the container.

## Summary Points for FastAPI & Docker:

*   **Host**: Always use `--host 0.0.0.0` in your Uvicorn command within Docker so the application can be reached via the mapped port.
*   **Workers in Production**:
    *   Use `--workers` with Uvicorn directly: `uvicorn main:app --host 0.0.0.0 --port 80 --workers 4`
    *   Or, preferably, use Gunicorn as a process manager: `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:80`
*   **Development**: `--reload` is useful during development, even within Docker (requires volume mounting for code changes to be reflected).
*   **Logging**: Configure appropriate log levels for development (`debug`) and production (`info` or `warning`).
*   **Official Image**: Consider using the [official Uvicorn Docker image](https://hub.docker.com/r/tiangolo/uvicorn-gunicorn-fastapi/) for FastAPI projects, as it comes pre-configured with Gunicorn and sensible defaults.

This summary should provide a good starting point for using Uvicorn with FastAPI. Always refer to the official documentation for the most up-to-date and detailed information.
```
