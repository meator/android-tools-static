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

"""Utility functions working with CycloneDX dicts."""

# https://cyclonedx.org/docs/1.6/json/

import enum
import re

import proj_types


class Licenses(enum.Enum):
    """License types supported by set_license()."""

    APACHE = enum.auto()
    MIT = enum.auto()


def set_license(
    component: proj_types.CycloneComponent,
    license: Licenses,
    override_license_url: str | None = None,
) -> None:
    """Set the license of the given component.

    Arguments:
        component: Component to modify in place.
        license: The license to be set.
        override_license_url: URL of the license to be used instead of a generic one.
    """
    match license:
        case Licenses.APACHE:
            spdx_id = "Apache-2.0"
            license_url = (
                override_license_url
                if override_license_url is not None
                else "https://www.apache.org/licenses/LICENSE-2.0"
            )
        case Licenses.MIT:
            spdx_id = "MIT"
            license_url = (
                override_license_url
                if override_license_url is not None
                else "https://opensource.org/license/mit"
            )
        case _:
            raise ValueError("Unknown license name specified!")
    component["licenses"] = [{"license": {"id": spdx_id, "url": license_url}}]
    if "externalReferences" in component and isinstance(
        component["externalReferences"], list
    ):
        externalReferences = component["externalReferences"]  # noqa: N806
    else:
        externalReferences = component["externalReferences"] = []  # noqa: N806
    externalReferences.append({"type": "license", "url": license_url})


class HashTypes(enum.StrEnum):
    """Hash types supported by CycloneDX."""

    MD5 = "MD5"
    SHA_1 = "SHA-1"
    SHA_256 = "SHA-256"
    SHA_384 = "SHA-384"
    SHA_512 = "SHA-512"
    SHA3_256 = "SHA3-256"
    SHA3_384 = "SHA3-384"
    SHA3_512 = "SHA3-512"
    BLAKE2b_256 = "BLAKE2b-256"
    BLAKE2b_384 = "BLAKE2b-384"
    BLAKE2b_512 = "BLAKE2b-512"
    BLAKE3 = "BLAKE3"


def set_hash(
    component: proj_types.CycloneComponent | proj_types.CycloneReference,
    hash_type: HashTypes,
    hash: str,
) -> None:
    """Set the hash of the given component.

    Arguments:
        component: Component, proj_types.CycloneReference or anything else that may
          accept a "hashes" key to modify in place.
        hash_type: Type of hash provided in hash argument.
        hash: Hash string (in hex) in the specified format.
    """
    match hash_type:
        case HashTypes.SHA_256:
            assert re.fullmatch(r"[a-f0-9]{64}", hash) is not None
        case _:
            raise RuntimeError(
                "Got unexpected hash type. This is likely a bug in the script"
            )
    component["hashes"] = [{"alg": str(hash_type), "content": hash}]
