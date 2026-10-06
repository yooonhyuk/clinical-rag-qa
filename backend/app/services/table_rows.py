"""Render table rows as self-describing text lines for chunking and retrieval."""


def _clean(row: list[str]) -> list[str]:
    return [" ".join(c.split()) for c in row]


def rows_to_lines(header_rows: list[list[str]], body_rows: list[list[str]]) -> list[str]:
    """Each body row becomes "h1: v1; h2: v2" (empty cells skipped).

    A wide table (e.g. DICOM PS3.15 Table E.1-1, 15 columns) then yields short lines that still
    say which column each value belongs to, so a single row survives chunking on its own.
    Several header rows (a spanning group row + column names) are merged column-wise. Without
    a header (no <thead>), the first row is used. A body row whose width differs from the
    header falls back to "v1 | v2 | ...".
    """
    header_rows = [_clean(r) for r in header_rows if any(c.strip() for c in r)]
    body_rows = [_clean(r) for r in body_rows if any(c.strip() for c in r)]
    if not header_rows and body_rows:
        header_rows, body_rows = [body_rows[0]], body_rows[1:]
    if not header_rows:
        return []
    width = max(len(r) for r in header_rows)
    header = [""] * width
    for row in header_rows:
        for i, cell in enumerate(row):
            if cell and cell not in header[i]:
                header[i] = f"{header[i]} {cell}".strip()
    lines: list[str] = []
    for row in body_rows:
        if len(row) == width and any(header):
            pairs = [f"{h}: {v}" if h else v for h, v in zip(header, row, strict=True) if v]
            lines.append("; ".join(pairs))
        else:
            lines.append(" | ".join(c for c in row if c))
    return lines
