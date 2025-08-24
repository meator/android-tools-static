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

"""Module used to generate GitHub Runner CycloneDX component."""

import sys

import cyclonedx.generic_component
import proj_types
from cyclonedx.generic_component import ComponentSupplier, ComponentType, ReferenceType
from purldb.keys import PurlDB, PurlNames


def get_runner(
    runner_name_ver_combo: str, purldb: PurlDB
) -> proj_types.CycloneComponent:
    """Get a CycloneDX component of the GitHub Runner used to build the project.

    Arguments:
        runner_name_ver_combo: Full name of the runner (including its version).
          examples: ubuntu-24.04, macos-14-xlarge... All runner names can be found at
          https://github.com/actions/runner-images
        purldb: purldb containing the PurlNames.github_runner key.
    """
    for runner in ("windows", "macos", "ubuntu"):
        if runner_name_ver_combo.startswith(runner + "-"):
            github_runner_name = runner
            github_runner_version = runner_name_ver_combo.removeprefix(f"{runner}-")
            break
    else:
        sys.exit(
            f"The GitHub runner '{runner_name_ver_combo}' has an unrecognized "
            "prefix. If it is a custom runner, you should know that this script "
            "currently supports official GitHub runners only (but adding support "
            "for it shouldn't be difficult)."
        )
    return cyclonedx.generic_component.generate(
        name=github_runner_name,
        version=github_runner_version,
        description=(
            "Official GitHub runner used to build the library. Tools provided by it "
            "by default may be used during the build."
        ),
        c_type=ComponentType.platform,
        ref=purldb[PurlNames.github_runner],
        supplier=ComponentSupplier(name="GitHub, Inc.", url="https://github.com/"),
        references=[
            cyclonedx.generic_component.generate_reference(
                type=ReferenceType.website,
                url="https://github.com/actions/runner-images",
            )
        ],
        properties={"github_runner_name": runner_name_ver_combo},
    )
