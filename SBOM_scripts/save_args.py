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

"""Helper script which saves all of its arguments to a specified file."""

import argparse
import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "output_file",
        help="file into which the rest of the arguments will be outputted",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="file into which the rest of the arguments will be outputted",
    )
    args = parser.parse_args()

    result = "\0".join(args.paths)

    if args.output_file == "-":
        sys.stdout.write(result)
    else:
        with open(args.output_file, "w") as file:
            file.write(result)
