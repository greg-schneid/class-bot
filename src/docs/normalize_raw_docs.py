from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
import shutil
from pathlib import Path

from pypdf import PdfReader


ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "data" / "course_docs" / "raw"
RAW_PROCESSED_DIR = RAW_DIR / "processed"
COURSE_DOCS_DIR = ROOT_DIR / "data" / "course_docs"
COURSE_UPDATES_DIR = ROOT_DIR / "data" / "course_updates"
MANIFEST_PATH = ROOT_DIR / "data" / "manifest.json"


@dataclass(frozen=True)
class RawDoc:
    filename: str
    course_code: str
    display_name: str
    doc_label: str
    archive_duplicates: tuple[str, ...] = ()

    @property
    def path(self) -> Path:
        primary = RAW_DIR / self.filename
        if primary.exists():
            return primary
        processed = RAW_PROCESSED_DIR / self.filename
        return processed


RAW_DOCS: tuple[RawDoc, ...] = (
    RawDoc(
        filename="Spring 2026_ Introduction to Thermodynamics and Heat Transfer.html",
        course_code="MTE309",
        display_name="MTE 309",
        doc_label="Course outline",
    ),
    RawDoc(
        filename="Course schedule_MTE309_S26.pdf",
        course_code="MTE309",
        display_name="MTE 309",
        doc_label="Course schedule",
    ),
    RawDoc(
        filename="MTE 320 - Spring 2026 - Course Outline.pdf",
        course_code="MTE320",
        display_name="MTE 320",
        doc_label="Course outline",
    ),
    RawDoc(
        filename="MTE 320 - Lab Schedule Spring 2026.pdf",
        course_code="MTE320",
        display_name="MTE 320",
        doc_label="Lab schedule",
        archive_duplicates=("MTE 320 - Lab Schedule Spring 2026 (1).pdf",),
    ),
    RawDoc(
        filename="MTE_321__Outline.pdf",
        course_code="MTE321",
        display_name="MTE 321",
        doc_label="Course outline",
    ),
    RawDoc(
        filename="MTE321_Project1.pdf",
        course_code="MTE321",
        display_name="MTE 321",
        doc_label="Project 1",
    ),
    RawDoc(
        filename="Spring 2026_ Microprocessor Systems and Interfacing for Mechatronics Engineering.html",
        course_code="MTE325",
        display_name="MTE 325",
        doc_label="Course outline",
    ),
    RawDoc(
        filename="MTE 325 Project.tex",
        course_code="MTE325",
        display_name="MTE 325",
        doc_label="Project guide",
    ),
    RawDoc(
        filename="Spring 2026_ Systems Models 1.html",
        course_code="MTE351",
        display_name="MTE 351",
        doc_label="Course outline",
    ),
    RawDoc(
        filename="MTE 3A Makeup Lecture Schedule_S26_Feb 18, 2026.pdf",
        course_code="GENERAL",
        display_name="General Mechatronics Info",
        doc_label="3A makeup lecture schedule",
    ),
    RawDoc(
        filename="MTE 3A Mid-term Exam Schedule_S26_Feb 27, 2026.pdf",
        course_code="GENERAL",
        display_name="General Mechatronics Info",
        doc_label="3A midterm exam schedule",
    ),
)

HTML_NOISE_PATTERNS: tuple[str, ...] = (
    r"<div id=\"local-copy-info\".*?</div>",
    r"<details[^>]*>\s*<summary>\s*Revision History\s*</summary>.*?</details>",
    r"<div class=\"clamp-width no-print\">.*?</div>\s*<article",
)

SKIP_EXACT_LINES: set[str] = {
    "Table of Contents",
    "schedule data automatically refreshed daily",
    "Course",
    "Published",
    "Revision History",
    "Faculty of Engineering Guiding Practices",
    "Faculty of Engineering Guiding Practices.",
    "Accreditation Data Collection",
}

SKIP_LINE_PREFIXES: tuple[str, ...] = (
    "View requirements for ",
    "This is an offline copy which can be shared, archived, or embedded.",
    "view original document online",
    "If you require a PDF version for any reason please use your browser's print function.",
    "A reminder that W Store has partnered",
    "*W Store can no longer request print books",
)

SKIP_BLOCK_PREFIXES: tuple[str, ...] = (
    "Turnitin.com:",
    "Mental Health:",
    "Academic integrity:",
    "Academic Integrity:",
    "Grievance:",
    "Discipline:",
    "Appeals:",
    "Territorial Acknowledgement",
    "Inclusive Teaching-Learning Spaces",
    "Inclusive Teaching–Learning Spaces",
    "Religious & Spiritual Observances",
    "Respectful Communication and Pronouns",
    "Mental Health and Wellbeing Resources",
    "Intellectual Property",
    "Continuity Plan",
    "Declaring Absences",
    "Declaring absences:",
    "Rescheduling Co-op Interviews",
    "Note for students with disabilities and disabling conditions:",
    "Note for Students with Disabilities and Disabling Conditions:",
)

SKIP_BLOCK_EXACT_LINES: set[str] = {
    "Accreditation Data Collection",
    "Faculty of Engineering Guiding Practices",
    "Faculty of Engineering Guiding Practices.",
}

SKIP_LINE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\*{5,}$"),
    re.compile(r"^Published\s+[A-Z][a-z]+\s+\d{1,2},\s+\d{4}\s+\(latest\)$"),
    re.compile(r"^\d+\s+University of Waterloo$"),
    re.compile(r"^[©©]\s*University of Waterloo,?\s+Spring\s+\d{4}$"),
)

SKIP_SECTION_TITLES: set[str] = {
    "## University Policy",
    "University Policy",
}

PDF_SECTION_TITLES: set[str] = {
    "Class Schedule",
    "Instructional Team",
    "Course Description",
    "Learning Outcomes",
    "Tentative Class Plan",
    "Required Materials & Technologies",
    "Readings",
    "Assessments & Activities",
    "Late / Missed Content",
    "Assignment Screening",
    "Generative AI",
    "Generative AI Policy",
    "Administrative Policy",
    "Course outline",
    "Study Material",
    "Laboratory Studies",
    "Notes on labs",
    "Tutorials",
    "LEARN",
    "Email Correspondences",
    "Marking Scheme",
    "Course Timetable",
    "Teaching Team’s Contact Information",
    "General Notes",
    "Project Rules",
    "Exam Rules",
    "Project",
    "Grading",
    "Exams",
    "Midterm Exam",
    "Final Exam",
    "Course Deliverables",
    "Notice of Recording",
}


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._ignored_depth = 0
        self._text_parts: list[str] = []
        self._table_cell_parts: list[str] = []
        self._table_row: list[str] = []
        self._in_table = False
        self._in_cell = False
        self._list_depth = 0
        self._list_item_open = False
        self.lines: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style"}:
            self._ignored_depth += 1
            return
        if self._ignored_depth:
            return
        if tag == "table":
            self._flush_text()
            self._in_table = True
        elif tag == "tr":
            self._flush_text()
            self._table_row = []
        elif tag in {"td", "th"}:
            self._in_cell = True
            self._table_cell_parts = []
        elif tag in {"ul", "ol"}:
            self._list_depth += 1
        elif tag == "li":
            self._flush_text()
            self._list_item_open = True
            self._text_parts.append("- ")
        elif tag == "br":
            self._flush_text()

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._ignored_depth > 0:
            self._ignored_depth -= 1
            return
        if self._ignored_depth:
            return
        if tag in {"td", "th"} and self._in_cell:
            cell_text = " ".join("".join(self._table_cell_parts).split())
            if cell_text:
                self._table_row.append(cell_text)
            self._table_cell_parts = []
            self._in_cell = False
        elif tag == "tr":
            row_text = " | ".join(part for part in self._table_row if part)
            if row_text:
                self.lines.append(row_text)
            self._table_row = []
        elif tag == "table":
            self._in_table = False
            self.lines.append("")
        elif tag in {"p", "div", "section", "article", "figure", "figcaption", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._flush_text()
        elif tag == "li":
            self._flush_text()
            self._list_item_open = False
        elif tag in {"ul", "ol"}:
            self._list_depth = max(0, self._list_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        if self._in_cell:
            self._table_cell_parts.append(data)
        else:
            self._text_parts.append(data)

    def _flush_text(self) -> None:
        text = " ".join("".join(self._text_parts).split())
        if text:
            self.lines.append(text)
        self._text_parts = []


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def extract_tex_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    document_match = re.search(r"\\begin\{document\}(.*)\\end\{document\}", text, flags=re.DOTALL)
    if document_match:
        text = document_match.group(1)
    introduction_match = re.search(r"\\section\{Introduction\}(.*)", text, flags=re.DOTALL)
    if introduction_match:
        text = introduction_match.group(0)
    text = re.sub(r"(?m)^%.*$", "", text)
    text = text.replace("\\\\", "\n")
    text = text.replace("\\%", "%")
    text = text.replace("\\_", "_")
    text = text.replace("~", " ")
    text = re.sub(r"\\(?:label|ref|pageref|autoref)\{[^}]*\}", " ", text)
    text = re.sub(r"\\url\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\href\{[^}]*\}\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\begin\{[^}]+\}", "\n", text)
    text = re.sub(r"\\end\{[^}]+\}", "\n", text)
    text = re.sub(r"\\(?:documentclass|input|hyphenation|renewcommand|setcounter|pagestyle)\b.*", "\n", text)
    text = re.sub(r"\\(?:maketitle|tableofcontents|newpage|vspace\*?\{[^}]*\})", "\n", text)
    text = re.sub(r"\\(?:section|subsection|subsubsection)\*?\{([^}]*)\}", r"\n\1\n", text)
    text = re.sub(r"\\(?:title|author|date)\{([^}]*)\}", r"\n\1\n", text)
    text = re.sub(r"\\item(?:\[[^]]+\])?", "\n- ", text)
    text = re.sub(r"\\[A-Za-z]+\*?(?:\[[^]]*\])?(?:\{([^}]*)\})?", r" \1 ", text)
    text = re.sub(r"\$[^$]*\$", " ", text)
    text = re.sub(r"(?m)^\[[^]]+\]$", "", text)
    text = re.sub(r"(?m)^\{\|.*\|\}$", "", text)
    text = re.sub(r"(?m)^[{}\[\]=,.\- ]+$", "", text)
    text = re.sub(r"(?m)^[A-Za-z]+:[A-Za-z]", lambda match: match.group(0).replace(":", ": "), text)
    text = re.sub(r"(?m)^.*(?:LaTeX Template|Original author|License:|CC BY-NC-SA).*$", "", text)
    text = re.sub(r"(?m)^\s*(?:fig|sec|app):[A-Za-z0-9_-]+\s*$", "", text)
    text = re.sub(r"(?m)^\s*h!+\s*$", "", text)
    return text


def extract_html_text(path: Path) -> str:
    raw_html = path.read_text(encoding="utf-8", errors="ignore")
    for pattern in HTML_NOISE_PATTERNS:
        raw_html = re.sub(pattern, "", raw_html, flags=re.DOTALL)
    article_match = re.search(
        r"<article class=\"outline-content\">(.*?)</article>",
        raw_html,
        flags=re.DOTALL,
    )
    html_to_parse = article_match.group(1) if article_match else raw_html

    parser = VisibleTextParser()
    parser.feed(html_to_parse)
    parser.close()
    lines = _cleanup_html_lines(_dedupe_lines(parser.lines))
    return "\n".join(lines)


def _dedupe_lines(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    previous = None
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line == previous:
            continue
        cleaned.append(line)
        previous = line
    return cleaned


def normalize_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = text.replace("", "-")
    text = text.replace("•", "-")
    text = text.replace("\uf0b7", "-")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def cleanup_extracted_text(text: str) -> str:
    text = normalize_text(text)
    text = re.sub(r"(?m)^## .+\n(?=\n## |\Z)", "", text)
    text = re.sub(r"\n## Administrative Policy.*?(?=\n## |\Z)", "\n", text, flags=re.DOTALL)
    text = re.sub(r"(?m)^([A-Za-z][A-Za-z /()'&.-]+):(?=\S)", r"\1: ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _cleanup_html_lines(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen_titles = False
    for line in lines:
        line = normalize_text(line)
        line = re.sub(r"(@uwaterloo\.ca)book a meeting\b", r"\1", line, flags=re.IGNORECASE)
        line = normalize_text(line)
        if re.fullmatch(r"Class Schedule|Instructional Team|Course Description|Learning Outcomes|Tentative Class Plan|Required Materials & Technologies|Readings|Technology|Other Materials|Assessments & Activities|Late / Missed Content|Assignment Screening|Generative AI(?: Policy)?|Notice of Recording|Administrative Policy|University Policy", line):
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            cleaned.append(f"## {line}")
            seen_titles = True
            continue
        cleaned.append(line)

    if seen_titles and cleaned and cleaned[0] == "":
        cleaned = cleaned[1:]
    return _filter_noise_lines(_collapse_blank_lines(cleaned))


def _cleanup_pdf_lines(text: str) -> str:
    lines = [normalize_text(line) for line in text.splitlines()]
    cleaned: list[str] = []
    skipping_contents = False
    found_first_section = False
    for line in lines:
        if not line:
            cleaned.append("")
            continue
        if line == "Contents":
            skipping_contents = True
            continue
        if skipping_contents:
            if re.fullmatch(r"1\s+Class Schedule", line):
                skipping_contents = False
                found_first_section = True
            else:
                continue
        if re.fullmatch(r"MTE \d+\s+[—-].*Spring 2026", line):
            continue
        if re.fullmatch(r"\d+\s+MTE \d+.*", line):
            continue
        if found_first_section and re.fullmatch(r"1\s+Class Schedule", line):
            found_first_section = False
        section_match = re.fullmatch(r"\d+\s+(.+)", line)
        if section_match and section_match.group(1) in PDF_SECTION_TITLES:
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            cleaned.append(f"## {section_match.group(1)}")
            continue
        if line in PDF_SECTION_TITLES:
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            cleaned.append(f"## {line}")
            continue
        cleaned.append(line)
    filtered = _filter_noise_lines(_collapse_blank_lines(cleaned))
    return "\n".join(filtered)


def _filter_noise_lines(lines: list[str]) -> list[str]:
    filtered: list[str] = []
    skip_until_heading = False
    skip_block = False

    for line in lines:
        if skip_block:
            if _is_heading_line(line):
                skip_block = False
            elif _starts_skip_block(line):
                continue
            else:
                continue

        if skip_until_heading:
            if _is_heading_line(line):
                skip_until_heading = False
            else:
                continue

        if _should_skip_entire_section(line):
            skip_until_heading = True
            continue

        if _starts_skip_block(line):
            skip_block = True
            continue

        if _should_skip_line(line):
            continue

        filtered.append(line)

    return _collapse_blank_lines(filtered)


def _should_skip_line(line: str) -> bool:
    if not line:
        return False
    if line in SKIP_EXACT_LINES:
        return True
    if any(line.startswith(prefix) for prefix in SKIP_LINE_PREFIXES):
        return True
    if line.startswith("https://"):
        return True
    return any(pattern.fullmatch(line) for pattern in SKIP_LINE_PATTERNS)


def _starts_skip_block(line: str) -> bool:
    return line in SKIP_BLOCK_EXACT_LINES or any(line.startswith(prefix) for prefix in SKIP_BLOCK_PREFIXES)


def _should_skip_entire_section(line: str) -> bool:
    normalized = line.strip()
    return normalized in SKIP_SECTION_TITLES or bool(
        re.fullmatch(r"\d+\s+(?:University Policy|Administrative Policy)", normalized)
    )


def _is_heading_line(line: str) -> bool:
    return line.startswith("## ") or bool(re.fullmatch(r"\d+\s+[A-Z].*", line))


def _collapse_blank_lines(lines: list[str]) -> list[str]:
    collapsed: list[str] = []
    previous_blank = False
    for line in lines:
        is_blank = not line
        if is_blank and previous_blank:
            continue
        collapsed.append(line)
        previous_blank = is_blank
    while collapsed and not collapsed[0]:
        collapsed.pop(0)
    while collapsed and not collapsed[-1]:
        collapsed.pop()
    return collapsed


def build_course_markdown(display_name: str, docs: list[RawDoc]) -> str:
    sections = [f"# {display_name}", "", "Standardized local source compiled from raw course files.", ""]
    sections.append("## Source Files")
    for doc in docs:
        sections.append(f"- `{doc.path.relative_to(ROOT_DIR)}` ({doc.doc_label})")
    sections.append("")

    extracted_sections: list[str] = []
    for doc in docs:
        suffix = doc.path.suffix.lower()
        if suffix == ".pdf":
            extracted = _cleanup_pdf_lines(extract_pdf_text(doc.path))
        elif suffix == ".tex":
            extracted = normalize_text(extract_tex_text(doc.path))
        else:
            extracted = extract_html_text(doc.path)
        extracted = _postprocess_extracted_text(doc.course_code, doc.doc_label, extracted)
        extracted = cleanup_extracted_text(extracted)
        if any(extracted and extracted in prior for prior in extracted_sections):
            continue
        extracted_sections.append(extracted)

        sections.append(f"## {doc.doc_label}")
        sections.append(f"Raw file: `{doc.path.relative_to(ROOT_DIR)}`")
        sections.append("")
        sections.append(extracted)
        sections.append("")

    markdown = "\n".join(sections).strip()
    markdown = re.sub(r"(?m)^## .+\n(?=\n## |\Z)", "", markdown)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    return markdown.strip() + "\n"


def _postprocess_extracted_text(course_code: str, doc_label: str, text: str) -> str:
    cleaned = text
    if course_code == "MTE320" and doc_label == "Course outline":
        cleaned = re.sub(
            r"\nMTE 320 Lab Schedule - Spring 2026.*?(?=\n## |\Z)",
            "\n",
            cleaned,
            flags=re.DOTALL,
        )
        learn_with_table = re.search(
            r"(## LEARN\n.*?drop boxes\.)\n\nLab\s+Description\s+In-Lab\s+Practice\s+Post-lab Report\s+Due Dates\s+Post-lab\s+Quiz.*?(?=\n## |\Z)",
            cleaned,
            flags=re.DOTALL,
        )
        if learn_with_table:
            cleaned = cleaned.replace(learn_with_table.group(0), learn_with_table.group(1))

    if course_code == "MTE321" and doc_label == "Course outline":
        cleaned = re.sub(
            r"Letting\s+Wdenote.*?Any reduction in the report weight is transferred to the exam weight\.",
            (
                "Project weights depend on the exam average. Each project keeps its full 25% weight if the "
                "average of the midterm and final is at least 55%. If the exam average is between 50% and 55%, "
                "each project weight is reduced proportionally. If the exam average is below 50%, each project "
                "weight becomes 0%, and the removed weight shifts to the exams."
            ),
            cleaned,
            flags=re.DOTALL,
        )
        cleaned = re.sub(r"TA 1:\s*Arya Amiri", "TA 1: Arya Amiri", cleaned)
        cleaned = re.sub(r"TA 2:\s*Mohamed Aboelkhier", "TA 2: Mohamed Aboelkhier", cleaned)
        cleaned = re.sub(r"TA 3:\s*Mohit\.?", "TA 3: Mohit", cleaned)
        cleaned = cleaned.replace("-All lectures and tutorials arein-person.", "- All lectures and tutorials are in-person.")
        cleaned = cleaned.replace("-In-class lecture notes will be posted on LEARN after each lecture.", "- In-class lecture notes will be posted on LEARN after each lecture.")
        cleaned = cleaned.replace("-A tentative course schedule is provided with this outline.", "- A tentative course schedule is provided with this outline.")
        cleaned = cleaned.replace("-For questions regarding course materials or projects, students are encouraged to first consult the", "- For questions regarding course materials or projects, students are encouraged to first consult the")
        cleaned = cleaned.replace("Final Exam Date & Location:TBD", "Final Exam Date & Location: TBD")

    if course_code == "MTE325" and doc_label == "Course outline":
        cleaned = re.sub(
            r"Overall Grade Calculation.*?Your overall grade is calculated using the following expression:.*?(?=\nNOTES:)",
            (
                "Overall Grade Calculation\n"
                "Project work is worth up to 30% and exams are worth at least 70%. To keep the full 30% project "
                "weight, the exam average must be at least 55%. If the exam average falls below 55%, the project "
                "weight decreases, with a minimum project weight of 15%, and the exam weight increases accordingly.\n"
            ),
            cleaned,
            flags=re.DOTALL,
        )

    if course_code == "MTE325" and doc_label == "Project guide":
        cleaned = re.sub(
            r"Tasks\s+This project is divided into multiple deliverables.*?\*Final project grade is capped at 30 points including bonuses\.",
            (
                "Tasks\n\n"
                "This project is divided into multiple deliverables across the term and is worth 30% of the final grade.\n"
                "- SOP Quiz: 1 point, before session 1\n"
                "- Tool Test: 0 points, session 1\n"
                "- Polling and Interrupts: 7 points, session 2\n"
                "- Limit Switches: 4 points, session 3\n"
                "- ADC Characterization: 5 points, session 3/4\n"
                "- Motor Characterization: 4 points plus 1 bonus point, session 4/5\n"
                "- Functional Objective: 4 points, session 5/6\n"
                "- Lab Notes: 3 points, after each work session as an online submission\n"
                "- Block Diagram: 2 points, session 3 onward as an online submission\n"
                "Final project grade is capped at 30 points including bonuses."
            ),
            cleaned,
            flags=re.DOTALL,
        )
        cleaned = re.sub(r"(?m)^\s*\{[^{}\n]+\}\{[^{}\n]+\}.*$", "", cleaned)
        cleaned = re.sub(r"(?m)^\s*Success Condition:.*$", "", cleaned)
        if "Before Your First Session" in cleaned:
            cleaned = cleaned.split("Before Your First Session", 1)[0].rstrip() + (
                "\n\nDetailed setup, tooling, and implementation instructions follow in the original project guide. "
                "They were omitted from this normalized summary to keep retrieval focused on course logistics, "
                "grading, expectations, and allowed collaboration.\n"
            )

    return cleaned


def build_updates_markdown(display_name: str) -> str:
    return (
        f"# {display_name} Updates\n\n"
        "Manually maintained updates and overrides go here.\n\n"
        "- Add newer policy changes, due date corrections, or announcement-driven overrides here.\n"
    )


def write_course_docs() -> dict[str, dict[str, str]]:
    COURSE_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    COURSE_UPDATES_DIR.mkdir(parents=True, exist_ok=True)
    RAW_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    grouped: dict[str, list[RawDoc]] = {}
    display_names: dict[str, str] = {}
    for doc in RAW_DOCS:
        if not doc.path.exists():
            continue
        grouped.setdefault(doc.course_code, []).append(doc)
        display_names[doc.course_code] = doc.display_name

    manifest_courses: dict[str, dict[str, str]] = {}
    for course_code in sorted(grouped):
        docs = grouped[course_code]
        docs.sort(key=lambda item: (item.doc_label, item.path.name))

        course_doc_path = COURSE_DOCS_DIR / f"{course_code}.md"
        course_doc_path.write_text(
            build_course_markdown(display_names[course_code], docs),
            encoding="utf-8",
        )

        updates_doc_path = COURSE_UPDATES_DIR / f"{course_code}_updates.md"
        if not updates_doc_path.exists():
            updates_doc_path.write_text(
                build_updates_markdown(display_names[course_code]),
                encoding="utf-8",
            )

        manifest_courses[course_code] = {
            "display_name": display_names[course_code],
            "main_doc": str(course_doc_path.relative_to(ROOT_DIR)),
            "updates_doc": str(updates_doc_path.relative_to(ROOT_DIR)),
        }

    return manifest_courses


def archive_processed_files() -> None:
    for doc in RAW_DOCS:
        _archive_if_needed(RAW_DIR / doc.filename)
        for duplicate in doc.archive_duplicates:
            _archive_if_needed(RAW_DIR / duplicate)


def _archive_if_needed(source: Path) -> None:
    if not source.exists() or not source.is_file():
        return
    target = RAW_PROCESSED_DIR / source.name
    if target.exists():
        if source.read_bytes() == target.read_bytes():
            source.unlink()
            return
        target = _dedupe_target(target)
    shutil.move(str(source), str(target))


def _dedupe_target(target: Path) -> Path:
    stem = target.stem
    suffix = target.suffix
    counter = 2
    candidate = target
    while candidate.exists():
        candidate = target.with_name(f"{stem}-{counter}{suffix}")
        counter += 1
    return candidate


def write_manifest(courses: dict[str, dict[str, str]]) -> None:
    manifest = {
        "version": 1,
        "courses": courses,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    archive_processed_files()
    courses = write_course_docs()
    write_manifest(courses)
    print(f"Normalized {len(courses)} course documents from {RAW_DIR.relative_to(ROOT_DIR)}.")


if __name__ == "__main__":
    main()
