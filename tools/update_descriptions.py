"""
update_descriptions.py
======================
Reads lesson/assignment description text files and injects
them into the corresponding course HTML pages.

Run from the project root:
    python tools/update_descriptions.py

Add a course name to update only that course:
    python tools/update_descriptions.py "Intro to Excel"
"""

import os
import re
import sys

# ── Configuration ─────────────────────────────────────────────────────────────
COURSES = {
    "Intro to Excel": {
        "html": "courses/intro-to-microsoft-excel.html",
        "sources": [
            {
                "txt":        "downloads/Intro to Excel/ENGLISH/LESSONS/lesson_descriptions.txt",
                "lang_tag":   "english",
                "item_types": {
                    "Lesson":     "Lesson",
                    "Assignment": "Assignment",
                },
            },
            {
                "txt":        "downloads/Intro to Excel/SPANISH/LECCIONES/descripciones_lecciones.txt",
                "lang_tag":   "spanish",
                "item_types": {
                    "Leccion": "Lecci",   # matches "Lección" in summary (HTML entity)
                    "Tarea":   "Tarea",
                },
            },
        ],
    },
    # ── Add more courses here as you populate them, e.g.: ─────────────────────
    # "Intro to Word": {
    #     "html": "courses/intro-to-microsoft-word.html",
    #     "sources": [ ... ],
    # },
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_descriptions(txt_path):
    """
    Parse a description text file into a dict:
        { "Lesson 1": "description text", "Assignment 2": "...", ... }
    Lines starting with # are ignored. Labels look like [Lesson 1].
    """
    descriptions = {}
    current_label = None
    current_lines = []

    with open(txt_path, encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")

            if line.lstrip().startswith("#"):
                continue

            label_match = re.match(r"^\[(.+?)\]", line.strip())
            if label_match:
                if current_label is not None:
                    descriptions[current_label] = " ".join(current_lines).strip()
                current_label = label_match.group(1).strip()
                current_lines = []
                continue

            if current_label is not None and line.strip():
                current_lines.append(line.strip())

    if current_label is not None:
        descriptions[current_label] = " ".join(current_lines).strip()

    return descriptions


def inject_descriptions(html_path, lang_tag, item_types, descriptions):
    """
    For each description, find the matching <details> block inside the
    correct language tab panel and replace the item-description paragraph.

    Strategy:
      1. Slice out just the panel's HTML by finding its open/close markers.
      2. Within that slice, find each <summary> that contains the right
         keyword + number.
      3. From that summary, find the next item-description paragraph and
         replace its content.
    """
    with open(html_path, encoding="utf-8") as f:
        html = f.read()

    # ── Find the tab panel slice ───────────────────────────────────────────────
    open_marker  = f'id="tab-{lang_tag}"'
    close_marker = f'<!-- /tab-{lang_tag} -->'

    panel_start_idx = html.find(open_marker)
    if panel_start_idx == -1:
        print(f"  Warning: tab panel 'tab-{lang_tag}' not found in HTML.")
        return 0

    panel_end_idx = html.find(close_marker, panel_start_idx)
    if panel_end_idx == -1:
        print(f"  Warning: closing marker for 'tab-{lang_tag}' not found.")
        return 0

    panel_end_idx += len(close_marker)
    panel_html = html[panel_start_idx:panel_end_idx]

    updated = 0

    for label, description in descriptions.items():
        if not description:
            continue

        # Match label to an item type keyword + number
        matched_keyword = None
        item_number = None
        for txt_prefix, html_keyword in item_types.items():
            m = re.match(rf"^{re.escape(txt_prefix)}\s+(\d+)$", label, re.IGNORECASE)
            if m:
                matched_keyword = html_keyword
                item_number = m.group(1)
                break

        if not matched_keyword:
            print(f"  Warning: could not match label '[{label}]' to an item type — skipping.")
            continue

        # Find the summary containing keyword + number inside the panel.
        # Summaries look like: <summary>Lesson 1 &mdash; ...<span...>+</span></summary>
        summary_pattern = re.compile(
            rf'<summary>{re.escape(matched_keyword)}[^<]*\b{item_number}\b.*?</summary>',
            re.DOTALL | re.IGNORECASE
        )
        summary_match = summary_pattern.search(panel_html)

        if not summary_match:
            print(f"  Warning: summary for '[{label}]' not found in tab '{lang_tag}' — skipping.")
            continue

        # From end of that summary, find the next item-description and replace it
        after_summary = summary_match.end()
        desc_pattern  = re.compile(
            r'(<p class="item-description">)(.*?)(</p>)',
            re.DOTALL
        )
        desc_match = desc_pattern.search(panel_html, after_summary)

        if not desc_match:
            print(f"  Warning: item-description for '[{label}]' not found — skipping.")
            continue

        panel_html = (
            panel_html[:desc_match.start()]
            + desc_match.group(1)
            + description
            + desc_match.group(3)
            + panel_html[desc_match.end():]
        )
        updated += 1
        print(f"  Updated: [{label}]")

    # Splice panel back into full HTML
    html = html[:panel_start_idx] + panel_html + html[panel_end_idx:]

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    return updated


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    script_dir   = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    filter_course = sys.argv[1] if len(sys.argv) > 1 else None

    for course_name, config in COURSES.items():
        if filter_course and filter_course.lower() not in course_name.lower():
            continue

        html_path = os.path.join(project_root, config["html"])
        if not os.path.exists(html_path):
            print(f"\n[{course_name}] HTML not found: {html_path}")
            continue

        print(f"\n[{course_name}]")

        total = 0
        for source in config["sources"]:
            txt_path = os.path.join(project_root, source["txt"])
            if not os.path.exists(txt_path):
                print(f"  Skipping — text file not found: {txt_path}")
                continue

            descriptions = parse_descriptions(txt_path)
            if not descriptions:
                print(f"  No descriptions found in {os.path.basename(txt_path)}")
                continue

            print(f"  Language: {source['lang_tag']}")
            n = inject_descriptions(
                html_path,
                source["lang_tag"],
                source["item_types"],
                descriptions,
            )
            total += n

        print(f"  Done — {total} description(s) updated in {config['html']}")

    print("\nAll courses processed.")


if __name__ == "__main__":
    main()
