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

"""Save the versions of components used into a machine-readable file.

This script is run from each Alpine musl cross-compiler Dockerfile to store info about
the cross-compiler into the image itself. This info is also stored in the resulting
container's labels, but Docker labels can be harder to work with from inside the
container.
"""

import argparse
import json
import sys
import typing


class _VersionInfo(typing.NamedTuple):
    version_flag_base: str


if __name__ == "__main__":
    _VI = _VersionInfo
    result_mapping = {
        "alpine": _VI("alpine"),
        "musl-cross-make": _VI("musl-cross-make"),
        "binutils": _VI("binutils"),
        "gcc": _VI("gcc"),
        "musl": _VI("musl"),
        "gmp": _VI("gmp"),
        "mpc": _VI("mpc"),
        "mpfr": _VI("mpfr"),
        "linux": _VI("linux"),
        "isl": _VI("isl"),
        "docker/setup-buildx-action": _VI("setup-buildx-action"),
        "docker/login-action": _VI("login-action"),
        "docker/metadata-action": _VI("metadata-action"),
        "docker/bake-action": _VI("bake-action"),
    }

    parser = argparse.ArgumentParser()

    for key_name, flag_base in result_mapping.items():
        parser.add_argument(
            f"--{flag_base.version_flag_base}-version", required=True, dest=key_name
        )

    args = parser.parse_args()

    result = {}

    for key_name, flag_base in result_mapping.items():
        version = getattr(args, key_name)
        if not version:
            sys.exit(
                f"Flag --{flag_base.version_flag_base}-version must not have empty "
                "version!"
            )
        result[key_name] = version

    json.dump(result, sys.stdout)
