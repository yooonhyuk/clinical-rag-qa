"""Heading detection for plain text extracted from PDFs (English and Korean regulatory docs).

PDF text has no structure, so headings are recognised by their numbering, conservatively:

    I. INTRODUCTION / Ⅳ. 탐색임상시험 / APPENDIX A: ... / Annex 1          level 1
    제3장 ... (level 1), 제2절 ... (level 2)
    A. Choice of Imaging Modality                                        level 2
    1 Background / 1. 세포독성 물질 / 4.2.1 ... / 1.1.1. 주요 목적          level 1 + depth
    가. 기록 및 보고                                                       level 6

A numbered *sentence* (ICH "2.4.2 Before initiating a trial, the investigator should ...", a
numbered recommendation list in a report) is not a heading: titles are short, have few words
and do not end like a sentence. Table-of-contents lines (dot leaders) are dropped entirely.
"""

import re
from dataclasses import dataclass

_ROMAN = r"(?:X{0,3}(?:IX|IV|V?I{1,3})|X{1,3}|V|IV|IX)"
_ROMAN_UNI = "ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ"
_MONTHS = "january|february|march|april|may|june|july|august|september|october|november|december"

_ROMAN_RE = re.compile(rf"^(?:{_ROMAN}|[{_ROMAN_UNI}])\.\s+(?P<title>\S.*)$")
_APPENDIX_RE = re.compile(
    r"^(?:APPENDIX|Appendix|ANNEX|Annex|부록)\s*[A-Z0-9IVX]*\s*[:.\-–]?\s*(?P<title>.*)$"
)
_CHAPTER_KO_RE = re.compile(r"^제\s*(?P<n>\d+)\s*(?P<unit>[편장절])\.?\s*(?P<title>\S.*)?$")
_LETTER_RE = re.compile(r"^[A-H]\.\s+(?P<title>[A-Z][^\s]*.*)$")
_NUMBER_RE = re.compile(r"^(?P<num>\d{1,2}(?:\.\d{1,2}){0,4})(?P<dot>\.?)\s+(?P<title>\S.*)$")
_HANGUL_ITEM_RE = re.compile(r"^[가나다라마바사아자차카타파하]\.\s+(?P<title>\S.*)$")
_TOC_LEADER_RE = re.compile(r"(?:\.\s?){5,}|(?:·\s?){5,}|(?:…\s?){2,}|(?:‥\s?){3,}")
_SENTENCE_END_RE = re.compile(r"(?:[.;,:]|다|음|함|임)\s*$")
_HANGUL_RE = re.compile(r"[가-힣]")
_MONTH_RE = re.compile(rf"^(?:{_MONTHS})\b", re.IGNORECASE)

MAX_TITLE_CHARS = 80
MAX_TITLE_WORDS = 12


@dataclass(frozen=True, slots=True)
class Heading:
    level: int
    text: str  # full heading line, numbering included ("6.1.2.4 Evaluation of activity")


def is_toc_line(line: str) -> bool:
    return bool(_TOC_LEADER_RE.search(line))


def _plausible_title(title: str, *, allow_sentence_end: bool = False) -> bool:
    title = title.strip()
    if not title or len(title) > MAX_TITLE_CHARS or len(title.split()) > MAX_TITLE_WORDS:
        return False
    digits = sum(c.isdigit() for c in title)
    if digits > sum(c.isalpha() for c in title):  # "B1-2006-2-001 2006.01" (revision table)
        return False
    if not allow_sentence_end and _SENTENCE_END_RE.search(title):
        return False
    if " should " in f" {title} " or _MONTH_RE.match(title):
        return False
    first = title[0]
    return first.isupper() or first.isdigit() or bool(_HANGUL_RE.match(first)) or first in '(“"'


def _continues_sentence(next_line: str | None) -> bool:
    """A wrapped numbered sentence continues on the next line with a lowercase word."""
    nxt = (next_line or "").strip()
    return bool(nxt) and nxt[0].isascii() and nxt[0].islower()


def detect_heading(line: str, next_line: str | None = None) -> Heading | None:
    """Return the heading on this line, or None for body text.

    `next_line` (the following non-empty line) rejects numbered sentences that wrap:
    "1.5 A qualified physician or, when appropriate, a qualified dentist (or other" is
    followed by "qualified healthcare professionals ...".
    """
    text = " ".join(line.split())
    if not text or len(text) > MAX_TITLE_CHARS + 12 or is_toc_line(text):
        return None
    if _continues_sentence(next_line):
        return None

    if m := _CHAPTER_KO_RE.match(text):
        level = {"편": 1, "장": 1, "절": 2}[m.group("unit")]
        title = m.group("title") or ""
        return Heading(level, text) if not title or _plausible_title(title) else None
    if m := _APPENDIX_RE.match(text):
        if text.split()[0].isupper() or text.startswith(("Appendix", "Annex", "부록")):
            title = m.group("title")
            if not title or _plausible_title(title, allow_sentence_end=title.endswith(":")):
                return Heading(1, text)
        return None
    if m := _ROMAN_RE.match(text):
        return Heading(1, text) if _plausible_title(m.group("title")) else None
    if m := _LETTER_RE.match(text):
        title = m.group("title")
        if len(title.split()) <= 10 and _plausible_title(title, allow_sentence_end=True):
            return Heading(2, text)
        return None
    if m := _NUMBER_RE.match(text):
        title = m.group("title")
        depth = m.group("num").count(".") + 1
        # "3 상 임상시험 이전에 ..." is a wrapped sentence, not a heading: a Korean title needs
        # a dotted number ("1.", "10.4", "1.1.1.").
        if _HANGUL_RE.match(title) and depth == 1 and not m.group("dot"):
            return None
        if not _plausible_title(title):
            return None
        return Heading(1 + depth, text)
    if m := _HANGUL_ITEM_RE.match(text):
        title = m.group("title")
        short = len(title) <= 25 and "," not in title
        return Heading(6, text) if short and _plausible_title(title) else None
    return None


def heading_continuation(heading: Heading, next_line: str) -> str | None:
    """Second line of a heading that wrapped, if `next_line` looks like one."""
    nxt = " ".join(next_line.split())
    if not nxt or detect_heading(nxt) is not None or len(nxt) > 60:
        return None
    letters = [c for c in heading.text if c.isalpha()]
    upper = bool(letters) and all(c.isupper() for c in letters)
    if upper and all(c.isupper() for c in nxt if c.isalpha()) and any(c.isalpha() for c in nxt):
        return nxt  # "APPENDIX A:" / "BEFORE IMAGING:  CHARTER CONSIDERATIONS"
    if heading.text.endswith(("-", "an", "the", "of", "for", "and", "to", "in")) or (
        nxt.endswith("?") and not heading.text.endswith("?")
    ):
        return nxt  # "B. Is Centralized ... for an Imaging-Based" / "Primary Endpoint?"
    return None


class SectionPath:
    """Heading stack: a new heading pops every open heading at the same or a deeper level."""

    def __init__(self, max_depth_shown: int = 3) -> None:
        self._stack: list[Heading] = []
        self._max_shown = max_depth_shown

    def push(self, heading: Heading) -> None:
        while self._stack and self._stack[-1].level >= heading.level:
            self._stack.pop()
        self._stack.append(heading)

    def title(self) -> str | None:
        if not self._stack:
            return None
        return " > ".join(h.text for h in self._stack[-self._max_shown :])
