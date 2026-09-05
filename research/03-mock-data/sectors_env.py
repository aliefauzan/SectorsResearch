#!/usr/bin/env python3
"""
One shared way to read configuration, so nobody on the team hardcodes a key.

Import this from any script that talks to the Sectors API — the capture harness, a
notebook, the demo app — and the whole team gets identical behaviour from one
git-ignored `.env` at the repository root.

    from sectors_env import api_key, base_url, budget

    headers = {"Authorization": api_key()}      # raises if unset, never prints it

Precedence, highest first: a real environment variable, then `.env`, then the default.
That ordering is what lets CI and one-off overrides work without editing the file:

    SECTORS_BASE_URL=http://127.0.0.1:8787 python3 your_script.py

Deliberately dependency-free — no `python-dotenv` install, no venv step for a teammate
who just cloned the repo.
"""
import os

DEFAULT_BASE_URL = "https://api.sectors.app"
DEFAULT_BUDGET = 250

_loaded_from = None


def load_dotenv(start=None):
    """Load the nearest `.env` into os.environ without overwriting anything already set.

    Walks up from `start` (default: this file's directory) to the filesystem root and
    loads the first `.env` it finds. Returns the path loaded, or None.

    Parses `KEY=value`, `export KEY=value`, `#` comments, blank lines, and single- or
    double-quoted values. Nothing else — there is no shell evaluation, so a key
    containing an odd character cannot surprise anyone.
    """
    global _loaded_from

    directory = start or os.path.dirname(os.path.abspath(__file__))
    path = None
    while True:
        candidate = os.path.join(directory, ".env")
        if os.path.isfile(candidate):
            path = candidate
            break
        parent = os.path.dirname(directory)
        if parent == directory:
            break
        directory = parent

    if path is None:
        return None

    with open(path) as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):].strip()
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            if key and key not in os.environ:
                os.environ[key] = value

    _loaded_from = path
    return path


def dotenv_path():
    """Where the loaded `.env` came from, for printing in a run header. Never its contents."""
    return _loaded_from


def api_key(required=True):
    """The raw Sectors API key. Never log or persist the return value."""
    key = os.environ.get("SECTORS_API_KEY") or ""
    if required and not key:
        raise SystemExit(
            "SECTORS_API_KEY is not set — refusing to run.\n"
            "Copy .env.example to .env at the repository root, put the team key in it, "
            "and re-run. A shell export still works and takes precedence."
        )
    return key


def base_url():
    """Live API by default; point at mock_server.py to rehearse for zero credits."""
    return os.environ.get("SECTORS_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def budget(default=DEFAULT_BUDGET):
    """Hard credit ceiling. The grant is 1,000 and does not top up."""
    try:
        return int(os.environ.get("SECTORS_BUDGET", default))
    except ValueError:
        raise SystemExit(f"SECTORS_BUDGET must be an integer, got "
                         f"{os.environ.get('SECTORS_BUDGET')!r}")


def is_live():
    """True when configured against the real, billing API rather than the mock."""
    return base_url().startswith(DEFAULT_BASE_URL)


load_dotenv()


if __name__ == "__main__":
    # `python3 sectors_env.py` — a preflight a teammate can run after cloning.
    print(f"env file : {dotenv_path() or 'none found'}")
    print(f"base url : {base_url()}{'   (LIVE — calls bill credits)' if is_live() else '   (mock)'}")
    print(f"budget   : {budget()}")
    print(f"api key  : {'set' if api_key(required=False) else 'MISSING — copy .env.example to .env'}")
