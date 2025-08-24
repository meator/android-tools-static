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

"""Windows SBOM generator script."""

# https://cyclonedx.org/docs/1.6/json/

import argparse
import configparser
import itertools
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import typing
import urllib.parse
import warnings
from pathlib import Path

import base
import base_versions
import cyclonedx.generators
import cyclonedx.generic_component
import cyclonedx.util
import git.submodule_parsing
import high_level.document
import meson.depmf
import meson.wrap_info
import proj_types
import shared_arguments
from cyclonedx.generic_component import (
    ComponentAuthor,
    ComponentSupplier,
    ComponentType,
    ReferenceType,
)
from cyclonedx.util import HashTypes, Licenses
from purldb.generate import generate as purldb_mod_generate
from purldb.keys import PurlDB, PurlNames


class _AdbWinApi_info(typing.NamedTuple):  # noqa: N801
    hash: str
    source_url: str


def _get_AdbWinApi_info(source_dir: Path) -> _AdbWinApi_info:  # noqa: N802
    """Return the SHA256SUM and source_url of currently used AdbWinApi dependency."""
    wrap = configparser.ConfigParser()
    wrap.read(source_dir / "subprojects/AdbWinApi.wrap")

    hash = wrap["wrap-file"]["source_hash"]

    assert re.fullmatch(r"[0-9a-f]{64}", hash) is not None

    return _AdbWinApi_info(hash=hash, source_url=wrap["wrap-file"]["source_url"])


def _get_AdbWinApi(  # noqa: N802
    source_dir: Path,
    purldb: PurlDB,
    adbwinapi_version: str,
    target: base.Target,
) -> proj_types.CycloneComponent:
    wrap = configparser.ConfigParser()
    wrap.read(source_dir / "subprojects/AdbWinApi.wrap")

    raw_url = wrap["wrap-file"]["source_url"]
    url = urllib.parse.urlsplit(raw_url)

    url_path = Path(url.path)
    zip_name = url_path.name

    assert zip_name.endswith(".zip")
    assert zip_name.startswith("AdbWinApi-")

    assert target.architecture in ("aarch64", "x86", "x86_64")

    sbom_name = (
        zip_name.removesuffix(".zip") + f"-{target.architecture}-sbom.cyclonedx.json"
    )

    url = url._replace(path=(url_path.parent / sbom_name).as_posix())

    sbom_link = urllib.parse.urlunsplit(url)

    adbwinapi_info = _get_AdbWinApi_info(source_dir)

    generate_reference = cyclonedx.generic_component.generate_reference

    distribution_reference = generate_reference(
        type=ReferenceType.distribution, url=adbwinapi_info.source_url
    )

    cyclonedx.util.set_hash(
        distribution_reference, HashTypes.SHA_256, adbwinapi_info.hash
    )

    result = cyclonedx.generic_component.generate(
        name="AdbWinApi",
        version=adbwinapi_version,
        description="Windows support libraries for android-tools",
        c_type=ComponentType.library,
        ref=purldb[PurlNames.adbwinapi],
        supplier=ComponentSupplier(name="GitHub, Inc.", url="https://github.com/"),
        author=ComponentAuthor(name="meator", email="meator.dev@gmail.com"),
        references=[
            generate_reference(type=ReferenceType.bom, url=sbom_link),
            generate_reference(
                type=ReferenceType.vcs, url="https://github.com/meator/AdbWinApi.git"
            ),
            generate_reference(
                type=ReferenceType.issue_tracker,
                url="https://github.com/meator/AdbWinApi/issues",
            ),
            generate_reference(
                type=ReferenceType.website, url="https://github.com/meator/AdbWinApi"
            ),
            distribution_reference,
        ],
    )

    cyclonedx.util.set_license(result, cyclonedx.util.Licenses.APACHE)
    cyclonedx.util.set_hash(result, HashTypes.SHA_256, adbwinapi_info.hash)

    return result


def _get_windows_version() -> str:
    try:
        import winreg
    except ModuleNotFoundError:
        sys.exit(
            "This script must be run on Windows! If you want to test it on other "
            "platforms, use the --fake-windows-version flag. Do not use SBOMs "
            "generated with this flag in production!"
        )
    # Use the version from platform module with the update revision added from the
    # registry.
    reg_key = winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
    )
    ubr, _ = winreg.QueryValueEx(reg_key, "UBR")
    winreg.CloseKey(reg_key)
    return f"{platform.version()}.{ubr}"


_Self = typing.TypeVar("_Self", bound="_MSYS2_package_versions")


class _MSYS2_package_versions(typing.NamedTuple):  # noqa: N801
    meson: str
    gcc: str
    cmake: str
    nasm: str

    @classmethod
    def from_pacman(  # noqa: D417
        cls: type[_Self],
        meson_pkg_name: str,
        gcc_pkg_name: str,
        cmake_pkg_name: str,
        nasm_pkg_name: str,
    ) -> _Self:
        """Get the currently installed versions of specified Pacman packages.

        This function works in MSYS2 only.

        Arguments:
            Names of the packages used.

        Returns:
            A mapping of package names from packages and their respective versions.
        """
        pkg_mapping = {
            meson_pkg_name: "meson",
            gcc_pkg_name: "gcc",
            cmake_pkg_name: "cmake",
            nasm_pkg_name: "nasm",
        }
        pacman_exe = shutil.which("pacman")
        if pacman_exe is None:
            raise RuntimeError(
                "Couldn't find 'pacman' executable! Are you running this script "
                "outside of MSYS2 or on non-Windows OS? If you want to test it on "
                "other platforms, use the --fake-windows-version flag. Do not use "
                "SBOMs generated with this flag in production!"
            )
        proc = subprocess.run(
            args=list(itertools.chain([pacman_exe, "-Q"], pkg_mapping.keys())),
            text=True,
            capture_output=True,
            check=True,
        )
        result = {}
        for keyver_line in proc.stdout.splitlines():
            pkgname, version = keyver_line.split()
            result[pkg_mapping[pkgname]] = version
        assert len(result) == len(pkg_mapping)
        assert all(name in result for name in pkg_mapping.values())
        return cls(**result)

    @classmethod
    def from_fake_version(cls: type[_Self], fake_version: str) -> _Self:
        """Construct the version tuple from a single incorrect version.

        This is useful when testing this script on non-Windows platforms.
        """
        return cls(*itertools.repeat(fake_version, len(cls._fields)))


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
        "--fake-windows-version",
        help=(
            "Fake the Windows version. Useful when testing this script on non-Windows "
            "hosts"
        ),
        action="store_true",
    )
    parser.add_argument(
        "meson_pkg_name",
        help="Name of the Meson MSYS2 package.",
    )
    parser.add_argument(
        "gcc_pkg_name",
        help="Name of the GCC MSYS2 package.",
    )
    parser.add_argument(
        "cmake_pkg_name",
        help="Name of the CMake MSYS2 package.",
    )
    parser.add_argument(
        "nasm_pkg_name",
        help="Name of the NASM MSYS2 package.",
    )
    parser.add_argument(
        "setup_msys2_version",
        help="Version of msys2/setup-msys2 GitHub Action.",
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

    target = base.Target(args.target_architecture, base.TargetOS.WINDOWS)

    #
    # Look for git.
    #
    git_path = shutil.which("git")
    if git_path is None:
        sys.exit("Couldn't find 'git' executable! Cannot proceed with SBOM generation.")

    #
    # Handle faking Windows versions on non-Windows hosts for testing.
    #
    Lifecycles = cyclonedx.generators.Lifecycles
    if args.fake_windows_version:
        windows_version = "invalid_version_this_SBOM_is_invalid"
        lifecycle = Lifecycles.design
        msys2_package_versions = _MSYS2_package_versions.from_fake_version(
            windows_version
        )
    else:
        windows_version = _get_windows_version()
        lifecycle = Lifecycles.build
        msys2_package_versions = _MSYS2_package_versions.from_pacman(
            meson_pkg_name=args.meson_pkg_name,
            gcc_pkg_name=args.gcc_pkg_name,
            cmake_pkg_name=args.cmake_pkg_name,
            nasm_pkg_name=args.nasm_pkg_name,
        )

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
        lifecycle,
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
    # Handle Windows-specific stuff.
    #
    adbwinapi_version = depmf_wrap_dict["AdbWinApi"].version

    assert adbwinapi_version is not None

    purldb[PurlNames.adbwinapi] = proj_types.Purl(
        f"{PurlNames.adbwinapi}@{adbwinapi_version}"
    )
    purldb[PurlNames.windows] = proj_types.Purl(
        f"{PurlNames.windows}@{windows_version}"
    )
    purldb[PurlNames.msys2_meson] = proj_types.Purl(
        f"pkg:msys2/{args.meson_pkg_name}@{msys2_package_versions.meson}"
    )
    purldb[PurlNames.msys2_gcc] = proj_types.Purl(
        f"pkg:msys2/{args.gcc_pkg_name}@{msys2_package_versions.gcc}"
    )
    purldb[PurlNames.msys2_cmake] = proj_types.Purl(
        f"pkg:msys2/{args.cmake_pkg_name}@{msys2_package_versions.cmake}"
    )
    purldb[PurlNames.msys2_nasm] = proj_types.Purl(
        f"pkg:msys2/{args.nasm_pkg_name}@{msys2_package_versions.nasm}"
    )
    purldb[PurlNames.setup_msys2] = proj_types.Purl(
        f"{PurlNames.setup_msys2}@{args.setup_msys2_version}"
    )

    msys2_supplier = ComponentSupplier(name="MSYS2", url="https://www.msys2.org/")

    setup_msys2 = cyclonedx.generic_component.generate(
        name="msys2/setup-msys2",
        version=args.setup_msys2_version,
        c_type=ComponentType.library,
        ref=purldb[PurlNames.setup_msys2],
        description=(
            "GitHub Action used to setup MSYS2 build environment and to install MSYS2 "
            "dependencies"
        ),
        supplier=ComponentSupplier(name="GitHub, Inc.", url="https://github.com/"),
        references=[
            cyclonedx.generic_component.generate_reference(
                type=ReferenceType.website, url="https://github.com/msys2/setup-msys2"
            )
        ],
    )
    cyclonedx.util.set_license(
        setup_msys2,
        Licenses.MIT,
        "https://github.com/msys2/setup-msys2/blob/main/LICENSE",
    )

    windows_components = [
        _get_AdbWinApi(source_dir, purldb, adbwinapi_version, target),
        cyclonedx.generic_component.generate(
            name="Microsoft Windows",
            version=windows_version,
            c_type=ComponentType.operating_system,
            ref=purldb[PurlNames.windows],
        ),
        cyclonedx.generic_component.generate(
            name="Meson",
            version=msys2_package_versions.meson,
            c_type=ComponentType.application,
            ref=purldb[PurlNames.msys2_meson],
            description="Meson build system",
            supplier=msys2_supplier,
            properties={
                "msys2_pkg_name": (
                    f"{args.meson_pkg_name}-{msys2_package_versions.meson}"
                )
            },
        ),
        cyclonedx.generic_component.generate(
            name="GCC",
            version=msys2_package_versions.gcc,
            c_type=ComponentType.application,
            ref=purldb[PurlNames.msys2_gcc],
            description="GNU Compiler Collection with MSYS2 additions",
            supplier=msys2_supplier,
            properties={
                "msys2_pkg_name": f"{args.gcc_pkg_name}-{msys2_package_versions.gcc}"
            },
        ),
        cyclonedx.generic_component.generate(
            name="CMake",
            version=msys2_package_versions.cmake,
            c_type=ComponentType.application,
            ref=purldb[PurlNames.msys2_cmake],
            description="CMake build system",
            supplier=msys2_supplier,
            properties={
                "msys2_pkg_name": (
                    f"{args.cmake_pkg_name}-{msys2_package_versions.cmake}"
                )
            },
        ),
        cyclonedx.generic_component.generate(
            name="NASM",
            version=msys2_package_versions.nasm,
            c_type=ComponentType.application,
            ref=purldb[PurlNames.msys2_nasm],
            description="Netwide Assembler",
            supplier=msys2_supplier,
            properties={
                "msys2_pkg_name": f"{args.nasm_pkg_name}-{msys2_package_versions.nasm}"
            },
        ),
        setup_msys2,
    ]

    document["components"].extend(windows_components)

    document["dependencies"] = [
        {
            "ref": purldb[PurlNames.android_tools_static],
            "dependsOn": [
                purldb[PurlNames.github_runner],
                purldb[PurlNames.action_gh_release],
                purldb[PurlNames.ags_core],
                purldb[PurlNames.ags_extras],
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
                purldb[PurlNames.adbwinapi],
                purldb[PurlNames.windows],
                purldb[PurlNames.msys2_meson],
                purldb[PurlNames.msys2_gcc],
                purldb[PurlNames.msys2_cmake],
                purldb[PurlNames.msys2_nasm],
                purldb[PurlNames.setup_msys2],
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
