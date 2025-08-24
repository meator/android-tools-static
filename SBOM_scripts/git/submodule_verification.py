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

"""Module used to verify that git submodules contain the expected patches."""

import typing
from pathlib import Path

import proj_types

from . import patch_id


class PatchIDError(RuntimeError):
    """Exception raised by verify_checkout_patches()."""

    def __init__(
        self,
        commit_patch_id: proj_types.PatchID,
        patch_patch_id: proj_types.PatchID,
        repo_dir: Path,
        patch_file: Path,
    ):
        """Initialize PatchInconsistencyError.

        Arguments:
            commit_patch_id: Patch id of the examined commit.
            patch_patch_id: Patch id of the examined patch.
            repo_dir: Git submodule directory.
            patch_file: Patch which was being verified.
        """
        super().__init__(
            f"Couldn't verify patch '{patch_file}' in git submodule '{repo_dir}'! "
            f"Commit patch id '{commit_patch_id}' != patch id '{patch_patch_id}'!"
        )
        self._commit_patch_id = commit_patch_id
        self._patch_patch_id = patch_patch_id
        self._repo_dir = repo_dir
        self._patch_file = patch_file

    @property
    def commit_patch_id(self) -> proj_types.PatchID:  # noqa: D102
        return self._commit_patch_id

    @property
    def patch_patch_id(self) -> proj_types.PatchID:  # noqa: D102
        return self._patch_patch_id

    @property
    def repo_dir(self) -> Path:  # noqa: D102
        return self._repo_dir

    @property
    def patch_file(self) -> Path:  # noqa: D102
        return self._patch_file


def verify_checkout_patches(
    git_exe: str, repo_path: Path, patch_series: typing.Iterable[Path]
) -> None:
    """Verify that the checkout contains the given patches in the given order.

    Patches must be on the top of HEAD.

    Arguments:
        git_exe: Path to git executable.
        repo_path: Path to git submodule.
        patch_series: A series of patch paths.

    Raises:
        PatchIDError: If the checkout doesn't contain one or more of the patches
          specified.
    """
    for patch_num, patch in enumerate(patch_series):
        commit_patch_id = patch_id.get_nth_head_commit_patch_id(
            repo_path, git_exe, patch_num
        )
        patch_patch_id = patch_id.get_file_patch_id(patch, git_exe)

        if commit_patch_id != patch_patch_id:
            raise PatchIDError(commit_patch_id, patch_patch_id, repo_path, patch)
