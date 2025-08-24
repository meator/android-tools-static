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

"""Alpine Linux (native version) SBOM generator script."""

# https://cyclonedx.org/docs/1.6/json/

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import typing
import warnings

import base
import base_versions
import cyclonedx.generic_component
import cyclonedx.util
import git.submodule_parsing
import high_level.document
import meson.depmf
import meson.wrap_info
import proj_types
import shared_arguments
from cyclonedx.generators import Lifecycles
from cyclonedx.generic_component import (
    ComponentSupplier,
    ComponentType,
    ReferenceType,
)
from cyclonedx.util import Licenses
from purldb.generate import generate as purldb_mod_generate
from purldb.keys import PurlNames

_AlpinePackageVersionsSelf = typing.TypeVar(
    "_AlpinePackageVersionsSelf", bound="AlpinePackageVersions"
)


class AlpinePackageVersions(typing.NamedTuple):
    """Versions of build dependencies provided by Alpine Linux repositories.

    This class is also used in alpine_cross.py.
    """

    meson: str
    gcc: str
    cmake: str
    linux_headers: str

    @classmethod
    def from_apk(cls: type[_AlpinePackageVersionsSelf]) -> _AlpinePackageVersionsSelf:
        """Get the currently installed versions of specified Apk packages.

        This function works in apk-based Linux distros only.
        """
        apk_exe = shutil.which("apk")
        if apk_exe is None:
            raise RuntimeError(
                "Couldn't find 'apk' executable! Are you running this script outside "
                "of Alpine Linux?"
            )
        result = {}
        for key_name, pkg_name in (
            ("meson", "meson"),
            ("gcc", "gcc"),
            ("cmake", "cmake"),
            ("linux_headers", "linux-headers"),
        ):
            args = [apk_exe, "list", "--installed", pkg_name]
            proc = subprocess.run(
                args=args,
                text=True,
                capture_output=True,
                check=True,
            )
            if not proc.stdout.startswith(f"{pkg_name}-"):
                raise RuntimeError(
                    f"Command `{shlex.join(args)}` produced unexpected output! "
                    f"Expected pkgver of '{pkg_name}' on the first (and only) line of "
                    f"output.\n\n`{shlex.join(args)}` stdout:\n{proc.stdout}"
                )
            result[key_name] = proc.stdout.split(maxsplit=1)[0].removeprefix(
                f"{pkg_name}-"
            )
        return cls(**result)


def _get_alpine_release() -> str:
    """Get the currently running version of Alpine Linux."""
    with open("/etc/alpine-release") as input:
        return input.read().strip()


if __name__ == "__main__":
    #
    # Load shared command line arguments and add Windows-specific ones.
    #
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    shared_arguments.add(parser)
    parser.add_argument(
        "setup_alpine_version",
        help="Version of jirutka/setup-alpine GitHub Action.",
    )
    args = parser.parse_args()

    #
    # Preliminary command line argument processing.
    #
    source_dir = args.source_dir

    depmf_wrap_dict = meson.depmf.get_subproject_data(args.meson_depmf_file)

    # Infer some info from the depmf.json file.
    project_version = depmf_wrap_dict["android-tools-static"].version
    uses_bundled_libusb = args.uses_bundled_libusb == "true"

    assert project_version is not None

    match args.color:
        case "always":
            color = True
        case "never":
            color = False
        case "auto":
            # https://no-color.org/
            if "NO_COLOR" in os.environ and len(os.environ["NO_COLOR"]) != 0:
                color = False
            else:
                color = sys.stderr.isatty()
        case _:
            sys.exit(
                f"Unknown color value '{args.color}'! This is likely a bug in the "
                "script"
            )

    if color:
        warnings.formatwarning = base.ansi_warning_format

    target = base.Target(args.target_architecture, base.TargetOS.LINUX)

    #
    # Look for git.
    #
    git_path = shutil.which("git")
    if git_path is None:
        sys.exit("Couldn't find 'git' executable! Cannot proceed with SBOM generation.")

    #
    # Process input from various places.
    #
    base_vers = base_versions.get_base_versions(source_dir)

    repo_link = high_level.document.handle_repolink(
        args.repolink_format, args.ref, git_path, source_dir
    )

    submodule_info = git.submodule_parsing.read_submodule_info(
        source_dir, git_path, uses_bundled_libusb, target
    )

    wraps = meson.wrap_info.get_wraps_info(depmf_wrap_dict, source_dir, target)

    #
    # Assemble the input into processed components shared across all SBOM entrypoint
    # scripts.
    #
    purldb = purldb_mod_generate(
        args.purl,
        project_version,
        base_vers.nmeum_version,
        base_vers.msys2_version,
        submodule_info,
        wraps,
        args.github_runner_name_ver,
        args.softprops_action_gh_release_version,
    )

    document = high_level.document.get_base_document(
        source_dir,
        purldb,
        git_path,
        Lifecycles.build,
        repo_link,
        base_vers.nmeum_version,
        base_vers.msys2_version,
        args.github_runner_name_ver,
        args.softprops_action_gh_release_version,
        args.base_repolink,
        args.nmeum_patch_series_file,
        args.added_patch_series_file,
        submodule_info,
        wraps,
        depmf_wrap_dict,
        target,
    )

    #
    # Handle Linux-specific stuff.
    #
    alpine_version = _get_alpine_release()

    apk_versions = AlpinePackageVersions.from_apk()

    for purl, ver in (
        (PurlNames.alpine, alpine_version),
        (PurlNames.alpine_meson, apk_versions.meson),
        (PurlNames.alpine_gcc, apk_versions.gcc),
        # It is assumed that the version of gcc and g++ is identical.
        (PurlNames.alpine_gpp, apk_versions.gcc),
        (PurlNames.alpine_cmake, apk_versions.cmake),
        (PurlNames.alpine_linux_headers, apk_versions.linux_headers),
        (PurlNames.setup_alpine, args.setup_alpine_version),
    ):
        purldb[purl] = proj_types.Purl(f"{purl}@{ver}")
        pass

    alpine_supplier = ComponentSupplier(
        name="Alpine Linux official repository", url="https://www.alpinelinux.org/"
    )

    setup_alpine = cyclonedx.generic_component.generate(
        name="jirutka/setup-alpine",
        version=args.setup_alpine_version,
        c_type=ComponentType.library,
        ref=purldb[PurlNames.setup_alpine],
        description=(
            "GitHub Action used to setup Alpine Linux and to install MSYS2 "
            "dependencies"
        ),
        supplier=ComponentSupplier(name="GitHub, Inc.", url="https://github.com/"),
        references=[
            cyclonedx.generic_component.generate_reference(
                type=ReferenceType.website,
                url="https://github.com/jirutka/setup-alpine",
            )
        ],
    )
    cyclonedx.util.set_license(
        setup_alpine,
        Licenses.MIT,
        "https://github.com/jirutka/setup-alpine/blob/master/LICENSE",
    )

    linux_components = [
        cyclonedx.generic_component.generate(
            name="Alpine Linux",
            version=alpine_version,
            c_type=ComponentType.operating_system,
            ref=purldb[PurlNames.alpine],
            description=(
                "Stable version of Alpine Linux used to build android-tools-static"
            ),
        ),
        cyclonedx.generic_component.generate(
            name="Meson",
            version=apk_versions.meson,
            c_type=ComponentType.application,
            ref=purldb[PurlNames.alpine_meson],
            description="Meson build system",
            supplier=alpine_supplier,
            properties={"alpine_pkg_name": f"meson-{apk_versions.meson}"},
        ),
        cyclonedx.generic_component.generate(
            name="GCC",
            version=apk_versions.gcc,
            c_type=ComponentType.application,
            ref=purldb[PurlNames.alpine_gcc],
            description="GNU Compiler Collection",
            supplier=alpine_supplier,
            properties={"alpine_pkg_name": f"gcc-{apk_versions.gcc}"},
        ),
        cyclonedx.generic_component.generate(
            name="G++",
            version=apk_versions.gcc,
            c_type=ComponentType.application,
            ref=purldb[PurlNames.alpine_gpp],
            description="GNU Compiler Collection - C++ compiler",
            supplier=alpine_supplier,
            properties={"alpine_pkg_name": f"g++-{apk_versions.gcc}"},
        ),
        cyclonedx.generic_component.generate(
            name="CMake",
            version=apk_versions.cmake,
            c_type=ComponentType.application,
            ref=purldb[PurlNames.alpine_cmake],
            description="CMake build system",
            supplier=alpine_supplier,
            properties={"alpine_pkg_name": f"cmake-{apk_versions.cmake}"},
        ),
        cyclonedx.generic_component.generate(
            name="linux-headers",
            version=apk_versions.linux_headers,
            c_type=ComponentType.library,
            ref=purldb[PurlNames.alpine_linux_headers],
            description="Linux kernel headers",
            supplier=alpine_supplier,
            properties={
                "alpine_pkg_name": f"linux-headers-{apk_versions.linux_headers}"
            },
        ),
        setup_alpine,
    ]

    document["components"].extend(linux_components)

    document["dependencies"] = [
        {
            "ref": purldb[PurlNames.android_tools_static],
            "dependsOn": [
                purldb[PurlNames.github_runner],
                purldb[PurlNames.action_gh_release],
                purldb[PurlNames.ags_core],
                purldb[PurlNames.ags_extras],
                purldb[PurlNames.ags_selinux],
                # purldb[PurlNames.ags_f2fs_tools]
                # purldb[PurlNames.ags_e2fsprogs]
                purldb[PurlNames.boringssl],
                purldb[PurlNames.ags_mkbootimg],
                purldb[PurlNames.ags_avb],
                purldb[PurlNames.ags_libbase],
                purldb[PurlNames.ags_libziparchive],
                purldb[PurlNames.ags_adb],
                purldb[PurlNames.ags_logging],
                # purldb[PurlNames.ags_libufdt]
                purldb[PurlNames.wrap_fmt],
                purldb[PurlNames.wrap_zlib],
                purldb[PurlNames.wrap_google_brotli],
                purldb[PurlNames.wrap_lz4],
                purldb[PurlNames.wrap_zstd],
                purldb[PurlNames.wrap_gtest],
                purldb[PurlNames.wrap_abseil_cpp],
                purldb[PurlNames.wrap_protobuf],
                purldb[PurlNames.wrap_pcre2],
                purldb[PurlNames.alpine],
                purldb[PurlNames.alpine_meson],
                purldb[PurlNames.alpine_gcc],
                purldb[PurlNames.alpine_gpp],
                purldb[PurlNames.alpine_cmake],
                purldb[PurlNames.alpine_linux_headers],
                purldb[PurlNames.setup_alpine],
            ],
        }
    ]

    dependsOn = document["dependencies"][0]["dependsOn"]  # noqa: N816

    if uses_bundled_libusb:
        dependsOn.append(purldb[PurlNames.libusb])
    else:
        dependsOn.append(purldb[PurlNames.wrap_libusb])

    try:
        json.dump(document, sys.stdout)
    except OSError as exc:
        sys.exit(str(exc))
