# Contributing

Thanks for considering a contribution to `pytest-pubsub`.

## Setup

```bash
git clone https://github.com/rhasan33/pytest-pubsub.git
cd pytest-pubsub
make install          # uv sync --all-extras
uv run pre-commit install
```

## Before opening a pull request

```bash
make check            # lint + typecheck + test (what CI runs)
```

Individual targets are also available: `make test`, `make lint`, `make format`, `make typecheck`.

Pre-commit hooks run automatically on `git commit` and cover the same lint/format/typecheck
checks, plus basic file hygiene.

## Commit and PR conventions

- Keep commits atomic: implementation and its tests land together, not as separate commits.
- Commit messages are a short title plus a one-sentence description of *why*, not a line-by-line changelog.
- Update `CHANGELOG.md` under `[Unreleased]` for any user-facing change.
- Fill in the pull request template checklist.

## Reporting bugs / requesting features

Use the GitHub issue templates. For security issues, see [SECURITY.md](SECURITY.md) instead of
opening a public issue.
