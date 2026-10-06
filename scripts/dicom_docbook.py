"""Fetch and parse the official DICOM DocBook XML (dicom.nema.org) for the rule builders.

The DICOM Standard is published as DocBook 5 XML per part, e.g.
  https://dicom.nema.org/medical/dicom/current/source/docbook/part15/part15.xml
`current` always points at the latest edition; archived editions live under
  https://dicom.nema.org/medical/dicom/<edition>/source/docbook/partNN/partNN.xml
(the newest edition is usually only reachable through `current`). The edition actually
fetched is read from the document subtitle ("DICOM PS3.15 2026d - ...") and recorded in the
generated rule files together with URL, retrieval date and SHA-256 of the source.
"""

import datetime as dt
import hashlib
import re
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

DB = "{http://docbook.org/ns/docbook}"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
BASE_URL = "https://dicom.nema.org/medical/dicom/{edition}/source/docbook/part{part:02d}/part{part:02d}.xml"
DEFAULT_CACHE = Path.home() / ".cache" / "clinical-rag-qa" / "dicom-standard"
TAG_RE = re.compile(r"^\(([0-9A-Fa-fx]{4}),([0-9A-Fa-fx]{4})\)$")


@dataclass(frozen=True)
class SourceInfo:
    part: str
    edition: str
    url: str
    retrieved: str
    sha256: str

    def as_dict(self) -> dict[str, str]:
        return {
            "part": self.part,
            "edition": self.edition,
            "url": self.url,
            "retrieved": self.retrieved,
            "sha256": self.sha256,
        }


def fetch_part(part: int, edition: str = "current", cache: Path = DEFAULT_CACHE) -> Path:
    """Download partNN.xml once per (edition, day) into the cache. Raises on network failure."""
    url = BASE_URL.format(edition=edition, part=part)
    target = cache / edition / dt.date.today().isoformat() / f"part{part:02d}.xml"
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, timeout=120) as res:  # noqa: S310 - fixed https host
            data = res.read()
        tmp = target.with_suffix(".tmp")
        tmp.write_bytes(data)
        tmp.replace(target)
    return target


def load(part: int, edition: str = "current", cache: Path = DEFAULT_CACHE):
    """Return (root element, SourceInfo) for one part of the standard."""
    path = fetch_part(part, edition, cache)
    data = path.read_bytes()
    root = ET.fromstring(data)
    subtitle = text(root.find(f"{DB}subtitle"))
    match = re.search(r"DICOM (PS3\.\d+) (\d{4}[a-e])", subtitle)
    if not match:
        raise RuntimeError(f"cannot read the edition from subtitle {subtitle!r}")
    info = SourceInfo(
        part=match.group(1),
        edition=match.group(2),
        url=BASE_URL.format(edition=edition, part=part),
        retrieved=path.parent.name,
        sha256=hashlib.sha256(data).hexdigest(),
    )
    return root, info


def text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return " ".join(" ".join(element.itertext()).replace("​", "").split())


def index_by_id(root: ET.Element, tag: str) -> dict[str, ET.Element]:
    return {e.get(XML_ID): e for e in root.iter(f"{DB}{tag}") if e.get(XML_ID)}


def caption(table: ET.Element) -> str:
    return text(table.find(f"{DB}caption"))


@dataclass
class Cell:
    text: str
    links: list[str]


def rows(table: ET.Element) -> Iterator[list[Cell]]:
    """Body rows (header row skipped) as cells with their text and xref targets."""
    body = table.find(f"{DB}tbody")
    for tr in (body if body is not None else table).iter(f"{DB}tr"):
        yield [Cell(text(td), [x.get("linkend") for x in td.iter(f"{DB}xref")]) for td in tr]


def parse_tag(raw: str) -> tuple[str, str] | None:
    """'(0010,0010)' -> ('0010', '0010'); repeating-group tags keep their 'x' (e.g. '60xx')."""
    match = TAG_RE.match(raw.strip())
    if not match:
        return None
    return match.group(1).upper().replace("X", "x"), match.group(2).upper().replace("X", "x")
