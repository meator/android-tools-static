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

"""Module combining several sources of info to get all available Meson Wrap info."""

import enum
import re
import typing
from pathlib import Path

import base
from purldb.keys import PurlNames

from . import depmf, wrap_parse


class _KnownWrapInfo(typing.NamedTuple):
    purl: PurlNames
    description: str


class KnownWraps(enum.StrEnum):
    """Enum of all Meson Wraps known to this SBOM generation module.

    If any of these wraps are missing (except for libusb, which may or may not be
    bundled) or if there are any wraps which aren't in this list, SBOM generation will
    not proceed.
    """

    fmt = "fmt"
    zlib = "zlib"
    google_brotli = "google-brotli"
    lz4 = "lz4"
    zstd = "zstd"
    libusb = "libusb"
    gtest = "gtest"
    abseil_cpp = "abseil-cpp"
    protobuf = "protobuf"
    pcre2 = "pcre2"


class MesonWrapInfo(typing.NamedTuple):
    """Complete info about a Meson Wrap."""

    version: str
    purl: PurlNames
    spdx_expression: str | None
    wrapdb_version: str
    description: str


def get_wraps_info(
    meson_depmf: dict[str, depmf.SubprojectInfo],
    source_dir: Path,
    target: base.Target,
) -> dict[str, MesonWrapInfo]:
    """Get info about all Meson Wraps used in the build.

    Arguments:
        meson_depmf: Processed contents of depmf.json file (coming from meson.depmf
          module).
        source_dir: Path to the source directory.
        target: Target system info. This is used when working with AdbWinApi, which is
          Windows-only.

    Returns:
        A dictionary with the wrap names (the name of the wrap is derived from the
        string passed to its project() function in Meson) and info about them.

        The values notably include both the "clean" versions of the wrap and the wrapdb
        versions of the wrap. It is guaranteed that these two versions will correspond
        with each other (the wrapdb_version will contain an additional revision
        suffix).
    """
    _KWI = _KnownWrapInfo  # noqa: N806

    known_wraps = {
        KnownWraps.fmt: _KWI(PurlNames.wrap_fmt, "Modern formatting library"),
        KnownWraps.zlib: _KWI(
            PurlNames.wrap_zlib, "General purpose data compression library"
        ),
        KnownWraps.google_brotli: _KWI(
            PurlNames.wrap_google_brotli,
            "Generic-purpose lossless compression algorithm",
        ),
        KnownWraps.lz4: _KWI(PurlNames.wrap_lz4, "Lossless compression algorithm"),
        KnownWraps.zstd: _KWI(
            PurlNames.wrap_zstd, "Fast lossless compression algorithm"
        ),
        KnownWraps.libusb: _KWI(
            PurlNames.wrap_libusb, "Cross-platform library to access USB devices"
        ),
        KnownWraps.gtest: _KWI(
            PurlNames.wrap_gtest, "Google Testing and Mocking Framework"
        ),
        KnownWraps.abseil_cpp: _KWI(
            PurlNames.wrap_abseil_cpp,
            "Open-source collection of C++ code (compliant to C++17) designed to "
            "augment the C++ standard library",
        ),
        KnownWraps.protobuf: _KWI(
            PurlNames.wrap_protobuf, "Google's data interchange format"
        ),
        KnownWraps.pcre2: _KWI(
            PurlNames.wrap_pcre2,
            "Set of C functions that implement regular expression pattern matching",
        ),
    }

    used_bundled_libusb = "libusb" in meson_depmf

    # This should only contain the Wraps used without the primary project (which is
    # also included in the full output of get_subproject_data), without BoringSSL,
    # for which Meson won't give any useful info and which isn't a Wrap from wrapdb and
    # without AdbWinApi, which is a conditional Windows-only subproject, which also
    # doesn't come from the wrapdb.
    filtered_subproject_data = {
        key: value
        for key, value in meson_depmf.items()
        if key not in ("android-tools-static", "BoringSSL")
    }

    if target.operating_system == base.TargetOS.WINDOWS:
        if "AdbWinApi" not in filtered_subproject_data:
            raise RuntimeError(
                "'AdbWinApi' is not present in the supplied depmf.json! You are "
                "probably using the wrong script entrypoint to build the SBOM (a "
                "Windows one instead of a Linux or MacOS one)."
            )
        del filtered_subproject_data["AdbWinApi"]

    known_wrap_names = {str(name) for name in KnownWraps.__members__.values()}

    missing_keys = known_wrap_names - filtered_subproject_data.keys()
    added_keys = filtered_subproject_data.keys() - known_wrap_names

    if not used_bundled_libusb:
        # If we're using libusb from a wrap, disable logic for vendored libusb (since
        # it isn't used).
        missing_keys.discard("libusb")

    if missing_keys or added_keys:
        error_description = ""
        if missing_keys:
            error_description = "missing expected Meson Wraps: " + ", ".join(
                missing_keys
            )
        if missing_keys and added_keys:
            error_description += "; "
        if added_keys:
            error_description += "extra unexpected Meson Wraps: " + ", ".join(
                added_keys
            )
        raise RuntimeError(
            "Parsed info about unknown Meson Wraps! If you have added or removed any "
            "wraps, you'll have to update the purldb of the SBOM generator and the "
            f"function which raised this exception ({error_description})."
        )

    result = {}

    wrap_name2key_name = {
        str(value): value for value in KnownWraps.__members__.values()
    }

    for wrap_name, wrap_info in filtered_subproject_data.items():
        wrap_path = source_dir / "subprojects" / (wrap_name + ".wrap")
        wrapdb_version = wrap_parse.get_wrap_info(wrap_path).wrapdb_version

        assert wrap_info.version is not None
        # Make sure that the version reported in depmf.json and the wrapdb_version in
        # the wrapfile match.
        # The logic below handles the revision number suffix, which is only in
        # wrapdb_version.
        if not wrapdb_version.startswith(wrap_info.version) or not re.fullmatch(
            r"-\d+", wrapdb_version.removeprefix(wrap_info.version)
        ):
            raise RuntimeError(
                f"Found non-matching versions of the '{wrap_name}' dependency wrap! "
                "The depmf.json input file (generated by Meson itself; this version "
                f"should be more authoritative) reports '{wrap_info.version}' (the "
                f"revision suffix is ignored), whereas the Wrap file '{wrap_path}' "
                f"reports version '{wrapdb_version}'"
            )
        known_wrap_key = wrap_name2key_name[wrap_name]
        result[wrap_name] = MesonWrapInfo(
            version=wrap_info.version,
            purl=known_wraps[known_wrap_key].purl,
            spdx_expression=wrap_info.spdx_license_identifier,
            wrapdb_version=wrapdb_version,
            description=known_wraps[known_wrap_key].description,
        )

    return result
