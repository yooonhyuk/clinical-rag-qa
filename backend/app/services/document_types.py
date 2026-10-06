"""Types shared by the text extractors (Markdown/TXT, PDF, JATS XML, HTML) and the chunker."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Section:
    """A contiguous piece of a document with its location metadata.

    `section_title` is the heading path ("III. ... > B. ..."). `page_spans` maps character
    offsets inside `text` to page numbers for sections that cross pages: ((0, 4), (812, 5))
    means text[0:812] is on page 4 and the rest on page 5. Empty when `page_number` is enough.
    """

    text: str
    page_number: int | None = None
    section_title: str | None = None
    page_spans: tuple[tuple[int, int], ...] = ()

    def page_at(self, offset: int) -> int | None:
        page = self.page_number
        for start, number in self.page_spans:
            if start > offset:
                break
            page = number
        return page


class ExtractionError(Exception):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
