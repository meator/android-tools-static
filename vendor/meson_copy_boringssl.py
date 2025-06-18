#!/usr/bin/env python3
"""Copy boringssl from vendor/ to subprojects/

This script has no external dependencies, it purely relies on Python standard library.

This script is stateless

This script uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting.
"""

import argparse
import shutil

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Helper Python script used by Meson to copy boringssl "
        + "from vendor/ to subprojects/.",
    )
    # These are passed as arguments to let Meson setup reconfigure dependencies.
    parser.add_argument(
        "source",
        help="Path to 'vendor/boringssl'.",
    )
    parser.add_argument(
        "destination",
        help="Path to 'subprojects/boringssl'.",
    )
    args = parser.parse_args()

    shutil.copytree(args.source, args.destination, dirs_exist_ok=True)
