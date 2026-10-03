from __future__ import annotations

import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path


ROOT = Path.cwd()
IMAGE_DIR = ROOT / "images" / "powerbi"
README = ROOT / "README.md"
SCRIPT_DIR = ROOT / "scripts"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)
SCRIPT_DIR.mkdir(parents=True, exist_ok=True)


def run(command, cwd=ROOT):
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            shell=False,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as exc:
        return 999, "", str(exc)


def image_type(path: Path):
    try:
        header = path.read_bytes()[:32]

        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return "png"

        if header.startswith(b"\xff\xd8\xff"):
            return "jpg"

        if header.startswith(b"RIFF") and b"WEBP" in header:
            return "webp"

    except Exception:
        pass

    return None


def png_dimensions(path: Path):
    try:
        raw = path.read_bytes()[:24]

        if raw.startswith(b"\x89PNG\r\n\x1a\n") and len(raw) >= 24:
            width, height = struct.unpack(">II", raw[16:24])
            return width, height
    except Exception:
        pass

    return None, None


def candidate_score(path: Path):
    name = path.name.lower()
    full = str(path).lower()

    score = 0

    if "powerbi_dashboard" in name:
        score += 1000

    if "executive_overview" in name:
        score += 900

    if "executive" in name:
        score += 800

    if "dashboard" in name:
        score += 700

    if "powerbi" in name or "power_bi" in name:
        score += 600

    if "overview" in name:
        score += 400

    if "marketing" in name:
        score += 100

    # Prefer images in the active project over old backups.
    if "images\\powerbi" in full or "images/powerbi" in full:
        score += 500

    if "backup" in full:
        score -= 200

    # Prefer larger image files.
    try:
        score += min(path.stat().st_size // 10000, 300)
    except Exception:
        pass

    return score


print()
print("=" * 68)
print(" CUSTOMER 360 - REPAIR POWER BI README IMAGE")
print("=" * 68)
print()

print("[INFO] Project:", ROOT)
print("[INFO] Searching for real Power BI dashboard images...")
print()


# ============================================================
# 1. FIND ALL REAL IMAGE FILES
# ============================================================

extensions = {".png", ".jpg", ".jpeg", ".webp"}

candidates = []

for path in ROOT.rglob("*"):

    if not path.is_file():
        continue

    if path.suffix.lower() not in extensions:
        continue

    # Ignore Git internals and virtual environments.
    lowered_parts = {part.lower() for part in path.parts}

    if ".git" in lowered_parts:
        continue

    if ".venv" in lowered_parts:
        continue

    if "venv" in lowered_parts:
        continue

    actual_type = image_type(path)

    if actual_type is None:
        continue

    candidates.append(path)


if not candidates:
    print("[ERROR] No genuine PNG/JPG/WEBP dashboard image was found.")
    print()
    print("Your README link cannot be repaired until a Power BI screenshot exists.")
    print()
    print("Save one Power BI dashboard screenshot anywhere inside the project")
    print("and rerun this same block.")
    sys.exit(1)


# ============================================================
# 2. RANK THE IMAGES
# ============================================================

ranked = sorted(
    candidates,
    key=lambda p: (candidate_score(p), p.stat().st_size),
    reverse=True,
)

print("[INFO] Images discovered:")
print()

for index, path in enumerate(ranked[:15], 1):
    print(
        f"{index:02d}. score={candidate_score(path):4d} "
        f"size={path.stat().st_size:9d}  "
        f"{path.relative_to(ROOT)}"
    )

print()


# ============================================================
# 3. SELECT BEST POWER BI IMAGE
# ============================================================

selected = ranked[0]

selected_type = image_type(selected)

if selected_type == "jpg":
    final_name = "powerbi_dashboard.jpg"
elif selected_type == "webp":
    final_name = "powerbi_dashboard.webp"
else:
    final_name = "powerbi_dashboard.png"

final_image = IMAGE_DIR / final_name


print("[OK] Selected image:")
print(selected)
print()


# ============================================================
# 4. PRESERVE SELECTED IMAGE BEFORE CLEANUP
# ============================================================

temporary = ROOT / f".customer360_selected_dashboard.{selected_type}"

shutil.copy2(selected, temporary)

if not temporary.exists() or temporary.stat().st_size == 0:
    print("[ERROR] Could not create temporary image copy.")
    sys.exit(2)


# ============================================================
# 5. REMOVE OLD DASHBOARD IMAGE FILES
# ============================================================

for old in list(IMAGE_DIR.iterdir()):

    if not old.is_file():
        continue

    if old.suffix.lower() in extensions:
        try:
            old.unlink()
        except Exception as exc:
            print("[WARNING] Could not remove:", old, exc)


# ============================================================
# 6. CREATE CANONICAL IMAGE
# ============================================================

shutil.copy2(temporary, final_image)

try:
    temporary.unlink()
except Exception:
    pass


if not final_image.exists():
    print("[ERROR] Final dashboard image was not created.")
    sys.exit(3)


if image_type(final_image) is None:
    print("[ERROR] Final dashboard image is not a valid image.")
    sys.exit(4)


if final_image.stat().st_size < 1000:
    print("[ERROR] Final dashboard image is suspiciously small.")
    sys.exit(5)


width = None
height = None

if selected_type == "png":
    width, height = png_dimensions(final_image)


print("[OK] Canonical dashboard image created:")
print(final_image)
print()

print("[OK] File size:", f"{final_image.stat().st_size:,}", "bytes")

if width and height:
    print("[OK] Dimensions:", f"{width} x {height}")

print()


# ============================================================
# 7. BUILD CORRECT README LINK
# ============================================================

relative_image = "images/powerbi/" + final_name

gallery = f"""<!-- DASHBOARD_GALLERY_START -->

## Power BI Dashboard

Below is the final Power BI dashboard from the Customer 360 & Revenue Growth Analytics project.

![Customer 360 Power BI Dashboard]({relative_image})

<!-- DASHBOARD_GALLERY_END -->"""


if README.exists():
    text = README.read_text(encoding="utf-8-sig")
else:
    text = "# Customer 360 & Revenue Growth Analytics\n"


# Remove existing gallery block.
text = re.sub(
    r"(?s)<!-- DASHBOARD_GALLERY_START -->.*?<!-- DASHBOARD_GALLERY_END -->",
    "",
    text,
)


# Remove standalone old Power BI image markdown.
text = re.sub(
    r"(?m)^!\[[^\]]*\]\(images/powerbi/[^\)]*\)\s*$",
    "",
    text,
)


# Remove old empty Power BI Dashboard heading/description if present.
text = re.sub(
    r"(?ms)^## Power BI Dashboard\s+"
    r"(?:Below is the final Power BI dashboard.*?\n+)?"
    r"(?=## |\Z)",
    "",
    text,
)


# Insert immediately before Author when possible.
author_match = re.search(
    r"(?m)^## Author\s*$",
    text,
)

if author_match:
    pos = author_match.start()

    text = (
        text[:pos].rstrip()
        + "\n\n"
        + gallery
        + "\n\n"
        + text[pos:].lstrip()
    )
else:
    text = text.rstrip() + "\n\n" + gallery + "\n"


# Reduce excessive blank lines.
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


print("[OK] README repaired.")
print("[OK] README now references:")
print(relative_image)
print()


# ============================================================
# 8. VERIFY README TARGET EXISTS EXACTLY
# ============================================================

resolved_from_readme = ROOT / relative_image

if not resolved_from_readme.exists():
    print("[ERROR] README target still does not exist.")
    sys.exit(6)

if resolved_from_readme.resolve() != final_image.resolve():
    print("[ERROR] README does not point to the canonical image.")
    sys.exit(7)


print("[OK] README image path resolves correctly.")


# ============================================================
# 9. CHECK GITIGNORE
# ============================================================

rc, out, err = run(
    ["git", "check-ignore", "-v", str(final_image)]
)

if rc == 0:
    print()
    print("[WARNING] Git currently ignores the dashboard image:")
    print(out)
    print("[INFO] The image will be force-added to Git.")
else:
    print("[OK] Dashboard image is not ignored by Git.")


# ============================================================
# 10. GIT ADD
# ============================================================

print()
print("[INFO] Updating Git...")

run(["git", "add", "-A"])

# Force-add the exact image in case a broad ignore rule catches it.
rc, out, err = run(
    ["git", "add", "-f", str(final_image)]
)

if rc != 0:
    print("[ERROR] Could not add dashboard image to Git.")
    print(err)
    sys.exit(8)

run(["git", "add", "README.md"])


# ============================================================
# 11. VERIFY IMAGE IS TRACKED/STAGED
# ============================================================

rc, tracked, err = run(
    ["git", "ls-files", "--stage", relative_image]
)

if rc != 0 or not tracked.strip():
    print("[ERROR] Dashboard image is not tracked by Git.")
    sys.exit(9)


print("[OK] Dashboard image is tracked by Git.")


# ============================================================
# 12. COMMIT
# ============================================================

rc, status, err = run(
    ["git", "status", "--porcelain"]
)

if status.strip():

    rc, out, err = run(
        [
            "git",
            "commit",
            "-m",
            "Fix Power BI dashboard image in README",
        ]
    )

    if rc != 0:
        print("[ERROR] Git commit failed.")
        print(err)
        sys.exit(10)

    print("[OK] Git commit created.")

else:
    print("[OK] No additional commit was required.")


# ============================================================
# 13. PUSH IF REMOTE EXISTS
# ============================================================

rc, origin, err = run(
    ["git", "remote", "get-url", "origin"]
)

if rc == 0 and origin.strip():

    print("[INFO] GitHub remote:")
    print(origin.strip())

    rc, out, err = run(
        ["git", "push", "origin", "main"]
    )

    if rc == 0:
        print("[OK] GitHub push completed.")
    else:
        print("[WARNING] GitHub push did not complete.")
        print(err)
        print("[INFO] Local commit remains safe.")

else:
    print("[WARNING] No GitHub origin remote is configured.")


# ============================================================
# 14. FINAL VERIFY
# ============================================================

remaining = [
    p
    for p in IMAGE_DIR.iterdir()
    if p.is_file()
    and p.suffix.lower() in extensions
]

print()
print("=" * 68)
print(" POWER BI IMAGE REPAIR COMPLETE")
print("=" * 68)
print()

print("Selected original image:")
print(selected)
print()

print("Portfolio image:")
print(final_image)
print()

print("README path:")
print(relative_image)
print()

print("Dashboard images remaining in images/powerbi:")
for item in remaining:
    print(" -", item.name)

print()

if len(remaining) == 1 and remaining[0].name == final_name:
    print("[PASS] Exactly one Power BI dashboard image remains.")
else:
    print("[WARNING] Unexpected number of dashboard images remain.")

print()

print("[PASS] README image target exists.")
print("[PASS] Image file is valid.")
print("[PASS] Image is tracked by Git.")

print()
print("=" * 68)