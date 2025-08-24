# Copyright 2025 meator
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module for obtaining patches applied against a Meson Wrap."""

import configparser
import enum
import shutil
import subprocess
import tempfile
from pathlib import Path


def _git_unpatch(git_exe: str, subproj_path: Path, patch_path: Path) -> None:
    subprocess.run(
        args=[git_exe, "apply", "--reverse", patch_path],
        capture_output=True,
        check=True,
        close_fds=True,
        cwd=subproj_path,
    )


def _patch_unpatch(patch_exe: str, subproj_path: Path, patch_path: Path) -> None:
    subprocess.run(
        args=[patch_exe, "-R", "-i", patch_path],
        capture_output=True,
        check=True,
        close_fds=True,
        cwd=subproj_path,
    )


class PatchStrategy(enum.Enum):
    """Patch strategy to use in get_wrap_patch_list()."""

    GIT = enum.auto()
    PATCH = enum.auto()


class MissingPatchError(RuntimeError):
    """Exception raised when get_wrap_patch_list() can't verify a patch."""

    pass


def get_wrap_patch_list(
    source_dir: Path, wrap_name: str, patch_strategy: PatchStrategy, git_patch_path: str
) -> list[Path]:
    """Get a verified list of patches applied to a wrap.

    This function attempts to verify that all the patches it returns are indeed applied
    and in use.

    Arguments:
        source_dir: Path to the root source repository.
        wrap_name: Name of the Meson Wrap.
        patch_strategy: How should patching be done? At the time of writing this,
          'patch' and 'git apply' are supported.
        git_patch_path: Path to the executable needed by patch_strategy. At the time of
          writing this, this may be a path to git or patch executable.
    """
    wrap = configparser.ConfigParser()
    wrap.read(source_dir / "subprojects" / (wrap_name + ".wrap"))

    if "diff_files" not in wrap["wrap-file"]:
        return []

    subproj_path = source_dir / "subprojects" / wrap["wrap-file"]["directory"]

    match patch_strategy:
        case PatchStrategy.GIT:

            def reverse_patch(path: Path, subproj_path: Path) -> None:
                return _git_unpatch(git_patch_path, subproj_path, path)

        case PatchStrategy.PATCH:

            def reverse_patch(path: Path, subproj_path: Path) -> None:
                return _patch_unpatch(git_patch_path, subproj_path, path)

        case _:
            raise RuntimeError(
                "Unknown patch_strategy! This is likely a bug in the script."
            )

    patch_list = [patch.strip() for patch in wrap["wrap-file"]["diff_files"].split(",")]

    # These checks aren't bulletproof, but they are better than nothing.
    # A more robust approach would be to replicate Meson's subproject setup process
    # 1. Find out the appropriate packagecache (it is dynamic, subprojects/packagecache
    #    might not be it).
    # 2. Find the source and patch archives.
    # 3. Extract them on top of each other in a temporary directory.
    # 4. Find and apply all patches.
    # 5. filecmp.dircmp() the temporary directory with
    #    source_dir / "subprojects" / wrap["wrap-file"]["directory"]
    #
    # 1. leaves me uncertain and the process is in general more complicated, so we'll
    # do with the current process instead.
    #
    # By the way, the current process copies the subprojects/<wrap> directory to a
    # temporary directory and tries to undo all of the patches marked in the Wrap file.
    # If this script cannot undo the patches, it likely means that the patch was never
    # applied in the first place, which will lead to an inconsistency in the supply
    # chain.
    with tempfile.TemporaryDirectory() as dir_name:
        dir_path = Path(dir_name)

        shutil.copytree(
            subproj_path, dir_path, copy_function=shutil.copyfile, dirs_exist_ok=True
        )

        result = []

        for patch_relpath in reversed(patch_list):
            patch_path = source_dir / "subprojects/packagefiles" / patch_relpath

            # This will throw if there are patch errors.
            try:
                reverse_patch(patch_path, dir_path)
            except subprocess.CalledProcessError as exc:
                raise MissingPatchError(
                    f"The '{patch_path}' patch doesn't appear to be applied to the "
                    f"'{subproj_path}' subproject! Please regenerate all subprojects "
                    "(which can be achieved by deleting all directories in "
                    "subprojects/ except subprojects/packagefiles/) and rebuild the "
                    "project."
                ) from exc

            result.append(patch_path)

        return result
