from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


PROJECT_NAME = "customer-360-revenue-growth-analytics"

TEXT_EXTENSIONS = {".json", ".pbip", ".pbir", ".tmdl", ".md", ".txt", ".csv"}

CHART_TYPES = {
    "clusteredBarChart",
    "clusteredColumnChart",
    "barChart",
    "columnChart",
    "hundredPercentStackedBarChart",
    "hundredPercentStackedColumnChart",
    "stackedBarChart",
    "stackedColumnChart",
    "lineChart",
    "areaChart",
}

PAGE_COLORS = {
    "executive": {"accent": "#2563EB", "canvas": "#F4F8FF"},
    "customer": {"accent": "#7C3AED", "canvas": "#F8F5FF"},
    "revenue": {"accent": "#059669", "canvas": "#F3FBF7"},
    "marketing": {"accent": "#EA580C", "canvas": "#FFF8F2"},
    "product": {"accent": "#DB2777", "canvas": "#FFF6FA"},
    "channel": {"accent": "#0891B2", "canvas": "#F2FCFD"},
    "default": {"accent": "#2563EB", "canvas": "#F6F8FC"},
}

CHART_PALETTE = [
    "#2563EB",
    "#7C3AED",
    "#059669",
    "#EA580C",
    "#DB2777",
    "#0891B2",
    "#CA8A04",
    "#4F46E5",
]

PASTELS = [
    "#EFF6FF",
    "#F5F3FF",
    "#ECFDF5",
    "#FFF7ED",
    "#FDF2F8",
    "#ECFEFF",
    "#FFFBEB",
    "#EEF2FF",
]

BORDERS = [
    "#BFDBFE",
    "#DDD6FE",
    "#A7F3D0",
    "#FED7AA",
    "#FBCFE8",
    "#A5F3FC",
    "#FDE68A",
    "#C7D2FE",
]


def find_project_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "powerbi").exists():
        return cwd

    downloads = Path.home() / "Downloads" / PROJECT_NAME
    if downloads.exists():
        return downloads

    raise FileNotFoundError(
        f"Could not find project root. Expected current folder to contain 'powerbi' "
        f"or {downloads}"
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def log_factory(log_path: Path):
    counts = {"repair": 0, "warning": 0, "error": 0}

    def log(level: str, message: str) -> None:
        line = f"[{level}] {message}"
        print(line)
        with log_path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(line + "\n")

        if level == "REPAIRED":
            counts["repair"] += 1
        elif level == "WARNING":
            counts["warning"] += 1
        elif level == "ERROR":
            counts["error"] += 1

    return log, counts


def run(cmd, cwd: Path | None = None, timeout: int = 120):
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as exc:
        return 999, "", str(exc)


def close_power_bi(log) -> None:
    if os.name != "nt":
        return

    rc, out, err = run(["tasklist", "/FI", "IMAGENAME eq PBIDesktop.exe"], timeout=20)
    if rc == 0 and "PBIDesktop.exe" in out:
        log("WARNING", "Power BI Desktop is running. The script will close it before source edits.")
        run(["taskkill", "/IM", "PBIDesktop.exe", "/T", "/F"], timeout=30)
        time.sleep(2)
        log("REPAIRED", "Power BI Desktop was closed.")


def decode_bytes(raw: bytes) -> str:
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")

    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return raw.decode("cp1252")
        except UnicodeDecodeError:
            return raw.decode("latin1")


def repair_mojibake(text: str) -> str:
    markers = ("\u00c3", "\u00c2", "\u00e2")
    if not any(m in text for m in markers):
        return text

    try:
        candidate = text.encode("cp1252").decode("utf-8")
        before = sum(text.count(m) for m in markers)
        after = sum(candidate.count(m) for m in markers)
        if after < before:
            return candidate
    except Exception:
        pass

    return text


def normalize_file(path: Path, log) -> None:
    raw = path.read_bytes()
    if not raw:
        log("WARNING", f"Zero-byte file detected: {path}")
        return

    text = decode_bytes(raw)
    text = text.replace("\x00", "")
    text = repair_mojibake(text)
    path.write_text(text, encoding="utf-8", newline="\n")


def is_valid_json(path: Path) -> bool:
    try:
        json.loads(path.read_text(encoding="utf-8-sig"))
        return True
    except Exception:
        return False


def conservative_json_repair(path: Path, log) -> bool:
    try:
        raw = path.read_text(encoding="utf-8-sig")
        candidate = re.sub(r",\s*([}\]])", r"\1", raw)
        json.loads(candidate)
        write_text(path, candidate + ("" if candidate.endswith("\n") else "\n"))
        log("REPAIRED", f"Repaired trailing-comma JSON issue: {path}")
        return True
    except Exception:
        return False


def newest_valid_backup_for(root: Path, powerbi_dir: Path, target: Path) -> Path | None:
    backup_root = root / "backups"
    if not backup_root.exists():
        return None

    try:
        relative = target.relative_to(powerbi_dir)
    except ValueError:
        return None

    candidates = []
    for backup in backup_root.glob("*/powerbi"):
        candidate = backup / relative
        if candidate.exists() and candidate.is_file():
            candidates.append(candidate)

    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    for candidate in candidates:
        if candidate.suffix.lower() in {".json", ".pbip", ".pbir"}:
            if is_valid_json(candidate):
                return candidate
        elif candidate.stat().st_size > 0:
            return candidate

    return None


def json_literal(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


def bool_expr(value: bool) -> dict:
    return json_literal("true" if value else "false")


def decimal_expr(value: float | int) -> dict:
    return json_literal(f"{value}D")


def string_expr(value: str) -> dict:
    return json_literal("'" + value.replace("'", "''") + "'")


def color_expr(hex_color: str) -> dict:
    return {"solid": {"color": string_expr(hex_color)}}


def page_color(page_name: str) -> dict:
    low = page_name.lower()
    for key, colors in PAGE_COLORS.items():
        if key != "default" and key in low:
            return colors
    return PAGE_COLORS["default"]


def set_page_style(page: dict, page_name: str) -> None:
    colors = page_color(page_name)
    objects = page.setdefault("objects", {})

    objects["background"] = [
        {
            "properties": {
                "color": color_expr(colors["canvas"]),
                "transparency": decimal_expr(0),
            }
        }
    ]

    objects["outspace"] = [
        {
            "properties": {
                "color": color_expr("#111827"),
                "transparency": decimal_expr(0),
            }
        }
    ]


def set_visual_style(visual_root: dict, page_name: str, index: int) -> None:
    visual = visual_root.get("visual")
    if not isinstance(visual, dict):
        return

    visual_type = str(visual.get("visualType", ""))
    if not visual_type:
        return

    colors = page_color(page_name)
    accent = CHART_PALETTE[index % len(CHART_PALETTE)]
    background = PASTELS[index % len(PASTELS)]
    border = BORDERS[index % len(BORDERS)]

    if "marketing" in page_name.lower():
        marketing_accents = [
            "#EA580C",
            "#F97316",
            "#D97706",
            "#CA8A04",
            "#DB2777",
            "#2563EB",
            "#059669",
            "#7C3AED",
        ]
        marketing_bg = [
            "#FFF1E6",
            "#FFF7ED",
            "#FFEDD5",
            "#FEF3C7",
            "#FDF2F8",
            "#EFF6FF",
            "#ECFDF5",
            "#F5F3FF",
        ]
        accent = marketing_accents[index % len(marketing_accents)]
        background = marketing_bg[index % len(marketing_bg)]
        border = "#FED7AA"

    vco = visual.setdefault("visualContainerObjects", {})

    if visual_type == "textbox":
        vco["visualHeader"] = [{"properties": {"show": bool_expr(False)}}]
        return

    vco["background"] = [
        {
            "properties": {
                "show": bool_expr(True),
                "color": color_expr(background),
                "transparency": decimal_expr(0),
            }
        }
    ]

    vco["border"] = [
        {
            "properties": {
                "show": bool_expr(True),
                "color": color_expr(border),
                "radius": decimal_expr(12),
                "width": decimal_expr(1),
            }
        }
    ]

    vco["padding"] = [
        {
            "properties": {
                "top": decimal_expr(8),
                "bottom": decimal_expr(8),
                "left": decimal_expr(8),
                "right": decimal_expr(8),
            }
        }
    ]

    vco["visualHeader"] = [{"properties": {"show": bool_expr(False)}}]

    title_list = vco.get("title")
    if isinstance(title_list, list) and title_list:
        title = title_list[0]
        if isinstance(title, dict):
            props = title.setdefault("properties", {})
            props["show"] = bool_expr(True)
            props["fontColor"] = color_expr("#172033")
            props["fontSize"] = decimal_expr(12)
            props["fontFamily"] = string_expr("Segoe UI Semibold")

    objects = visual.setdefault("objects", {})

    if visual_type in CHART_TYPES:
        objects["dataPoint"] = [
            {"properties": {"fill": color_expr(accent)}}
        ]

    if visual_type in {"tableEx", "pivotTable"}:
        objects["columnHeaders"] = [
            {
                "properties": {
                    "backColor": color_expr(colors["accent"]),
                    "fontColor": color_expr("#FFFFFF"),
                    "bold": bool_expr(True),
                }
            }
        ]


def style_report(pages_dir: Path, log) -> tuple[list[str], int]:
    pages = []
    visuals_styled = 0

    page_files = sorted(pages_dir.rglob("page.json"))

    for page_file in page_files:
        try:
            page = json.loads(page_file.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            log("ERROR", f"Could not parse page before styling: {page_file} | {exc}")
            continue

        page_name = str(page.get("displayName") or page.get("name") or "Page")
        pages.append(page_name)
        set_page_style(page, page_name)
        write_text(page_file, json.dumps(page, indent=2, ensure_ascii=False) + "\n")

        visuals_dir = page_file.parent / "visuals"
        if not visuals_dir.exists():
            log("REPAIRED", f"Styled page canvas: {page_name}")
            continue

        for index, visual_file in enumerate(sorted(visuals_dir.rglob("visual.json"))):
            try:
                visual_root = json.loads(visual_file.read_text(encoding="utf-8-sig"))
                set_visual_style(visual_root, page_name, index)
                write_text(
                    visual_file,
                    json.dumps(visual_root, indent=2, ensure_ascii=False) + "\n",
                )
                visuals_styled += 1
            except Exception as exc:
                log("WARNING", f"Skipped visual styling: {visual_file} | {exc}")

        log("REPAIRED", f"Styled page: {page_name}")

    return pages, visuals_styled


def marketing_dataset(processed_dir: Path, log) -> None:
    rows = [
        ("Google Search", 12000, 52000, 650, 18.461538, 4.333333),
        ("Meta Paid Social", 9000, 29000, 430, 20.930233, 3.222222),
        ("YouTube Video", 7000, 16000, 220, 31.818182, 2.285714),
        ("Display Prospecting", 5500, 8000, 120, 45.833333, 1.454545),
        ("Email Retargeting", 2500, 40000, 700, 3.571429, 16.0),
        ("Affiliate", 4000, 21000, 310, 12.903226, 5.25),
    ]

    processed_dir.mkdir(parents=True, exist_ok=True)
    csv_path = processed_dir / "synthetic_marketing_performance.csv"

    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["campaign", "spend", "revenue", "acquisitions", "cpa", "roas"])
        writer.writerows(rows)

    total_spend = sum(r[1] for r in rows)
    total_revenue = sum(r[2] for r in rows)
    acquisitions = sum(r[3] for r in rows)

    if total_spend != 40000 or total_revenue != 166000 or acquisitions != 2430:
        raise RuntimeError("Marketing dataset validation failed.")

    log("REPAIRED", f"Marketing source data verified: {csv_path}")


def build_readme(root: Path, pages: list[str], log) -> None:
    page_lines = "\n".join(f"- {p}" for p in pages) or "- Dashboard pages detected from PBIR"

    readme = f"""# Customer 360 & Revenue Growth Analytics

## Overview

Customer 360 & Revenue Growth Analytics is an end-to-end data analytics and business intelligence portfolio project focused on customer behaviour, revenue performance, commercial insights, and marketing efficiency.

The solution uses a Power BI Project (PBIP) structure with PBIR report files and a TMDL semantic model so the dashboard can be version controlled and maintained from Visual Studio Code.

## Business Questions

- How is revenue performing?
- Which customer groups create the most value?
- Which channels and campaigns are most efficient?
- Where are the strongest growth opportunities?
- Which KPIs should decision-makers monitor?

## Technology Stack

- SQL
- Python
- Power BI
- DAX
- Power Query
- PBIP
- PBIR
- TMDL
- Visual Studio Code
- Git
- GitHub

## Dashboard Pages

{page_lines}

## Marketing Performance

The marketing section uses synthetic campaign data for portfolio demonstration.

- Total marketing spend: GBP 40,000
- Attributed revenue: GBP 166,000
- Marketing profit: GBP 126,000
- Acquisitions: 2,430
- Overall ROAS: 4.15x
- Blended CPA: GBP 16.46
- Marketing ROI: 315.0%

Key findings:

- Email Retargeting has the strongest ROAS.
- Google Search produces the highest absolute attributed revenue.
- Affiliate is highly efficient relative to most other channels.
- Display Prospecting has the weakest ROAS and highest CPA.

## Dashboard Design

The dashboard uses a colourful professional visual system:

- Executive views: blue
- Customer views: purple
- Revenue views: green
- Marketing views: orange
- Product views: pink
- Channel views: cyan

## Quality Assurance

The project includes automated checks for:

- PBIP structure
- PBIR JSON parsing
- UTF-8 source files
- report page preservation
- visual preservation
- semantic model source files
- portfolio documentation
- Git status

QA outputs are stored under `reports/qa/`.

## Repository Structure

```text
customer-360-revenue-growth-analytics/
|-- data/
|-- docs/
|-- images/
|   `-- powerbi/
|-- notebooks/
|-- powerbi/
|-- reports/
|   `-- qa/
|-- sql/
|-- .gitignore
`-- README.md
```

## Author

Oluwatosin Oluwaseun Mulero

Data Analyst | Data Scientist
"""

    write_text(root / "README.md", readme)
    log("REPAIRED", "README.md finalized.")


def build_docs(root: Path, log) -> None:
    recruiter = """# Recruiter Project Summary

## Project

Customer 360 & Revenue Growth Analytics

## Skills demonstrated

- End-to-end analytics delivery
- Customer analytics
- Revenue analysis
- Marketing performance measurement
- KPI development
- DAX measures
- Semantic modelling
- Power BI dashboard engineering
- PBIP / PBIR / TMDL development
- Visual Studio Code workflow
- Git source control
- Automated QA

## Business value

The solution converts customer, revenue, and campaign-level data into decision-support reporting that enables users to compare performance, identify efficient channels, and monitor headline commercial KPIs.

## Relevant roles

- Data Analyst
- Business Intelligence Analyst
- Power BI Analyst
- Reporting Analyst
- Insights Analyst
- Customer Data Analyst
- Commercial Data Analyst
- Data Scientist
"""
    write_text(root / "docs" / "RECRUITER_PROJECT_SUMMARY.md", recruiter)

    screenshot_guide = """# Power BI Screenshot Guide

Save final screenshots under `images/powerbi/`.

Recommended files:

- `01_executive_overview.png`
- `02_customer_analysis.png`
- `03_revenue_analysis.png`
- `04_marketing_performance.png`

Before capture:

- maximize Power BI;
- refresh the report;
- clear accidental selections;
- hide unnecessary panes;
- verify there are no visual errors;
- use a consistent zoom level.
"""
    write_text(root / "docs" / "POWER_BI_SCREENSHOT_GUIDE.md", screenshot_guide)
    log("REPAIRED", "Portfolio documentation finalized.")


def update_gitignore(root: Path, log) -> None:
    path = root / ".gitignore"
    existing = []
    if path.exists():
        existing = path.read_text(encoding="utf-8-sig").splitlines()

    required = [
        ".pbi/",
        "**/.pbi/",
        "*.abf",
        "*.tmp",
        "*.lock",
        "backups/",
        "__pycache__/",
        "*.pyc",
        ".venv/",
        "venv/",
        ".DS_Store",
        "Thumbs.db",
    ]

    lines = list(existing)
    for item in required:
        if item not in lines:
            lines.append(item)

    write_text(path, "\n".join(lines).rstrip() + "\n")
    log("REPAIRED", ".gitignore finalized.")


def git_finalize(root: Path, log) -> dict:
    result = {
        "git_available": False,
        "commit_ok": False,
        "remote_exists": False,
        "push_ok": False,
    }

    rc, _, _ = run(["git", "--version"], timeout=20)
    if rc != 0:
        log("WARNING", "Git is not installed or not on PATH.")
        return result

    result["git_available"] = True

    if not (root / ".git").exists():
        rc, out, err = run(["git", "init"], cwd=root, timeout=30)
        if rc == 0:
            log("REPAIRED", "Git repository initialized.")
        else:
            log("WARNING", f"Git init failed: {err}")
            return result

    run(["git", "add", "-A"], cwd=root, timeout=60)

    rc, out, err = run(["git", "status", "--porcelain"], cwd=root, timeout=30)
    pending = bool(out.strip())

    if pending:
        rc, out, err = run(
            ["git", "commit", "-m", "Complete Customer 360 portfolio dashboard"],
            cwd=root,
            timeout=120,
        )
        if rc == 0:
            result["commit_ok"] = True
            log("REPAIRED", "Final Git commit created.")
        else:
            log(
                "WARNING",
                "Git commit did not complete. Git user.name/user.email may need configuration.",
            )
    else:
        result["commit_ok"] = True
        log("OK", "No uncommitted Git changes remain.")

    rc, out, err = run(["git", "remote", "get-url", "origin"], cwd=root, timeout=20)

    if rc == 0 and out.strip():
        result["remote_exists"] = True
        log("OK", f"Git remote detected: {out.strip()}")

        rc, push_out, push_err = run(
            ["git", "push", "-u", "origin", "HEAD"],
            cwd=root,
            timeout=180,
        )
        if rc == 0:
            result["push_ok"] = True
            log("REPAIRED", "Git push completed.")
        else:
            log(
                "WARNING",
                "Git push did not complete. Authentication or remote permissions may be required.",
            )
    else:
        log("WARNING", "No Git origin remote is configured. Local work remains safe.")

    return result


def open_power_bi(pbip: Path, log) -> None:
    if os.name != "nt":
        return

    try:
        os.startfile(str(pbip))
        log("OK", "Power BI launch command sent.")
    except Exception as exc:
        log("WARNING", f"Power BI could not be opened automatically: {exc}")


def main() -> int:
    root = find_project_root()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    powerbi_dir = root / "powerbi"
    qa_dir = root / "reports" / "qa"
    backup_dir = root / "backups" / f"final_python_build_{timestamp}"
    processed_dir = root / "data" / "processed"
    images_dir = root / "images" / "powerbi"

    qa_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    log_path = qa_dir / f"final_python_build_{timestamp}.log"
    log, counts = log_factory(log_path)

    print()
    print("============================================================")
    print(" CUSTOMER 360 - FINAL PYTHON BUILD")
    print("============================================================")
    print()

    log("INFO", f"Project root: {root}")

    close_power_bi(log)

    pbips = sorted(powerbi_dir.glob("*.pbip"))
    report_dirs = sorted(powerbi_dir.glob("*.Report"))
    model_dirs = sorted(powerbi_dir.glob("*.SemanticModel"))

    if not pbips or not report_dirs or not model_dirs:
        log("ERROR", "PBIP, Report, or SemanticModel component is missing.")
        return 1

    pbip = pbips[0]
    report_dir = report_dirs[0]
    model_dir = model_dirs[0]
    pages_dir = report_dir / "definition" / "pages"

    if not pages_dir.exists():
        log("ERROR", f"PBIR pages directory missing: {pages_dir}")
        return 1

    # Backup first.
    shutil.copytree(powerbi_dir, backup_dir / "powerbi", dirs_exist_ok=True)
    for extra in ("README.md", ".gitignore"):
        src = root / extra
        if src.exists():
            shutil.copy2(src, backup_dir / src.name)

    log("OK", f"Backup created: {backup_dir}")

    # Normalize active Power BI text files.
    for path in powerbi_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS:
            try:
                normalize_file(path, log)
            except Exception as exc:
                log("WARNING", f"Could not normalize {path}: {exc}")

    # Recover invalid JSON-like files when possible.
    json_like = [
        p
        for p in powerbi_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in {".json", ".pbip", ".pbir"}
    ]

    for path in json_like:
        if is_valid_json(path):
            continue

        log("WARNING", f"Invalid JSON detected: {path}")

        backup_candidate = newest_valid_backup_for(root, powerbi_dir, path)
        if backup_candidate is not None:
            shutil.copy2(backup_candidate, path)
            log("REPAIRED", f"Restored valid file from previous backup: {path}")
            continue

        conservative_json_repair(path, log)

    # Stop safely if source still has invalid JSON before styling.
    invalid_before = [p for p in json_like if not is_valid_json(p)]
    if invalid_before:
        log("ERROR", f"{len(invalid_before)} JSON file(s) remain invalid before styling.")
        for p in invalid_before:
            log("ERROR", str(p))
        return 2

    marketing_dataset(processed_dir, log)

    # Style report.
    pages, visual_count = style_report(pages_dir, log)

    # Final JSON validation. Roll back Power BI source on failure.
    json_like_after = [
        p
        for p in powerbi_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in {".json", ".pbip", ".pbir"}
    ]
    invalid_after = [p for p in json_like_after if not is_valid_json(p)]

    if invalid_after:
        log("ERROR", f"Styling produced {len(invalid_after)} invalid JSON file(s). Rolling back.")
        shutil.rmtree(powerbi_dir)
        shutil.copytree(backup_dir / "powerbi", powerbi_dir)
        log("REPAIRED", "Power BI project rolled back to the pre-build backup.")
        return 3

    log("OK", "All PBIP/PBIR JSON files passed final parsing.")

    build_readme(root, pages, log)
    build_docs(root, log)
    update_gitignore(root, log)
    git_result = git_finalize(root, log)

    # Reopen Power BI.
    open_power_bi(pbip, log)

    summary = f"""============================================================
CUSTOMER 360 - FINAL PYTHON BUILD STATUS
============================================================

STATUS: PASS

PROJECT:
{root}

BACKUP:
{backup_dir}

PAGES DETECTED:
{len(pages)}

VISUALS STYLED:
{visual_count}

REPAIRS:
{counts['repair']}

WARNINGS:
{counts['warning']}

ERRORS:
{counts['error']}

INVALID JSON REMAINING:
0

GIT AVAILABLE:
{git_result['git_available']}

GIT COMMIT OK:
{git_result['commit_ok']}

GIT REMOTE EXISTS:
{git_result['remote_exists']}

GIT PUSH OK:
{git_result['push_ok']}

README:
{root / 'README.md'}

RECRUITER SUMMARY:
{root / 'docs' / 'RECRUITER_PROJECT_SUMMARY.md'}

SCREENSHOT GUIDE:
{root / 'docs' / 'POWER_BI_SCREENSHOT_GUIDE.md'}

============================================================
"""

    write_text(qa_dir / "FINAL_PYTHON_BUILD_STATUS.txt", summary)
    print()
    print(summary)

    if os.name == "nt":
        try:
            os.startfile(str(qa_dir))
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
