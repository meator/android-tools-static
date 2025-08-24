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

"""Module used to get the patch id of patch files and git commits."""

import subprocess
from pathlib import Path

import proj_types


def get_file_patch_id(patch_path: Path, git_exe: str) -> proj_types.PatchID:
    """Get the patch id of the specified patch file.

    This uses `git patch-id --stable` under the hood.

    Arguments:
        patch_path: Path to the patch whose patch id is computed.
        git_exe: Path to the git executable.
    """
    with patch_path.open() as input:
        exec_proc = subprocess.run(
            args=(git_exe, "patch-id", "--stable"),
            stdin=input,
            capture_output=True,
            text=True,
            check=True,
            close_fds=True,
        )

    return proj_types.PatchID(exec_proc.stdout[:40])


def get_nth_head_commit_patch_id(
    repo_dir: Path, git_exe: str, n: int
) -> proj_types.PatchID:
    """Get HEAD~n th patch id from the specified git repository.

    Arguments:
        repo_dir: Path to the examined repository.
        git_exe: Path to the git executable.
        n: The HEAD~n commit is examined.
    """
    git_diff_args = [git_exe, "diff", f"HEAD~{n}^!"]
    git_diff_proc = subprocess.Popen(
        args=git_diff_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
        cwd=repo_dir,
    )
    git_patch_id_args = [git_exe, "patch-id", "--stable"]
    git_patch_id_proc = subprocess.Popen(
        args=git_patch_id_args,
        stdin=git_diff_proc.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
    )

    # Make mypy happy.
    assert git_diff_proc.stdout is not None

    git_diff_proc.stdout.close()

    git_patch_id_stdout, git_patch_id_stderr = git_patch_id_proc.communicate()
    git_diff_stderr = git_diff_proc.communicate()[1]

    if git_diff_proc.returncode != 0:
        raise subprocess.CalledProcessError(
            git_diff_proc.returncode, git_diff_args, None, git_diff_stderr
        )
    if git_patch_id_proc.returncode != 0:
        raise subprocess.CalledProcessError(
            git_patch_id_proc.returncode,
            git_patch_id_args,
            git_patch_id_stdout,
            git_patch_id_stderr,
        )

    return proj_types.PatchID(git_patch_id_stdout.decode()[:40])
