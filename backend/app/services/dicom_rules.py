"""Rule files for required / privacy DICOM tags (YAML)."""

from dataclasses import dataclass
from pathlib import Path

import yaml

REQUIRED_RULES_FILE = "required_tags.yaml"
PRIVACY_RULES_FILE = "privacy_tags.yaml"


@dataclass(frozen=True, slots=True)
class PrivacyRule:
    name: str
    message: str


@dataclass(frozen=True, slots=True)
class DicomRules:
    common_required: tuple[str, ...]
    required_by_modality: dict[str, tuple[str, ...]]
    privacy: tuple[PrivacyRule, ...]
    source: str

    def required_for(self, modality: str | None) -> tuple[str, ...]:
        extra = self.required_by_modality.get((modality or "").upper(), ())
        return self.common_required + tuple(t for t in extra if t not in self.common_required)


def load_rules(rules_dir: Path) -> DicomRules:
    required = yaml.safe_load((rules_dir / REQUIRED_RULES_FILE).read_text(encoding="utf-8"))
    privacy = yaml.safe_load((rules_dir / PRIVACY_RULES_FILE).read_text(encoding="utf-8"))
    return DicomRules(
        common_required=tuple(required.get("common", [])),
        required_by_modality={
            k.upper(): tuple(v) for k, v in (required.get("by_modality") or {}).items()
        },
        privacy=tuple(
            PrivacyRule(name=item["name"], message=item.get("message", f"{item['name']} exists"))
            for item in privacy.get("tags", [])
        ),
        source=f"rules/{REQUIRED_RULES_FILE}, rules/{PRIVACY_RULES_FILE}",
    )
