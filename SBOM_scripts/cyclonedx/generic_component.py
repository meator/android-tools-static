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

"""Module generating CycloneDX components."""

import enum
import typing

import proj_types

from . import util


class ComponentType(enum.StrEnum):
    """Type of a CycloneDX component."""

    application = "application"
    framework = "framework"
    library = "library"
    container = "container"
    platform = "platform"
    operating_system = "operating-system"
    device = "device"
    device_driver = "device-driver"
    firmware = "firmware"
    file = "file"
    machine_learning_model = "machine-learning-model"
    data = "data"
    cryptographic_asset = "cryptographic-asset"


class ComponentSupplier(typing.NamedTuple):
    """CycloneDX component supplier information."""

    name: str
    url: str | None = None


class ComponentAuthor(typing.NamedTuple):
    """CycloneDX component author information."""

    name: str
    email: str


class ReferenceType(enum.StrEnum):
    """Type of a CycloneDX reference."""

    vcs = "vcs"
    issue_tracker = "issue-tracker"
    website = "website"
    advisories = "advisories"
    bom = "bom"
    mailing_list = "mailing-list"
    social = "social"
    chat = "chat"
    documentation = "documentation"
    support = "support"
    source_distribution = "source-distribution"
    distribution = "distribution"
    distribution_intake = "distribution-intake"
    license = "license"
    build_meta = "build-meta"
    build_system = "build-system"
    release_notes = "release-notes"
    security_contact = "security-contact"
    model_card = "model-card"
    log = "log"
    configuration = "configuration"
    evidence = "evidence"
    formulation = "formulation"
    attestation = "attestation"
    threat_model = "threat-model"
    adversary_model = "adversary-model"
    risk_assessment = "risk-assessment"
    vulnerability_assertion = "vulnerability-assertion"
    exploitability_statement = "exploitability-statement"
    pentest_report = "pentest-report"
    static_analysis_report = "static-analysis-report"
    dynamic_analysis_report = "dynamic-analysis-report"
    runtime_analysis_report = "runtime-analysis-report"
    component_analysis_report = "component-analysis-report"
    maturity_report = "maturity-report"
    certification_report = "certification-report"
    codified_infrastructure = "codified-infrastructure"
    quality_metrics = "quality-metrics"
    poam = "poam"
    electronic_signature = "electronic-signature"
    digital_signature = "digital-signature"
    rfc_9116 = "rfc-9116"
    other = "other"


class ReferenceHash(typing.NamedTuple):
    """Hash info for Reference.

    You can use cyclonedx.util.set_hash() to safely set this on a Reference.
    """

    hash_type: util.HashTypes
    hash: str


def generate_reference(type: ReferenceType, url: str) -> proj_types.CycloneReference:
    """Generate a CycloneDX reference."""
    return proj_types.CycloneReference({"type": str(type), "url": url})


def generate(
    *,
    name: str,
    version: str,
    description: str | None = None,
    c_type: ComponentType,
    ref: proj_types.Purl,
    supplier: ComponentSupplier | None = None,
    author: ComponentAuthor | None = None,
    references: typing.Iterable[proj_types.CycloneReference] | None = None,
    properties: dict[str, str] | None = None,
    components: typing.Iterable[proj_types.CycloneComponent] | None = None
) -> proj_types.CycloneComponent:
    """Generate a CycloneDX component.

    More specific functions in cyclonedx.generate should be preferred if available.

    Arguments:
        name: Name of the component.
        version: Version of the component.
        description: Optional description of the component.
        c_type: Type of the component.
        ref: purl/bom-ref of the component.
        supplier: Optional supplier of the component.
        author: Optional author of the component.
        references: Optional reference links.
        properties: A dictionary of properties. Supplying several properties with the
          same name is not currently supported.
        components: Subcomponents of this component. Making component a "child" of
          another component doesn't affect the dependency relation of the components.
    """
    result: dict[str, typing.Any] = {
        "type": str(c_type),
        "name": name,
        "version": version,
        "bom-ref": ref,
        "purl": ref,
    }

    if description is not None:
        result["description"] = description

    if supplier is not None:
        result["supplier"] = {"name": supplier.name}
        if supplier.url is not None:
            result["supplier"]["url"] = [supplier.url]

    if author is not None:
        result["authors"] = [
            {
                "name": author.name,
                "email": author.email,
            }
        ]

    if references:
        result["externalReferences"] = list(references)

    if properties:
        result["properties"] = [
            {"name": key, "value": value} for key, value in properties.items()
        ]

    if components:
        result["components"] = list(components)

    return proj_types.CycloneComponent(result)
