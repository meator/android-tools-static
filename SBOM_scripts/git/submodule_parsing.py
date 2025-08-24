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

"""Module used to parse and return info about git submodules used."""

import configparser
import shlex
import subprocess
import typing
import urllib.parse
from pathlib import Path

import base


class ModuleInfo(typing.NamedTuple):
    """Info about a git submodule."""

    pinned_hash: str
    name: str
    base_repository: str
    url: str


class SubmoduleInfo(typing.NamedTuple):
    """Named tuple storing info about all git modules.

    boringssl is a Meson Wrap, but it is a git module in original nmeum/android-tools
    and the wrap retrieves it by hash, so storing it is still relevant.
    """

    # The values below should be kept up to date with the read_submodule_info()
    # function below.

    core: ModuleInfo
    extras: ModuleInfo
    # selinux isn't used on Windows
    selinux: ModuleInfo | None
    boringssl: ModuleInfo
    mkbootimg: ModuleInfo
    # TODO: Is avb used?
    avb: ModuleInfo
    libbase: ModuleInfo
    libziparchive: ModuleInfo
    adb: ModuleInfo
    logging: ModuleInfo
    # Meson uses Wrap fmtlib
    # fmtlib: ModuleInfo
    # If bundled libusb is used, this will have a non-None value.
    libusb: ModuleInfo | None
    # f2fs is currently not implemented
    f2fs_tools: None = None
    # e2fsprogs is currently not implemented
    e2fsprogs: None = None
    # libufdt is currently not implemented
    libufdt: None = None


def read_submodule_info(
    source_dir: Path, git_exe: str, use_bundled_libusb: bool, target: base.Target
) -> SubmoduleInfo:
    """Read submodule info by executing git and return SubmoduleInfo.

    Arguments:
        source_dir: Path to the root source directory.
        git_exe: Path to the git executable.
        use_bundled_libusb: Is bundled libusb used? If yes, include it in returned
          result.
        target: Target info. Some submodules aren't used on Windows to give an example.
    """
    args = [
        git_exe,
        "ls-tree",
        "HEAD",
        "-z",
        "--format=%(objecttype)%(objectname)%(path)",
    ]
    proc = subprocess.run(
        args=args, capture_output=True, text=True, cwd=source_dir / "vendor"
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"`{shlex.join(args)}` exited with exit status {proc.returncode}!\n\n"
            f"stderr:\n{proc.stderr}"
        )
    file_lines = proc.stdout.split("\0")

    hashes = {}

    for line in file_lines:
        if not line.startswith("commit"):
            continue
        # Sample line:
        # commitce9ea51f30f69f7560db692f7cb4d5d5502c3653adb
        hashes[line[46:]] = line[6:46]

    gitmodules = configparser.ConfigParser()
    gitmodules.read(source_dir / ".gitmodules")

    result = {}

    for section_name, section in gitmodules.items():
        if section_name == configparser.DEFAULTSECT:
            continue
        submodule_path = Path(section["path"])
        submodule_name = submodule_path.name
        submodule_url = section["url"]
        submodule_processed_url = urllib.parse.urlsplit(submodule_url)
        assert submodule_processed_url.hostname is not None
        result[submodule_name] = ModuleInfo(
            pinned_hash=hashes[submodule_name],
            name=submodule_processed_url.path.removeprefix("/"),
            base_repository=submodule_processed_url.scheme
            + "://"
            + submodule_processed_url.hostname,
            url=submodule_url,
        )

    selinux = (
        result["selinux"] if target.operating_system != base.TargetOS.WINDOWS else None
    )
    libusb = result["libusb"] if use_bundled_libusb else None

    return SubmoduleInfo(
        core=result["core"],
        extras=result["extras"],
        boringssl=result["boringssl"],
        mkbootimg=result["mkbootimg"],
        avb=result["avb"],
        libbase=result["libbase"],
        libziparchive=result["libziparchive"],
        adb=result["adb"],
        logging=result["logging"],
        selinux=selinux,
        libusb=libusb,
    )
