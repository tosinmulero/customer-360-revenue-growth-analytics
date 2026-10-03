from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path.cwd()
POWERBI_DIR = ROOT / "powerbi"
IMAGE_DIR = ROOT / "images" / "powerbi"
QA_DIR = ROOT / "reports" / "qa"
README = ROOT / "README.md"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)
QA_DIR.mkdir(parents=True, exist_ok=True)


EXPECTED_PAGES = [
    ("Executive Overview", "01_executive_overview.png"),
    ("Customer & Retention", "02_customer_retention.png"),
    ("Acquisition & Product Performance", "03_acquisition_product_performance.png"),
    ("Forecasting & Experimentation", "04_forecasting_experimentation.png"),
    ("Marketing Performance", "05_marketing_performance.png"),
]


def run(command, timeout=300):
    try:
        result = subprocess.run(
            [str(x) for x in command],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )

        if result.stdout.strip():
            print(result.stdout.strip())

        if result.stderr.strip():
            print(result.stderr.strip())

        return result.returncode, result.stdout.strip(), result.stderr.strip()

    except Exception as exc:
        return 999, "", str(exc)


def install(package):
    print(f"[INFO] Installing {package}...")

    code, _, error = run(
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

    if code != 0:
        print("[ERROR]", error)
        return False

    return True


def normalise(value):
    return re.sub(
        r"\s+",
        " ",
        str(value).strip().lower(),
    )


def image_difference(path1, path2):
    from PIL import Image, ImageChops, ImageStat

    try:
        image1 = Image.open(path1).convert("RGB").resize((320, 180))
        image2 = Image.open(path2).convert("RGB").resize((320, 180))

        diff = ImageChops.difference(image1, image2)
        stat = ImageStat.Stat(diff)

        return sum(stat.mean) / len(stat.mean)

    except Exception:
        return 999.0


def valid_image(path):
    try:
        from PIL import Image

        with Image.open(path) as image:
            image.verify()

        return (
            path.exists()
            and path.stat().st_size > 10000
        )

    except Exception:
        return False


print()
print("=" * 72)
print(" CUSTOMER 360 - CAPTURE THE CORRECT POWER BI PAGES")
print("=" * 72)
print()


# ============================================================
# 1. VERIFY THE ACTUAL PBIR PAGES
# ============================================================

report_dirs = list(
    POWERBI_DIR.glob("*.Report")
)

if not report_dirs:
    print("[ERROR] Power BI Report project folder not found.")
    sys.exit(1)


report_dir = report_dirs[0]

pages_dir = (
    report_dir
    / "definition"
    / "pages"
)


if not pages_dir.exists():
    print("[ERROR] PBIR pages directory not found.")
    sys.exit(2)


actual_pages = []

for page_file in pages_dir.rglob("page.json"):

    try:
        data = json.loads(
            page_file.read_text(
                encoding="utf-8-sig"
            )
        )

        display_name = (
            data.get("displayName")
            or data.get("name")
        )

        if display_name:
            actual_pages.append(
                str(display_name)
            )

    except Exception:
        pass


print("[INFO] Pages found inside the real Customer 360 PBIR project:")
print()

for page in actual_pages:
    print("  -", page)

print()


missing_project_pages = []

for required, _ in EXPECTED_PAGES:

    if normalise(required) not in {
        normalise(x)
        for x in actual_pages
    }:

        missing_project_pages.append(required)


if missing_project_pages:

    print("[ERROR] Required pages are missing from the actual PBIR project:")

    for item in missing_project_pages:
        print(" -", item)

    sys.exit(3)


print("[OK] All five required pages exist in this Customer 360 report.")


# ============================================================
# 2. INSTALL AUTOMATION PACKAGES
# ============================================================

try:
    import pyautogui
except Exception:
    if not install("pyautogui"):
        sys.exit(4)

    import pyautogui


try:
    from PIL import Image
except Exception:
    if not install("pillow"):
        sys.exit(5)

    from PIL import Image


try:
    from pywinauto import Desktop
except Exception:
    if not install("pywinauto"):
        sys.exit(6)

    from pywinauto import Desktop


# ============================================================
# 3. FIND THE CUSTOMER 360 POWER BI WINDOW
# ============================================================

print()
print("[INFO] Looking for the Customer 360 Power BI window...")


desktop = Desktop(
    backend="uia"
)


powerbi_windows = []

for window in desktop.windows():

    try:
        title = window.window_text()

        if not title:
            continue

        lower = title.lower()

        if "power bi" in lower:

            rect = window.rectangle()

            area = (
                max(rect.width(), 0)
                * max(rect.height(), 0)
            )

            powerbi_windows.append(
                (
                    area,
                    window,
                    title,
                )
            )

    except Exception:
        continue


if not powerbi_windows:

    print()
    print("[ERROR] Power BI Desktop is not open.")
    print()
    print("Open:")
    print("Customer_360_Revenue_Growth_Dashboard.pbip")
    print()
    print("Wait for the report to load, then rerun this script.")
    sys.exit(7)


# Prefer Customer 360 title if Windows exposes it.
customer_windows = [
    item
    for item in powerbi_windows
    if (
        "customer" in item[2].lower()
        or "revenue" in item[2].lower()
        or "360" in item[2].lower()
    )
]


if customer_windows:
    selected_window = sorted(
        customer_windows,
        key=lambda x: x[0],
        reverse=True,
    )[0]
else:
    selected_window = sorted(
        powerbi_windows,
        key=lambda x: x[0],
        reverse=True,
    )[0]


window = selected_window[1]

print("[OK] Power BI window:")
print(selected_window[2])


try:
    window.restore()
except Exception:
    pass


try:
    window.maximize()
except Exception:
    pass


try:
    window.set_focus()
except Exception:
    pass


time.sleep(3)


# ============================================================
# 4. DELETE ALL OLD / WRONG GALLERY IMAGES
# ============================================================

print()
print("[INFO] Removing the old Power BI gallery images...")

for path in list(IMAGE_DIR.iterdir()):

    if (
        path.is_file()
        and path.suffix.lower()
        in {
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
            ".gif",
        }
    ):

        try:
            path.unlink()
            print("[REMOVED]", path.name)
        except Exception as exc:
            print("[WARNING]", exc)


# ============================================================
# 5. TRY TO CLICK AN EXACT POWER BI PAGE TAB
# ============================================================

def click_exact_page(page_title):

    wanted = normalise(
        page_title
    )

    control_types = [
        "TabItem",
        "Button",
        "Text",
    ]

    for control_type in control_types:

        try:

            controls = window.descendants(
                control_type=control_type
            )

        except Exception:
            controls = []

        matches = []

        for control in controls:

            try:

                title = normalise(
                    control.window_text()
                )

                if title != wanted:
                    continue

                rect = control.rectangle()

                if (
                    rect.width() <= 0
                    or rect.height() <= 0
                ):
                    continue

                matches.append(
                    (
                        rect.top,
                        control,
                    )
                )

            except Exception:
                continue


        if matches:

            # Power BI page tabs normally sit near the bottom.
            matches.sort(
                key=lambda x: x[0],
                reverse=True,
            )

            control = matches[0][1]

            try:
                control.click_input()
                time.sleep(2.5)

                print(
                    "[OK] Selected exact Power BI page:",
                    page_title,
                )

                return True

            except Exception:
                pass

    return False


# ============================================================
# 6. WINDOW SCREENSHOT
# ============================================================

def capture_window(path):

    rect = window.rectangle()

    left = max(
        int(rect.left),
        0,
    )

    top = max(
        int(rect.top),
        0,
    )

    width = int(
        rect.width()
    )

    height = int(
        rect.height()
    )

    if (
        width < 800
        or height < 500
    ):
        raise RuntimeError(
            "Power BI window is unexpectedly small."
        )


    shot = pyautogui.screenshot(
        region=(
            left,
            top,
            width,
            height,
        )
    )

    shot.save(
        str(path)
    )


# ============================================================
# 7. CAPTURE USING EXACT PAGE TABS FIRST
# ============================================================

captured = []

exact_click_success = True


for title, filename in EXPECTED_PAGES:

    print()
    print("=" * 60)
    print("PAGE:", title)
    print("=" * 60)

    found = click_exact_page(
        title
    )

    if not found:

        print(
            "[WARNING] Exact UI page tab was not accessible:",
            title,
        )

        exact_click_success = False
        break


    output = (
        IMAGE_DIR
        / filename
    )


    capture_window(
        output
    )


    if not valid_image(
        output
    ):

        print(
            "[ERROR] Capture failed:",
            title,
        )

        exact_click_success = False
        break


    if captured:

        diff = image_difference(
            captured[-1],
            output,
        )

        print(
            "[INFO] Difference from previous page:",
            round(diff, 2),
        )


        if diff < 1.0:

            print(
                "[ERROR] New capture is effectively identical "
                "to the previous page."
            )

            print(
                "[ERROR] Refusing to add potentially wrong images."
            )

            exact_click_success = False
            break


    captured.append(
        output
    )

    print(
        "[CAPTURED]",
        filename,
    )


# ============================================================
# 8. FALLBACK TO VERIFIED SEQUENTIAL PAGE NAVIGATION
# ============================================================

if (
    not exact_click_success
    or len(captured) != 5
):

    print()
    print("=" * 72)
    print(" EXACT TAB MODE FAILED - USING PAGE ORDER FALLBACK")
    print("=" * 72)
    print()


    # Remove partial captures.
    for path in IMAGE_DIR.glob("*.png"):

        try:
            path.unlink()
        except Exception:
            pass


    captured = []


    try:
        window.set_focus()
    except Exception:
        pass


    # Move all the way back to the first report page.
    for _ in range(10):

        pyautogui.hotkey(
            "ctrl",
            "pageup",
        )

        time.sleep(
            0.35
        )


    time.sleep(
        2
    )


    for index, (title, filename) in enumerate(
        EXPECTED_PAGES
    ):

        output = (
            IMAGE_DIR
            / filename
        )


        print(
            "[INFO] Capturing ordered page:",
            title,
        )


        time.sleep(
            2
        )


        capture_window(
            output
        )


        if not valid_image(
            output
        ):

            print(
                "[ERROR] Invalid capture:",
                output,
            )

            sys.exit(8)


        if captured:

            diff = image_difference(
                captured[-1],
                output,
            )

            print(
                "[INFO] Difference from previous page:",
                round(diff, 2),
            )


            if diff < 1.0:

                print()
                print(
                    "[ERROR] Power BI did not visibly move "
                    "to the next page."
                )

                print(
                    "[ERROR] Images have NOT been added "
                    "to the README."
                )

                sys.exit(9)


        captured.append(
            output
        )


        if index < 4:

            pyautogui.hotkey(
                "ctrl",
                "pagedown",
            )

            time.sleep(
                2.5
            )


# ============================================================
# 9. ABSOLUTE FINAL IMAGE VALIDATION
# ============================================================

if len(captured) != 5:

    print(
        "[ERROR] Exactly five dashboard pages were not captured."
    )

    sys.exit(10)


for title, filename in EXPECTED_PAGES:

    path = (
        IMAGE_DIR
        / filename
    )

    if not valid_image(
        path
    ):

        print(
            "[ERROR] Missing or invalid:",
            title,
        )

        sys.exit(11)


print()
print("[PASS] Five fresh images captured directly from Customer 360 Power BI.")


# ============================================================
# 10. CHECK THAT THE FIVE IMAGES ARE NOT DUPLICATES
# ============================================================

for i in range(
    len(captured)
):

    for j in range(
        i + 1,
        len(captured),
    ):

        diff = image_difference(
            captured[i],
            captured[j],
        )

        if diff < 0.75:

            print()
            print(
                "[ERROR] Two dashboard images are nearly identical:"
            )

            print(
                captured[i].name
            )

            print(
                captured[j].name
            )

            print(
                "[ERROR] README will NOT be updated."
            )

            sys.exit(12)


print(
    "[PASS] All five captures are visually distinct."
)


# ============================================================
# 11. REMOVE OLD README DASHBOARD SECTIONS
# ============================================================

if README.exists():

    readme = README.read_text(
        encoding="utf-8-sig"
    )

else:

    readme = (
        "# Customer 360 & Revenue Growth Analytics\n"
    )


readme = re.sub(
    r"(?s)<!-- DASHBOARD_GALLERY_START -->.*?"
    r"<!-- DASHBOARD_GALLERY_END -->",
    "",
    readme,
)


readme = re.sub(
    r"(?ms)^## Power BI Dashboard Gallery\s+.*?"
    r"(?=^## |\Z)",
    "",
    readme,
)


readme = re.sub(
    r"(?ms)^## Power BI Dashboard\s+.*?"
    r"(?=^## |\Z)",
    "",
    readme,
)


readme = re.sub(
    r"(?ms)^## Dashboard Pages\s+.*?"
    r"(?=^## |\Z)",
    "",
    readme,
)


# ============================================================
# 12. BUILD THE CORRECT CUSTOMER 360 GALLERY
# ============================================================

gallery = [
    "## Dashboard Pages",
    "",
]


for title, filename in EXPECTED_PAGES:

    gallery.append(
        "- " + title
    )


gallery.extend(
    [
        "",
        "## Power BI Dashboard Gallery",
        "",
        (
            "The following screenshots were captured directly "
            "from the Customer 360 & Revenue Growth Analytics "
            "Power BI report."
        ),
        "",
    ]
)


for title, filename in EXPECTED_PAGES:

    gallery.extend(
        [
            "### " + title,
            "",
            f"![{title}](images/powerbi/{filename})",
            "",
        ]
    )


gallery_text = "\n".join(
    gallery
).rstrip()


author = re.search(
    r"(?m)^## Author\s*$",
    readme,
)


if author:

    position = (
        author.start()
    )

    readme = (
        readme[:position].rstrip()
        + "\n\n"
        + gallery_text
        + "\n\n"
        + readme[position:].lstrip()
    )

else:

    readme = (
        readme.rstrip()
        + "\n\n"
        + gallery_text
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


print(
    "[PASS] README rebuilt using only fresh Customer 360 captures."
)


# ============================================================
# 13. GIT TRACKING
# ============================================================

git = shutil.which(
    "git"
)


if git:

    run(
        [
            git,
            "add",
            "-A",
        ]
    )


    for _, filename in EXPECTED_PAGES:

        run(
            [
                git,
                "add",
                "-f",
                "images/powerbi/"
                + filename,
            ]
        )


    # Verify tracking.
    tracking_ok = True


    for _, filename in EXPECTED_PAGES:

        relative = (
            "images/powerbi/"
            + filename
        )

        code, output, _ = run(
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

            tracking_ok = False

            print(
                "[ERROR] Git is not tracking:",
                relative,
            )


    if not tracking_ok:

        sys.exit(13)


    print(
        "[PASS] Git tracks all five fresh dashboard screenshots."
    )


    code, status, _ = run(
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
                "Replace gallery with correct Customer 360 Power BI screenshots",
            ],
            timeout=120,
        )


        if code == 0:

            print(
                "[OK] Git commit created."
            )

        else:

            print(
                "[WARNING] Git commit failed:",
                error,
            )


    code, origin, _ = run(
        [
            git,
            "remote",
            "get-url",
            "origin",
        ]
    )


    if (
        code == 0
        and origin.strip()
    ):

        print(
            "[INFO] Pushing corrected gallery to GitHub..."
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

            print(
                "[PASS] GitHub updated successfully."
            )

        else:

            print(
                "[WARNING] GitHub push failed:"
            )

            print(
                error
            )


# ============================================================
# 14. QA REPORT
# ============================================================

qa = """CUSTOMER 360 DASHBOARD SCREENSHOT STATUS

STATUS: PASS

SOURCE:
Current Customer 360 Power BI Desktop report

SCREENSHOTS:
1. Executive Overview
2. Customer & Retention
3. Acquisition & Product Performance
4. Forecasting & Experimentation
5. Marketing Performance

OLD / SEARCHED IMAGES USED:
NO

NHS DASHBOARD USED:
NO

README GALLERY:
PASS

ALL CAPTURES DISTINCT:
PASS
"""


qa_path = (
    QA_DIR
    / "CORRECT_POWERBI_SCREENSHOTS.txt"
)


qa_path.write_text(
    qa,
    encoding="utf-8",
)


print()
print("=" * 72)
print(" CORRECT CUSTOMER 360 DASHBOARD GALLERY COMPLETE")
print("=" * 72)
print()

for title, filename in EXPECTED_PAGES:

    print(
        "[PASS]",
        title,
        "->",
        filename,
    )

print()
print(
    "No old screenshots were searched or reused."
)

print(
    "No NHS dashboard image was used."
)

print()
print(
    "QA:",
    qa_path,
)