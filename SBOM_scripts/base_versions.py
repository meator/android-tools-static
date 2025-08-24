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

"""Module for handling base_versions.ini."""

import configparser
import typing
from pathlib import Path


class BaseVersions(typing.NamedTuple):
    """Versions of base projects of android-tools-static."""

    nmeum_version: str
    msys2_version: str


def get_base_versions(source_dir: Path) -> BaseVersions:
    """Get the versions of base projects of android-tools-static.

    Arguments:
        source_dir: Path to the source directory.
    """
    config = configparser.ConfigParser()
    config.read(source_dir / "base_versions.ini")
    return BaseVersions(
        nmeum_version=config["base_versions"]["nmeum_version"],
        msys2_version=config["base_versions"]["msys2_version"],
    )
