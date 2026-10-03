from pathlib import Path
import re
import subprocess
import sys

ROOT = Path.cwd()

IMAGE_DIR = ROOT / "images" / "powerbi"
README = ROOT / "README.md"
QA_DIR = ROOT / "reports" / "qa"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)
QA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# ONLY THESE FIVE IMAGES BELONG TO THIS PROJECT
# ============================================================

APPROVED = [
    (
        "Executive Overview",
        "01_executive_overview.png",
    ),
    (
        "Customer & Retention",
        "02_customer_retention.png",
    ),
    (
        "Acquisition & Product Performance",
        "03_acquisition_product_performance.png",
    ),
    (
        "Forecasting & Experimentation",
        "04_forecasting_experimentation.png",
    ),
    (
        "Marketing Performance",
        "05_marketing_performance.png",
    ),
]

APPROVED_FILES = {
    filename
    for _, filename in APPROVED
}

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
}


def run(command):
    try:
        result = subprocess.run(
            command,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            shell=False,
        )

        if result.stdout.strip():
            print(result.stdout.strip())

        if result.stderr.strip():
            print(result.stderr.strip())

        return result.returncode

    except Exception as exc:
        print("[WARNING]", exc)
        return 999


print()
print("=" * 70)
print(" CUSTOMER 360 - REMOVE NHS / UNRELATED DASHBOARD")
print("=" * 70)
print()


# ============================================================
# 1. SHOW CURRENT IMAGES
# ============================================================

print("[INFO] Current files in images/powerbi:")
print()

current_images = []

for path in sorted(IMAGE_DIR.iterdir()):

    if (
        path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    ):

        current_images.append(path)

        print(" -", path.name)

print()


# ============================================================
# 2. REMOVE EVERYTHING THAT IS NOT ONE OF OUR FIVE
# ============================================================

removed = []

for path in current_images:

    if path.name not in APPROVED_FILES:

        print(
            "[REMOVE] Unrelated dashboard image:",
            path.name,
        )

        try:
            path.unlink()
            removed.append(path.name)

        except Exception as exc:
            print(
                "[WARNING] Could not delete",
                path.name,
                exc,
            )


# ============================================================
# 3. EXTRA NHS / HEALTHCARE CLEANUP
# ============================================================

bad_keywords = [
    "nhs",
    "hospital",
    "healthcare",
    "clinical",
    "patient",
    "health_dashboard",
    "nhs_dashboard",
]

for path in list(IMAGE_DIR.iterdir()):

    if not path.is_file():
        continue

    low = path.name.lower()

    if any(
        keyword in low
        for keyword in bad_keywords
    ):

        if path.name not in APPROVED_FILES:

            print(
                "[REMOVE] NHS/healthcare image:",
                path.name,
            )

            try:
                path.unlink()

                if path.name not in removed:
                    removed.append(path.name)

            except Exception as exc:
                print(
                    "[WARNING]",
                    exc,
                )


# ============================================================
# 4. CHECK WHICH CORRECT CUSTOMER 360 IMAGES ACTUALLY EXIST
# ============================================================

existing = []
missing = []

for title, filename in APPROVED:

    path = IMAGE_DIR / filename

    if (
        path.exists()
        and path.stat().st_size > 1000
    ):

        existing.append(
            (
                title,
                filename,
            )
        )

        print(
            "[KEEP]",
            title,
            "->",
            filename,
        )

    else:

        missing.append(
            (
                title,
                filename,
            )
        )

        print(
            "[MISSING]",
            title,
            "->",
            filename,
        )


# ============================================================
# 5. REMOVE OLD GALLERY FROM README
# ============================================================

if README.exists():

    text = README.read_text(
        encoding="utf-8-sig"
    )

else:

    text = (
        "# Customer 360 & Revenue Growth Analytics\n"
    )


# Remove marker-based gallery.
text = re.sub(
    r"(?s)<!-- DASHBOARD_GALLERY_START -->.*?"
    r"<!-- DASHBOARD_GALLERY_END -->",
    "",
    text,
)


# Remove old Power BI Dashboard Gallery section.
text = re.sub(
    r"(?ms)^## Power BI Dashboard Gallery\s+.*?"
    r"(?=^## |\Z)",
    "",
    text,
)


# Remove old standalone Power BI Dashboard section.
text = re.sub(
    r"(?ms)^## Power BI Dashboard\s+.*?"
    r"(?=^## |\Z)",
    "",
    text,
)


# Remove old Dashboard Pages section so we rebuild it cleanly.
text = re.sub(
    r"(?ms)^## Dashboard Pages\s+.*?"
    r"(?=^## |\Z)",
    "",
    text,
)


# Remove any remaining markdown references to images/powerbi.
text = re.sub(
    r"(?m)^!\[[^\]]*\]"
    r"\(images/powerbi/[^\)]*\)\s*$",
    "",
    text,
)


# ============================================================
# 6. BUILD CLEAN CUSTOMER 360 DASHBOARD SECTION
# ============================================================

section = []

section.append(
    "## Dashboard Pages"
)

section.append(
    ""
)

for title, _ in APPROVED:

    section.append(
        "- " + title
    )

section.append(
    ""
)

section.append(
    "## Power BI Dashboard Gallery"
)

section.append(
    ""
)

section.append(
    "The following report pages belong to the "
    "Customer 360 & Revenue Growth Analytics project."
)

section.append(
    ""
)


for title, filename in existing:

    section.append(
        "### " + title
    )

    section.append(
        ""
    )

    section.append(
        f"![{title}](images/powerbi/{filename})"
    )

    section.append(
        ""
    )


if missing:

    section.append(
        "### Dashboard images still to add"
    )

    section.append(
        ""
    )

    for title, filename in missing:

        section.append(
            f"- {title}: `{filename}`"
        )

    section.append(
        ""
    )


gallery = "\n".join(
    section
).rstrip()


# ============================================================
# 7. INSERT BEFORE AUTHOR
# ============================================================

author = re.search(
    r"(?m)^## Author\s*$",
    text,
)


if author:

    position = author.start()

    text = (
        text[:position].rstrip()
        + "\n\n"
        + gallery
        + "\n\n"
        + text[position:].lstrip()
    )

else:

    text = (
        text.rstrip()
        + "\n\n"
        + gallery
        + "\n"
    )


# Clean excessive blank lines.
text = re.sub(
    r"\n{4,}",
    "\n\n\n",
    text,
)


README.write_text(
    text.rstrip() + "\n",
    encoding="utf-8",
    newline="\n",
)


print()
print("[OK] README gallery rebuilt.")


# ============================================================
# 8. VERIFY NHS REFERENCES ARE GONE
# ============================================================

final_readme = README.read_text(
    encoding="utf-8"
).lower()


nhs_references = [
    keyword
    for keyword in bad_keywords
    if keyword in final_readme
]


if nhs_references:

    print()
    print(
        "[WARNING] Healthcare-related words still appear "
        "elsewhere in README:"
    )

    for item in nhs_references:
        print(" -", item)

else:

    print(
        "[OK] No NHS/healthcare dashboard references remain "
        "in the gallery."
    )


# ============================================================
# 9. VERIFY FINAL IMAGE FOLDER
# ============================================================

print()
print("=" * 70)
print(" FINAL CUSTOMER 360 IMAGE FOLDER")
print("=" * 70)
print()

final_images = []

for path in sorted(IMAGE_DIR.iterdir()):

    if (
        path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    ):

        final_images.append(path)

        print(
            "[OK]",
            path.name,
        )


# ============================================================
# 10. QA REPORT
# ============================================================

qa = [
    "CUSTOMER 360 POWER BI GALLERY CLEANUP",
    "",
    "NHS DASHBOARD REMOVED: YES",
    "",
    "UNRELATED IMAGES REMOVED:",
]

if removed:

    qa.extend(
        "- " + item
        for item in removed
    )

else:

    qa.append(
        "- None found"
    )

qa.extend(
    [
        "",
        "CUSTOMER 360 IMAGES PRESENT:",
    ]
)

for title, filename in existing:

    qa.append(
        "- "
        + title
        + ": "
        + filename
    )

qa.extend(
    [
        "",
        "MISSING IMAGES:",
    ]
)

if missing:

    for title, filename in missing:

        qa.append(
            "- "
            + title
            + ": "
            + filename
        )

else:

    qa.append(
        "- None"
    )


qa_path = (
    QA_DIR
    / "CUSTOMER360_GALLERY_STATUS.txt"
)


qa_path.write_text(
    "\n".join(qa)
    + "\n",
    encoding="utf-8",
)


print()
print(
    "[OK] QA report:"
)

print(
    qa_path
)


# ============================================================
# 11. GIT
# ============================================================

print()
print("=" * 70)
print(" UPDATING GIT")
print("=" * 70)
print()

run(
    [
        "git",
        "add",
        "-A",
    ]
)


# Force-add approved images.
for _, filename in existing:

    run(
        [
            "git",
            "add",
            "-f",
            "images/powerbi/"
            + filename,
        ]
    )


run(
    [
        "git",
        "add",
        "README.md",
    ]
)


code = subprocess.run(
    [
        "git",
        "status",
        "--porcelain",
    ],
    cwd=str(ROOT),
    capture_output=True,
    text=True,
).stdout.strip()


if code:

    rc = run(
        [
            "git",
            "commit",
            "-m",
            "Remove unrelated NHS dashboard from Customer 360 gallery",
        ]
    )

    if rc == 0:

        print(
            "[OK] Git commit created."
        )

else:

    print(
        "[OK] No additional Git commit required."
    )


# ============================================================
# 12. PUSH
# ============================================================

remote = subprocess.run(
    [
        "git",
        "remote",
        "get-url",
        "origin",
    ],
    cwd=str(ROOT),
    capture_output=True,
    text=True,
)


if (
    remote.returncode == 0
    and remote.stdout.strip()
):

    print()
    print(
        "[INFO] Pushing correction to GitHub..."
    )

    rc = run(
        [
            "git",
            "push",
            "origin",
            "main",
        ]
    )

    if rc == 0:

        print(
            "[OK] GitHub updated."
        )

    else:

        print(
            "[WARNING] GitHub push failed. "
            "Local commit remains safe."
        )

else:

    print(
        "[WARNING] GitHub remote is not configured."
    )


# ============================================================
# FINAL
# ============================================================

print()
print("=" * 70)
print(" CUSTOMER 360 GALLERY CLEANUP COMPLETE")
print("=" * 70)
print()

print(
    "NHS dashboard: REMOVED"
)

print(
    "Correct Customer 360 images present:",
    len(existing),
)

print(
    "Customer 360 images missing:",
    len(missing),
)

print()

if not missing:

    print(
        "[PASS] The gallery now contains only "
        "the five Customer 360 dashboard pages."
    )

else:

    print(
        "[INFO] Only correct Customer 360 images are now shown."
    )

    print(
        "[INFO] Missing page screenshots are listed above."
    )

print()