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

"""Module generating parts of the resulting SBOM."""

# https://cyclonedx.org/docs/1.6/json/

import datetime
import enum
import typing
import uuid
from pathlib import Path

import base
import proj_types
from purldb.keys import PurlDB, PurlNames

from . import util


def _generate_timestamp() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


class Lifecycles(enum.StrEnum):
    """CycloneDX lifecycles."""

    design = "design"
    pre_build = "pre-build"
    build = "build"
    post_build = "post-build"
    operations = "operations"
    discovery = "discovery"
    decommission = "decommission"


def get_template(lifecycle: Lifecycles) -> dict[str, typing.Any]:
    """Get the basic CycloneDX 1.6 template."""
    return {
        "$schema": "https://cyclonedx.org/schema/bom-1.6.schema.json",
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": uuid.uuid4().urn,
        "version": 1,
        "metadata": {
            "timestamp": _generate_timestamp(),
            "lifecycles": [{"phase": str(lifecycle)}],
            "supplier": {
                "name": "GitHub, Inc.",
                "url": ["https://github.com/"],
            },
        },
    }


def get_commit(
    commit_sha: str,
    patch_url: str | None,
    author_name: str,
    author_email: str,
    message: str,
) -> proj_types.CycloneCommit:
    """Return a CycloneDX commit object.

    Arguments:
        commit_sha: The commit SHA.
        patch_url: Absolute link to the patch file. It is not feasible to link to
          repositories containing the commits, so this is an alternative.
        author_name: Author name part of 'Author name <e-mail>'.
        author_email: E-mail part of 'Author name <e-mail>'.
        message: Commit message.
    """
    result = {
        "uid": commit_sha,
        "author": {
            "name": author_name,
            "email": author_email,
        },
        "message": message,
    }
    if patch_url is not None:
        result["url"] = patch_url
    return proj_types.CycloneCommit(result)


def get_primary_component(
    purldb: PurlDB,
    version: str,
    nmeum_version: str,
    msys2_version: str,
    base_website: str,
    nmeum_commits: list[proj_types.CycloneCommit],
    added_commits: list[proj_types.CycloneCommit],
    target: base.Target,
) -> proj_types.CycloneComponent:
    """Get the primary CycloneDX component.

    This can be considered a specialized version of
    cyclonedx.generic_component.generate().

    Arguments:
        purldb: purl database.
        version: Version of android-tools-static.
        nmeum_version: Version of nmeum/android-tools underlying project.
        msys2_version: Version of MSYS2 android-tools underlying project.
        base_website: URL of android-tools-static. Website url is base_website, vcs url
          is base_website + ".git" and issue-tracker is base_website + "/issues".
        nmeum_commits: A list of valid CycloneDX commit objects from
          nmeum/android-tools.
        added_commits: A list of valid CycloneDX commit objects from
          android-tools-static.
        target: Target info. Components included in returned object may change based on
          the value of target.

    Returns:
        A CycloneDX component.
    """
    nmeum_base = proj_types.CycloneComponent(
        {
            "type": "application",
            "authors": [{"name": "nmeum"}],
            "name": "nmeum/android-tools",
            "version": nmeum_version,
            "bom-ref": purldb[PurlNames.nmeum_android_tools],
            "purl": purldb[PurlNames.nmeum_android_tools],
            "description": (
                "Unoffical CMake-based build system for android command line utilities"
            ),
            "pedigree": {"commits": nmeum_commits},
            "externalReferences": [
                {"type": "website", "url": "https://github.com/nmeum/android-tools"},
                {"type": "vcs", "url": "https://github.com/nmeum/android-tools.git"},
                {
                    "type": "issue-tracker",
                    "url": "https://github.com/nmeum/android-tools/issues",
                },
            ],
        }
    )
    util.set_license(nmeum_base, util.Licenses.APACHE)

    msys2_base = proj_types.CycloneComponent(
        {
            "type": "application",
            "authors": [{"name": "Biswapriyo Nath", "email": "nathbappai@gmail.com"}],
            "name": "MSYS2/mingw-w64-android-tools",
            "version": msys2_version,
            "bom-ref": purldb[PurlNames.msys2_android_tools],
            "purl": purldb[PurlNames.msys2_android_tools],
            "description": (
                "MSYS2 package including patches made to nmeum/android-tools to add "
                "Windows support"
            ),
            "externalReferences": [
                {
                    "type": "website",
                    "url": "https://packages.msys2.org/base/mingw-w64-android-tools",
                },
            ],
        }
    )

    result = proj_types.CycloneComponent(
        {
            "type": "application",
            "authors": [
                {
                    "name": "meator",
                    "email": "meator.dev@gmail.com",
                }
            ],
            "name": "android-tools-static",
            "version": version,
            "bom-ref": purldb[PurlNames.android_tools_static],
            "purl": purldb[PurlNames.android_tools_static],
            "description": "Meson port of android-tools with fullstatic support",
            "externalReferences": [
                {"type": "website", "url": base_website},
                {"type": "vcs", "url": base_website + ".git"},
                {"type": "issue-tracker", "url": base_website + "/issues"},
            ],
            "pedigree": {
                "ancestors": [nmeum_base, msys2_base],
                "commits": added_commits,
            },
            "properties": target.props(),
        }
    )
    util.set_license(result, util.Licenses.APACHE)
    return result


def get_submodule_component(
    name: str, version: str, purl: proj_types.Purl, vcs: str
) -> proj_types.CycloneComponent:
    """Generate a CycloneDX component for a vendored git submodule.

    This can be considered a specialized version of
    cyclonedx.generic_component.generate().

    Arguments:
        name: Name of the submodule.
        version: Version of the submodule.
        purl: purl of the package.
        vcs: URL of the git repository.
    """
    return proj_types.CycloneComponent(
        {
            "type": "library",
            "name": name,
            "version": version,
            "supplier": {"name": "Google"},
            "bom-ref": purl,
            "purl": purl,
            "description": "One of android-tools-static git submodule components",
            "externalReferences": [
                {"type": "vcs", "url": vcs},
            ],
        }
    )


class PatchType(enum.StrEnum):
    """All recognized CycloneDX patch types."""

    unofficial = "unofficial"
    monkey = "monkey"
    backport = "backport"
    cherry_pick = "cherry-pick"


class IssueType(enum.StrEnum):
    """All recognized CycloneDX patch types."""

    defect = "defect"
    enhancement = "enhancement"
    security = "security"


class Issue(typing.NamedTuple):
    """Info about the issue a CycloneDX patch solves."""

    type: IssueType
    name: str
    description: str
    source_name: str | None
    source_url: str | None


def get_patch(
    type: PatchType,
    patch_path: Path,
    source_root: Path,
    repo_link: proj_types.RepoLink,
    issue: Issue | None,
) -> proj_types.CyclonePatch:
    """Generate a CycloneDX patch/diff object.

    Arguments:
        type: Type of the patch.
        patch_path: Path to the patch.
        source_root: Path to the source repository.
        repo_link: The repo link function.
        issue: Optional field describing the issue resolved by the diff.
    """
    with patch_path.open() as input:
        patch_content = input.read()

    result = proj_types.CyclonePatch(
        {
            "type": str(type),
            "diff": {
                "text": {"content": patch_content},
            },
        }
    )

    if issue is not None:
        if (issue.source_name, issue.source_url).count(None) == 1:
            raise ValueError(
                "Both source_name and source_url of Issue must be either set or None!"
            )
        result["resolves"] = [
            {
                "type": str(issue.type),
                "name": issue.name,
                "description": issue.description,
            }
        ]

        if issue.source_name is not None:
            result["resolves"][0]["source"] = {
                "name": issue.source_name,
                "url": issue.source_url,
            }

    if repo_link is not None:
        result["diff"]["url"] = repo_link(
            patch_path.relative_to(source_root).as_posix()
        )

    return result


def get_wrap_component(
    name: str,
    version: str,
    purl: proj_types.Purl,
    description: str | None,
    patches: list[proj_types.CyclonePatch] | None,
    spdx_expression: str,
) -> proj_types.CycloneComponent:
    """Generate a CycloneDX component for a Meson Wrap.

    This can be considered a specialized version of
    cyclonedx.generic_component.generate().

    Arguments:
        name: Name of the wrap.
        version: Version of the wrap.
        purl: purl of the package.
        description: Optional description of the wrap.
        patches: Optional list of processed patches applied to the Wrap.
        spdx_expression: SPDX license expression describing the license of the Wrap.
    """
    result = proj_types.CycloneComponent(
        {
            "type": "library",
            "name": name,
            "version": version,
            "bom-ref": purl,
            "purl": purl,
            "description": (
                description
                if description is not None
                else "One of android-tools-static Meson Wrap dependencies"
            ),
            "supplier": {
                "name": "mesonbuild",
                "url": ["https://mesonbuild.com/"],
            },
            "licenses": [{"expression": spdx_expression}],
        }
    )

    if patches:
        result["pedigree"] = {"patches": patches}
    return result
