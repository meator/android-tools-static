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

"""Module storing internal purl keys."""

import enum
import typing

import proj_types


class PurlNames(enum.StrEnum):
    """Key type of purldb.

    Looking at the members of this enum will give you an overview of all the
    dependencies android-tools-static could have.

    Some other dependency databases in this SBOM generator can include conditional
    elements (dependencies which are used only in certain environments). This class is
    not conditional, since it is an enum.

    The resulting purldb will however not contain all members listed here.
    """

    android_tools_static = "main_project_placeholder"
    nmeum_android_tools = "pkg:github/nmeum/android-tools"
    msys2_android_tools = "pkg:msys2/mingw-w64-android-tools"

    pip_meson = "pkg:pip/meson"

    action_gh_release = "pkg:github/softprops/action-gh-release"

    github_runner = "pkg:generic/github-actions-runner"

    # NOTE: git submodule purls are not stored in purldb, they are stored separately
    #       (in a submodule database, which is an instance of SubmoduleInfo)

    #
    # Vendored git submodule dependencies
    #

    # The modules below require a vcs_url:
    # https://github.com/package-url/purl-spec/blob/main/types-doc/generic-definition.md
    # ags = android googlesource
    ags_core = "pkg:generic/platform/system/core"
    ags_extras = "pkg:generic/platform/system/extras"
    ags_selinux = "pkg:generic/platform/external/selinux"
    ags_f2fs_tools = "pkg:generic/platform/external/f2fs-tools"
    ags_e2fsprogs = "pkg:generic/platform/external/e2fsprogs"
    boringssl = "pkg:generic/boringssl"
    ags_mkbootimg = "pkg:generic/platform/system/tools/mkbootimg"
    ags_avb = "pkg:generic/platform/external/avb"
    ags_libbase = "pkg:generic/platform/system/libbase"
    ags_libziparchive = "pkg:generic/platform/system/libziparchive"
    ags_adb = "pkg:generic/platform/packages/modules/adb"
    ags_logging = "pkg:generic/platform/system/logging"
    # see comment above; Meson fmtlib is used instead of git submodule one
    # ags_fmtlib = "pkg:wrapdb/fmt"
    ags_libufdt = "pkg:generic/platform/system/libufdt"
    # Bundled version.
    libusb = "libusb_placeholder"

    #
    # Meson Wraps
    #
    wrap_fmt = "pkg:wrapdb/fmt"
    wrap_zlib = "pkg:wrapdb/zlib"
    wrap_google_brotli = "pkg:wrapdb/google-brotli"
    wrap_lz4 = "pkg:wrapdb/lz4"
    wrap_zstd = "pkg:wrapdb/zstd"
    # Meson wrap version.
    wrap_libusb = "pkg:wrapdb/libusb"
    wrap_gtest = "pkg:wrapdb/gtest"
    wrap_abseil_cpp = "pkg:wrapdb/abseil-cpp"
    wrap_protobuf = "pkg:wrapdb/protobuf"
    wrap_pcre2 = "pkg:wrapdb/pcre2"

    #
    # Windows specific dependencies
    #
    adbwinapi = "pkg:generic/AdbWinApi"
    windows = "pkg:microsoft/windows"
    msys2_meson = "msys2_meson_placeholder"
    msys2_gcc = "msys2_gcc_placeholder"
    msys2_cmake = "msys2_cmake_placeholder"
    msys2_nasm = "msys2_nasm_placeholder"
    setup_msys2 = "pkg:github/msys2/setup-msys2"

    #
    # Linux specific dependencies
    #
    alpine = "pkg:generic/alpine"
    alpine_meson = "pkg:apk/alpine/meson"
    alpine_gcc = "pkg:apk/alpine/gcc"
    alpine_gpp = "pkg:apk/alpine/g++"
    alpine_cmake = "pkg:apk/alpine/cmake"
    alpine_linux_headers = "pkg:apk/alpine/linux_headers"
    setup_alpine = "pkg:github/jirutka/setup-alpine"

    musl_cross_make = "pkg:github/richfelker/musl-cross-make"
    gcc_binutils = "pkg:generic/binutils"
    gcc_gcc = "pkg:generic/gcc"
    gcc_musl = "pkg:generic/musl"
    gcc_gmp = "pkg:generic/gmp"
    gcc_mpc = "pkg:generic/mpc"
    gcc_mpfr = "pkg:generic/mpfr"
    gcc_linux = "pkg:generic/linux"
    gcc_isl = "pkg:generic/isl"
    docker_setup_buildx = "pkg:github/docker/setup-buildx-action"
    docker_login = "pkg:github/docker/login-action"
    docker_metadata = "pkg:github/docker/metadata-action"
    docker_bake = "pkg:github/docker/bake-action"

    #
    # MacOS specific dependencies
    #
    macos = "pkg:generic/macos"
    brew_meson = "pkg:brew/meson"
    brew_cmake = "pkg:brew/cmake"
    apple_clang = "pkg:generic/apple_clang"
    apple_clangpp = "pkg:generic/apple_clang++"


PurlDB = typing.NewType("PurlDB", dict[PurlNames, proj_types.Purl])
