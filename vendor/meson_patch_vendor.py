#!/usr/bin/env python3
"""Helper Python script used by Meson to patch git submodules.

This script has no external dependencies, it purely relies on Python standard library.

This script is stateless. It doesn't store patch progress anywhere. It first tries
to undo any previously applied patches and then it applies them all again.

It is expected that the caller calls 'git submodule [--quiet] update' if appropriate.
This is a global operation, this script only handles per-submodule patching and
cleanup.

This script uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting.
"""

import argparse
import os
import pathlib
import shlex
import subprocess
import sys


def _printerr(*to_print, end: str = "\n") -> None:
    """Shorthand for print(..., file=sys.stderr)."""
    print(*to_print, end=end, file=sys.stderr)


def _failed_git_invocation(reason: str, exc: subprocess.CalledProcessError) -> None:
    _printerr(reason + "\n\ngit error message:\n" + exc.stderr.rstrip(), end="")
    sys.exit(1)


def _failed_patch_invocation(reason: str, exc: subprocess.CalledProcessError) -> None:
    # See _run_patch for the reason why stdout is used instead of stderr.
    _printerr(reason + "\n\npatch error message:\n" + exc.stdout.rstrip(), end="")
    sys.exit(1)


def _run_command(args: list[str]) -> None:
    command = shlex.join(args)
    print(f"    >>>>> Running: {command}", flush=True)
    subprocess.run(args, check=True, stderr=subprocess.PIPE, text=True)


def _run_patch(patch: str, args: list[str]) -> None:
    command = shlex.join(args)
    # The following log message is purely informative, it isn't used for
    # anything (no need to worry about quoting issues).
    print(f"    >>>>> Running: {command} < {shlex.quote(patch)}", flush=True)
    with open(patch) as input:
        # At least GNU patch seems to report --check errors to stdout,
        # so it makes sense to use stdout as primary error message
        # source.
        subprocess.run(
            args,
            check=True,
            stdin=input,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )


def _reset_git_submodule(git_executable: str, submodule_rel_path: str) -> None:
    """Reset the specified submodule into the pre-patched state.

    Arguments:
        git_executable: Path or filename of the git executable.
        submodule_rel_path: Path to the submodule relative to repository root.
    """
    try:
        _run_command([git_executable, "-C", submodule_rel_path, "reset", "--hard"])
        _run_command(
            [
                git_executable,
                "-C",
                submodule_rel_path,
                "clean",
                "--force",
                "-d",
                "-x",
            ]
        )
    except subprocess.CalledProcessError as exc:
        _failed_git_invocation(
            f"Could not clean up the '{submodule_rel_path}' submodule!", exc
        )


def _try_revert_nogit_git(
    git_executable: str, submodule_rel_path: str, patch: str
) -> None:
    """Revert the given patch safely with 'git am' (used during initial cleanup).

    Arguments:
        git_executable: Path or filename of the git executable.
        submodule_rel_path: Path to the submodule relative to repository root.
        patch: Path to the patch to revert.
    """
    _run_command(
        [
            git_executable,
            "-C",
            submodule_rel_path,
            "apply",
            "--check",
            "--reverse",
            patch,
        ]
    )
    # If the call above fails, do not execute the following code
    # and let the caller handle the exception.
    try:
        _run_command(
            [
                git_executable,
                "-C",
                submodule_rel_path,
                "apply",
                "--reverse",
                patch,
            ]
        )
    except subprocess.CalledProcessError as exc:
        _failed_git_invocation(
            f"A revert of patch '{patch}' of vendored project "
            + f"'{submodule_rel_path}' was unsuccessful even though a "
            + "previous --check was successful!",
            exc,
        )


def _try_revert_patch(
    patch_executable: str, submodule_rel_path: str, patch: str
) -> None:
    """Revert the given patch safely with 'patch' (used during initial cleanup).

    Arguments:
        patch_executable: Path or filename of the patch executable.
        submodule_rel_path: Path to the submodule relative to repository root.
        patch: Path to the patch to revert.
    """
    _run_patch(
        patch,
        [
            patch_executable,
            # -d is posix
            "-d",
            submodule_rel_path,
            # -p is posix
            "-p",
            "1",
            # -R is posix
            "-R",
            # --dry-run is not posix
            # tested on Linux; FreeBSD and OpenBSD manpages claim
            # support for this flag too
            "--dry-run",
        ],
    )
    # If the call above fails, do not execute the following code
    # and let the caller handle the exception.
    try:
        _run_patch(patch, [patch_executable, "-d", submodule_rel_path, "-p", "1", "-R"])
    except subprocess.CalledProcessError as exc:
        _failed_patch_invocation(
            f"A revert of patch '{patch}' of vendored project "
            + f"'{submodule_rel_path}' was unsuccessful even though a "
            + "previous --dry-run was successful!",
            exc,
        )


def _apply_git_norepo_patch(
    git_executable: str, submodule_rel_path: str, patch: str
) -> None:
    """Apply a single patch safely using 'git apply'.

    Arguments:
        git_executable: Path or filename of the git executable.
        submodule_rel_path: Path to the submodule relative to repository root.
        patch: Path to the patch to apply.
    """
    try:
        _run_command(
            [
                git_executable,
                "-C",
                submodule_rel_path,
                "apply",
                "--check",
                "--verbose",
                patch,
            ]
        )
    except subprocess.CalledProcessError as exc:
        try:
            _run_command(
                [
                    args.git_executable,
                    "-C",
                    submodule_rel_path,
                    "apply",
                    "--reverse",
                    "--check",
                    patch,
                ]
            )
        except subprocess.CalledProcessError:
            _failed_git_invocation(
                f"Could not apply patch '{patch}' for "
                + f"'{submodule_rel_path}' submodule!",
                exc,
            )
        else:
            # The cleanup stage should eliminate these cases, this check could
            # perhaps be dropped.
            print(
                f"    ======= Patch '{patch}' applied already,",
                "doing nothing... =======",
            )
    else:
        try:
            _run_command(
                [
                    git_executable,
                    "-C",
                    submodule_rel_path,
                    "apply",
                    "--verbose",
                    patch,
                ]
            )
        except subprocess.CalledProcessError as exc:
            _failed_git_invocation(
                f"Could not apply patch '{patch}' for "
                + f"'{submodule_rel_path}' submodule! A previous --check "
                + "git apply invocation was successful for this patch.",
                exc,
            )


def _apply_patch(patch_executable: str, submodule_rel_path: str, patch: str) -> None:
    """Apply a single patch safely using 'patch'.

    Arguments:
        patch_executable: Path or filename of the patch executable.
        submodule_rel_path: Path to the submodule relative to repository root.
        patch: Path to the patch to apply.
    """
    try:
        _run_patch(
            patch,
            [
                patch_executable,
                "-d",
                submodule_rel_path,
                "-p",
                "1",
                "--dry-run",
            ],
        )
    except subprocess.CalledProcessError as exc:
        try:
            _run_patch(
                patch,
                [
                    patch_executable,
                    "-d",
                    submodule_rel_path,
                    "-p",
                    "1",
                    "--dry-run",
                    "-R",
                ],
            )
        except subprocess.CalledProcessError:
            _failed_patch_invocation(
                f"Could not apply patch '{patch}' for "
                + f"'{submodule_rel_path}' submodule!",
                exc,
            )
        else:
            # The cleanup stage should eliminate these cases, this check could
            # perhaps be dropped.
            print(
                f"    ======= Patch '{patch}' applied already,",
                "doing nothing... =======",
            )
    else:
        try:
            _run_patch(
                patch,
                [
                    patch_executable,
                    "-d",
                    submodule_rel_path,
                    "-p",
                    "1",
                ],
            )
        except subprocess.CalledProcessError as exc:
            _failed_patch_invocation(
                f"Could not apply patch '{patch}' for "
                + f"'{submodule_rel_path}' submodule! A previous --dry-run "
                + "patch invocation was successful for this patch.",
                exc,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Helper Python script used by Meson to patch git submodules.

environment:
  MESON_SOURCE_ROOT Path to the root of the repository. If unspecified, it is
                    assumed that the repository is in the parent directory of
                    the directory where the script is located.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "git_executable",
        help="Path to the 'git' executable (empty string if not available)",
    )
    parser.add_argument(
        "patch_executable",
        help="Path to the 'patch' executable (empty string if not available)",
    )
    parser.add_argument("submodule_name", help="Name of the submodule to patch")
    parser.add_argument("patches", nargs="+", help="List of patches to apply")

    args = parser.parse_args()

    if "MESON_SOURCE_ROOT" in os.environ:
        os.chdir(os.environ["MESON_SOURCE_ROOT"])
    else:
        os.chdir(pathlib.Path(__file__).parent.parent)

    if args.git_executable == "" and args.patch_executable == "":
        sys.exit(
            "At least one patch executable must be specified! This is "
            "likely a bug in the Meson build system, which should handle "
            "this edge case itself."
        )

    submodule_name = args.submodule_name
    submodule_rel_path = "vendor" + os.sep + submodule_name
    is_in_git_repo = os.path.exists(".git")

    if args.git_executable and is_in_git_repo:
        print(
            "    ===== Using 'git am' patch strategy, we are in a git",
            "repository =====",
        )
        print("    ======= Cleaning up submodules =======")

        _reset_git_submodule(args.git_executable, submodule_rel_path)

        possible_failed_git_am = pathlib.Path(
            ".git", "modules", "vendor", submodule_name, "rebase-apply"
        ).exists()

        print("    ======= Applying patches =======")
        try:
            _run_command(
                [
                    args.git_executable,
                    # Try to not rely on the environment (the user/builder
                    # may not have a git identity set for example).
                    "-c",
                    "safe.directory=*",
                    "-c",
                    "user.name=android-tools-static's build system",
                    "-c",
                    "user.email=email@invalid.invalid",
                    "-C",
                    submodule_rel_path,
                    "am",
                ]
                + args.patches
            )
        except subprocess.CalledProcessError as exc:
            _printerr(
                f"Could not apply patches for '{submodule_rel_path}'",
                "submodule!",
                end="",
            )
            if possible_failed_git_am:
                _printerr(
                    " This error is likely caused by a previous failed",
                    "invocation of `git am`. To fix this, run the following",
                    "command:\n\n",
                    end="",
                )
                _printerr(
                    f"git -C vendor/{submodule_name} am --abort\n\n",
                    end="",
                )
                _printerr(
                    "from the repository root and then reconfigure the",
                    "builddir.",
                )
            elif next(pathlib.Path(submodule_rel_path).iterdir(), None) is None:
                _printerr(
                    " The submodule doesn't seem to be initialized. To initialize all",
                    "submodules, run the following command:\n\n", end="",
                )
                _printerr(
                    "git submodule update --init\n\n", end="",
                )
                _printerr(
                    "from the repository root and then reconfigure the",
                    "builddir. Alternatively, you can use -src release archives in",
                    "https://github.com/meator/android-tools-static/releases which",
                    "already include the necessary submodules."
                )
            else:
                _printerr()
            _printerr()
            _printerr("git error message:")
            _printerr(exc.stderr.rstrip(), end="")
            sys.exit(1)
    else:
        if not is_in_git_repo:
            print(
                "    ===== WARNING: Not in a git repository, using",
                "potentially less reliable patching strategy =====",
            )
        elif is_in_git_repo and not args.git_executable:
            print(
                "    ===== WARNING: It looks like we are in a git repo (likely",
                "cloned with 'git clone'), but the 'git' executable is nowhere",
                "to be found. It is recommended to use 'git' for patching",
                "(using 'git am') the vendored submodules, because it is",
                "simpler to handle and revert bad patches. =====",
            )

        if args.git_executable:

            def revert_func(submodule_rel_path, patch):
                return _try_revert_nogit_git(
                    args.git_executable, submodule_rel_path, patch
                )

            def apply_func(reason, exc):
                return _apply_git_norepo_patch(args.git_executable, reason, exc)

            fail_func = _failed_git_invocation

            print(
                "    ===== Using 'git apply' patch strategy, we are not in a",
                "git repository =====",
            )
        elif args.patch_executable:

            def revert_func(submodule_rel_path, patch):
                return _try_revert_patch(
                    args.patch_executable, submodule_rel_path, patch
                )

            def apply_func(reason, exc):
                return _apply_patch(args.patch_executable, reason, exc)

            fail_func = _failed_patch_invocation

            if is_in_git_repo:
                print(
                    "    ===== Using 'patch' patch strategy, we are in a git",
                    "repository (irrelevant for 'patch') =====",
                )
            else:
                print(
                    "    ===== Using 'patch' patch strategy, we are not in a",
                    "git repository (irrelevant for 'patch') =====",
                )
        print("    ======= Cleaning up vendored projects =======")
        expects_successful_reverts = False
        for patch in reversed(args.patches):
            try:
                revert_func(submodule_rel_path, patch)
            except subprocess.CalledProcessError as exc:
                if expects_successful_reverts:
                    fail_func(
                        f"Couldn't revert patch '{patch}' of submodule "
                        + f"'{submodule_rel_path}'! This error is not "
                        + "recoverable without manual intervention. If that "
                        + "isn't possible, please restore this project into "
                        + "its original state (by for example reextracting a "
                        + "release tarball if that is this project's origin).",
                        exc,
                    )
                else:
                    print(
                        "    ========= Invocation failed, patch was likely",
                        "never applied =========",
                        flush=True,
                    )
            else:
                expects_successful_reverts = True
        print("    ======= Applying patches =======")
        for patch in args.patches:
            apply_func(submodule_rel_path, patch)
