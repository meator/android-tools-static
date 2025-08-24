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

"""Helper types used throughout all SBOM generation scripts."""

# https://cyclonedx.org/docs/1.6/json/

import typing

CycloneComponent = typing.NewType("CycloneComponent", dict[str, typing.Any])
CycloneProperty = typing.NewType("CycloneProperty", dict[str, typing.Any])
CycloneCommit = typing.NewType("CycloneCommit", dict[str, typing.Any])
CyclonePatch = typing.NewType("CyclonePatch", dict[str, typing.Any])
CycloneReference = typing.NewType("CycloneReference", dict[str, typing.Any])
PatchID = typing.NewType("PatchID", str)
Purl = typing.NewType("Purl", str)
RepoLink = typing.Callable[[str], str] | None
