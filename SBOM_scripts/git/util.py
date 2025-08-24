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

"""Utility functions interacting with git."""

import subprocess
from pathlib import Path


def get_head(git_exe: str, repo_dir: Path) -> str:
    """Get the commit hash of HEAD.

    Arguments:
        git_exe: Path to the git executable.
        repo_dir: Path to the repository.
    """
    proc = subprocess.run(
        args=[git_exe, "rev-parse", "--verify", "HEAD"],
        capture_output=True,
        text=True,
        cwd=repo_dir,
        close_fds=True,
        check=True,
    )
    return proc.stdout.strip()
