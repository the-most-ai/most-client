# Repository Guidelines

## Project Structure & Module Organization
Core client code lives in `most/`, with synchronous endpoints in files like `api.py` and async variants in `async_api.py`, `async_catalog.py`, and related helpers. Shared data contracts reside in `types.py` and `search_types.py`, while `score_calculation.py` handles evaluation logic. Entry points for quick experiments sit in `main.py` and `main_async.py`. Tests are split between `tests/unit` for focused behaviour checks and `tests/e2e` for high-level flows. Packaging assets (`setup.py`, `MANIFEST.in`, `dist/`) support PyPI releases, and exploratory notebooks belong under `notebooks/`.

## Build, Test, and Development Commands
- `make deps`: install the pinned toolchain from `requirements.txt`.
- `make lint`: run `isort --profile black` and `black --line-length 64` across `most/`.
- `ruff check .`: mirror the CI linter before opening a PR.
- `pytest tests/unit`: run unit coverage; add `tests/e2e` for full validation.
- `make wheel`: build a distributable wheel (also used in release automation).

## Coding Style & Naming Conventions
Python code is formatted with Black (64-character lines) and import-sorted with the matching isort profile. Keep modules and functions in `snake_case`, classes in `PascalCase`, and constants in `UPPER_SNAKE_CASE`. Type hints should accompany public interfaces, matching the patterns in `most/types.py`. Avoid ad-hoc prints; prefer structured logging where required by integrations. Run Ruff (configured in CI) to catch lint violations before pushing.

## Testing Guidelines
Use Pytest for both unit and end-to-end suites, naming files and functions `test_*` so discovery stays automatic. Keep unit tests close to the modules they cover, mocking remote calls via fixtures. End-to-end tests may call live services; gate them behind environment variables when adding new cases. When touching critical flows, run `pytest --maxfail=1 --disable-warnings --junitxml=report.xml` locally to replicate CI. Leverage the `coverage` package if changes impact request pipelines, aiming to maintain existing coverage levels.

## Commit & Pull Request Guidelines
Follow the existing history of short, imperative commit subjects (e.g., `fix update_dialog api`, `add anonymization api`). Group related edits into a single commit when reasonable. Every PR should explain the motivation, reference related issues, and include before/after or sample payloads for API changes. Attach screenshots or logs when tweaking notebooks or evaluation outputs, and confirm that `make lint` and the relevant `pytest` targets pass locally. Flag any breaking API changes prominently in the PR description.
