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

"""Module used for parsing git .patch files.

In comparison to other modules in this package, git is not directly executed here.
"""

import email
import email.headerregistry
import email.message
import email.policy
import typing
from pathlib import Path


class CommitPatchInfo(typing.NamedTuple):
    """Info about a 'git format-patch'-like .patch file."""

    sha: str
    author_name: str
    author_email: str
    message: str


def get_commit_patch_info(patch_path: Path) -> CommitPatchInfo:
    """Retrieve info from a 'git format-patch'-like .patch file.

    Arguments:
        patch_path: Path to the patch.
    """
    with patch_path.open() as input:
        sha_line = input.readline()
        email_msg = email.message_from_file(input, policy=email.policy.default)

    addresses = email_msg["From"].addresses

    assert len(addresses) == 1
    assert isinstance(addresses[0], email.headerregistry.Address)

    message_header = email_msg["Subject"].removeprefix("[PATCH] ")
    assert not email_msg.is_multipart()
    message_body = email_msg.get_payload().split("---", maxsplit=1)[0].strip()

    if message_body:
        message = f"{message_header}\n\n{message_body}"
    else:
        message = message_header

    return CommitPatchInfo(
        sha=sha_line[5:45],
        author_name=addresses[0].display_name,
        author_email=addresses[0].addr_spec,
        message=message,
    )
