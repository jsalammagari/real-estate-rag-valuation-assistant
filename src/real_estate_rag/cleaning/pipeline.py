"""Custom cleaning and normalization pipeline for Story 3."""

from __future__ import annotations

from dataclasses import dataclass
import re

from real_estate_rag.ingestion import IngestedDocument, PageExtraction


@dataclass(frozen=True)
class CleaningConfig:
    """Configuration for deterministic text cleaning."""

    min_text_length: int = 20
    dedupe_similarity_threshold: float = 0.9


@dataclass(frozen=True)
class CleanSegment:
    """Cleaned segment contract consumed by downstream chunking."""

    text: str
    doc_id: str
    page_span: tuple[int, int]
    silo: str
    content_type: str
    normalized_fields: dict[str, str]
    warnings: tuple[str, ...] = ()


_PAGE_NUMBER_RE = re.compile(r"^(?:page\s*)?\d+(?:\s*(?:of|/)\s*\d+)?$", re.IGNORECASE)
_MULTISPACE_RE = re.compile(r"[ \t]{2,}")
_AREA_UNIT_RE = re.compile(r"\b(?:sq\.?\s*ft|sqft|sf)\b", re.IGNORECASE)
_CURRENCY_TEXT_RE = re.compile(r"\$\s*(\d[\d,]*(?:\.\d+)?)\s*([kmb])?\b", re.IGNORECASE)
_DATE_SLASH_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
_DATE_DASH_RE = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")
_CAP_RATE_RE = re.compile(
    r"\bcap\s*rate\b(?:\s*[:=]\s*|\s+is\s+|\s+of\s+)?([0-9]+(?:\.[0-9]+)?%)",
    re.IGNORECASE,
)
_TOKEN_RE = re.compile(r"\w+")


def clean_documents(
    documents: tuple[IngestedDocument, ...],
    config: CleaningConfig | None = None,
) -> tuple[CleanSegment, ...]:
    """Clean multiple documents while preserving deterministic order."""
    cfg = config or CleaningConfig()
    cleaned: list[CleanSegment] = []
    for document in documents:
        cleaned.extend(clean_ingested_document(document, cfg))
    return tuple(cleaned)


def clean_ingested_document(
    document: IngestedDocument,
    config: CleaningConfig | None = None,
) -> tuple[CleanSegment, ...]:
    """Clean one document into deduplicated, normalized segments."""
    cfg = config or CleaningConfig()
    repeated_lines = _detect_repeated_edge_lines(document.pages)
    seen_tokens: list[set[str]] = []
    output_segments: list[CleanSegment] = []

    for page in document.pages:
        cleaned_text, stage_warnings = _clean_page_text(page.text, repeated_lines)
        normalized_text, normalized_fields = _normalize_text(cleaned_text)
        content_type = _infer_content_type(normalized_text)

        page_warnings = list(page.warnings)
        if page.scan_suspected and "scan_suspected" not in page_warnings:
            page_warnings.append("scan_suspected")

        if len(normalized_text) < cfg.min_text_length:
            continue

        current_tokens = _tokenize(normalized_text)
        if _is_near_duplicate(current_tokens, seen_tokens, cfg.dedupe_similarity_threshold):
            continue
        seen_tokens.append(current_tokens)

        all_warnings = tuple(sorted(set(stage_warnings + page_warnings + list(document.warnings))))
        output_segments.append(
            CleanSegment(
                text=normalized_text,
                doc_id=document.doc_id,
                page_span=(page.page_index, page.page_index),
                silo=document.silo,
                content_type=content_type,
                normalized_fields=normalized_fields,
                warnings=all_warnings,
            )
        )
    return tuple(output_segments)


def _detect_repeated_edge_lines(pages: tuple[PageExtraction, ...]) -> set[str]:
    counts: dict[str, int] = {}
    for page in pages:
        lines = _to_lines(page.text)
        if len(lines) < 2:
            continue
        edge_lines = {lines[0], lines[-1]}
        for line in edge_lines:
            if line:
                counts[line] = counts.get(line, 0) + 1
    return {line for line, count in counts.items() if count > 1}


def _clean_page_text(text: str, repeated_lines: set[str]) -> tuple[str, list[str]]:
    warnings: list[str] = []
    kept_lines: list[str] = []
    for raw_line in _to_lines(text):
        if raw_line in repeated_lines:
            warnings.append("removed_repeated_header_footer")
            continue
        if _PAGE_NUMBER_RE.match(raw_line):
            warnings.append("removed_page_number_line")
            continue
        kept_lines.append(raw_line)

    cleaned = "\n".join(kept_lines).strip()
    return cleaned, warnings


def _normalize_text(text: str) -> tuple[str, dict[str, str]]:
    normalized_fields: dict[str, str] = {}
    value = _MULTISPACE_RE.sub(" ", text).strip()

    value = _AREA_UNIT_RE.sub("sqft", value)

    def _currency_replacer(match: re.Match[str]) -> str:
        number = match.group(1).replace(" ", "")
        suffix = (match.group(2) or "").upper()
        normalized = f"${number}{suffix}"
        normalized_fields["currency_example"] = normalized
        return normalized

    value = _CURRENCY_TEXT_RE.sub(_currency_replacer, value)

    def _slash_date_replacer(match: re.Match[str]) -> str:
        month, day, year = match.groups()
        iso = f"{year}-{int(month):02d}-{int(day):02d}"
        normalized_fields["date_example"] = iso
        return iso

    value = _DATE_SLASH_RE.sub(_slash_date_replacer, value)

    dash_match = _DATE_DASH_RE.search(value)
    if dash_match:
        year, month, day = dash_match.groups()
        normalized_fields.setdefault("date_example", f"{year}-{int(month):02d}-{int(day):02d}")

    cap_rate_match = _CAP_RATE_RE.search(value)
    if cap_rate_match:
        normalized_fields["cap_rate"] = cap_rate_match.group(1)

    return value, normalized_fields


def _infer_content_type(text: str) -> str:
    table_cues = 0
    if "|" in text:
        table_cues += 1
    if "\t" in text:
        table_cues += 1
    if len(re.findall(r"[^\n]+\s{2,}[^\n]+", text)) > 0:
        table_cues += 1
    return "table_like" if table_cues >= 1 else "narrative"


def _to_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in _TOKEN_RE.findall(text)}


def _is_near_duplicate(
    tokens: set[str],
    seen_tokens: list[set[str]],
    threshold: float,
) -> bool:
    if not tokens:
        return True
    for seen in seen_tokens:
        intersection = len(tokens.intersection(seen))
        union = len(tokens.union(seen))
        similarity = intersection / union if union else 1.0
        if similarity >= threshold:
            return True
    return False
