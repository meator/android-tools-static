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

"""Module for obtaining compiler information from 'meson introspect'."""

import enum
import json
import subprocess
import typing
from pathlib import Path


class CompilerID(enum.StrEnum):
    """All compiler IDs known to Meson.

    This list was captured when Meson 1.8.3 was the latest version of Meson.
    """

    arm = "arm"
    armclang = "armclang"
    ccomp = "ccomp"
    ccrx = "ccrx"
    clang = "clang"
    clang_cl = "clang-cl"
    dmd = "dmd"
    emscripten = "emscripten"
    flang = "flang"
    g95 = "g95"
    gcc = "gcc"
    intel = "intel"
    intel_cl = "intel-cl"
    intel_llvm = "intel-llvm"
    intel_llvm_cl = "intel-llvm-cl"
    lcc = "lcc"
    llvm = "llvm"
    llvm_flang = "llvm-flang"
    mono = "mono"
    mwccarm = "mwccarm"
    mwcceppc = "mwcceppc"
    msvc = "msvc"
    nagfor = "nagfor"
    nvidia_hpc = "nvidia_hpc"
    nvcc = "nvcc"
    open64 = "open64"
    pathscale = "pathscale"
    pgi = "pgi"
    rustc = "rustc"
    sun = "sun"
    c2000 = "c2000"
    c6000 = "c6000"
    ti = "ti"
    valac = "valac"
    xc16 = "xc16"
    cython = "cython"
    nasm = "nasm"
    yasm = "yasm"
    ml = "ml"
    armasm = "armasm"
    mwasmarm = "mwasmarm"
    mwasmeppc = "mwasmeppc"
    tasking = "tasking"


def _get_compiler_id(name: str) -> CompilerID:
    try:
        return CompilerID(name)
    except ValueError:
        raise RuntimeError(
            f"Meson reported unknown compiler id '{name}'! This most likely means "
            "that you are using a newer version of Meson than anticipated which added "
            "support for compilers which weren't known at the time this subpackage of "
            "the SBOM generation framework was updated. The module which raised this "
            "exception will have to be updated."
        ) from None


class Compiler(typing.NamedTuple):
    """Info about a single C/C++ compiler."""

    id: CompilerID
    version: str
    full_version: str


class CompilerMachineInfo(typing.NamedTuple):
    """Info about C and C++ compilers in a host/build machine."""

    c_compiler: Compiler
    cpp_compiler: Compiler


class Compilers(typing.NamedTuple):
    """Info about C and C++ compilers used in both host and build machines."""

    host: CompilerMachineInfo
    build: CompilerMachineInfo


def get_compilers(meson_exe: str, build_dir: Path) -> Compilers:
    """Get info about the compilers used in a builddir."""
    args = [meson_exe, "introspect", "--compilers"]
    proc = subprocess.Popen(
        args=args,
        text=True,
        cwd=build_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Make mypy happy.
    assert proc.stdout is not None

    json_doc = json.load(proc.stdout)

    stderr = proc.communicate()[1]

    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, args, None, stderr)

    return Compilers(
        host=CompilerMachineInfo(
            c_compiler=Compiler(
                id=_get_compiler_id(json_doc["host"]["c"]["id"]),
                version=json_doc["host"]["c"]["version"],
                full_version=json_doc["host"]["c"]["full_version"],
            ),
            cpp_compiler=Compiler(
                id=_get_compiler_id(json_doc["host"]["cpp"]["id"]),
                version=json_doc["host"]["cpp"]["version"],
                full_version=json_doc["host"]["cpp"]["full_version"],
            ),
        ),
        build=CompilerMachineInfo(
            c_compiler=Compiler(
                id=_get_compiler_id(json_doc["build"]["c"]["id"]),
                version=json_doc["build"]["c"]["version"],
                full_version=json_doc["build"]["c"]["full_version"],
            ),
            cpp_compiler=Compiler(
                id=_get_compiler_id(json_doc["build"]["cpp"]["id"]),
                version=json_doc["build"]["cpp"]["version"],
                full_version=json_doc["build"]["cpp"]["full_version"],
            ),
        ),
    )
