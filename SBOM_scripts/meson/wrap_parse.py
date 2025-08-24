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

"""Module for parsing Meson .wrap files."""

import configparser
import typing
from pathlib import Path


class WrapInfo(typing.NamedTuple):
    """Info about a Wrap.

    This info may not be 100% reliable, since the extracted subproject in subprojects/
    can be altered. It is easy for the wrap and any old lingering subprojects to get
    out of sync. It is therefore best to build the project from a clean checkout.

    This class currently doesn't provide much info. It can be extended in the future if
    needed.
    """

    wrapdb_version: str


def get_wrap_info(wrap_path: Path) -> WrapInfo:
    """Get info about a specified Wrap by parsing its .wrap file.

    Arguments:
        wrap_path: Path to the .wrap file.
    """
    wrap = configparser.ConfigParser()
    wrap.read(wrap_path)
    return WrapInfo(wrapdb_version=wrap["wrap-file"]["wrapdb_version"])
