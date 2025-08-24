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

"""Module for parsing depmf.json dependency manifest files."""

import json
import typing
from pathlib import Path


class SubprojectInfo(typing.NamedTuple):
    """Info about all subproject used.

    The primary project (android-tools-static) is also considered a subproject for the
    purposes of depmf.json parsing.
    """

    spdx_license_identifier: str | None
    version: str | None


def get_subproject_data(depmf_path: Path) -> dict[str, SubprojectInfo]:
    """Get a list of subprojects used including their metadata from depmf.json.

    The primary project (android-tools-static) is also considered a subproject for the
    purposes of depmf.json parsing.

    Arguments:
        depmf_path: Path to depmf.json file.

    Returns:
        A dictionary whose keys are subproject names (determined by their project()
        function call, these names may not correspond with the .wrap file names) and
        whose values are SubprojectInfo.
    """
    with open(depmf_path) as input:
        depmf = json.load(input)

    if "type" not in depmf:
        raise RuntimeError(
            f"The input file '{depmf_path}' is not a Meson dependency manifest file! "
            "It is missing the 'type' top-level key!"
        )
    if depmf["type"] != "dependency manifest":
        raise RuntimeError(
            f"The input file '{depmf_path}' is not a Meson dependency manifest file! "
            "Its 'type' top-level key is not 'dependency manifest'!"
        )
    if int(depmf["version"].split(".", maxsplit=1)[0]) != 1:
        raise RuntimeError(
            f"The input file '{depmf_path}' is not a compatible Meson dependency "
            "manifest file! Expected Meson dependency manifest with major version "
            f"'1', got version '{depmf['version']}'."
        )

    result = {}

    for subproject_name, info in depmf["projects"].items():
        version = info["version"] if info["version"] != "undefined" else None

        assert len(info["license"]) == 1

        spdx_license = info["license"][0] if info["license"][0] != "unknown" else None

        result[subproject_name] = SubprojectInfo(
            spdx_license_identifier=spdx_license,
            version=version,
        )

    return result
