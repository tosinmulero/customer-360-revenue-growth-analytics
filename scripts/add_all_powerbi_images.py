from __future__ import annotations

import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path


# ============================================================
# CUSTOMER 360
# FIND / CAPTURE / ADD ALL FIVE POWER BI DASHBOARD IMAGES
# ============================================================

ROOT = Path.cwd()

POWERBI_DIR = ROOT / "powerbi"
IMAGE_DIR = ROOT / "images" / "powerbi"
QA_DIR = ROOT / "reports" / "qa"
SCRIPT_DIR = ROOT / "scripts"
README = ROOT / "README.md"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)
QA_DIR.mkdir(parents=True, exist_ok=True)
SCRIPT_DIR.mkdir(parents=True, exist_ok=True)


PAGES = [
    {
        "title": "Executive Overview",
        "file": "01_executive_overview.png",
        "keywords": [
            "executive",
            "overview",
            "executive overview",
        ],
    },
    {
        "title": "Customer & Retention",
        "file": "02_customer_retention.png",
        "keywords": [
            "customer",
            "retention",
            "customer retention",
        ],
    },
    {
        "title": "Acquisition & Product Performance",
        "file": "03_acquisition_product_performance.png",
        "keywords": [
            "acquisition",
            "product",
            "performance",
            "acquisition product",
        ],
    },
    {
        "title": "Forecasting & Experimentation",
        "file": "04_forecasting_experimentation.png",
        "keywords": [
            "forecast",
            "forecasting",
            "experiment",
            "experimentation",
        ],
    },
    {
        "title": "Marketing Performance",
        "file": "05_marketing_performance.png",
        "keywords": [
            "marketing",
            "campaign",
            "roas",
            "marketing performance",
        ],
    },
]


IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}


def log(message: str):
    print(message)


def run(command, cwd=ROOT, timeout=300):
    try:
        result = subprocess.run(
            [str(item) for item in command],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )

        return (
            result.returncode,
            result.stdout.strip(),
            result.stderr.strip(),
        )

    except Exception as exc:
        return 999, "", str(exc)


def image_type(path: Path):
    try:
        header = path.read_bytes()[:32]

        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return "png"

        if header.startswith(b"\xff\xd8\xff"):
            return "jpg"

        if (
            header.startswith(b"RIFF")
            and b"WEBP" in header
        ):
            return "webp"

    except Exception:
        pass

    return None


def png_dimensions(path: Path):
    try:
        raw = path.read_bytes()[:24]

        if (
            raw.startswith(b"\x89PNG\r\n\x1a\n")
            and len(raw) >= 24
        ):
            return struct.unpack(
                ">II",
                raw[16:24],
            )

    except Exception:
        pass

    return None, None


def normalize(value: str):
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        value.lower(),
    ).strip()


def valid_candidate(path: Path):
    if not path.exists():
        return False

    if not path.is_file():
        return False

    if path.suffix.lower() not in IMAGE_EXTENSIONS:
        return False

    if image_type(path) is None:
        return False

    try:
        if path.stat().st_size < 5000:
            return False
    except Exception:
        return False

    return True


def candidate_score(path: Path, spec):
    name = normalize(path.stem)
    full = normalize(str(path))

    score = 0

    for keyword in spec["keywords"]:
        keyword_normalized = normalize(keyword)

        if keyword_normalized in name:
            score += 400

        elif keyword_normalized in full:
            score += 150

    title_words = normalize(spec["title"]).split()

    for word in title_words:
        if len(word) < 4:
            continue

        if word in name:
            score += 120

    # Strongly prefer standard page-number naming.
    expected_prefix = spec["file"].split("_", 1)[0]

    if path.name.startswith(expected_prefix + "_"):
        score += 500

    # Prefer active portfolio image folder.
    try:
        path.relative_to(IMAGE_DIR)
        score += 350
    except ValueError:
        pass

    # Backups are useful, but active project files rank higher.
    if "backup" in str(path).lower():
        score += 40

    # Prefer larger screenshots.
    try:
        size_bonus = min(
            int(path.stat().st_size / 20000),
            250,
        )
        score += size_bonus
    except Exception:
        pass

    return score


def scan_directory(base: Path):
    found = []

    if not base.exists():
        return found

    try:
        iterator = base.rglob("*")
    except Exception:
        return found

    for path in iterator:
        try:
            if not path.is_file():
                continue

            if path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            lowered = {
                part.lower()
                for part in path.parts
            }

            if ".git" in lowered:
                continue

            if ".venv" in lowered:
                continue

            if "venv" in lowered:
                continue

            if "node_modules" in lowered:
                continue

            if valid_candidate(path):
                found.append(path)

        except Exception:
            continue

    return found


def install_python_package(package):
    code, out, err = run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            package,
            "--quiet",
        ],
        timeout=300,
    )

    return code == 0


def get_pbip():
    candidates = list(
        POWERBI_DIR.glob("*.pbip")
    )

    if not candidates:
        return None

    return candidates[0]


def read_powerbi_page_order():
    report_dirs = list(
        POWERBI_DIR.glob("*.Report")
    )

    if not report_dirs:
        return []

    pages_dir = (
        report_dirs[0]
        / "definition"
        / "pages"
    )

    if not pages_dir.exists():
        return []

    page_map = {}

    for page_json in pages_dir.rglob("page.json"):
        try:
            data = json.loads(
                page_json.read_text(
                    encoding="utf-8-sig"
                )
            )

            internal = str(
                data.get("name")
                or page_json.parent.name
            )

            display = str(
                data.get("displayName")
                or internal
            )

            page_map[internal] = display

        except Exception:
            continue

    pages_metadata = (
        pages_dir
        / "pages.json"
    )

    order = []

    if pages_metadata.exists():
        try:
            meta = json.loads(
                pages_metadata.read_text(
                    encoding="utf-8-sig"
                )
            )

            for page_id in meta.get(
                "pageOrder",
                [],
            ):
                page_id = str(page_id)

                if page_id in page_map:
                    order.append(
                        page_map[page_id]
                    )

        except Exception:
            pass

    for display in page_map.values():
        if display not in order:
            order.append(display)

    return order


def canonical_page(title):
    target = normalize(title)

    best = None
    best_score = -1

    for spec in PAGES:
        score = 0

        spec_title = normalize(
            spec["title"]
        )

        if target == spec_title:
            score += 1000

        for keyword in spec["keywords"]:
            if normalize(keyword) in target:
                score += 100

        if score > best_score:
            best_score = score
            best = spec

    if best_score <= 0:
        return None

    return best


def capture_missing_pages(missing_specs):
    if not missing_specs:
        return 0

    if os.name != "nt":
        return 0

    pbip = get_pbip()

    if pbip is None:
        log(
            "[WARNING] PBIP file not found. "
            "Automatic capture unavailable."
        )
        return 0

    log("")
    log(
        "[INFO] Some page screenshots were not found."
    )
    log(
        "[INFO] Attempting automatic Power BI capture..."
    )

    try:
        import pyautogui
    except Exception:
        log(
            "[INFO] Installing pyautogui..."
        )

        if not install_python_package(
            "pyautogui"
        ):
            return 0

        import pyautogui

    try:
        import pygetwindow as gw
    except Exception:
        log(
            "[INFO] Installing pygetwindow..."
        )

        if not install_python_package(
            "pygetwindow"
        ):
            return 0

        import pygetwindow as gw

    try:
        os.startfile(str(pbip))
    except Exception as exc:
        log(
            "[WARNING] Could not open Power BI: "
            + str(exc)
        )
        return 0

    log(
        "[INFO] Waiting for Power BI Desktop..."
    )

    deadline = time.time() + 75
    window = None

    while time.time() < deadline:

        windows = []

        try:
            for item in gw.getAllWindows():
                title = (
                    item.title
                    or ""
                )

                if (
                    "Power BI" in title
                    or "Customer_360" in title
                    or "Customer 360" in title
                ):
                    if (
                        item.width > 600
                        and item.height > 400
                    ):
                        windows.append(item)

        except Exception:
            pass

        if windows:
            window = windows[0]
            break

        time.sleep(2)

    if window is None:
        log(
            "[WARNING] Power BI window was not detected."
        )
        return 0

    try:
        window.restore()
    except Exception:
        pass

    try:
        window.maximize()
    except Exception:
        pass

    try:
        window.activate()
    except Exception:
        pass

    time.sleep(3)

    actual_order = read_powerbi_page_order()

    if not actual_order:
        actual_order = [
            spec["title"]
            for spec in PAGES
        ]

    log("")
    log(
        "[INFO] Power BI page order:"
    )

    for idx, title in enumerate(
        actual_order,
        1,
    ):
        log(
            f"  {idx}. {title}"
        )

    # Move to first report page.
    for _ in range(
        len(actual_order) + 3
    ):
        pyautogui.hotkey(
            "ctrl",
            "pageup",
        )
        time.sleep(0.35)

    captured = 0

    for page_index, title in enumerate(
        actual_order
    ):

        time.sleep(2)

        spec = canonical_page(
            title
        )

        if spec is not None:

            target = (
                IMAGE_DIR
                / spec["file"]
            )

            should_capture = (
                spec in missing_specs
                or not target.exists()
            )

            if should_capture:

                left = max(
                    int(window.left),
                    0,
                )

                top = max(
                    int(window.top),
                    0,
                )

                width = int(
                    window.width
                )

                height = int(
                    window.height
                )

                try:
                    shot = pyautogui.screenshot(
                        region=(
                            left,
                            top,
                            width,
                            height,
                        )
                    )

                    shot.save(
                        str(target)
                    )

                    if valid_candidate(
                        target
                    ):
                        captured += 1

                        log(
                            "[OK] Captured: "
                            + spec["title"]
                        )

                except Exception as exc:
                    log(
                        "[WARNING] Capture failed for "
                        + title
                        + ": "
                        + str(exc)
                    )

        if (
            page_index
            < len(actual_order) - 1
        ):
            pyautogui.hotkey(
                "ctrl",
                "pagedown",
            )

    try:
        pyautogui.hotkey(
            "ctrl",
            "s",
        )
    except Exception:
        pass

    return captured


print()
print("=" * 72)
print(
    " CUSTOMER 360 - FIND AND ADD ALL POWER BI PAGE IMAGES"
)
print("=" * 72)
print()


# ============================================================
# 1. SEARCH FOR EXISTING SCREENSHOTS
# ============================================================

SEARCH_LOCATIONS = [
    ROOT,
    Path.home() / "Downloads",
    Path.home() / "Pictures",
    Path.home() / "Desktop",
]

all_candidates = []

seen_paths = set()

for location in SEARCH_LOCATIONS:

    if not location.exists():
        continue

    log(
        "[INFO] Searching: "
        + str(location)
    )

    for candidate in scan_directory(
        location
    ):

        try:
            resolved = candidate.resolve()
        except Exception:
            continue

        if resolved in seen_paths:
            continue

        seen_paths.add(
            resolved
        )

        all_candidates.append(
            candidate
        )


log("")
log(
    "[INFO] Genuine image files found: "
    + str(len(all_candidates))
)
log("")


# ============================================================
# 2. FIND THE BEST IMAGE FOR EACH PAGE
# ============================================================

used = set()
matched = {}

for spec in PAGES:

    ranked = []

    for candidate in all_candidates:

        try:
            resolved = candidate.resolve()
        except Exception:
            continue

        if resolved in used:
            continue

        score = candidate_score(
            candidate,
            spec,
        )

        if score > 0:
            ranked.append(
                (
                    score,
                    candidate.stat().st_size,
                    candidate,
                )
            )

    ranked.sort(
        key=lambda item: (
            item[0],
            item[1],
        ),
        reverse=True,
    )

    if ranked:

        best_score, best_size, best = ranked[0]

        # Require a meaningful filename/path match.
        if best_score >= 250:

            matched[
                spec["title"]
            ] = best

            used.add(
                best.resolve()
            )

            log(
                "[FOUND] "
                + spec["title"]
            )

            log(
                "        "
                + str(best)
            )

            log(
                "        score="
                + str(best_score)
            )

            log("")


# ============================================================
# 3. COPY FOUND IMAGES TO CANONICAL FILENAMES
# ============================================================

for spec in PAGES:

    title = spec["title"]

    if title not in matched:
        continue

    source = matched[title]

    target = (
        IMAGE_DIR
        / spec["file"]
    )

    try:

        if (
            source.resolve()
            != target.resolve()
        ):

            shutil.copy2(
                source,
                target,
            )

        if valid_candidate(target):

            log(
                "[OK] Prepared: "
                + spec["file"]
            )

    except Exception as exc:

        log(
            "[WARNING] Could not prepare "
            + title
            + ": "
            + str(exc)
        )


# ============================================================
# 4. DETERMINE WHAT IS STILL MISSING
# ============================================================

missing = []

for spec in PAGES:

    target = (
        IMAGE_DIR
        / spec["file"]
    )

    if not valid_candidate(
        target
    ):
        missing.append(
            spec
        )


if missing:

    log("")
    log(
        "[INFO] Missing page images:"
    )

    for spec in missing:
        log(
            "  - "
            + spec["title"]
        )

    capture_missing_pages(
        missing
    )


# ============================================================
# 5. FINAL IMAGE VALIDATION
# ============================================================

still_missing = []

for spec in PAGES:

    target = (
        IMAGE_DIR
        / spec["file"]
    )

    if not valid_candidate(
        target
    ):
        still_missing.append(
            spec
        )


if still_missing:

    log("")
    log(
        "[ERROR] The following page images are still missing:"
    )

    for spec in still_missing:
        log(
            "  - "
            + spec["title"]
        )

    log("")
    log(
        "The script will not create broken README links."
    )

    sys.exit(2)


# ============================================================
# 6. REMOVE OLD/UNWANTED DASHBOARD IMAGES
# ============================================================

allowed = {
    spec["file"]
    for spec in PAGES
}

for image in IMAGE_DIR.iterdir():

    if (
        image.is_file()
        and image.suffix.lower()
        in IMAGE_EXTENSIONS
        and image.name not in allowed
    ):

        try:
            image.unlink()

            log(
                "[REMOVED] Old image: "
                + image.name
            )

        except Exception:
            pass


# ============================================================
# 7. VERIFY ALL FIVE
# ============================================================

log("")
log(
    "=" * 72
)

log(
    " VERIFIED POWER BI IMAGES"
)

log(
    "=" * 72
)

for spec in PAGES:

    image = (
        IMAGE_DIR
        / spec["file"]
    )

    width, height = (
        png_dimensions(image)
    )

    size = image.stat().st_size

    line = (
        "[OK] "
        + spec["title"]
        + " -> "
        + spec["file"]
        + " | "
        + f"{size:,} bytes"
    )

    if width and height:
        line += (
            " | "
            + str(width)
            + "x"
            + str(height)
        )

    log(line)


# ============================================================
# 8. REBUILD README DASHBOARD SECTIONS
# ============================================================

if README.exists():
    readme = README.read_text(
        encoding="utf-8-sig"
    )
else:
    readme = (
        "# Customer 360 & Revenue Growth Analytics\n"
    )


# Remove old single-image gallery.
readme = re.sub(
    r"(?s)<!-- DASHBOARD_GALLERY_START -->.*?<!-- DASHBOARD_GALLERY_END -->",
    "",
    readme,
)


# Remove existing Dashboard Pages section.
readme = re.sub(
    r"(?ms)^## Dashboard Pages\s+.*?(?=^## |\Z)",
    "",
    readme,
)


# Remove an old standalone Power BI Dashboard section.
readme = re.sub(
    r"(?ms)^## Power BI Dashboard\s+.*?(?=^## |\Z)",
    "",
    readme,
)


page_list = "\n".join(
    "- " + spec["title"]
    for spec in PAGES
)


gallery_parts = [
    "## Dashboard Pages",
    "",
    page_list,
    "",
    "## Power BI Dashboard Gallery",
    "",
    (
        "The five report pages below form the complete "
        "Customer 360 & Revenue Growth Analytics dashboard."
    ),
    "",
]


for spec in PAGES:

    gallery_parts.extend(
        [
            "### " + spec["title"],
            "",
            (
                "!["
                + spec["title"]
                + "](images/powerbi/"
                + spec["file"]
                + ")"
            ),
            "",
        ]
    )


gallery = "\n".join(
    gallery_parts
).rstrip()


author_match = re.search(
    r"(?m)^## Author\s*$",
    readme,
)


if author_match:

    insertion = (
        author_match.start()
    )

    readme = (
        readme[:insertion].rstrip()
        + "\n\n"
        + gallery
        + "\n\n"
        + readme[insertion:].lstrip()
    )

else:

    readme = (
        readme.rstrip()
        + "\n\n"
        + gallery
        + "\n"
    )


readme = re.sub(
    r"\n{4,}",
    "\n\n\n",
    readme,
)


README.write_text(
    readme.rstrip()
    + "\n",
    encoding="utf-8",
    newline="\n",
)


log("")
log(
    "[OK] README updated with all five dashboard images."
)


# ============================================================
# 9. VERIFY EVERY README IMAGE LINK
# ============================================================

failed_links = []

for spec in PAGES:

    relative = (
        "images/powerbi/"
        + spec["file"]
    )

    absolute = (
        ROOT
        / relative
    )

    if not valid_candidate(
        absolute
    ):

        failed_links.append(
            relative
        )


if failed_links:

    for link in failed_links:
        log(
            "[ERROR] Broken README image: "
            + link
        )

    sys.exit(3)


log(
    "[OK] All five README image links resolve locally."
)


# ============================================================
# 10. GIT TRACKING
# ============================================================

git = shutil.which(
    "git"
)

if git is None:

    log(
        "[WARNING] Git is unavailable."
    )

    sys.exit(0)


run(
    [
        git,
        "add",
        "-A",
    ]
)


for spec in PAGES:

    path = (
        "images/powerbi/"
        + spec["file"]
    )

    run(
        [
            git,
            "add",
            "-f",
            path,
        ]
    )


run(
    [
        git,
        "add",
        "README.md",
    ]
)


all_tracked = True

for spec in PAGES:

    relative = (
        "images/powerbi/"
        + spec["file"]
    )

    code, output, error = run(
        [
            git,
            "ls-files",
            "--stage",
            relative,
        ]
    )

    if (
        code != 0
        or not output.strip()
    ):

        all_tracked = False

        log(
            "[ERROR] Not tracked by Git: "
            + relative
        )


if all_tracked:

    log(
        "[OK] All five dashboard images are tracked by Git."
    )


# ============================================================
# 11. COMMIT
# ============================================================

code, status, error = run(
    [
        git,
        "status",
        "--porcelain",
    ]
)


if status.strip():

    code, output, error = run(
        [
            git,
            "commit",
            "-m",
            "Add all Power BI dashboard page images",
        ],
        timeout=120,
    )

    if code == 0:

        log(
            "[OK] Git commit created."
        )

    else:

        log(
            "[WARNING] Git commit failed: "
            + error
        )

else:

    log(
        "[OK] No new Git commit required."
    )


# ============================================================
# 12. PUSH TO GITHUB
# ============================================================

code, origin, error = run(
    [
        git,
        "remote",
        "get-url",
        "origin",
    ]
)


push_success = False


if (
    code == 0
    and origin.strip()
):

    log(
        "[INFO] GitHub remote: "
        + origin.strip()
    )

    code, output, error = run(
        [
            git,
            "push",
            "origin",
            "main",
        ],
        timeout=300,
    )

    if code == 0:

        push_success = True

        log(
            "[OK] GitHub push completed."
        )

    else:

        log(
            "[WARNING] GitHub push failed: "
            + error
        )

else:

    log(
        "[WARNING] No GitHub origin remote configured."
    )


# ============================================================
# 13. QA REPORT
# ============================================================

qa_report = [
    "============================================================",
    "CUSTOMER 360 - POWER BI IMAGE STATUS",
    "============================================================",
    "",
    "STATUS: PASS",
    "",
    "DASHBOARD IMAGES: 5",
    "",
]


for spec in PAGES:

    qa_report.extend(
        [
            spec["title"] + ":",
            "images/powerbi/" + spec["file"],
            "",
        ]
    )


qa_report.extend(
    [
        "README LINKS: PASS",
        "",
        "GIT TRACKING: "
        + (
            "PASS"
            if all_tracked
            else "REVIEW REQUIRED"
        ),
        "",
        "GITHUB PUSH: "
        + (
            "PASS"
            if push_success
            else "NOT COMPLETED"
        ),
        "",
        "============================================================",
    ]
)


qa_path = (
    QA_DIR
    / "POWER_BI_IMAGES_STATUS.txt"
)


qa_path.write_text(
    "\n".join(
        qa_report
    )
    + "\n",
    encoding="utf-8",
)


log("")
log(
    "=" * 72
)

log(
    " ALL FIVE POWER BI DASHBOARD IMAGES ADDED"
)

log(
    "=" * 72
)

log("")
log(
    "Executive Overview"
)
log(
    "Customer & Retention"
)
log(
    "Acquisition & Product Performance"
)
log(
    "Forecasting & Experimentation"
)
log(
    "Marketing Performance"
)

log("")
log(
    "[PASS] All five image files exist."
)
log(
    "[PASS] All five README links work locally."
)

if all_tracked:
    log(
        "[PASS] All five images are tracked by Git."
    )

if push_success:
    log(
        "[PASS] Changes pushed to GitHub."
    )

log("")
log(
    "QA report:"
)
log(
    str(
        qa_path
    )
)
log("")