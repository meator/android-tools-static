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

"""Module used to generate the common part of the SBOM document."""

import string
import sys
import typing
import warnings
from pathlib import Path

import base
import cyclonedx.generators
import cyclonedx.generic_component
import cyclonedx.util
import git.patch_parsing
import git.submodule_parsing
import git.submodule_verification
import git.util
import meson.depmf
import meson.wrap_info
import meson.wrap_patches
import proj_types
from cyclonedx.generic_component import ComponentSupplier, ComponentType, ReferenceType
from cyclonedx.util import Licenses
from purldb.keys import PurlDB, PurlNames

from . import github_runner


def handle_repolink(
    repolink_format: str,
    repolink_ref: str | None,
    git_exe: str | None,
    source_dir: Path,
) -> proj_types.RepoLink:
    """Return a RepoLink callable object.

    RepoLink takes a posix path relative to repository root and returns an URL
    (possibly pinned to a commit) to that path in the repository.

    Arguments:
        repolink_format: The repolink template string. ${path} and ${ref} are
          recognized substitutions. ${path} is mandatory, ${ref} is optional.
        repolink_ref: A value to use for ${ref} substitution instead of asking git for
          it.
        git_exe: Path to git executable.
        source_dir: Path to repository root.
    """
    repolink_template = string.Template(repolink_format)

    if "path" not in repolink_template.get_identifiers():
        sys.exit("The repolink_format argument must contain a ${path} substitution!")

    get_file_link: proj_types.RepoLink

    # Facilitate a flexible mechanism for making repo links to files.
    # This mechanism does not hardcode the repository name or owner.
    # It optionaly supports ref substitution, which will include the commit SHA/tag
    # in the link making it permanent.
    if "ref" in repolink_template.get_identifiers():
        if repolink_ref is not None:

            def get_file_link(path: str) -> str:
                return repolink_template.substitute(path=path, ref=repolink_ref)

        else:
            if (
                git_exe is None
                or (hash := git.util.get_head(git_exe, source_dir)) is None
            ):
                get_file_link = None
            else:

                # This is used as a more advanced and easy to read lambda, no need to
                # docstring it for D103.
                def get_file_link(path: str) -> str:
                    return repolink_template.substitute(path=path, ref=hash)

    else:

        def get_file_link(path: str) -> str:
            return repolink_template.substitute(path=path)

    return get_file_link


class _BasePatchIssueInfo(typing.NamedTuple):
    issue_name: str
    issue_description: str
    source_name: str | None
    source_url: str | None


class _DefectPatchIssueInfo(_BasePatchIssueInfo):
    pass


class _EnhancementPatchIssueInfo(_BasePatchIssueInfo):
    pass


def _process_known_patches(
    input: dict[str, _DefectPatchIssueInfo | _EnhancementPatchIssueInfo],
    source_dir: Path,
) -> dict[Path, _DefectPatchIssueInfo | _EnhancementPatchIssueInfo]:
    return {
        source_dir / "subprojects/packagefiles" / key: value
        for key, value in input.items()
    }


def _get_wrap_component(
    wrap_name: str,
    wrap_info: meson.wrap_info.MesonWrapInfo,
    known_patches: dict[Path, _DefectPatchIssueInfo | _EnhancementPatchIssueInfo],
    source_dir: Path,
    git_exe: str,
    purldb: PurlDB,
    repo_link: proj_types.RepoLink,
) -> proj_types.CycloneComponent:
    raw_patch_list = meson.wrap_patches.get_wrap_patch_list(
        source_dir, wrap_name, meson.wrap_patches.PatchStrategy.GIT, git_exe
    )

    IssueType = cyclonedx.generators.IssueType  # noqa: N806
    Issue = cyclonedx.generators.Issue  # noqa: N806

    if raw_patch_list:
        patch_list = []
        for patch_path in raw_patch_list:
            patch_info = known_patches.pop(patch_path, None)
            if patch_info is None:
                warnings.warn(
                    f"Found unknown patch '{patch_path}'! The function which raised "
                    "this warning should likely be updated to include info about this "
                    "patch.",
                    stacklevel=1,
                )
                patch_list.append(
                    cyclonedx.generators.get_patch(
                        cyclonedx.generators.PatchType.unofficial,
                        patch_path,
                        source_dir,
                        repo_link,
                        None,
                    )
                )
            else:
                if isinstance(patch_info, _DefectPatchIssueInfo):
                    issue_type = IssueType.defect
                elif isinstance(patch_info, _EnhancementPatchIssueInfo):
                    issue_type = IssueType.enhancement
                else:
                    raise RuntimeError(
                        "Unknown issue type! This is likely a bug in the script."
                    )
                patch_list.append(
                    cyclonedx.generators.get_patch(
                        cyclonedx.generators.PatchType.unofficial,
                        patch_path,
                        source_dir,
                        repo_link,
                        Issue(
                            type=issue_type,
                            name=patch_info.issue_name,
                            description=patch_info.issue_description,
                            source_name=patch_info.source_name,
                            source_url=patch_info.source_url,
                        ),
                    )
                )

    assert wrap_info.spdx_expression is not None

    return cyclonedx.generators.get_wrap_component(
        wrap_name,
        wrap_info.wrapdb_version,
        purldb[wrap_info.purl],
        wrap_info.description,
        patch_list if raw_patch_list else None,
        wrap_info.spdx_expression,
    )


def get_base_document(
    source_dir: Path,
    purldb: PurlDB,
    git_exe: str,
    lifecycle: cyclonedx.generators.Lifecycles,
    repo_link: proj_types.RepoLink,
    nmeum_version: str,
    msys2_version: str,
    github_runner_name_ver: str,
    action_gh_release_version: str,
    base_repolink: str,
    nmeum_patch_series_file: Path,
    added_patch_series_file: Path,
    submodules: git.submodule_parsing.SubmoduleInfo,
    wraps: dict[str, meson.wrap_info.MesonWrapInfo],
    meson_depmf: dict[str, meson.depmf.SubprojectInfo],
    target: base.Target,
) -> dict[str, typing.Any]:
    """Generate the shared part of the SBOM.

    This function will generate the majority of the resulting SBOM. OS-specific scripts
    will call this function and add their OS-specific components and dependencies on
    top of what this function returns.

    There are too many arguments to document. Their purpose should hopefully be
    self-explanatory.
    """
    project_version = meson_depmf["android-tools-static"].version

    assert project_version is not None

    nmeum_patch_list: dict[str, list[Path]] = {}
    orig_patch_list: dict[str, list[Path]] = {}

    for result_patch_dict, patch_list_path in (
        (nmeum_patch_list, nmeum_patch_series_file),
        (orig_patch_list, added_patch_series_file),
    ):
        with open(patch_list_path) as file:
            for raw_patch_path in file.read().split("\0"):
                relative_path = Path(raw_patch_path)
                result_patch_dict.setdefault(relative_path.parts[0], []).append(
                    source_dir / "patches" / relative_path
                )

    merged_patch_list = nmeum_patch_list.copy()
    for submodule_name, patch_list in orig_patch_list.items():
        # Be careful about shallow copies unintentionally writing into nmeum_patch_list
        # here.
        if submodule_name in merged_patch_list:
            merged_patch_list[submodule_name] = (
                merged_patch_list[submodule_name] + patch_list
            )
        else:
            merged_patch_list[submodule_name] = patch_list

    for submodule_name, patch_list in merged_patch_list.items():
        git.submodule_verification.verify_checkout_patches(
            git_exe, source_dir / "vendor" / submodule_name, reversed(patch_list)
        )

    nmeum_cyclonedx_patches: list[proj_types.CycloneCommit] = []
    added_cyclonedx_patches: list[proj_types.CycloneCommit] = []
    for cyclonedx_patches, patch_dict in (
        (nmeum_cyclonedx_patches, nmeum_patch_list),
        (added_cyclonedx_patches, orig_patch_list),
    ):
        for patch_series in patch_dict.values():
            for patch_path in patch_series:
                commit_info = git.patch_parsing.get_commit_patch_info(patch_path)
                url = (
                    repo_link(patch_path.relative_to(source_dir).as_posix())
                    if repo_link is not None
                    else None
                )
                cyclonedx_patches.append(
                    cyclonedx.generators.get_commit(
                        commit_info.sha,
                        url,
                        commit_info.author_name,
                        commit_info.author_email,
                        commit_info.message,
                    )
                )

    document = cyclonedx.generators.get_template(lifecycle)
    document["metadata"]["component"] = cyclonedx.generators.get_primary_component(
        purldb,
        project_version,
        nmeum_version,
        msys2_version,
        base_repolink,
        nmeum_cyclonedx_patches,
        added_cyclonedx_patches,
        target,
    )

    action_gh_release = cyclonedx.generic_component.generate(
        name="softprops/action-gh-release",
        version=action_gh_release_version,
        c_type=ComponentType.application,
        ref=purldb[PurlNames.action_gh_release],
        description="GitHub Action used to publish GitHub Releases",
        supplier=ComponentSupplier(name="GitHub, Inc.", url="https://github.com/"),
        references=[
            cyclonedx.generic_component.generate_reference(
                type=ReferenceType.website,
                url="https://github.com/softprops/action-gh-release",
            )
        ],
    )
    cyclonedx.util.set_license(
        action_gh_release,
        Licenses.MIT,
        "https://github.com/softprops/action-gh-release/blob/master/LICENSE",
    )

    submodule_mapping = [
        (PurlNames.ags_core, submodules.core),
        (PurlNames.ags_extras, submodules.extras),
        (PurlNames.boringssl, submodules.boringssl),
        (PurlNames.ags_mkbootimg, submodules.mkbootimg),
        (PurlNames.ags_avb, submodules.avb),
        (PurlNames.ags_libbase, submodules.libbase),
        (PurlNames.ags_libziparchive, submodules.libziparchive),
        (PurlNames.ags_adb, submodules.adb),
        (PurlNames.ags_logging, submodules.logging),
    ]

    if submodules.selinux is not None:
        submodule_mapping.append((PurlNames.ags_selinux, submodules.selinux))
    if submodules.libusb is not None:
        submodule_mapping.append((PurlNames.libusb, submodules.libusb))

    submodule_components = []

    for purl_key, submodule in submodule_mapping:
        submodule_components.append(
            cyclonedx.generators.get_submodule_component(
                submodule.name, submodule.pinned_hash, purldb[purl_key], submodule.url
            )
        )

    wrap_components = []

    _DPII = _DefectPatchIssueInfo  # noqa: N806
    _EPII = _EnhancementPatchIssueInfo  # noqa: N806

    noinstall = _EPII(
        "installation process",
        "Prevent the Wrap from installing its libraries and pkg-config files, since "
        "they are not needed.",
        None,
        None,
    )

    known_patches_in: dict[str, _DefectPatchIssueInfo | _EnhancementPatchIssueInfo] = {
        "abseil-cpp/0001-build-both-host-and-build-libs-in-cross.patch": _DPII(
            "cross build",
            "Make abseil-cpp usable when both its cross and its native versions are "
            "needed.",
            "WrapDB GitHub Issues",
            "https://github.com/mesonbuild/wrapdb/issues/1856",
        ),
        "abseil-cpp/0002-do-not-bother-building-unused-native-libs.patch": _EPII(
            "optimization",
            "(Patch modifying "
            "abseil-cpp/0001-build-both-host-and-build-libs-in-cross.patch) Build "
            "only needed libraries twice during cross compilation.",
            None,
            None,
        ),
        "fmt/noinstall.patch": noinstall,
        "libusb/noinstall.patch": noinstall,
        "lz4/noinstall.patch": noinstall,
        "pcre2/noinstall.patch": noinstall,
        "protobuf/0001-fix-host-abseil-compilation.patch": _EPII(
            "cross build",
            "Adapt protobuf's build system to changes in "
            "abseil-cpp/0001-build-both-host-and-build-libs-in-cross.patch which "
            "improves cross compilation",
            "WrapDB GitHub Issues",
            "https://github.com/mesonbuild/wrapdb/issues/1856",
        ),
        "protobuf/0002-do-not-build-nonnative-protoc-during-cross-build.patch": _EPII(
            "optimization", "Do not build non-native (host machine) protoc", None, None
        ),
        "protobuf/0003-fix-windows-symlinks.patch": _DPII(
            "build",
            "Do not use symlinks on Windows, since they require admin permissions or "
            "a special setting enabled",
            "WrapDB GitHub Pull request",
            "https://github.com/mesonbuild/wrapdb/pull/2212",
        ),
        "protobuf/0004-fix-gcc-15-release-compilation.patch": _DPII(
            "build",
            "Fixe protobuf compilation on MSYS2 in release mode.",
            "protobuf GitHub Issues",
            "https://github.com/protocolbuffers/protobuf/issues/21333",
        ),
        "zlib/noinstall.patch": noinstall,
        "zstd/noinstall.patch": noinstall,
    }

    # The items in the dict below will be removed as they are processed. The dict
    # should be empty after all patches are processed.
    known_patches = _process_known_patches(known_patches_in, source_dir)

    for wrap_name, wrap_info in wraps.items():
        wrap_components.append(
            _get_wrap_component(
                wrap_name,
                wrap_info,
                known_patches,
                source_dir,
                git_exe,
                purldb,
                repo_link,
            )
        )

    if known_patches:
        raise RuntimeError(
            "This SBOM script is out of date! Expected patches made to Meson Wraps "
            "were not found! Expected: "
            + ", ".join(str(path) for path in known_patches.keys())
        )

    document["components"] = (
        [github_runner.get_runner(github_runner_name_ver, purldb), action_gh_release]
        + submodule_components
        + wrap_components
    )

    return document
