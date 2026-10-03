from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


# ============================================================
# CUSTOMER 360 & REVENUE GROWTH ANALYTICS
# STAGE 6 - COMPLETE VS CODE DELIVERY
#
# EVERYTHING IS CONTROLLED FROM VS CODE.
#
# Creates:
# - scripts/
# - docs/
# - images/powerbi/
# - reports/qa/
# - .vscode/
# - README.md
# - recruiter summary
# - screenshot guide
# - GitHub publishing checklist
# - VS Code tasks
#
# Also:
# - validates PBIP/PBIR
# - validates JSON
# - launches Power BI
# - attempts screenshots
# - configures Git
# - configures GitHub CLI
# - authenticates GitHub
# - creates GitHub repo
# - commits
# - pushes
# ============================================================


PROJECT_NAME = "customer-360-revenue-growth-analytics"

REPO_NAME = PROJECT_NAME

REPO_VISIBILITY = "private"

REPO_DESCRIPTION = (
    "Customer 360 and Revenue Growth Analytics portfolio built "
    "with Power BI, DAX, PBIP, PBIR, TMDL, Python, SQL and Git."
)


# ============================================================
# COMMAND HELPER
# ============================================================


def run(
    command,
    cwd=None,
    timeout=300,
    capture=True,
):
    print()
    print(
        "$",
        " ".join(
            str(x)
            for x in command
        )
    )

    try:

        result = subprocess.run(
            [
                str(x)
                for x in command
            ],
            cwd=(
                str(cwd)
                if cwd
                else None
            ),
            text=True,
            capture_output=capture,
            timeout=timeout,
            shell=False,
        )

        if capture:

            if result.stdout.strip():
                print(
                    result.stdout.strip()
                )

            if result.stderr.strip():
                print(
                    result.stderr.strip()
                )

        return (
            result.returncode,
            (
                result.stdout.strip()
                if capture
                else ""
            ),
            (
                result.stderr.strip()
                if capture
                else ""
            ),
        )

    except Exception as exc:

        print(
            "[ERROR]",
            exc,
        )

        return (
            999,
            "",
            str(exc),
        )


# ============================================================
# FILE HELPERS
# ============================================================


def write_text(
    path: Path,
    text: str,
):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )


def find_root() -> Path:

    current = Path.cwd()

    if (
        current / "powerbi"
    ).exists():

        return current

    downloads = (
        Path.home()
        / "Downloads"
        / PROJECT_NAME
    )

    if downloads.exists():

        return downloads

    raise SystemExit(
        "Project not found. Open the Customer 360 project "
        "folder in VS Code and run the script again."
    )


def valid_json(
    path: Path,
) -> bool:

    try:

        json.loads(
            path.read_text(
                encoding="utf-8-sig"
            )
        )

        return True

    except Exception:

        return False


def slug(
    value: str,
) -> str:

    clean = re.sub(
        r"[^A-Za-z0-9]+",
        "_",
        value.strip(),
    )

    clean = clean.strip(
        "_"
    ).lower()

    return (
        clean
        or "page"
    )


# ============================================================
# PROJECT ROOT
# ============================================================


root = find_root()

timestamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)


powerbi = (
    root
    / "powerbi"
)

docs = (
    root
    / "docs"
)

qa = (
    root
    / "reports"
    / "qa"
)

images = (
    root
    / "images"
    / "powerbi"
)

scripts = (
    root
    / "scripts"
)

vscode = (
    root
    / ".vscode"
)

backups = (
    root
    / "backups"
)


for folder in [
    docs,
    qa,
    images,
    scripts,
    vscode,
    backups,
]:

    folder.mkdir(
        parents=True,
        exist_ok=True,
    )


log_path = (
    qa
    / f"stage6_{timestamp}.log"
)

status_path = (
    qa
    / "FINAL_STAGE6_STATUS.txt"
)


warnings = []

errors = []


# ============================================================
# LOGGING
# ============================================================


def log(
    level,
    message,
):

    line = (
        f"[{level}] "
        + message
    )

    print(
        line
    )

    with log_path.open(
        "a",
        encoding="utf-8",
        newline="\n",
    ) as handle:

        handle.write(
            line
            + "\n"
        )

    if level == "WARNING":

        warnings.append(
            message
        )

    if level == "ERROR":

        errors.append(
            message
        )


print()

print(
    "=" * 60
)

print(
    " CUSTOMER 360 - STAGE 6 VS CODE DELIVERY"
)

print(
    "=" * 60
)

print()


log(
    "INFO",
    f"Project root: {root}",
)


# ============================================================
# 1. VERIFY POWER BI PROJECT
# ============================================================


pbips = list(
    powerbi.glob(
        "*.pbip"
    )
)

reports = list(
    powerbi.glob(
        "*.Report"
    )
)

models = list(
    powerbi.glob(
        "*.SemanticModel"
    )
)


if not pbips:

    raise SystemExit(
        "PBIP file is missing."
    )


if not reports:

    raise SystemExit(
        "PBIR Report directory is missing."
    )


if not models:

    raise SystemExit(
        "SemanticModel directory is missing."
    )


pbip = pbips[0]

report_dir = reports[0]

model_dir = models[0]


pages_dir = (
    report_dir
    / "definition"
    / "pages"
)

pages_json = (
    pages_dir
    / "pages.json"
)


if not pages_dir.exists():

    raise SystemExit(
        "PBIR pages directory is missing."
    )


log(
    "OK",
    f"PBIP: {pbip}",
)

log(
    "OK",
    f"Report: {report_dir}",
)

log(
    "OK",
    f"Semantic model: {model_dir}",
)


# ============================================================
# 2. VALIDATE POWER BI JSON
# ============================================================


json_like = [

    path

    for path in powerbi.rglob(
        "*"
    )

    if (
        path.is_file()

        and path.suffix.lower()
        in {
            ".json",
            ".pbip",
            ".pbir",
        }
    )
]


bad_json = [

    path

    for path in json_like

    if not valid_json(
        path
    )
]


if bad_json:

    for path in bad_json:

        log(
            "ERROR",
            f"Invalid JSON: {path}",
        )

    raise SystemExit(
        "Stage 6 stopped because invalid Power BI JSON exists."
    )


log(
    "OK",
    (
        "Power BI JSON valid: "
        + str(
            len(json_like)
        )
        + " files"
    ),
)


# ============================================================
# 3. READ PAGE ORDER
# ============================================================


page_map = {}


for page_file in pages_dir.rglob(
    "page.json"
):

    try:

        data = json.loads(
            page_file.read_text(
                encoding="utf-8-sig"
            )
        )

        page_id = str(
            data.get(
                "name",
                page_file.parent.name,
            )
        )

        display_name = str(
            data.get(
                "displayName"
            )
            or data.get(
                "name"
            )
            or page_file.parent.name
        )

        page_map[
            page_id
        ] = display_name

    except Exception:

        pass


page_ids = []


if (
    pages_json.exists()
    and valid_json(
        pages_json
    )
):

    try:

        metadata = json.loads(
            pages_json.read_text(
                encoding="utf-8-sig"
            )
        )

        page_ids = [

            str(item)

            for item in metadata.get(
                "pageOrder",
                [],
            )
        ]

    except Exception:

        pass


ordered_pages = [

    page_map[
        page_id
    ]

    for page_id in page_ids

    if page_id
    in page_map
]


for page_name in page_map.values():

    if (
        page_name
        not in ordered_pages
    ):

        ordered_pages.append(
            page_name
        )


log(
    "OK",
    (
        "Pages detected: "
        + str(
            len(ordered_pages)
        )
    ),
)


for page_name in ordered_pages:

    log(
        "INFO",
        f"Page: {page_name}",
    )


# ============================================================
# 4. README
# ============================================================


page_lines = "\n".join(

    f"- {page}"

    for page in ordered_pages
)


readme = f"""# Customer 360 & Revenue Growth Analytics

## Overview

Customer 360 & Revenue Growth Analytics is an end-to-end business intelligence portfolio project covering customer behaviour, retention, acquisition, product performance, forecasting, experimentation and marketing efficiency.

The solution uses Power BI Project (PBIP), PBIR report source, a TMDL semantic model, Python, SQL, DAX, Visual Studio Code and Git.

## Dashboard Pages

{page_lines}

## Marketing Performance

The Marketing Performance section uses synthetic campaign data for portfolio demonstration.

- Total marketing spend: GBP 40,000
- Attributed revenue: GBP 166,000
- Marketing profit: GBP 126,000
- Acquisitions: 2,430
- Overall ROAS: 4.15x
- Blended CPA: GBP 16.46
- Marketing ROI: 315.0%

### Campaign Insights

- Email Retargeting has the strongest ROAS.
- Google Search generates the highest absolute attributed revenue.
- Affiliate demonstrates strong efficiency.
- Display Prospecting has the weakest ROAS and highest CPA.

## Dashboard Design

The dashboard uses a colourful professional design system.

- Executive views: blue
- Customer and retention: purple
- Revenue: green
- Marketing: orange
- Product: pink
- Channel: cyan

## Technology Stack

- Microsoft Power BI
- DAX
- Power Query
- PBIP
- PBIR
- TMDL
- Python
- SQL
- Visual Studio Code
- Git
- GitHub

## Quality Assurance

Automated checks validate:

- PBIP structure
- PBIR JSON
- semantic-model presence
- page preservation
- report documentation
- Git status
- GitHub publication

QA output is stored under:

`reports/qa/`

<!-- DASHBOARD_GALLERY_START -->

## Dashboard Gallery

Final screenshots are stored in:

`images/powerbi/`

<!-- DASHBOARD_GALLERY_END -->

## Author

Oluwatosin Oluwaseun Mulero

Data Analyst | Data Scientist
"""


write_text(
    root
    / "README.md",
    readme,
)


log(
    "OK",
    "README.md created/updated.",
)


# ============================================================
# 5. RECRUITER SUMMARY
# ============================================================


recruiter_summary = f"""# Recruiter Project Summary

## Project

Customer 360 & Revenue Growth Analytics

## Dashboard Pages

{page_lines}

## Skills Demonstrated

- Customer analytics
- Revenue analysis
- Retention analysis
- Acquisition analysis
- Product performance
- Forecasting
- Experimentation
- Marketing analytics
- KPI development
- DAX
- Semantic modelling
- Power BI dashboard engineering
- PBIP
- PBIR
- TMDL
- Python
- SQL
- Git
- Automated QA

## Business Value

The project converts customer, revenue and marketing data into decision-support reporting that enables users to monitor commercial KPIs, compare channels, analyse retention and identify growth opportunities.

## Relevant Roles

- Data Analyst
- Business Intelligence Analyst
- Power BI Analyst
- Reporting Analyst
- Insights Analyst
- Customer Data Analyst
- Commercial Data Analyst
- Data Scientist
"""


write_text(
    docs
    / "RECRUITER_PROJECT_SUMMARY.md",
    recruiter_summary,
)


# ============================================================
# 6. GITHUB CHECKLIST
# ============================================================


publish_checklist = """# GitHub Publish Checklist

## Power BI

- [x] PBIP detected
- [x] PBIR detected
- [x] Semantic model detected
- [x] Power BI JSON validation passed
- [x] Colourful styling completed

## Portfolio

- [x] README created
- [x] Recruiter project summary created
- [x] Screenshot folder created
- [x] VS Code workspace tasks created
- [x] Git repository prepared

## Screenshots

Screenshots are stored under:

`images/powerbi/`

## GitHub

The repository is prepared and published using GitHub CLI from the VS Code terminal.
"""


write_text(
    docs
    / "GITHUB_PUBLISH_CHECKLIST.md",
    publish_checklist,
)


# ============================================================
# 7. SCREENSHOT GUIDE
# ============================================================


screenshot_lines = [

    "# Power BI Screenshot Guide",

    "",

    "Screenshots are stored under `images/powerbi/`.",

    "",
]


for index, page_name in enumerate(
    ordered_pages,
    1,
):

    screenshot_lines.append(

        (
            f"- `{index:02d}_"
            + slug(
                page_name
            )
            + f".png` - {page_name}"
        )
    )


write_text(
    docs
    / "POWER_BI_SCREENSHOT_GUIDE.md",
    "\n".join(
        screenshot_lines
    )
    + "\n",
)


log(
    "OK",
    "Portfolio documentation created.",
)


# ============================================================
# 8. VS CODE TASKS
# ============================================================


tasks = {

    "version": "2.0.0",

    "tasks": [

        {

            "label":
                "Customer 360 - Stage 6 Publish",

            "type":
                "shell",

            "command":
                "python",

            "args": [

                "${workspaceFolder}/scripts/stage6_publish.py"

            ],

            "group": {

                "kind": "build",

                "isDefault": True,

            },

            "problemMatcher": [],

        },

        {

            "label":
                "Customer 360 - Open Power BI",

            "type":
                "shell",

            "command":
                "powershell",

            "args": [

                "-NoProfile",

                "-Command",

                (
                    'Start-Process "'
                    + str(
                        pbip
                    )
                    + '"'
                ),

            ],

            "problemMatcher": [],

        },

    ],
}


write_text(
    vscode
    / "tasks.json",
    json.dumps(
        tasks,
        indent=2,
    )
    + "\n",
)


settings = {

    "files.encoding":
        "utf8",

    "files.eol":
        "\n",

    "python.terminal.activateEnvironment":
        True,

    "terminal.integrated.cwd":
        "${workspaceFolder}",

}


write_text(
    vscode
    / "settings.json",
    json.dumps(
        settings,
        indent=2,
    )
    + "\n",
)


log(
    "OK",
    "VS Code tasks and settings created.",
)


# ============================================================
# 9. GITIGNORE
# ============================================================


gitignore = (
    root
    / ".gitignore"
)


if gitignore.exists():

    ignore_lines = gitignore.read_text(
        encoding="utf-8-sig"
    ).splitlines()

else:

    ignore_lines = []


required_ignore = [

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


for rule in required_ignore:

    if rule not in ignore_lines:

        ignore_lines.append(
            rule
        )


write_text(
    gitignore,
    "\n".join(
        ignore_lines
    ).rstrip()
    + "\n",
)


# ============================================================
# 10. PACKAGE INSTALL HELPER
# ============================================================


def install_package(
    package,
):

    code, _, _ = run(

        [

            sys.executable,

            "-m",

            "pip",

            "install",

            package,

            "--quiet",

        ],

        cwd=root,

        timeout=300,

    )

    return (
        code == 0
    )


# ============================================================
# 11. OPEN POWER BI + SCREENSHOT ATTEMPT
# ============================================================


def screenshot_attempt():

    if os.name != "nt":

        return 0

    try:

        import pyautogui

    except Exception:

        if not install_package(
            "pyautogui"
        ):

            log(
                "WARNING",
                "Could not install pyautogui. Screenshot automation skipped.",
            )

            return 0

        import pyautogui


    try:

        try:

            import pygetwindow as gw

        except Exception:

            install_package(
                "pygetwindow"
            )

            import pygetwindow as gw


        try:

            os.startfile(
                str(
                    pbip
                )
            )

        except Exception as exc:

            log(
                "WARNING",
                (
                    "Could not open Power BI automatically: "
                    + str(
                        exc
                    )
                ),
            )

            return 0


        log(
            "INFO",
            "Waiting for Power BI to load...",
        )


        time.sleep(
            12
        )


        window = None

        deadline = (
            time.time()
            + 60
        )


        while (
            time.time()
            < deadline
            and window is None
        ):

            candidates = []


            for title in gw.getAllTitles():

                if not title:

                    continue

                if (
                    "Power BI"
                    in title

                    or PROJECT_NAME.lower()
                    in title.lower()
                ):

                    candidates.extend(

                        gw.getWindowsWithTitle(
                            title
                        )
                    )


            candidates = [

                candidate

                for candidate
                in candidates

                if (
                    getattr(
                        candidate,
                        "width",
                        0,
                    )
                    > 500

                    and getattr(
                        candidate,
                        "height",
                        0,
                    )
                    > 400
                )
            ]


            if candidates:

                window = (
                    candidates[0]
                )

                break


            time.sleep(
                2
            )


        if window is not None:

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


            time.sleep(
                2
            )


        # Move to first report page.

        for _ in range(
            max(
                len(
                    ordered_pages
                ),
                1,
            )
            + 2
        ):

            pyautogui.hotkey(
                "ctrl",
                "pageup",
            )

            time.sleep(
                0.5
            )


        captured = 0


        for index, page_name in enumerate(
            ordered_pages,
            1,
        ):

            time.sleep(
                2
            )


            screenshot_path = (

                images

                / (
                    f"{index:02d}_"
                    + slug(
                        page_name
                    )
                    + ".png"
                )
            )


            if window is not None:

                region = (

                    max(
                        window.left,
                        0,
                    ),

                    max(
                        window.top,
                        0,
                    ),

                    window.width,

                    window.height,

                )


                image = pyautogui.screenshot(
                    region=region
                )


                image.save(
                    str(
                        screenshot_path
                    )
                )

            else:

                pyautogui.screenshot(
                    str(
                        screenshot_path
                    )
                )


            if (
                screenshot_path.exists()

                and screenshot_path.stat().st_size
                > 1000
            ):

                captured += 1

                log(
                    "OK",
                    (
                        "Screenshot captured: "
                        + screenshot_path.name
                    ),
                )


            if (
                index
                < len(
                    ordered_pages
                )
            ):

                pyautogui.hotkey(
                    "ctrl",
                    "pagedown",
                )


        pyautogui.hotkey(
            "ctrl",
            "s",
        )


        time.sleep(
            3
        )


        return captured


    except Exception as exc:

        log(
            "WARNING",
            (
                "Screenshot automation could not finish: "
                + str(
                    exc
                )
            ),
        )

        return 0


screenshots_auto = screenshot_attempt()


# ============================================================
# 12. BUILD README GALLERY
# ============================================================


pngs = sorted(
    images.glob(
        "*.png"
    )
)


gallery_lines = [

    "<!-- DASHBOARD_GALLERY_START -->",

    "",

    "## Dashboard Gallery",

    "",
]


if pngs:

    for image_file in pngs:

        gallery_title = (

            image_file.stem

            .replace(
                "_",
                " ",
            )

            .title()
        )


        gallery_lines.extend(

            [

                f"### {gallery_title}",

                "",

                (
                    f"![{gallery_title}]"
                    f"(images/powerbi/{image_file.name})"
                ),

                "",

            ]
        )

else:

    gallery_lines.extend(

        [

            "Final dashboard screenshots will be added here.",

            "",

        ]
    )


gallery_lines.append(

    "<!-- DASHBOARD_GALLERY_END -->"

)


gallery = "\n".join(
    gallery_lines
)


readme_path = (
    root
    / "README.md"
)


readme_text = readme_path.read_text(
    encoding="utf-8-sig"
)


start_marker = (
    "<!-- DASHBOARD_GALLERY_START -->"
)

end_marker = (
    "<!-- DASHBOARD_GALLERY_END -->"
)


start_position = readme_text.find(
    start_marker
)

end_position = readme_text.find(
    end_marker
)


if (
    start_position >= 0

    and end_position >= 0
):

    end_position += len(
        end_marker
    )


    readme_text = (

        readme_text[
            :start_position
        ]

        + gallery

        + readme_text[
            end_position:
        ]
    )


write_text(
    readme_path,
    readme_text,
)


log(
    "OK",
    "README dashboard gallery updated.",
)


# ============================================================
# 13. VERIFY GIT
# ============================================================


git = shutil.which(
    "git"
)


if not git:

    raise SystemExit(
        "Git is not installed or not available on PATH."
    )


code, git_version, _ = run(

    [
        git,
        "--version",
    ],

    cwd=root,
)


if code != 0:

    raise SystemExit(
        "Git could not run."
    )


log(
    "OK",
    git_version,
)


# ============================================================
# 14. INITIALIZE GIT IF NEEDED
# ============================================================


if not (
    root
    / ".git"
).exists():

    code, _, message = run(

        [
            git,
            "init",
        ],

        cwd=root,
    )


    if code != 0:

        raise SystemExit(
            "git init failed: "
            + message
        )


    log(
        "OK",
        "Git repository initialized.",
    )


run(

    [
        git,
        "branch",
        "-M",
        "main",
    ],

    cwd=root,
)


log(
    "OK",
    "Git branch set to main.",
)


# ============================================================
# 15. GITHUB CLI
# ============================================================


gh = shutil.which(
    "gh"
)


if not gh:

    winget = shutil.which(
        "winget"
    )


    if winget:

        log(
            "INFO",
            "GitHub CLI not found. Installing with winget.",
        )


        run(

            [

                winget,

                "install",

                "--id",

                "GitHub.cli",

                "-e",

                "--source",

                "winget",

                "--accept-source-agreements",

                "--accept-package-agreements",

            ],

            timeout=300,
        )


        possible_gh = [

            Path(
                r"C:\Program Files\GitHub CLI\gh.exe"
            ),

            (
                Path.home()
                / "AppData"
                / "Local"
                / "Programs"
                / "GitHub CLI"
                / "gh.exe"
            ),

        ]


        for candidate in possible_gh:

            if candidate.exists():

                gh = str(
                    candidate
                )

                break


        if not gh:

            gh = shutil.which(
                "gh"
            )


# ============================================================
# 16. GITHUB AUTH
# ============================================================


github_username = ""

remote_url = ""


if gh:

    code, _, _ = run(

        [

            gh,

            "auth",

            "status",

            "--hostname",

            "github.com",

        ],

        timeout=60,
    )


    if code != 0:

        print()

        print(
            "=" * 60
        )

        print(
            " GITHUB SIGN-IN"
        )

        print(
            "=" * 60
        )

        print()

        print(
            "Complete the GitHub browser login."
        )

        print()


        code, _, login_error = run(

            [

                gh,

                "auth",

                "login",

                "--hostname",

                "github.com",

                "--git-protocol",

                "https",

                "--web",

            ],

            timeout=900,
        )


        if code != 0:

            log(
                "WARNING",
                (
                    "GitHub authentication did not complete: "
                    + login_error
                ),
            )


    code, github_username, _ = run(

        [

            gh,

            "api",

            "user",

            "--jq",

            ".login",

        ],

        timeout=60,
    )


    if code == 0:

        github_username = (
            github_username.strip()
        )


    if github_username:

        log(
            "OK",
            (
                "GitHub account: "
                + github_username
            ),
        )


        run(

            [

                gh,

                "auth",

                "setup-git",

            ],

            timeout=60,
        )


        # Use local repository Git identity.

        run(

            [

                git,

                "config",

                "user.name",

                "Oluwatosin Oluwaseun Mulero",

            ],

            cwd=root,
        )


        code, git_email, _ = run(

            [

                git,

                "config",

                "--get",

                "user.email",

            ],

            cwd=root,
        )


        if not git_email.strip():

            noreply = (

                github_username

                + "@users.noreply.github.com"
            )


            run(

                [

                    git,

                    "config",

                    "user.email",

                    noreply,

                ],

                cwd=root,
            )


            log(
                "OK",
                (
                    "Git local email configured using GitHub noreply address."
                ),
            )


else:

    log(
        "WARNING",
        (
            "GitHub CLI could not be installed. "
            "The project will still be committed locally."
        ),
    )


# ============================================================
# 17. STAGE AND COMMIT
# ============================================================


code, _, message = run(

    [
        git,
        "add",
        "-A",
    ],

    cwd=root,
)


if code != 0:

    raise SystemExit(
        "git add failed: "
        + message
    )


code, pending, _ = run(

    [

        git,

        "status",

        "--porcelain",

    ],

    cwd=root,
)


if pending.strip():

    code, _, commit_error = run(

        [

            git,

            "commit",

            "-m",

            "Finalize Customer 360 analytics portfolio",

        ],

        cwd=root,

        timeout=120,
    )


    if code != 0:

        raise SystemExit(
            "Git commit failed: "
            + commit_error
        )


    log(
        "OK",
        "Final Git commit created.",
    )


else:

    log(
        "OK",
        "No uncommitted changes remain.",
    )


# ============================================================
# 18. CREATE / CONNECT GITHUB REPOSITORY
# ============================================================


if (
    gh
    and github_username
):

    code, origin, _ = run(

        [

            git,

            "remote",

            "get-url",

            "origin",

        ],

        cwd=root,
    )


    origin = (
        origin.strip()
    )


    full_repo = (

        github_username

        + "/"

        + REPO_NAME
    )


    if not origin:

        code, existing_url, _ = run(

            [

                gh,

                "repo",

                "view",

                full_repo,

                "--json",

                "url",

                "--jq",

                ".url",

            ],

            timeout=60,
        )


        if (
            code == 0
            and existing_url.strip()
        ):

            remote_url = (

                existing_url.strip()
            )


            run(

                [

                    git,

                    "remote",

                    "add",

                    "origin",

                    (
                        "https://github.com/"
                        + full_repo
                        + ".git"
                    ),

                ],

                cwd=root,
            )


            log(
                "OK",
                (
                    "Existing GitHub repository connected: "
                    + remote_url
                ),
            )


        else:

            visibility_flag = (

                "--public"

                if REPO_VISIBILITY
                == "public"

                else "--private"
            )


            print()

            print(
                (
                    "Creating GitHub repository as "
                    + REPO_VISIBILITY.upper()
                )
            )

            print()


            code, output, create_error = run(

                [

                    gh,

                    "repo",

                    "create",

                    REPO_NAME,

                    visibility_flag,

                    "--source",

                    str(
                        root
                    ),

                    "--remote",

                    "origin",

                    "--description",

                    REPO_DESCRIPTION,

                ],

                cwd=root,

                timeout=180,
            )


            if code == 0:

                log(
                    "OK",
                    (
                        "GitHub repository created as "
                        + REPO_VISIBILITY
                    ),
                )

            else:

                log(
                    "WARNING",
                    (
                        "GitHub repository creation failed: "
                        + create_error
                    ),
                )


    code, origin, _ = run(

        [

            git,

            "remote",

            "get-url",

            "origin",

        ],

        cwd=root,
    )


    if (
        code == 0
        and origin.strip()
    ):

        remote_url = (
            origin.strip()
        )


        code, _, push_error = run(

            [

                git,

                "push",

                "-u",

                "origin",

                "main",

            ],

            cwd=root,

            timeout=300,
        )


        if code == 0:

            log(
                "OK",
                "GitHub push completed.",
            )


        else:

            log(
                "WARNING",
                (
                    "Initial GitHub push failed. "
                    "Attempting fetch/rebase."
                ),
            )


            fetch_code, _, _ = run(

                [

                    git,

                    "fetch",

                    "origin",

                ],

                cwd=root,

                timeout=120,
            )


            if fetch_code == 0:

                pull_code, _, _ = run(

                    [

                        git,

                        "pull",

                        "--rebase",

                        "origin",

                        "main",

                    ],

                    cwd=root,

                    timeout=180,
                )


                if pull_code == 0:

                    code, _, push_error = run(

                        [

                            git,

                            "push",

                            "-u",

                            "origin",

                            "main",

                        ],

                        cwd=root,

                        timeout=300,
                    )


                    if code == 0:

                        log(
                            "OK",
                            "GitHub push completed after rebase.",
                        )


            if code != 0:

                log(
                    "WARNING",
                    (
                        "GitHub push did not complete. "
                        "Local commits are safe. "
                        + push_error
                    ),
                )


# ============================================================
# 19. FINAL GIT STATUS
# ============================================================


code, git_status, _ = run(

    [

        git,

        "status",

        "--short",

    ],

    cwd=root,
)


working_tree_clean = (

    not git_status.strip()
)


if working_tree_clean:

    log(
        "OK",
        "Git working tree is clean.",
    )


else:

    log(
        "WARNING",
        "Git working tree still contains changes.",
    )


# ============================================================
# 20. SAVE THIS SCRIPT INSIDE /SCRIPTS
# ============================================================


try:

    source_script = Path(
        __file__
    ).resolve()

    permanent_script = (

        scripts

        / "stage6_publish.py"
    )


    if (
        source_script
        != permanent_script
    ):

        shutil.copy2(

            source_script,

            permanent_script,
        )

except Exception:

    pass


# ============================================================
# 21. FINAL REPORT
# ============================================================


final_pngs = list(
    images.glob(
        "*.png"
    )
)


status = (

    "PASS"

    if (
        not errors

        and not bad_json
    )

    else "REVIEW REQUIRED"
)


report = f"""
============================================================
CUSTOMER 360 - FINAL STAGE 6 STATUS
============================================================

STATUS:
{status}

PROJECT:
{root}

PBIP:
{pbip}

POWER BI PAGES:
{len(ordered_pages)}

POWER BI JSON ERRORS:
{len(bad_json)}

SCREENSHOTS PRESENT:
{len(final_pngs)}

SCREENSHOTS AUTO-CAPTURED:
{screenshots_auto}

GIT WORKING TREE CLEAN:
{working_tree_clean}

GITHUB ACCOUNT:
{github_username or "NOT AUTHENTICATED"}

GITHUB REMOTE:
{remote_url or "NOT CONFIGURED"}

REPOSITORY VISIBILITY:
{REPO_VISIBILITY if remote_url else "N/A"}

WARNINGS:
{len(warnings)}

ERRORS:
{len(errors)}

README:
{root / "README.md"}

RECRUITER SUMMARY:
{docs / "RECRUITER_PROJECT_SUMMARY.md"}

SCREENSHOT GUIDE:
{docs / "POWER_BI_SCREENSHOT_GUIDE.md"}

GITHUB CHECKLIST:
{docs / "GITHUB_PUBLISH_CHECKLIST.md"}

VS CODE TASKS:
{vscode / "tasks.json"}

SCREENSHOT FOLDER:
{images}

============================================================
"""


write_text(
    status_path,
    report.strip()
    + "\n",
)


print()

print(
    report
)


# ============================================================
# 22. OPEN QA FOLDER
# ============================================================


if os.name == "nt":

    try:

        os.startfile(
            str(
                qa
            )
        )

    except Exception:

        pass


# ============================================================
# 23. OPEN GITHUB REPO IN BROWSER
# ============================================================


if (
    gh
    and remote_url
):

    try:

        run(

            [

                gh,

                "repo",

                "view",

                "--web",

            ],

            cwd=root,

            timeout=30,
        )

    except Exception:

        pass


print()

print(
    "=" * 60
)

print(
    " STAGE 6 COMPLETE"
)

print(
    "=" * 60
)

print()

print(
    "Final status file:"
)

print(
    status_path
)

print()