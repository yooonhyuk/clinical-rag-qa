"""Heading detection for plain text extracted from PDFs (English and Korean regulatory docs).

PDF text has no structure, so headings are recognised by their numbering, conservatively:

    I. INTRODUCTION / Ⅳ. 탐색임상시험 / APPENDIX A: ... / Annex 1          level 1
    제3장 ... (level 1), 제2절 ... (level 2)
    A. Choice of Imaging Modality                                        level 2
    1 Background / 1. 세포독성 물질 / 4.2.1 ... / 1.1.1. 주요 목적          level 1 + depth
    가. 기록 및 보고                                                       level 6
    Table 4 Schedule of Assessments (caption)                            level 9

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


# A table caption is a heading of its own (deepest level): "Table 4 Schedule of Assessments ..."
# starts a section that ends at the next heading of any kind, so the rows of a schedule /
# synopsis table are chunked under their caption instead of under the previous paragraph.
TABLE_LEVEL = 9
_TABLE_CAPTION_RE = re.compile(
    r"^Table\s+(?:\d{1,3}(?:[.\-]\d{1,3})*|[A-Z]\d{0,2}(?:[.\-]\d{1,3})*)[.:]?\s+(?P<title>\S.*)$"
)


@dataclass(frozen=True, slots=True)
class Heading:
    level: int
    text: str  # full heading line, numbering included ("6.1.2.4 Evaluation of activity")
    # "8.1.2" -> (8, 1, 2) for decimal-numbered headings, else None
    number: tuple[int, ...] | None = None
    kind: str = "other"  # decimal | appendix | table | other


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
                return Heading(1, text, kind="appendix")
        return None
    if m := _TABLE_CAPTION_RE.match(text):
        title = m.group("title")
        if _plausible_title(title, allow_sentence_end=True) and not title[0].isdigit():
            return Heading(TABLE_LEVEL, text, kind="table")
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
        number = tuple(int(part) for part in m.group("num").split("."))
        return Heading(1 + depth, text, number=number, kind="decimal")
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


# --- numbered-heading consistency (long protocols / SAPs) -------------------------------------
#
# A 200-page protocol quotes section numbers everywhere outside its headings: the amendment
# history table ("5.2 Exclusion Criteria | Updated wording ..."), cross-references that start
# a wrapped line, numbered inclusion criteria. Taken as headings they corrupt the section path
# of everything that follows. Real headings form a chain in reading order where each number
# continues the previous one (child "8.1" -> "8.1.1", sibling "8.1.2" -> "8.1.3", or the next
# section "8.1.3" -> "8.2" / "9"); small gaps are allowed (a heading the extractor missed).
# `consistent_headings` keeps the longest such chain and turns the rest back into body text.

_MAX_STEP = 3  # largest allowed jump of one number component ("4.2" -> "4.5")


def _is_step(prev: tuple[int, ...] | None, cur: tuple[int, ...]) -> bool:
    """Can heading number `cur` directly follow `prev` (None = start of a segment)?"""
    if prev is None:
        return all(part <= _MAX_STEP for part in cur)
    k = 0
    while k < min(len(prev), len(cur)) and prev[k] == cur[k]:
        k += 1
    if k == len(cur):  # same number again, or going back up to an ancestor
        return False
    if k == len(prev):  # child: "8.1" -> "8.1.1"
        gap = cur[k]
    else:
        gap = cur[k] - prev[k]
    return 1 <= gap <= _MAX_STEP and all(part <= _MAX_STEP for part in cur[k + 1 :])


def _longest_chain(numbers: list[tuple[int, ...]]) -> set[int]:
    """Indexes of the longest subsequence in which every element is a valid step."""
    n = len(numbers)
    best = [1 if _is_step(None, num) else 0 for num in numbers]
    back = [-1] * n
    for i in range(n):
        for j in range(i):
            if best[j] and best[j] + 1 > best[i] and _is_step(numbers[j], numbers[i]):
                best[i], back[i] = best[j] + 1, j
    if not n or max(best) == 0:
        return set()
    i = max(range(n), key=lambda idx: (best[idx], -idx))
    chain: set[int] = set()
    while i >= 0:
        chain.add(i)
        i = back[i]
    return chain


def consistent_headings(headings: list[Heading]) -> list[bool]:
    """Keep-mask over headings in reading order.

    Decimal headings are kept only on the longest consistent chain of their segment; segments
    restart numbering after a non-decimal level-1/2 heading ("Ⅴ. ...", "제2장", "APPENDIX B",
    "A. ..."), as Korean guidelines and appendices do. Appendix headings that come before the
    first chapter "1" of a document that has one are references in a front-matter table
    (amendment history) and are dropped too.

    Left as they are: documents with fewer than 8 decimal headings, and Korean documents.
    Korean guidelines nest "1." under "가." under "4." and repeat inline "부록(ADDENDUM)"
    markers, which a single numeric chain cannot model (measured on corpus/public: it dropped
    real headings of 05_mfds_ich_gcp_ko.pdf).
    """
    keep = [True] * len(headings)
    decimal = [i for i, h in enumerate(headings) if h.kind == "decimal"]
    if len(decimal) < 8 or any(_HANGUL_RE.search(h.text) for h in headings):
        return keep
    first_chapter = _first_chapter(headings)
    if first_chapter is not None:
        for i in range(first_chapter):
            if headings[i].kind == "appendix":
                keep[i] = False

    segment: list[int] = []

    def close() -> None:
        numbers = [headings[i].number or () for i in segment]
        chain = _longest_chain(numbers)
        for pos, i in enumerate(segment):
            keep[i] = pos in chain
        segment.clear()

    for i, h in enumerate(headings):
        if h.kind == "decimal":
            segment.append(i)
        elif keep[i] and h.kind != "table" and h.level <= 2:
            close()
    close()
    return keep


def _first_chapter(headings: list[Heading]) -> int | None:
    """Index of the first "1 ..." heading followed (within 6 decimal headings) by "1.1"/"2"."""
    decimal = [i for i, h in enumerate(headings) if h.kind == "decimal"]
    for pos, i in enumerate(decimal):
        if headings[i].number == (1,):
            following = [headings[j].number for j in decimal[pos + 1 : pos + 7]]
            if (1, 1) in following or (2,) in following:
                return i
    return None


class SectionPath:
    """Heading stack: a new heading pops every open heading at the same or a deeper level."""

    def __init__(self, max_depth_shown: int = 3) -> None:
        self._stack: list[Heading] = []
        self._max_shown = max_depth_shown

    def push(self, heading: Heading) -> None:
        while self._stack and (
            self._stack[-1].level >= heading.level or _not_ancestor(self._stack[-1], heading)
        ):
            self._stack.pop()
        self._stack.append(heading)

    def title(self) -> str | None:
        if not self._stack:
            return None
        return " > ".join(h.text for h in self._stack[-self._max_shown :])


def _not_ancestor(open_heading: Heading, new: Heading) -> bool:
    """ "4.2" must not stay open under "1 Background": numbers say who the parent is."""
    if open_heading.number is None or new.number is None:
        return False
    return new.number[: len(open_heading.number)] != open_heading.number
