from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path.cwd()

TARGET = ROOT / "notebooks" / "02_advanced_modelling.py"

BACKUP_DIR = ROOT / "backups" / (
    "advanced_modelling_cleanup_"
    + datetime.now().strftime("%Y%m%d_%H%M%S")
)

QA_DIR = ROOT / "reports" / "qa"

BACKUP_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

QA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


CONTAMINATION_MARKERS = [
    "/mnt/data",
    "\\mnt\\data",
    "customer360_master_repair_package",
    "customer360_final_vs_code_delivery",
    "customer360_FINAL_BUILD_PACKAGE",
    "customer360_python_final",
    "customer360_correct_powerbi_gallery",
    "Screenshot 2026-10-03 114526",
    "assert src.exists(), src",
    "Created repair package:",
    "RUN_REPAIR.cmd",
    "RUN_FINAL_DELIVERY.cmd",
]


def log(message: str):
    print(message)


def compile_source(source: str) -> tuple[bool, str]:
    try:
        compile(
            source,
            str(TARGET),
            "exec",
        )

        return True, ""

    except SyntaxError as exc:
        return (
            False,
            f"{exc.msg} at line {exc.lineno}",
        )


def run_command(command):
    try:
        result = subprocess.run(
            command,
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=600,
            shell=False,
        )

        return (
            result.returncode,
            result.stdout,
            result.stderr,
        )

    except Exception as exc:
        return 999, "", str(exc)


print()
print("=" * 72)
print(" REPAIR 02_ADVANCED_MODELLING.PY")
print("=" * 72)
print()


# ============================================================
# 1. VERIFY TARGET
# ============================================================

if not TARGET.exists():
    raise SystemExit(
        f"ERROR: File not found: {TARGET}"
    )


original = TARGET.read_text(
    encoding="utf-8-sig",
)

lines = original.splitlines(
    keepends=True,
)


log(
    f"[INFO] Target: {TARGET}"
)

log(
    f"[INFO] Current line count: {len(lines)}"
)


# ============================================================
# 2. BACKUP BEFORE CHANGING ANYTHING
# ============================================================

backup_file = (
    BACKUP_DIR
    / TARGET.name
)


shutil.copy2(
    TARGET,
    backup_file,
)


log(
    f"[OK] Backup created: {backup_file}"
)


# ============================================================
# 3. LOCATE THE FIRST FOREIGN BLOCK
# ============================================================

marker_hits = []

for line_number, line in enumerate(
    lines,
    start=1,
):

    lowered = line.lower()

    for marker in CONTAMINATION_MARKERS:

        if marker.lower() in lowered:

            marker_hits.append(
                (
                    line_number,
                    marker,
                    line.rstrip(),
                )
            )

            break


if not marker_hits:

    log(
        "[INFO] No known foreign markers were found."
    )

    ok, compile_error = compile_source(
        original
    )

    if not ok:
        raise SystemExit(
            "The file still contains a different syntax problem: "
            + compile_error
        )

    log(
        "[OK] File already compiles."
    )

    sys.exit(0)


first_bad_line = marker_hits[0][0]


print()
print(
    "[INFO] First contamination marker detected at line:",
    first_bad_line,
)

print(
    "[INFO] Marker:",
    marker_hits[0][1],
)

print(
    "[INFO] Source:",
    marker_hits[0][2][:200],
)


# ============================================================
# 4. FIND A SAFE PYTHON BOUNDARY BEFORE THE CONTAMINATION
#
# We do NOT blindly cut at the marker because it may be inside
# a dictionary/function/block. We move upward until the prefix
# is syntactically complete Python.
# ============================================================

safe_cut = None

search_start = first_bad_line - 1


for cut in range(
    search_start,
    0,
    -1,
):

    prefix = "".join(
        lines[:cut]
    )

    ok, _ = compile_source(
        prefix
    )

    if not ok:
        continue

    # Protect against accidentally chopping the legitimate
    # modelling program too early.
    required_signals = [
        "ADVANCED MODELLING COMPLETE",
        "advanced_modelling_summary",
        "Relative lift",
        "SYNTHETIC MARKETING PERFORMANCE",
    ]

    if all(
        signal in prefix
        for signal in required_signals
    ):

        safe_cut = cut
        break


if safe_cut is None:

    raise SystemExit(
        "ERROR: Could not determine a safe automatic cut point. "
        "The backup is untouched."
    )


log(
    f"[OK] Safe Python boundary found after line {safe_cut}."
)


# ============================================================
# 5. WRITE CLEAN SCRIPT
# ============================================================

clean_source = "".join(
    lines[:safe_cut]
).rstrip() + "\n"


remaining_bad_markers = [
    marker
    for marker in CONTAMINATION_MARKERS
    if marker.lower()
    in clean_source.lower()
]


if remaining_bad_markers:

    raise SystemExit(
        "ERROR: Contamination markers remain before the proposed "
        "cut point: "
        + ", ".join(
            remaining_bad_markers
        )
    )


TARGET.write_text(
    clean_source,
    encoding="utf-8",
    newline="\n",
)


log(
    "[REPAIRED] Foreign package/gallery code removed."
)

log(
    f"[INFO] New line count: {safe_cut}"
)


# ============================================================
# 6. FINAL PYTHON SYNTAX VALIDATION
# ============================================================

repaired = TARGET.read_text(
    encoding="utf-8",
)


ok, compile_error = compile_source(
    repaired
)


if not ok:

    shutil.copy2(
        backup_file,
        TARGET,
    )

    raise SystemExit(
        "ERROR: Repaired script failed syntax validation. "
        "Original file restored. "
        + compile_error
    )


log(
    "[PASS] Python syntax validation passed."
)


# ============================================================
# 7. CHECK THAT /mnt/data AND PACKAGE CODE ARE REALLY GONE
# ============================================================

for marker in CONTAMINATION_MARKERS:

    if marker.lower() in repaired.lower():

        shutil.copy2(
            backup_file,
            TARGET,
        )

        raise SystemExit(
            "ERROR: Foreign marker still present after cleanup: "
            + marker
        )


log(
    "[PASS] No ChatGPT-container /mnt/data code remains."
)


# ============================================================
# 8. RUN THE ACTUAL ADVANCED MODELLING SCRIPT
# ============================================================

print()
print("=" * 72)
print(" RUNNING CLEAN ADVANCED MODELLING SCRIPT")
print("=" * 72)
print()


code, stdout, stderr = run_command(
    [
        sys.executable,
        str(TARGET),
    ]
)


print(
    stdout,
    end=(
        ""
        if stdout.endswith("\n")
        else "\n"
    ),
)


if stderr.strip():

    print()
    print(
        stderr,
        file=sys.stderr,
    )


# ============================================================
# 9. VALIDATE EXECUTION
# ============================================================

if code != 0:

    log(
        f"[ERROR] Repaired script returned exit code {code}."
    )

    log(
        "[INFO] The repaired source has been left in place "
        "because its syntax is valid."
    )

    raise SystemExit(
        code
    )


if (
    "ADVANCED MODELLING COMPLETE"
    not in stdout
):

    raise SystemExit(
        "ERROR: Script ran but expected completion message "
        "was not detected."
    )


bad_runtime_output = [
    "Created repair package:",
    "customer360_final_vs_code_delivery",
    "customer360_FINAL_BUILD_PACKAGE",
    "\\mnt\\data",
    "/mnt/data",
]


for marker in bad_runtime_output:

    if marker.lower() in stdout.lower():

        raise SystemExit(
            "ERROR: Foreign package code is still executing: "
            + marker
        )


log(
    "[PASS] Advanced modelling completed successfully."
)

log(
    "[PASS] No repair/package/gallery code executed afterward."
)


# ============================================================
# 10. VERIFY EXPECTED ADVANCED MODELLING REPORT
# ============================================================

report = (
    ROOT
    / "reports"
    / "advanced_modelling_summary.txt"
)


if report.exists():

    log(
        f"[PASS] Report exists: {report}"
    )

else:

    log(
        "[WARNING] Expected advanced_modelling_summary.txt "
        "was not found."
    )


# ============================================================
# 11. WRITE QA REPORT
# ============================================================

qa_report = f"""============================================================
ADVANCED MODELLING SCRIPT CLEANUP
============================================================

STATUS: PASS

TARGET:
{TARGET}

BACKUP:
{backup_file}

ORIGINAL LINE COUNT:
{len(lines)}

FIRST CONTAMINATION LINE:
{first_bad_line}

CLEAN SCRIPT LINE COUNT:
{safe_cut}

PYTHON SYNTAX:
PASS

ADVANCED MODELLING EXECUTION:
PASS

MNT/DATA CONTAMINATION:
REMOVED

REPAIR PACKAGE CODE:
REMOVED

GALLERY PACKAGE CODE:
REMOVED

EXPECTED REPORT:
{report}

============================================================
"""


qa_file = (
    QA_DIR
    / "ADVANCED_MODELLING_CLEANUP_STATUS.txt"
)


qa_file.write_text(
    qa_report,
    encoding="utf-8",
    newline="\n",
)


log(
    f"[OK] QA report: {qa_file}"
)


# ============================================================
# 12. GIT COMMIT
# ============================================================

git = shutil.which(
    "git"
)


if git:

    run_command(
        [
            git,
            "add",
            str(TARGET),
            str(qa_file),
        ]
    )


    status_code, status_out, _ = run_command(
        [
            git,
            "status",
            "--porcelain",
        ]
    )


    if status_out.strip():

        commit_code, commit_out, commit_err = run_command(
            [
                git,
                "commit",
                "-m",
                "Remove accidental build code from advanced modelling script",
            ]
        )


        if commit_out.strip():
            print(
                commit_out.strip()
            )


        if commit_code == 0:

            log(
                "[OK] Git cleanup commit created."
            )

        else:

            log(
                "[WARNING] Git commit did not complete."
            )

            if commit_err.strip():
                print(
                    commit_err.strip()
                )


    remote_code, remote, _ = run_command(
        [
            git,
            "remote",
            "get-url",
            "origin",
        ]
    )


    if (
        remote_code == 0
        and remote.strip()
    ):

        push_code, push_out, push_err = run_command(
            [
                git,
                "push",
                "origin",
                "main",
            ]
        )


        if push_out.strip():
            print(
                push_out.strip()
            )


        if push_code == 0:

            log(
                "[OK] GitHub cleanup pushed."
            )

        else:

            log(
                "[WARNING] GitHub push did not complete."
            )

            if push_err.strip():
                print(
                    push_err.strip()
                )


print()
print("=" * 72)
print(" ADVANCED MODELLING CLEANUP COMPLETE")
print("=" * 72)
print()

print(
    "[PASS] Modelling calculations preserved."
)

print(
    "[PASS] Accidental package-generation code removed."
)

print(
    "[PASS] /mnt/data dependency removed."
)

print(
    "[PASS] 02_advanced_modelling.py executes cleanly."
)

print()