
#!/usr/bin/env python3
"""
pc_helper.py — Lifecycle helper for proxy_converter

Responsibilities:
- Locate the proxy_converter project directory.
- Ensure venv exists (create if missing) inside the project directory.
- On first creation only: install dependencies from requirements.txt.
- Always upgrade pip/setuptools/wheel immediately after creating venv.
- Run proxy_converter.py with the venv's Python.
- Offer cleanup options after the run:
  - Delete venv entirely
  - Purge venv dependencies (keep pip/setuptools/wheel)
  - Delete ~/.bindproxy.json
- Supports non-interactive mode via --yes and explicit flags.

Usage examples:
  # Basic run (interactive prompts after run)
  python pc_helper.py run

  # Non-interactive run, then delete venv and bindproxy.json without prompting
  python pc_helper.py run --yes --clean-venv --delete-bindproxy

  # Only purge dependencies (keep venv), ask interactively
  python pc_helper.py clean --purge-venv

  # Set project path via env
  PROXY_CONVERTER_PATH=/path/to/proxy_converter python pc_helper.py run
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional, Tuple


# ---------------------------
# Configuration & Constants
# ---------------------------

DEFAULT_DIRNAME = "proxy_converter"
DEFAULT_VENV_NAME = "venv"
DEFAULT_SCRIPT = "proxy_converter.py"
BINDPROXY_JSON = os.path.expanduser("~/.bindproxy.json")

# Packages we DO NOT uninstall when purging venv deps
KEEP_WHEN_PURGING = {"pip", "setuptools", "wheel"}


@dataclass
class Paths:
    project: str
    venv_dir: str
    venv_bin: str
    venv_python: str
    requirements: str
    script: str
    is_windows: bool


def resolve_paths(project_path: Optional[str]) -> Paths:
    """Resolve all important paths with sensible defaults."""
    if not project_path:
        project_path = os.environ.get("PROXY_CONVERTER_PATH") or os.path.join(
            os.path.expanduser("~"), DEFAULT_DIRNAME
        )

    project_path = os.path.abspath(os.path.expanduser(project_path))
    is_windows = os.name == "nt"

    venv_dir = os.path.join(project_path, DEFAULT_VENV_NAME)
    venv_bin = os.path.join(venv_dir, "Scripts" if is_windows else "bin")
    venv_python = os.path.join(venv_bin, "python.exe" if is_windows else "python")
    requirements = os.path.join(project_path, "requirements.txt")
    script = os.path.join(project_path, DEFAULT_SCRIPT)

    return Paths(
        project=project_path,
        venv_dir=venv_dir,
        venv_bin=venv_bin,
        venv_python=venv_python,
        requirements=requirements,
        script=script,
        is_windows=is_windows,
    )


# ---------------------------
# Utilities
# ---------------------------

def shout(msg: str) -> None:
    print(f"[pc-helper] {msg}")


def fail(msg: str, code: int = 1) -> None:
    shout(f"ERROR: {msg}")
    sys.exit(code)


def run_cmd(cmd: list[str], cwd: Optional[str] = None, check: bool = True) -> int:
    """Run a command; return exit code (or raise if check=True)."""
    shout(f"$ {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=cwd)
    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)
    return proc.returncode


def file_exists(path: str) -> bool:
    return os.path.isfile(path)


def dir_exists(path: str) -> bool:
    return os.path.isdir(path)


def confirm(prompt: str, default_no: bool = True, assume_yes: bool = False) -> bool:
    """
    Ask the user to confirm. Returns True if confirmed.
    - default_no=True -> Enter without input means 'No'.
    - assume_yes=True -> Non-interactive/CI: auto-confirm ('Yes').
    """
    if assume_yes:
        shout(f"{prompt} [auto-yes]")
        return True

    # If not a TTY, default to 'No'
    if not sys.stdin.isatty():
        shout(f"{prompt} [non-interactive: default {'No' if default_no else 'Yes'}]")
        return not default_no

    suffix = " [y/N]: " if default_no else " [Y/n]: "
    while True:
        resp = input(prompt + suffix).strip().lower()
        if not resp:
            return not default_no
        if resp in {"y", "yes"}:
            return True
        if resp in {"n", "no"}:
            return False
        print("Please answer 'y' or 'n'.")


# ---------------------------
# Venv & Dependency Management
# ---------------------------

def ensure_project(paths: Paths) -> None:
    if not dir_exists(paths.project):
        fail(
            f"Project directory not found: {paths.project}\n"
            f"Set PROXY_CONVERTER_PATH or create {os.path.join(os.path.expanduser('~'), DEFAULT_DIRNAME)}"
        )


def ensure_venv(paths: Paths, creator_python: Optional[str], upgrade_toolchain: bool = True) -> Tuple[bool, str]:
    """
    Ensure venv exists. If created, optionally upgrade pip/setuptools/wheel.
    Returns (created: bool, venv_python_path: str)
    """
    if dir_exists(paths.venv_dir) and file_exists(paths.venv_python):
        shout(f"Using existing venv at {paths.venv_dir}")
        return False, paths.venv_python

    shout(f"Creating venv at {paths.venv_dir}")
    os.makedirs(paths.project, exist_ok=True)

    py = creator_python or sys.executable
    try:
        run_cmd([py, "-m", "venv", paths.venv_dir], check=True)
    except subprocess.CalledProcessError:
        fail("Failed to create virtual environment.")

    if upgrade_toolchain:
        try:
            run_cmd([paths.venv_python, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)
        except subprocess.CalledProcessError:
            fail("Failed to upgrade pip/setuptools/wheel inside venv.")

    return True, paths.venv_python


def install_requirements_if_new(paths: Paths, venv_python: str, venv_was_created: bool) -> None:
    """
    Install requirements ONLY when venv was first created.
    If requirements.txt is missing, warn and continue.
    """
    if not venv_was_created:
        shout("Skipping dependency installation (venv already exists).")
        return

    if not file_exists(paths.requirements):
        shout(f"requirements.txt not found at {paths.requirements} — continuing without installs.")
        return

    shout(f"Installing dependencies from {paths.requirements}")
    try:
        run_cmd([venv_python, "-m", "pip", "install", "-r", paths.requirements], check=True)
    except subprocess.CalledProcessError:
        fail("Dependency installation failed.")


# ---------------------------
# Running the application
# ---------------------------

def run_proxy_converter(paths: Paths, venv_python: str, passthrough_args: list[str]) -> int:
    if not file_exists(paths.script):
        fail(f"Script not found: {paths.script}")

    cmd = [venv_python, paths.script] + passthrough_args
    shout("Running proxy_converter...")
    rc = run_cmd(cmd, cwd=paths.project, check=False)
    if rc == 0:
        shout("Proxy conversion completed.")
    else:
        shout(f"Proxy converter exited with code: {rc}")
    return rc


# ---------------------------
# Cleanup operations
# ---------------------------

def delete_venv(paths: Paths) -> bool:
    if not dir_exists(paths.venv_dir):
        shout(f"No venv to delete at {paths.venv_dir}")
        return False
    shout(f"Deleting venv at {paths.venv_dir}")
    shutil.rmtree(paths.venv_dir)
    return True


def purge_venv_dependencies(paths: Paths, venv_python: str) -> None:
    """
    Uninstall all packages except pip/setuptools/wheel.
    Leaves venv structure intact.
    """
    shout("Purging venv dependencies (keeping pip/setuptools/wheel)...")

    # Get installed packages in a 'name==version' format
    try:
        freeze_out = subprocess.check_output([venv_python, "-m", "pip", "freeze"], text=True)
    except subprocess.CalledProcessError:
        fail("Failed to list installed packages for purge.")

    pkgs = []
    for line in freeze_out.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Extract the package name for KEEP_WHEN_PURGING filtering
        name = line.split("==")[0].split("@")[0].split("[")[0].strip()
        if name.lower() in KEEP_WHEN_PURGING:
            continue
        pkgs.append(line)

    if not pkgs:
        shout("No installed third-party packages to uninstall.")
        return

    # Uninstall in one go (fast path); pip will parse specifiers in freeze
    cmd = [venv_python, "-m", "pip", "uninstall", "-y"] + pkgs
    try:
        run_cmd(cmd, check=True)
        shout("Venv dependencies purged.")
    except subprocess.CalledProcessError:
        fail("Failed to purge venv dependencies.")


def delete_bindproxy_json() -> bool:
    if not file_exists(BINDPROXY_JSON):
        shout(f"No bindproxy file at {BINDPROXY_JSON}")
        return False
    shout(f"Deleting {BINDPROXY_JSON}")
    try:
        os.remove(BINDPROXY_JSON)
        return True
    except OSError as e:
        fail(f"Failed to delete {BINDPROXY_JSON}: {e}")
    return False


# ---------------------------
# CLI
# ---------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pc-helper",
        description="Helper for proxy_converter lifecycle (venv, deps, run, cleanup).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--project-path", help="Path to proxy_converter project (defaults to PROXY_CONVERTER_PATH or ~/proxy_converter).")
    p.add_argument("--python", help="Interpreter to create the venv with (defaults to current Python).")

    sub = p.add_subparsers(dest="cmd", required=True)

    # run command
    pr = sub.add_parser("run", help="Ensure venv, install deps if new, run proxy_converter.py, then offer cleanup.")
    pr.add_argument("--yes", action="store_true", help="Auto-confirm cleanup prompts (non-interactive).")
    pr.add_argument("--no-prompts", action="store_true", help="Do not prompt for any cleanup actions.")
    pr.add_argument("--clean-venv", action="store_true", help="Delete the venv after run.")
    pr.add_argument("--purge-venv", action="store_true", help="Purge venv dependencies after run (keep venv).")
    pr.add_argument("--delete-bindproxy", action="store_true", help="Delete ~/.bindproxy.json after run.")
    pr.add_argument("passthrough", nargs=argparse.REMAINDER, help="Arguments after '--' are passed to proxy_converter.py.")

    # clean command
    pc = sub.add_parser("clean", help="Run cleanup actions without running the app.")
    pc.add_argument("--yes", action="store_true", help="Auto-confirm prompts.")
    pc.add_argument("--clean-venv", action="store_true", help="Delete the venv directory.")
    pc.add_argument("--purge-venv", action="store_true", help="Purge venv dependencies (keep venv).")
    pc.add_argument("--delete-bindproxy", action="store_true", help="Delete ~/.bindproxy.json.")

    return p


def handle_run(args, paths: Paths) -> int:
    ensure_project(paths)
    venv_created, vpython = ensure_venv(paths, args.python, upgrade_toolchain=True)
    install_requirements_if_new(paths, vpython, venv_created)

    # Extract passthrough args, respecting '--'
    passthrough = []
    if args.passthrough:
        # argparse.REMAINDER includes the leading '--' if present; strip it
        passthrough = [a for a in args.passthrough if a != "--"]

    exit_code = run_proxy_converter(paths, vpython, passthrough)

    # Decide cleanup behavior
    # Priority: explicit flags. If none provided and prompts allowed, ask.
    do_prompts = not args.no_prompts

    # ---- VENV cleanup (delete OR purge) ----
    if args.clean_venv:
        if confirm("Delete the venv directory?", default_no=True, assume_yes=args.yes):
            delete_venv(paths)
    elif args.purge_venv:
        if confirm("Purge all venv dependencies (keep venv)?", default_no=True, assume_yes=args.yes):
            purge_venv_dependencies(paths, vpython)
    elif do_prompts:
        # Offer a two-step: delete OR purge OR skip
        if confirm("Do you want to DELETE the venv directory?", default_no=True, assume_yes=False if args.yes is False else True):
            delete_venv(paths)
        elif confirm("Do you want to PURGE venv dependencies (keep venv)?", default_no=True, assume_yes=False if args.yes is False else True):
            purge_venv_dependencies(paths, vpython)

    # ---- bindproxy cleanup ----
    if args.delete_bindproxy:
        if confirm(f"Delete {BINDPROXY_JSON}?", default_no=True, assume_yes=args.yes):
            delete_bindproxy_json()
    elif do_prompts:
        if file_exists(BINDPROXY_JSON):
            if confirm(f"Delete {BINDPROXY_JSON}?", default_no=True, assume_yes=False if args.yes is False else True):
                delete_bindproxy_json()

    return exit_code


def handle_clean(args, paths: Paths) -> int:
    ensure_project(paths)
    # For purge we need venv python; if venv missing, short-circuit
    vpython = paths.venv_python

    any_action = False

    if args.clean_venv:
        any_action = True
        if confirm("Delete the venv directory?", default_no=True, assume_yes=args.yes):
            delete_venv(paths)

    if args.purge_venv:
        any_action = True
        if not file_exists(vpython):
            shout("No venv/python found; nothing to purge.")
        else:
            if confirm("Purge all venv dependencies (keep venv)?", default_no=True, assume_yes=args.yes):
                purge_venv_dependencies(paths, vpython)

    if args.delete_bindproxy:
        any_action = True
        if confirm(f"Delete {BINDPROXY_JSON}?", default_no=True, assume_yes=args.yes):
            delete_bindproxy_json()

    if not any_action:
        shout("No cleanup flags provided. Nothing to do.")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = resolve_paths(args.project_path)

    if args.cmd == "run":
        return handle_run(args, paths)
    if args.cmd == "clean":
        return handle_clean(args, paths)

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

