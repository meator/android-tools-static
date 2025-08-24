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

"""Alpine Linux (cross version) SBOM generator script."""

# https://cyclonedx.org/docs/1.6/json/

import argparse
import json
import os
import shutil
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
from alpine_native import AlpinePackageVersions
from cyclonedx.generators import Lifecycles
from cyclonedx.generic_component import (
    ComponentSupplier,
    ComponentType,
    ReferenceType,
)
from cyclonedx.util import Licenses
from purldb.generate import generate as purldb_mod_generate
from purldb.keys import PurlNames

_CrossVersionsSelf = typing.TypeVar("_CrossVersionsSelf", bound="_CrossVersions")


class _CrossVersions(typing.NamedTuple):
    alpine: str
    musl_cross_make: str
    binutils: str
    gcc: str
    musl: str
    gmp: str
    mpc: str
    mpfr: str
    linux: str
    isl: str
    setup_buildx_action: str
    login_action: str
    metadata_action: str
    bake_action: str

    @classmethod
    def read_root_version_file(cls: type[_CrossVersionsSelf]) -> _CrossVersionsSelf:
        with open("/version-info.json") as input:
            doc = json.load(input)
        return cls(
            alpine=doc["alpine"],
            musl_cross_make=doc["musl-cross-make"],
            binutils=doc["binutils"],
            gcc=doc["gcc"],
            musl=doc["musl"],
            gmp=doc["gmp"],
            mpc=doc["mpc"],
            mpfr=doc["mpfr"],
            linux=doc["linux"],
            isl=doc["isl"],
            setup_buildx_action=doc["docker/setup-buildx-action"],
            login_action=doc["docker/login-action"],
            metadata_action=doc["docker/metadata-action"],
            bake_action=doc["docker/bake-action"],
        )


if __name__ == "__main__":
    #
    # Load shared command line arguments and add Windows-specific ones.
    #
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    shared_arguments.add(parser)
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
    cross_versions = _CrossVersions.read_root_version_file()

    apk_versions = AlpinePackageVersions.from_apk()

    for purl, ver in (
        (PurlNames.alpine, cross_versions.alpine),
        (PurlNames.alpine_meson, apk_versions.meson),
        (PurlNames.alpine_gcc, apk_versions.gcc),
        # It is assumed that the version of gcc and g++ is identical.
        (PurlNames.alpine_gpp, apk_versions.gcc),
        (PurlNames.alpine_cmake, apk_versions.cmake),
        (PurlNames.alpine_linux_headers, apk_versions.linux_headers),
        (PurlNames.musl_cross_make, cross_versions.musl_cross_make),
        (PurlNames.docker_setup_buildx, cross_versions.setup_buildx_action),
        (PurlNames.docker_login, cross_versions.login_action),
        (PurlNames.docker_metadata, cross_versions.metadata_action),
        (PurlNames.docker_bake, cross_versions.bake_action),
        (PurlNames.gcc_binutils, cross_versions.binutils),
        (PurlNames.gcc_gcc, cross_versions.gcc),
        (PurlNames.gcc_musl, cross_versions.musl),
        (PurlNames.gcc_gmp, cross_versions.gmp),
        (PurlNames.gcc_mpc, cross_versions.mpc),
        (PurlNames.gcc_mpfr, cross_versions.mpfr),
        (PurlNames.gcc_linux, cross_versions.linux),
        (PurlNames.gcc_isl, cross_versions.isl),
    ):
        purldb[purl] = proj_types.Purl(f"{purl}@{ver}")
        pass

    alpine_supplier = ComponentSupplier(
        name="Alpine Linux official repository", url="https://www.alpinelinux.org/"
    )
    github_supplier = ComponentSupplier(name="GitHub, Inc.", url="https://github.com/")

    toolchain_components = [
        cyclonedx.generic_component.generate(
            name="binutils",
            version=cross_versions.binutils,
            c_type=ComponentType.library,
            ref=purldb[PurlNames.gcc_binutils],
            description=("binutils components of musl-cross-make gcc toolchain"),
        ),
        cyclonedx.generic_component.generate(
            name="gcc",
            version=cross_versions.gcc,
            c_type=ComponentType.library,
            ref=purldb[PurlNames.gcc_gcc],
            description=("gcc components of musl-cross-make gcc toolchain"),
        ),
        cyclonedx.generic_component.generate(
            name="musl",
            version=cross_versions.musl,
            c_type=ComponentType.library,
            ref=purldb[PurlNames.gcc_musl],
            description=("musl components of musl-cross-make gcc toolchain"),
        ),
        cyclonedx.generic_component.generate(
            name="gmp",
            version=cross_versions.gmp,
            c_type=ComponentType.library,
            ref=purldb[PurlNames.gcc_gmp],
            description=("gmp components of musl-cross-make gcc toolchain"),
        ),
        cyclonedx.generic_component.generate(
            name="mpc",
            version=cross_versions.mpc,
            c_type=ComponentType.library,
            ref=purldb[PurlNames.gcc_mpc],
            description=("mpc components of musl-cross-make gcc toolchain"),
        ),
        cyclonedx.generic_component.generate(
            name="mpfr",
            version=cross_versions.mpfr,
            c_type=ComponentType.library,
            ref=purldb[PurlNames.gcc_mpfr],
            description=("mpfr components of musl-cross-make gcc toolchain"),
        ),
        cyclonedx.generic_component.generate(
            name="linux",
            version=cross_versions.linux,
            c_type=ComponentType.library,
            ref=purldb[PurlNames.gcc_linux],
            description=("Linux headers components of musl-cross-make gcc toolchain"),
        ),
        cyclonedx.generic_component.generate(
            name="isl",
            version=cross_versions.isl,
            c_type=ComponentType.library,
            ref=purldb[PurlNames.gcc_isl],
            description=("isl components of musl-cross-make gcc toolchain"),
        ),
    ]

    musl_cross_make = cyclonedx.generic_component.generate(
        name="musl-cross-make GCC toolchain",
        version=cross_versions.musl_cross_make,
        c_type=ComponentType.application,
        ref=purldb[PurlNames.musl_cross_make],
        description="Primary toolchain used build android-tools-static for target architecture",
        references=[
            cyclonedx.generic_component.generate_reference(
                type=ReferenceType.website,
                url="https://github.com/richfelker/musl-cross-make",
            )
        ],
        components=toolchain_components,
    )

    cyclonedx.util.set_license(
        musl_cross_make,
        Licenses.MIT,
        "https://github.com/richfelker/musl-cross-make/blob/master/LICENSE",
    )

    docker_setup_buildx = cyclonedx.generic_component.generate(
        name="docker/setup-buildx-action",
        version=cross_versions.setup_buildx_action,
        c_type=ComponentType.library,
        ref=purldb[PurlNames.docker_setup_buildx],
        description=("GitHub Action used to setup Docker buildx environment."),
        supplier=github_supplier,
        references=[
            cyclonedx.generic_component.generate_reference(
                type=ReferenceType.website,
                url="https://github.com/docker/setup-buildx-action",
            )
        ],
    )
    docker_login = cyclonedx.generic_component.generate(
        name="docker/login-action",
        version=cross_versions.login_action,
        c_type=ComponentType.library,
        ref=purldb[PurlNames.docker_login],
        description=("GitHub Action used to login to GitHub Container Registry."),
        supplier=github_supplier,
        references=[
            cyclonedx.generic_component.generate_reference(
                type=ReferenceType.website,
                url="https://github.com/docker/login-action",
            )
        ],
    )
    docker_metadata = cyclonedx.generic_component.generate(
        name="docker/metadata-action",
        version=cross_versions.metadata_action,
        c_type=ComponentType.library,
        ref=purldb[PurlNames.docker_metadata],
        description=("GitHub Action used to handle Docker image metadata."),
        supplier=github_supplier,
        references=[
            cyclonedx.generic_component.generate_reference(
                type=ReferenceType.website,
                url="https://github.com/docker/metadata-action",
            )
        ],
    )
    docker_bake = cyclonedx.generic_component.generate(
        name="docker/bake-action",
        version=cross_versions.bake_action,
        c_type=ComponentType.library,
        ref=purldb[PurlNames.docker_bake],
        description=(
            "GitHub Action used build and publish Docker images containing "
            "musl-cross-make cross-compilers used to compile android-tools-static."
        ),
        supplier=github_supplier,
        references=[
            cyclonedx.generic_component.generate_reference(
                type=ReferenceType.website,
                url="https://github.com/docker/bake-action",
            )
        ],
    )

    for component, url in (
        (
            docker_setup_buildx,
            "https://github.com/docker/setup-buildx-action/blob/master/LICENSE",
        ),
        (docker_login, "https://github.com/docker/login-action/blob/master/LICENSE"),
        (
            docker_metadata,
            "https://github.com/docker/metadata-action/blob/master/LICENSE",
        ),
        (docker_bake, "https://github.com/docker/bake-action/blob/master/LICENSE"),
    ):
        cyclonedx.util.set_license(component, Licenses.APACHE, url)

    linux_components = [
        cyclonedx.generic_component.generate(
            name="Alpine Linux",
            version=cross_versions.alpine,
            c_type=ComponentType.operating_system,
            ref=purldb[PurlNames.alpine],
            supplier=ComponentSupplier(
                name="Docker Hub", url="https://hub.docker.com/"
            ),
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
            description="GNU Compiler Collection - native version",
            supplier=alpine_supplier,
            properties={"alpine_pkg_name": f"gcc-{apk_versions.gcc}"},
        ),
        cyclonedx.generic_component.generate(
            name="G++",
            version=apk_versions.gcc,
            c_type=ComponentType.application,
            ref=purldb[PurlNames.alpine_gpp],
            description="GNU Compiler Collection - C++ compiler, native version",
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
            description="Linux kernel headers - native version",
            supplier=alpine_supplier,
            properties={
                "alpine_pkg_name": f"linux-headers-{apk_versions.linux_headers}"
            },
        ),
        musl_cross_make,
        docker_setup_buildx,
        docker_login,
        docker_metadata,
        docker_bake,
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
                purldb[PurlNames.musl_cross_make],
                purldb[PurlNames.docker_setup_buildx],
                purldb[PurlNames.docker_login],
                purldb[PurlNames.docker_metadata],
                purldb[PurlNames.docker_bake],
            ],
        },
        {
            "ref": purldb[PurlNames.musl_cross_make],
            "dependsOn": [
                purldb[PurlNames.gcc_binutils],
                purldb[PurlNames.gcc_gcc],
                purldb[PurlNames.gcc_musl],
                purldb[PurlNames.gcc_gmp],
                purldb[PurlNames.gcc_mpc],
                purldb[PurlNames.gcc_mpfr],
                purldb[PurlNames.gcc_linux],
                purldb[PurlNames.gcc_isl],
            ],
        },
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
