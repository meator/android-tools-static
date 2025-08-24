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

"""MacOS SBOM generator script."""

# https://cyclonedx.org/docs/1.6/json/

import argparse
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import typing
import warnings
from pathlib import Path

import base
import base_versions
import cyclonedx.generic_component
import cyclonedx.util
import git.submodule_parsing
import high_level.document
import meson.depmf
import meson.introspect_compiler
import meson.wrap_info
import proj_types
import shared_arguments
from cyclonedx.generators import Lifecycles
from cyclonedx.generic_component import (
    ComponentSupplier,
    ComponentType,
)
from purldb.generate import generate as purldb_mod_generate
from purldb.keys import PurlNames

_BrewPackageVersionsSelf = typing.TypeVar(
    "_BrewPackageVersionsSelf", bound="BrewPackageVersions"
)


class BrewPackageVersions(typing.NamedTuple):
    """Versions of build dependencies provided by Homebrew."""

    meson: str
    cmake: str

    @classmethod
    def from_brew(cls: type[_BrewPackageVersionsSelf]) -> _BrewPackageVersionsSelf:
        """Get the currently installed versions of specified brew packages."""
        brew_exe = shutil.which("brew")
        if brew_exe is None:
            raise RuntimeError(
                "Couldn't find 'brew' executable! Are you running this script outside "
                "of MacOS?"
            )
        result = {}
        for pkg_name in ("meson", "cmake"):
            args = [brew_exe, "list", "--versions", pkg_name]
            proc = subprocess.run(
                args=args,
                text=True,
                capture_output=True,
                check=True,
            )
            if not proc.stdout.startswith(f"{pkg_name} "):
                raise RuntimeError(
                    f"Command `{shlex.join(args)}` produced unexpected output! "
                    f"Expected package name '{pkg_name}' on the first (and only) line "
                    f"of output.\n\n`{shlex.join(args)}` stdout:\n{proc.stdout}"
                )
            result[pkg_name] = proc.stdout.split(maxsplit=2)[1]
        return cls(**result)


if __name__ == "__main__":
    #
    # Load shared command line arguments and add Windows-specific ones.
    #
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    shared_arguments.add(parser)
    parser.add_argument("build_dir", type=Path, help="Path of the build directory")
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

    target = base.Target(args.target_architecture, base.TargetOS.MACOS)

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
    brew_versions = BrewPackageVersions.from_brew()

    meson_exe = shutil.which("meson")
    if meson_exe is None:
        sys.exit("Couldn't find 'meson' executable!")
    compilers = meson.introspect_compiler.get_compilers(meson_exe, args.build_dir)

    clang_version = compilers.host.c_compiler.version
    clangpp_version = compilers.host.cpp_compiler.version

    assert compilers.host.c_compiler.id == meson.introspect_compiler.CompilerID.clang
    assert compilers.host.cpp_compiler.id == meson.introspect_compiler.CompilerID.clang

    for purl, ver in (
        (PurlNames.macos, platform.mac_ver()[0]),
        (PurlNames.brew_meson, brew_versions.meson),
        (PurlNames.brew_cmake, brew_versions.cmake),
        (PurlNames.apple_clang, clang_version),
        (PurlNames.apple_clangpp, clangpp_version),
    ):
        purldb[purl] = proj_types.Purl(f"{purl}@{ver}")
        pass

    brew_supplier = ComponentSupplier(name="Homebrew", url="https://brew.sh/")

    macos_components = [
        cyclonedx.generic_component.generate(
            name="macOS",
            version=platform.mac_ver()[0],
            c_type=ComponentType.operating_system,
            ref=purldb[PurlNames.macos],
            description=("macOS operating system"),
            properties={"full_macos_version": platform.version()},
        ),
        cyclonedx.generic_component.generate(
            name="Meson",
            version=brew_versions.meson,
            c_type=ComponentType.application,
            ref=purldb[PurlNames.brew_meson],
            description="Meson build system",
            supplier=brew_supplier,
            properties={"brew_pkg_name": f"meson-{brew_versions.meson}"},
        ),
        cyclonedx.generic_component.generate(
            name="Apple clang",
            version=clang_version,
            c_type=ComponentType.application,
            ref=purldb[PurlNames.apple_clang],
            description="Apple version of LLVM clang",
            properties={"full_version": compilers.host.c_compiler.full_version},
        ),
        cyclonedx.generic_component.generate(
            name="Apple clang++",
            version=clangpp_version,
            c_type=ComponentType.application,
            ref=purldb[PurlNames.apple_clangpp],
            description="Apple version of LLVM clang++",
            properties={"full_version": compilers.host.cpp_compiler.full_version},
        ),
        cyclonedx.generic_component.generate(
            name="CMake",
            version=brew_versions.cmake,
            c_type=ComponentType.application,
            ref=purldb[PurlNames.brew_cmake],
            description="CMake build system",
            supplier=brew_supplier,
            properties={"brew_pkg_name": f"cmake-{brew_versions.cmake}"},
        ),
    ]

    document["components"].extend(macos_components)

    document["dependencies"] = [
        {
            "ref": purldb[PurlNames.android_tools_static],
            "dependsOn": [
                purldb[PurlNames.github_runner],
                purldb[PurlNames.action_gh_release],
                purldb[PurlNames.ags_core],
                purldb[PurlNames.ags_extras],
                # TODO: Is selinux used on macOS?
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
                purldb[PurlNames.macos],
                purldb[PurlNames.brew_meson],
                purldb[PurlNames.brew_cmake],
                purldb[PurlNames.apple_clang],
                purldb[PurlNames.apple_clangpp],
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
