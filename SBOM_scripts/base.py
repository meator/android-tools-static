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

"""Things that didn't fit anywhere else."""

# https://cyclonedx.org/docs/1.6/json/

import datetime
import enum
import sys
import warnings

# enum.StrEnum requires 3.11
if sys.version_info[0] != 3 or sys.version_info[1] < 11:
    sys.exit("This script requires Python version >=3.11")


def _generate_timestamp() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


class TargetOS(enum.StrEnum):
    """Target OS types supported by Target class."""

    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"


class TargetEndian(enum.Enum):
    """Target endian types supported by Target class.

    Endian is assumed to be little during SBOM generation, since android-tools
    currently doesn't support big endian systems. See the top of the root meson.build
    file for more info.
    """

    LITTLE = enum.auto()
    BIG = enum.auto()


def ansi_warning_format(message, category, filename, lineno, line=None) -> str:  # type: ignore
    """Warnings module compatible formatter which prints category in bold yellow."""
    return f"{filename}:{lineno}: \033[1;33m{category.__name__}\033[0m: {message}\n"


class Target:
    """Helper class documenting target (or host machine in Meson's terms) system."""

    def __init__(self, architecture: str, operating_system: TargetOS):
        """Initialize Target.

        Endian is assumed to be little, since android-tools currently doesn't support
        big endian systems. See the top of the root meson.build file for more info.

        Arguments:
            architecture: One of CPU families recognized by Meson
              (https://mesonbuild.com/Reference-tables.html#cpu-families). A warning is
              issued when the argument is not in the table (or if the internal copy
              of the table contained in this function is outdated).
            operating_system: Target operating system.
        """
        if architecture not in (
            "aarch64",
            "alpha",
            "arc",
            "arm",
            "avr",
            "c2000",
            "c6000",
            "csky",
            "dspic",
            "e2k",
            "ft32",
            "ia64",
            "loongarch64",
            "m68k",
            "microblaze",
            "mips",
            "mips64",
            "msp430",
            "parisc",
            "pic24",
            "ppc",
            "ppc64",
            "riscv32",
            "riscv64",
            "rl78",
            "rx",
            "s390",
            "s390x",
            "sh4",
            "sparc",
            "sparc64",
            "sw_64",
            "wasm32",
            "wasm64",
            "x86",
            "x86_64",
            "tricore",
        ):
            warnings.warn(
                (
                    f"Architecture '{architecture}' is not one of the recognized "
                    "architectures"
                ),
                stacklevel=2,
            )
        self._architecture = architecture
        self._operating_system = operating_system
        # used in props()
        self._props = [
            {
                "name": "target.architecture",
                "value": self._architecture,
            },
            {
                "name": "target.endian",
                "value": "little",
            },
            {
                "name": "target.os",
                "value": str(self._operating_system),
            },
        ]

    def __repr__(self) -> str:  # noqa: D105
        return (
            f"Target(architecture={self._architecture!r}, "
            f"operating_system={self._operating_system.__class__.__name__}."
            f"{self._operating_system.name})"
        )

    @property
    def architecture(self) -> str:
        """Get target/host machine architecture."""
        return self._architecture

    @property
    def endian(self) -> TargetEndian:
        """Get target/host machine endian."""
        return TargetEndian.LITTLE

    @property
    def operating_system(self) -> str:
        """Get target/host machine OS."""
        return self._operating_system

    def props(self) -> list[dict[str, str]]:
        """Get "standard" CycloneDX property pairs.

        The return value of this function can be appended to the "properties" key of a
        CycloneDX component to mark its target properties.

        The non-standard "target.architecture", "target.endian" and "target.os" keys
        are used. The same keys are also used in AdbWinApi.
        """
        return self._props
