# Repository Guidelines

## Project Structure & Module Organization
The application is packaged under `ding/`, with `api/` hosting the FastAPI service (`ding/api/main.py`), `grpc_service/` providing gRPC servers and generated stubs, `models/` containing Pydantic schemas, and `utils/` for shared helpers such as configuration (`ding/utils/config.py`). Root-level `main.py` orchestrates all services; standalone scripts live alongside. Protocol buffers reside in `protos/`, and generated files should remain in `ding/grpc_service/`. Place new integration assets under a dedicated subfolder and keep prototype notebooks outside the repo.

## Build, Test, and Development Commands
- `uv sync` installs dependencies defined in `pyproject.toml`.
- `uv run python -m ding.main` launches the orchestration entry point.
- `uv run python -m ding.grpc_service.video_server` and `uv run python -m ding.grpc_service.doorbell_server` run individual gRPC services during focused work.
- Regenerate gRPC bindings after editing `.proto` files: `uv run python -m grpc_tools.protoc -I protos --python_out=ding/grpc_service --grpc_python_out=ding/grpc_service protos/doorbell.proto protos/video_stream.proto`.

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indentation and type hints on public functions. Module names should stay lowercase with underscores; classes use PascalCase; async handlers and RPC methods use descriptive verbs (`start_video_session`). Keep FastAPI route handlers in `api/main.py`, gRPC servicers in per-service files, and share reusable logic through `utils/`. Prefer docstrings for complex flows and log with the configured `logging` module.

## Testing Guidelines
The project lacks automated tests—add `pytest` suites under `tests/`. Mirror package paths (e.g., `tests/api/test_main.py`) and give tests descriptive snake_case names. Include async unit tests for FastAPI routes and gRPC handlers using fixtures. Run locally with `uv run pytest`; target meaningful coverage for new features and document gaps in the PR.

## Commit & Pull Request Guidelines
Use concise, imperative commit subjects similar to existing history (`lint`, `init project`). Reference issues in commit bodies when relevant. Pull requests should explain the problem, the solution, and testing performed; attach screenshots or logs if behavior changes. Request reviewers for cross-service changes and highlight follow-up work in a checklist.

## Security & Configuration Tips
Never commit secrets; rely on environment variables documented in `README.md`. Validate inbound payloads with Pydantic models and enforce authentication stubs where marked TODO. If you introduce new ports or services, update configuration defaults in `ding/utils/config.py` and mention them in the PR summary.
