#!/usr/bin/env python3

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

"""Module storing argparse arguments shared across all three SBOM generation scripts."""

import argparse
from pathlib import Path


def add(parser: argparse.ArgumentParser) -> None:
    """Add arguments common to all SBOM generator entrypoints.

    Different OS-specific SBOM generator entrypoints may have their own arguments. This
    function adds the base set of arguments shared with all entrypoints.
    """
    parser.add_argument("source_dir", type=Path, help="Path of the source directory")
    parser.add_argument(
        "meson_depmf_file", type=Path, help="Path to the depmf.json file"
    )
    parser.add_argument("purl", help="purl of this package")
    parser.add_argument(
        "nmeum_patch_series_file",
        type=Path,
        help="File containing null-separated patches originating from nmeum/android-tools",
    )
    parser.add_argument(
        "added_patch_series_file",
        type=Path,
        help="File containing null-separated patches originating from android-tools-static",
    )
    parser.add_argument(
        "base_repolink",
        help=(
            "A link to the repository. It is used to fill out the homepage, the vcs "
            "link (base_repoling + .git) and the issue tracker link (base_repoling + "
            "/issues)."
        ),
    )
    parser.add_argument(
        "repolink_format",
        help=(
            "A format string representing a permanent link to a file. Must contain "
            "the ${path} substitution. May contain the ${ref} substitution."
        ),
    )
    parser.add_argument(
        "--ref",
        help=(
            "Specify ${ref} for repolink_format argument. Unused if not used in "
            "repolink_format. If repolink_format requests ${ref} but it is not "
            "overriden, this script will try to retrieve the current git hash with "
            "git. If that is not successful, a warning is issued and sections "
            "requiring file links are ommited."
        ),
    )
    parser.add_argument(
        "uses_bundled_libusb",
        help="Is bundled libusb used?",
        choices=["true", "false"],
    )
    parser.add_argument("target_architecture", help="Target architecture")
    parser.add_argument(
        "github_runner_name_ver",
        help="Name of the GitHub runner used to build the project.",
    )
    parser.add_argument(
        "softprops_action_gh_release_version",
        help="Version of softprops/action-gh-release GitHub Action.",
    )
    parser.add_argument(
        "--color",
        choices=["always", "never", "auto"],
        default="auto",
        help=(
            "Display ANSI colors (currently for warnings only, overrides $NO_COLOR "
            "env variable, default: %(default)s)"
        ),
    )
