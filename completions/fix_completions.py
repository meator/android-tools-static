#!/usr/bin/env python3
#
# Copyright 2026 meator
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

"""Helper script which fixes upstream shell completions.

See https://github.com/nmeum/android-tools/issues/22.

Input is provided via stdin and output is written to stdout.

This script is provided by android-tools-static, not by nmeum/android-tools.
nmeum/android-tools uses a different approach to solve this issue: it keeps upstream
completions intact and it provides a wrapper script which fixes the completions up and
then sources the upstream completions. This approach doesn't work in release archives,
this script keeps the completions in a single file which is more flexible.
"""

import argparse
import shutil
import sys

_common_prefix = """
# See https://github.com/nmeum/android-tools/issues/22

function check_type() {
    type -t "$1"
}

""".lstrip()

_zsh_prefix = """
# Zsh needs bashcompinit called to support bash-style completion.
if ! declare -f complete >/dev/null; then
    autoload -U bashcompinit && bashcompinit
fi

""".lstrip()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="shell", required=True)

    subparsers.add_parser("bash")
    subparsers.add_parser("zsh")

    args = parser.parse_args()

    match args.shell:
        case "bash":
            sys.stdout.write(_common_prefix)
            sys.stdout.flush()
        case "zsh":
            sys.stdout.write(_common_prefix)
            sys.stdout.write(_zsh_prefix)
            sys.stdout.flush()

    shutil.copyfileobj(sys.stdin.buffer, sys.stdout.buffer, length=1024 * 64)
