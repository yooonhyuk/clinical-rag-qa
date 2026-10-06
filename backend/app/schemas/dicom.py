from typing import Any

from pydantic import Field

from app.schemas.common import CamelModel


class DicomAnalyzeRequest(CamelModel):
    file_path: str = Field(min_length=1)
    explain: bool = Field(default=True, description="Generate the LLM explanation")


class QAResult(CamelModel):
    """MVP-1 compatible view: passed Type 1/2 attributes, Layer 2 messages, missing ones."""

    passed: list[str]
    warnings: list[str]
    missing: list[str]


class DicomFinding(CamelModel):
    """One rule finding. Never carries an attribute value."""

    code: str = Field(description="e.g. L1-TYPE1-ABSENT, DEID-X-PRESENT, QR-MISSING")
    severity: str = Field(description="error | warning | info")
    message: str
    source: str = Field(description='Citation, e.g. "PS3.15 2026d Table E.1-1"')
    attribute: str | None = None
    tag: str | None = None
    action: str | None = Field(default=None, description="PS3.15 profile action (Layer 2)")
    count: int = 1
    paths: list[str] = Field(default_factory=list, description="Keyword paths into sequences")
    details: dict[str, Any] = Field(default_factory=dict)


class IodInfo(CamelModel):
    key: str | None
    name: str | None
    determined_by: str | None
    source: str | None


class Layer1Result(CamelModel):
    standard: str
    iod: IodInfo
    passed: list[str]
    findings: list[DicomFinding]


class DeidOptionApplied(CamelModel):
    key: str
    name: str
    origin: str = Field(description="policy | claimed")


class DeidMethodCode(CamelModel):
    scheme: str
    code: str
    meaning: str


class ClaimedDeid(CamelModel):
    patient_identity_removed: str = Field(description="YES | NO | absent | empty | ...")
    deidentification_method: str = Field(description="presence only (free text)")
    method_codes: list[DeidMethodCode]
    unknown_method_codes: int
    basic_profile_claimed: bool


class Layer2Result(CamelModel):
    profile: str
    profile_edition: str
    options_applied: list[DeidOptionApplied]
    claimed_deid: ClaimedDeid
    findings: list[DicomFinding]


class QuantitationReadiness(CamelModel):
    applicable: bool
    ready: bool | None
    label: str | None = None
    findings: list[DicomFinding]


class SeverityCounts(CamelModel):
    error: int
    warning: int
    info: int


class DicomCounts(CamelModel):
    layer1: SeverityCounts
    layer2: SeverityCounts
    quantitation_readiness: SeverityCounts


class DicomAnalyzeResponse(CamelModel):
    file_name: str
    summary: str
    summary_source: str
    tag_summary: dict[str, Any] = Field(
        description="Allowlisted coded/numeric values; everything else exists/empty/absent"
    )
    layer1: Layer1Result
    layer2: Layer2Result
    quantitation_readiness: QuantitationReadiness
    counts: DicomCounts
    # MVP-1 compatible fields (derived from layer1 / layer2)
    privacy_warnings: list[str]
    missing_required_tags: list[str]
    qa_result: QAResult
    rule_source: str
    disclaimer: str


class DicomFileListResponse(CamelModel):
    files: list[str]
