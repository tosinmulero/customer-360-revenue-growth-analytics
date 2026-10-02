from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from statsmodels.tsa.holtwinters import Holt
from statsmodels.stats.proportion import proportions_ztest


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

PROCESSED = ROOT / "data" / "processed"
SYNTHETIC = ROOT / "data" / "synthetic"
IMAGES = ROOT / "images"
REPORTS = ROOT / "reports"

SYNTHETIC.mkdir(parents=True, exist_ok=True)
IMAGES.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)


# ============================================================
# IMPORTANT METHODOLOGY NOTE
# ============================================================

# REAL DATA:
# Google GA4 public sample e-commerce dataset.
#
# SYNTHETIC DATA:
# Marketing campaign spend and A/B experiment data created
# solely to demonstrate analytical methods.
#
# Synthetic results must NOT be described as observed GA4
# campaign or experimental performance.


# ============================================================
# PART A
# REAL REVENUE FORECASTING
# ============================================================

daily = pd.read_csv(
    PROCESSED / "25_daily_revenue.csv"
)

daily["date"] = pd.to_datetime(
    daily["date"]
)

daily["revenue"] = pd.to_numeric(
    daily["revenue"],
    errors="coerce"
).fillna(0)

daily = (
    daily
    .sort_values("date")
    .set_index("date")
)

# Ensure every calendar day exists
full_dates = pd.date_range(
    daily.index.min(),
    daily.index.max(),
    freq="D"
)

daily = daily.reindex(
    full_dates,
    fill_value=0
)

daily.index.name = "date"


# ------------------------------------------------------------
# TRAIN / TEST SPLIT
# ------------------------------------------------------------

test_days = 14

train = daily.iloc[:-test_days].copy()
test = daily.iloc[-test_days:].copy()


# ------------------------------------------------------------
# HOLT TREND MODEL
# ------------------------------------------------------------

model = Holt(
    train["revenue"],
    damped_trend=True,
    initialization_method="estimated"
)

fit = model.fit(
    optimized=True
)

test_forecast = fit.forecast(
    test_days
)


# ------------------------------------------------------------
# FORECAST ACCURACY
# ------------------------------------------------------------

actual = test["revenue"].to_numpy()
predicted = test_forecast.to_numpy()

mae = np.mean(
    np.abs(
        actual - predicted
    )
)

rmse = np.sqrt(
    np.mean(
        (actual - predicted) ** 2
    )
)


# ------------------------------------------------------------
# FINAL MODEL + 14 DAY FORECAST
# ------------------------------------------------------------

final_model = Holt(
    daily["revenue"],
    damped_trend=True,
    initialization_method="estimated"
)

final_fit = final_model.fit(
    optimized=True
)

forecast_days = 14

future_forecast = final_fit.forecast(
    forecast_days
)

future_dates = pd.date_range(
    daily.index.max()
    + pd.Timedelta(days=1),
    periods=forecast_days,
    freq="D"
)

forecast_df = pd.DataFrame({
    "date": future_dates,
    "forecast_revenue": future_forecast.values
})

forecast_df.to_csv(
    PROCESSED / "26_revenue_forecast.csv",
    index=False
)


# ------------------------------------------------------------
# FORECAST CHART
# ------------------------------------------------------------

plt.figure(
    figsize=(12, 6)
)

plt.plot(
    daily.index,
    daily["revenue"],
    label="Actual Revenue"
)

plt.plot(
    future_dates,
    future_forecast.values,
    linestyle="--",
    label="14-Day Forecast"
)

plt.title(
    "Daily Revenue and 14-Day Forecast"
)

plt.xlabel(
    "Date"
)

plt.ylabel(
    "Revenue"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    IMAGES / "09_revenue_forecast.png",
    dpi=180,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# PART B
# SYNTHETIC A/B TEST
# ============================================================

# Baseline comes from the REAL GA4 conversion funnel.
# Experiment observations below are SYNTHETIC.

funnel = pd.read_csv(
    PROCESSED / "12_conversion_funnel.csv"
)

baseline_rate = (
    float(
        funnel.loc[
            0,
            "overall_conversion_pct"
        ]
    )
    / 100
)


# ------------------------------------------------------------
# REPRODUCIBLE SYNTHETIC EXPERIMENT
# ------------------------------------------------------------

rng = np.random.default_rng(
    42
)

control_users = 20000
variant_users = 20000

control_probability = baseline_rate

# Synthetic variant assumes a 12% relative improvement
variant_probability = (
    baseline_rate
    * 1.12
)

control_conversions = rng.binomial(
    control_users,
    control_probability
)

variant_conversions = rng.binomial(
    variant_users,
    variant_probability
)

control_rate = (
    control_conversions
    / control_users
)

variant_rate = (
    variant_conversions
    / variant_users
)

relative_lift = (
    variant_rate
    / control_rate
    - 1
) * 100


# ------------------------------------------------------------
# TWO-PROPORTION Z TEST
# ------------------------------------------------------------

counts = np.array([
    control_conversions,
    variant_conversions
])

observations = np.array([
    control_users,
    variant_users
])

z_stat, p_value = proportions_ztest(
    counts,
    observations
)


if p_value < 0.05:
    significance = "Statistically significant"
else:
    significance = "Not statistically significant"


ab_test = pd.DataFrame({
    "variant": [
        "Control",
        "Variant"
    ],
    "users": [
        control_users,
        variant_users
    ],
    "conversions": [
        control_conversions,
        variant_conversions
    ],
    "conversion_rate_pct": [
        control_rate * 100,
        variant_rate * 100
    ],
    "data_type": [
        "Synthetic",
        "Synthetic"
    ]
})

ab_test.to_csv(
    SYNTHETIC / "synthetic_ab_test.csv",
    index=False
)


# ------------------------------------------------------------
# A/B TEST CHART
# ------------------------------------------------------------

plt.figure(
    figsize=(8, 6)
)

plt.bar(
    ab_test["variant"],
    ab_test["conversion_rate_pct"]
)

plt.title(
    "Synthetic A/B Test Conversion Rate"
)

plt.ylabel(
    "Conversion Rate (%)"
)

plt.tight_layout()

plt.savefig(
    IMAGES / "10_synthetic_ab_test.png",
    dpi=180,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# PART C
# SYNTHETIC MARKETING CAMPAIGN DATA
# ============================================================

marketing = pd.DataFrame({

    "campaign": [
        "Google Search",
        "Meta Paid Social",
        "YouTube Video",
        "Display Prospecting",
        "Email Retargeting",
        "Affiliate"
    ],

    "spend": [
        12000,
        9000,
        7000,
        5500,
        2500,
        4000
    ],

    "impressions": [
        450000,
        600000,
        800000,
        1000000,
        160000,
        250000
    ],

    "clicks": [
        18000,
        15000,
        10000,
        7000,
        14000,
        9000
    ],

    "conversions": [
        650,
        430,
        220,
        120,
        700,
        310
    ],

    "revenue": [
        52000,
        29000,
        16000,
        8000,
        40000,
        21000
    ]
})


marketing["ctr_pct"] = (
    marketing["clicks"]
    / marketing["impressions"]
    * 100
)

marketing["cpc"] = (
    marketing["spend"]
    / marketing["clicks"]
)

marketing["conversion_rate_pct"] = (
    marketing["conversions"]
    / marketing["clicks"]
    * 100
)

marketing["cpa"] = (
    marketing["spend"]
    / marketing["conversions"]
)

marketing["roas"] = (
    marketing["revenue"]
    / marketing["spend"]
)

marketing["data_type"] = "Synthetic"

marketing.to_csv(
    SYNTHETIC /
    "synthetic_marketing_campaign_performance.csv",
    index=False
)


# ------------------------------------------------------------
# CAMPAIGN ROAS CHART
# ------------------------------------------------------------

marketing_chart = (
    marketing
    .sort_values(
        "roas"
    )
)

plt.figure(
    figsize=(11, 7)
)

plt.barh(
    marketing_chart["campaign"],
    marketing_chart["roas"]
)

plt.title(
    "Synthetic Marketing Campaign ROAS"
)

plt.xlabel(
    "Return on Ad Spend"
)

plt.ylabel(
    "Campaign"
)

plt.tight_layout()

plt.savefig(
    IMAGES / "11_synthetic_campaign_roas.png",
    dpi=180,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# MARKETING SUMMARY
# ============================================================

best_roas = (
    marketing
    .sort_values(
        "roas",
        ascending=False
    )
    .iloc[0]
)

lowest_cpa = (
    marketing
    .sort_values(
        "cpa"
    )
    .iloc[0]
)


# ============================================================
# WRITE ADVANCED MODELLING REPORT
# ============================================================

report = []

report.append(
    "CUSTOMER 360 & REVENUE GROWTH ANALYTICS"
)

report.append(
    "ADVANCED MODELLING REPORT"
)

report.append(
    "=" * 65
)

report.append("")

report.append(
    "SECTION 1 - REAL GA4 REVENUE FORECAST"
)

report.append(
    "-" * 65
)

report.append(
    f"Historical days analysed: {len(daily):,}"
)

report.append(
    f"Forecast horizon: {forecast_days} days"
)

report.append(
    f"Holdout MAE: {mae:,.2f}"
)

report.append(
    f"Holdout RMSE: {rmse:,.2f}"
)

report.append(
    "Forecast data source: REAL GA4 sample data"
)

report.append("")


report.append(
    "SECTION 2 - SYNTHETIC A/B TEST"
)

report.append(
    "-" * 65
)

report.append(
    "IMPORTANT: Experiment observations are synthetic."
)

report.append(
    f"GA4 baseline conversion used: "
    f"{baseline_rate * 100:.2f}%"
)

report.append(
    f"Control users: {control_users:,}"
)

report.append(
    f"Control conversions: "
    f"{control_conversions:,}"
)

report.append(
    f"Control conversion rate: "
    f"{control_rate * 100:.2f}%"
)

report.append(
    f"Variant users: {variant_users:,}"
)

report.append(
    f"Variant conversions: "
    f"{variant_conversions:,}"
)

report.append(
    f"Variant conversion rate: "
    f"{variant_rate * 100:.2f}%"
)

report.append(
    f"Relative lift: "
    f"{relative_lift:.2f}%"
)

report.append(
    f"Z statistic: "
    f"{z_stat:.4f}"
)

report.append(
    f"P-value: "
    f"{p_value:.4f}"
)

report.append(
    f"Result: {significance}"
)

report.append("")


report.append(
    "SECTION 3 - SYNTHETIC MARKETING ROI"
)

report.append(
    "-" * 65
)

report.append(
    "IMPORTANT: Campaign spend data are synthetic."
)

report.append(
    f"Total synthetic spend: "
    f"{marketing['spend'].sum():,.2f}"
)

report.append(
    f"Total synthetic revenue: "
    f"{marketing['revenue'].sum():,.2f}"
)

overall_roas = (
    marketing["revenue"].sum()
    / marketing["spend"].sum()
)

report.append(
    f"Overall synthetic ROAS: "
    f"{overall_roas:.2f}x"
)

report.append(
    f"Highest ROAS campaign: "
    f"{best_roas['campaign']} "
    f"({best_roas['roas']:.2f}x)"
)

report.append(
    f"Lowest CPA campaign: "
    f"{lowest_cpa['campaign']} "
    f"({lowest_cpa['cpa']:.2f})"
)

report.append("")

report.append(
    "METHODOLOGY DISCLOSURE"
)

report.append(
    "-" * 65
)

report.append(
    "Revenue forecasting uses real Google GA4 "
    "public sample e-commerce data."
)

report.append(
    "A/B testing observations are synthetic and are "
    "included only to demonstrate experimentation methods."
)

report.append(
    "Marketing spend, impressions, clicks and campaign "
    "metrics are synthetic and are included only to "
    "demonstrate CAC, CPA and ROAS analysis."
)


report_path = (
    REPORTS /
    "advanced_modelling_summary.txt"
)

report_path.write_text(
    "\n".join(report),
    encoding="utf-8"
)


# ============================================================
# OUTPUT
# ============================================================

print("")
print("=" * 65)
print("ADVANCED MODELLING COMPLETE")
print("=" * 65)

print("")
print("REAL FORECAST")
print(
    f"MAE: {mae:,.2f}"
)
print(
    f"RMSE: {rmse:,.2f}"
)

print("")
print("SYNTHETIC A/B TEST")
print(
    ab_test.to_string(
        index=False
    )
)

print("")
print(
    f"Relative lift: "
    f"{relative_lift:.2f}%"
)

print(
    f"P-value: "
    f"{p_value:.4f}"
)

print(
    f"Conclusion: "
    f"{significance}"
)

print("")
print("SYNTHETIC MARKETING PERFORMANCE")

print(
    marketing[
        [
            "campaign",
            "spend",
            "revenue",
            "cpa",
            "roas"
        ]
    ].to_string(
        index=False
    )
)

print("")
print(
    f"Report saved to: "
    f"{report_path}"
)

from pathlib import Path
import zipfile

out = Path("/mnt/data/customer360_repair_package")
out.mkdir(parents=True, exist_ok=True)

ps1 = r'''param(
    [string]$Root = ""
)

$ErrorActionPreference = "Continue"

function Write-NoBom {
    param([string]$Path, [string]$Text)
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Text, $enc)
}

function Test-Json {
    param([string]$Path)
    try {
        $raw = [System.IO.File]::ReadAllText($Path)
        $null = $raw | ConvertFrom-Json -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

function Resolve-Root {
    param([string]$Requested)

    if (-not [string]::IsNullOrWhiteSpace($Requested)) {
        if (Test-Path -LiteralPath $Requested) {
            return (Resolve-Path -LiteralPath $Requested).Path
        }
    }

    $known = Join-Path $env:USERPROFILE "Downloads\customer-360-revenue-growth-analytics"
    if (Test-Path -LiteralPath $known) {
        return (Resolve-Path -LiteralPath $known).Path
    }

    $cwd = (Get-Location).Path
    if (Test-Path -LiteralPath (Join-Path $cwd "powerbi")) {
        return $cwd
    }

    return $null
}

$root = Resolve-Root -Requested $Root

if ($null -eq $root) {
    Write-Host ""
    Write-Host "ERROR: Project folder not found."
    Write-Host "Expected:"
    Write-Host (Join-Path $env:USERPROFILE "Downloads\customer-360-revenue-growth-analytics")
    Write-Host ""
    exit 1
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$powerbiDir = Join-Path $root "powerbi"
$qaDir = Join-Path $root "reports\qa"
$docsDir = Join-Path $root "docs"
$imagesDir = Join-Path $root "images\powerbi"
$backupRoot = Join-Path $root "backups"
$backupDir = Join-Path $backupRoot ("master_repair_" + $timestamp)
$logFile = Join-Path $qaDir ("master_repair_" + $timestamp + ".log")
$summaryFile = Join-Path $qaDir "FINAL_REPAIR_STATUS.txt"

$script:Repairs = 0
$script:Warnings = 0
$script:Errors = 0

foreach ($dir in @($powerbiDir, $qaDir, $docsDir, $imagesDir, $backupRoot, $backupDir)) {
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

function Log {
    param([string]$Level, [string]$Message)

    $line = "[" + $Level + "] " + $Message
    Write-Host $line

    try {
        [System.IO.File]::AppendAllText(
            $logFile,
            $line + [Environment]::NewLine,
            (New-Object System.Text.UTF8Encoding($false))
        )
    }
    catch {
    }

    if ($Level -eq "REPAIRED") { $script:Repairs++ }
    if ($Level -eq "WARNING") { $script:Warnings++ }
    if ($Level -eq "ERROR") { $script:Errors++ }
}

Write-Host ""
Write-Host "============================================================"
Write-Host " CUSTOMER 360 - MASTER REPAIR"
Write-Host "============================================================"
Write-Host ""
Log "INFO" ("Project: " + $root)

# Close Power BI so files are not locked.
$pbis = @(Get-Process -Name "PBIDesktop" -ErrorAction SilentlyContinue)

if ($pbis.Count -gt 0) {
    Log "INFO" "Closing Power BI Desktop before repair."

    foreach ($p in $pbis) {
        try {
            $null = $p.CloseMainWindow()
        }
        catch {
        }
    }

    Start-Sleep -Seconds 4

    $remaining = @(Get-Process -Name "PBIDesktop" -ErrorAction SilentlyContinue)

    if ($remaining.Count -gt 0) {
        foreach ($p in $remaining) {
            try {
                Stop-Process -Id $p.Id -Force -ErrorAction Stop
            }
            catch {
            }
        }
        Log "REPAIRED" "Power BI Desktop was force-closed."
    }
    else {
        Log "OK" "Power BI Desktop closed cleanly."
    }
}

if (-not (Test-Path -LiteralPath $powerbiDir)) {
    Log "ERROR" "Power BI project folder is missing."
    exit 1
}

# Full backup first.
try {
    Copy-Item -LiteralPath $powerbiDir -Destination (Join-Path $backupDir "powerbi") -Recurse -Force -ErrorAction Stop

    $readme = Join-Path $root "README.md"
    if (Test-Path -LiteralPath $readme) {
        Copy-Item -LiteralPath $readme -Destination $backupDir -Force
    }

    $gitignoreExisting = Join-Path $root ".gitignore"
    if (Test-Path -LiteralPath $gitignoreExisting) {
        Copy-Item -LiteralPath $gitignoreExisting -Destination $backupDir -Force
    }

    Log "OK" ("Backup created: " + $backupDir)
}
catch {
    Log "ERROR" ("Backup failed: " + $_.Exception.Message)
    Write-Host "STOPPED: No active project files were repaired."
    exit 1
}

# Remove safe cache and temporary files.
$cacheFolders = @(Get-ChildItem -LiteralPath $powerbiDir -Directory -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq ".pbi" })

foreach ($folder in $cacheFolders) {
    try {
        Remove-Item -LiteralPath $folder.FullName -Recurse -Force -ErrorAction Stop
        Log "REPAIRED" ("Removed cache: " + $folder.FullName)
    }
    catch {
        Log "WARNING" ("Could not remove cache: " + $folder.FullName)
    }
}

$tempFiles = @(Get-ChildItem -LiteralPath $powerbiDir -File -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.Extension -eq ".tmp" -or $_.Extension -eq ".lock" -or $_.Name -like "~`$*" })

foreach ($file in $tempFiles) {
    try {
        Remove-Item -LiteralPath $file.FullName -Force -ErrorAction Stop
        Log "REPAIRED" ("Removed temp file: " + $file.FullName)
    }
    catch {
        Log "WARNING" ("Could not remove temp file: " + $file.FullName)
    }
}

# Normalize Power BI text files to UTF8 without BOM.
$textExtensions = @(".json", ".pbip", ".pbir", ".tmdl")
$textFiles = @(Get-ChildItem -LiteralPath $powerbiDir -File -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $textExtensions -contains $_.Extension.ToLower() })

foreach ($file in $textFiles) {
    try {
        if ($file.Length -eq 0) {
            Log "ERROR" ("Zero-byte source file: " + $file.FullName)
            continue
        }

        $text = [System.IO.File]::ReadAllText($file.FullName)

        if ($text.Length -gt 0 -and [int][char]$text[0] -eq 65279) {
            $text = $text.Substring(1)
            Log "REPAIRED" ("Removed BOM marker: " + $file.FullName)
        }

        $nul = [string][char]0
        if ($text.Contains($nul)) {
            $text = $text.Replace($nul, "")
            Log "REPAIRED" ("Removed NUL characters: " + $file.FullName)
        }

        Write-NoBom -Path $file.FullName -Text $text
    }
    catch {
        Log "ERROR" ("Could not normalize: " + $file.FullName + " | " + $_.Exception.Message)
    }
}

# Validate JSON-like Power BI files.
$jsonFiles = @(Get-ChildItem -LiteralPath $powerbiDir -File -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.Extension.ToLower() -in @(".json", ".pbip", ".pbir") })

foreach ($file in $jsonFiles) {
    if (Test-Json -Path $file.FullName) {
        continue
    }

    Log "WARNING" ("Invalid JSON found: " + $file.FullName)

    # Try a conservative trailing-comma repair.
    try {
        $raw = [System.IO.File]::ReadAllText($file.FullName)
        $candidate = [regex]::Replace($raw, ",\s*([}\]])", '$1')
        $candidatePath = $file.FullName + ".repaircandidate"

        Write-NoBom -Path $candidatePath -Text $candidate

        if (Test-Json -Path $candidatePath) {
            Move-Item -LiteralPath $candidatePath -Destination $file.FullName -Force
            Log "REPAIRED" ("JSON trailing comma issue repaired: " + $file.FullName)
        }
        else {
            Remove-Item -LiteralPath $candidatePath -Force -ErrorAction SilentlyContinue
        }
    }
    catch {
    }
}

# Final JSON validation.
$invalidJson = @()

$jsonFiles = @(Get-ChildItem -LiteralPath $powerbiDir -File -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.Extension.ToLower() -in @(".json", ".pbip", ".pbir") })

foreach ($file in $jsonFiles) {
    if (-not (Test-Json -Path $file.FullName)) {
        $invalidJson += $file.FullName
        Log "ERROR" ("Invalid JSON remains: " + $file.FullName)
    }
}

# Final BOM validation.
$bomFiles = @()

$textFiles = @(Get-ChildItem -LiteralPath $powerbiDir -File -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $textExtensions -contains $_.Extension.ToLower() })

foreach ($file in $textFiles) {
    try {
        $bytes = [System.IO.File]::ReadAllBytes($file.FullName)

        if ($bytes.Length -ge 3 -and $bytes[0] -eq 239 -and $bytes[1] -eq 187 -and $bytes[2] -eq 191) {
            $bomFiles += $file.FullName
            $text = [System.IO.File]::ReadAllText($file.FullName)
            Write-NoBom -Path $file.FullName -Text $text
            Log "REPAIRED" ("Forced UTF8 without BOM: " + $file.FullName)
        }
    }
    catch {
    }
}

# Discover project components.
$pbip = Get-ChildItem -LiteralPath $powerbiDir -Filter "*.pbip" -File -ErrorAction SilentlyContinue | Select-Object -First 1
$reportFolders = @(Get-ChildItem -LiteralPath $powerbiDir -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*.Report" })
$modelFolders = @(Get-ChildItem -LiteralPath $powerbiDir -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*.SemanticModel" })
$pageFiles = @(Get-ChildItem -LiteralPath $powerbiDir -Filter "page.json" -File -Recurse -ErrorAction SilentlyContinue)
$visualFiles = @(Get-ChildItem -LiteralPath $powerbiDir -Filter "visual.json" -File -Recurse -ErrorAction SilentlyContinue)
$tmdlFiles = @(Get-ChildItem -LiteralPath $powerbiDir -Filter "*.tmdl" -File -Recurse -ErrorAction SilentlyContinue)
$zeroByteFiles = @(Get-ChildItem -LiteralPath $powerbiDir -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $textExtensions -contains $_.Extension.ToLower() -and $_.Length -eq 0 })

$totalMeasures = 0
$measureNames = @()

foreach ($file in $tmdlFiles) {
    try {
        $text = [System.IO.File]::ReadAllText($file.FullName)
        $matches = [regex]::Matches($text, "(?m)^\s*measure\s+(.+?)\s*=")
        $totalMeasures += $matches.Count

        foreach ($match in $matches) {
            $measureNames += $match.Groups[1].Value.Trim()
        }
    }
    catch {
        Log "WARNING" ("Could not inspect TMDL: " + $file.FullName)
    }
}

$duplicateMeasures = @($measureNames | Group-Object | Where-Object { $_.Count -gt 1 })

# Repair .gitignore.
$gitignore = Join-Path $root ".gitignore"
$requiredIgnore = @(
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
    "Thumbs.db"
)

$ignoreLines = @()

if (Test-Path -LiteralPath $gitignore) {
    $ignoreLines = @([System.IO.File]::ReadAllLines($gitignore))
}

foreach ($line in $requiredIgnore) {
    if ($ignoreLines -notcontains $line) {
        $ignoreLines += $line
    }
}

Write-NoBom -Path $gitignore -Text (($ignoreLines -join [Environment]::NewLine) + [Environment]::NewLine)
Log "REPAIRED" ".gitignore verified."

# Initialize Git if possible.
$gitCmd = Get-Command git -ErrorAction SilentlyContinue

if ($null -ne $gitCmd) {
    if (-not (Test-Path -LiteralPath (Join-Path $root ".git"))) {
        Push-Location $root
        try {
            git init | Out-Null
            Log "REPAIRED" "Git repository initialized."
        }
        catch {
            Log "WARNING" "Git initialization failed."
        }
        Pop-Location
    }
    else {
        Log "OK" "Git repository detected."
    }
}
else {
    Log "WARNING" "Git is not installed or not available on PATH."
}

$status = "PASS"

if ($null -eq $pbip) { $status = "REVIEW REQUIRED" }
if ($reportFolders.Count -eq 0) { $status = "REVIEW REQUIRED" }
if ($modelFolders.Count -eq 0) { $status = "REVIEW REQUIRED" }
if ($invalidJson.Count -gt 0) { $status = "REVIEW REQUIRED" }
if ($zeroByteFiles.Count -gt 0) { $status = "REVIEW REQUIRED" }

$summary = @"
============================================================
CUSTOMER 360 - FINAL REPAIR STATUS
============================================================

STATUS: $status

PROJECT:
$root

BACKUP:
$backupDir

REPAIRS:
$script:Repairs

WARNINGS:
$script:Warnings

ERRORS:
$script:Errors

PBIP PRESENT:
$($null -ne $pbip)

REPORT FOLDERS:
$($reportFolders.Count)

SEMANTIC MODEL FOLDERS:
$($modelFolders.Count)

REPORT PAGES:
$($pageFiles.Count)

VISUAL DEFINITIONS:
$($visualFiles.Count)

TMDL FILES:
$($tmdlFiles.Count)

MEASURES DETECTED:
$totalMeasures

DUPLICATE MEASURE NAMES:
$($duplicateMeasures.Count)

INVALID JSON REMAINING:
$($invalidJson.Count)

ZERO BYTE SOURCE FILES:
$($zeroByteFiles.Count)

============================================================
"@

Write-NoBom -Path $summaryFile -Text $summary

Write-Host ""
Write-Host $summary

if ($null -ne $gitCmd) {
    Write-Host "GIT STATUS"
    Write-Host "------------------------------------------------------------"

    Push-Location $root
    try {
        git status --short
    }
    catch {
    }
    Pop-Location

    Write-Host "------------------------------------------------------------"
}

try {
    Start-Process -FilePath "explorer.exe" -ArgumentList $qaDir
}
catch {
}

if ($status -eq "PASS" -and $null -ne $pbip) {
    Write-Host ""
    Write-Host "Opening Power BI..."

    try {
        Start-Process -FilePath $pbip.FullName -ErrorAction Stop
        Write-Host "[OK] Power BI launch command sent."
    }
    catch {
        try {
            Invoke-Item -LiteralPath $pbip.FullName -ErrorAction Stop
            Write-Host "[OK] Power BI launch command sent."
        }
        catch {
            Write-Host "[WARNING] Open the PBIP manually:"
            Write-Host $pbip.FullName
        }
    }
}
else {
    Write-Host ""
    Write-Host "Power BI was not auto-opened because validation still requires review."
}

Write-Host ""
Write-Host "============================================================"
Write-Host " REPAIR FINISHED"
Write-Host "============================================================"
Write-Host "STATUS: $status"
Write-Host "Summary: $summaryFile"
Write-Host "Log: $logFile"
Write-Host "============================================================"
'''

cmd = r'''@echo off
setlocal
title Customer 360 Master Repair

set "SCRIPT=%~dp0customer360_master_repair.ps1"

if not exist "%SCRIPT%" (
    echo ERROR: customer360_master_repair.ps1 was not found beside this launcher.
    echo.
    pause
    exit /b 1
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"

echo.
echo Repair process finished.
pause
'''

readme = r'''CUSTOMER 360 MASTER REPAIR
==========================

1. Save any work currently open in Power BI.
2. Extract this ZIP.
3. Double-click RUN_REPAIR.cmd.
4. The repair automatically targets:
   %USERPROFILE%\Downloads\customer-360-revenue-growth-analytics
5. A full backup is created before project files are changed.
6. If file-level validation passes, Power BI reopens automatically.
7. Final status is written to:
   reports\qa\FINAL_REPAIR_STATUS.txt

This package uses ASCII-only executable script text to avoid the earlier
Unicode/mojibake PowerShell parser errors.
'''

ps1_path = out / "customer360_master_repair.ps1"
cmd_path = out / "RUN_REPAIR.cmd"
readme_path = out / "README_REPAIR.txt"

ps1_path.write_text(ps1, encoding="ascii")
cmd_path.write_text(cmd, encoding="ascii")
readme_path.write_text(readme, encoding="ascii")

zip_path = Path("/mnt/data/customer360_master_repair_package.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(ps1_path, ps1_path.name)
    z.write(cmd_path, cmd_path.name)
    z.write(readme_path, readme_path.name)

print(f"Created repair package: {zip_path}")
print("Executable PowerShell script is ASCII-only:", all(ord(c) < 128 for c in ps1))
print("Launcher is ASCII-only:", all(ord(c) < 128 for c in cmd))
print("Package contents:", ", ".join([ps1_path.name, cmd_path.name, readme_path.name]))



from pathlib import Path
import zipfile, textwrap, os, json, re, subprocess, shutil

base = Path("/mnt/data/customer360_final_delivery")
base.mkdir(parents=True, exist_ok=True)

ps1 = r'''param(
    [string]$Root = ""
)

$ErrorActionPreference = "Continue"

# ============================================================
# CUSTOMER 360 - FINAL VS CODE DELIVERY
# ASCII-SAFE ONE-SHOT SCRIPT
# ============================================================

function Write-NoBom {
    param([string]$Path, [string]$Text)
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Text, $enc)
}

function Resolve-Root {
    param([string]$Requested)

    if (-not [string]::IsNullOrWhiteSpace($Requested)) {
        if (Test-Path -LiteralPath $Requested) {
            return (Resolve-Path -LiteralPath $Requested).Path
        }
    }

    $known = Join-Path $env:USERPROFILE "Downloads\customer-360-revenue-growth-analytics"
    if (Test-Path -LiteralPath $known) {
        return (Resolve-Path -LiteralPath $known).Path
    }

    $cwd = (Get-Location).Path
    if (Test-Path -LiteralPath (Join-Path $cwd "powerbi")) {
        return $cwd
    }

    return $null
}

function Log {
    param([string]$Level, [string]$Message)

    $line = "[" + $Level + "] " + $Message
    Write-Host $line

    try {
        [System.IO.File]::AppendAllText(
            $script:LogFile,
            $line + [Environment]::NewLine,
            (New-Object System.Text.UTF8Encoding($false))
        )
    }
    catch {
    }

    if ($Level -eq "REPAIRED") { $script:Repairs++ }
    if ($Level -eq "WARNING") { $script:Warnings++ }
    if ($Level -eq "ERROR") { $script:Errors++ }
}

function Set-OrAddProperty {
    param(
        $Object,
        [string]$Name,
        $Value
    )

    if ($null -eq $Object) {
        return
    }

    if ($Object.PSObject.Properties.Name -contains $Name) {
        $Object.$Name = $Value
    }
    else {
        $Object | Add-Member -MemberType NoteProperty -Name $Name -Value $Value -Force
    }
}

function BoolExpr {
    param([bool]$Value)

    $v = if ($Value) { "true" } else { "false" }

    return @{
        expr = @{
            Literal = @{
                Value = $v
            }
        }
    }
}

function DecimalExpr {
    param([double]$Value)

    return @{
        expr = @{
            Literal = @{
                Value = (
                    [string]::Format(
                        [System.Globalization.CultureInfo]::InvariantCulture,
                        "{0}D",
                        $Value
                    )
                )
            }
        }
    }
}

function StringExpr {
    param([string]$Value)

    return @{
        expr = @{
            Literal = @{
                Value = "'" + $Value + "'"
            }
        }
    }
}

function ColorExpr {
    param([string]$Hex)

    return @{
        solid = @{
            color = @{
                expr = @{
                    Literal = @{
                        Value = "'" + $Hex + "'"
                    }
                }
            }
        }
    }
}

function BackgroundObject {
    param(
        [string]$Color,
        [double]$Transparency = 0
    )

    return @(
        @{
            properties = @{
                show = BoolExpr -Value $true
                color = ColorExpr -Hex $Color
                transparency = DecimalExpr -Value $Transparency
            }
        }
    )
}

function BorderObject {
    param(
        [string]$Color,
        [double]$Radius = 12,
        [double]$Width = 1
    )

    return @(
        @{
            properties = @{
                show = BoolExpr -Value $true
                color = ColorExpr -Hex $Color
                radius = DecimalExpr -Value $Radius
                width = DecimalExpr -Value $Width
            }
        }
    )
}

function PaddingObject {
    param([double]$Padding = 8)

    return @(
        @{
            properties = @{
                top = DecimalExpr -Value $Padding
                bottom = DecimalExpr -Value $Padding
                left = DecimalExpr -Value $Padding
                right = DecimalExpr -Value $Padding
            }
        }
    )
}

function Test-JsonFile {
    param([string]$Path)

    try {
        $raw = [System.IO.File]::ReadAllText($Path)
        $null = $raw | ConvertFrom-Json -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

function Get-PageAccent {
    param([string]$Name)

    $n = $Name.ToLower()

    if ($n -match "executive") { return "#2563EB" }
    if ($n -match "customer") { return "#7C3AED" }
    if ($n -match "revenue") { return "#059669" }
    if ($n -match "marketing") { return "#EA580C" }
    if ($n -match "product") { return "#DB2777" }
    if ($n -match "channel") { return "#0891B2" }

    return "#2563EB"
}

function Get-PageCanvas {
    param([string]$Name)

    $n = $Name.ToLower()

    if ($n -match "executive") { return "#F4F8FF" }
    if ($n -match "customer") { return "#F8F5FF" }
    if ($n -match "revenue") { return "#F3FBF7" }
    if ($n -match "marketing") { return "#FFF8F2" }
    if ($n -match "product") { return "#FFF6FA" }
    if ($n -match "channel") { return "#F2FCFD" }

    return "#F6F8FC"
}

function Get-PagePastels {
    param([string]$Name)

    $n = $Name.ToLower()

    if ($n -match "marketing") {
        return @(
            "#FFF1E6",
            "#FFF7ED",
            "#FFEDD5",
            "#FEF3C7",
            "#FDF2F8",
            "#EFF6FF",
            "#ECFDF5",
            "#F5F3FF"
        )
    }

    if ($n -match "customer") {
        return @(
            "#F5F3FF",
            "#EDE9FE",
            "#FAF5FF",
            "#EFF6FF",
            "#FDF2F8",
            "#ECFDF5",
            "#FFF7ED",
            "#ECFEFF"
        )
    }

    if ($n -match "revenue") {
        return @(
            "#ECFDF5",
            "#D1FAE5",
            "#F0FDF4",
            "#EFF6FF",
            "#FFFBEB",
            "#F5F3FF",
            "#FFF7ED",
            "#ECFEFF"
        )
    }

    return @(
        "#EFF6FF",
        "#F5F3FF",
        "#ECFDF5",
        "#FFF7ED",
        "#FDF2F8",
        "#ECFEFF",
        "#FFFBEB",
        "#EEF2FF"
    )
}

function Capture-Window {
    param(
        [IntPtr]$Handle,
        [string]$OutputPath
    )

    Add-Type -AssemblyName System.Drawing

    $signature = @"
using System;
using System.Runtime.InteropServices;

public class WinRect {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
}
"@

    try {
        if (-not ("WinRect" -as [type])) {
            Add-Type $signature
        }

        $rect = New-Object WinRect+RECT
        $ok = [WinRect]::GetWindowRect($Handle, [ref]$rect)

        if (-not $ok) {
            return $false
        }

        $width = $rect.Right - $rect.Left
        $height = $rect.Bottom - $rect.Top

        if ($width -lt 100 -or $height -lt 100) {
            return $false
        }

        [WinRect]::SetForegroundWindow($Handle) | Out-Null
        Start-Sleep -Milliseconds 700

        $bmp = New-Object System.Drawing.Bitmap($width, $height)
        $graphics = [System.Drawing.Graphics]::FromImage($bmp)

        $graphics.CopyFromScreen(
            $rect.Left,
            $rect.Top,
            0,
            0,
            $bmp.Size
        )

        $bmp.Save(
            $OutputPath,
            [System.Drawing.Imaging.ImageFormat]::Png
        )

        $graphics.Dispose()
        $bmp.Dispose()

        return $true
    }
    catch {
        return $false
    }
}

$root = Resolve-Root -Requested $Root

if ($null -eq $root) {
    Write-Host ""
    Write-Host "ERROR: Could not find the project root."
    Write-Host "Expected:"
    Write-Host (Join-Path $env:USERPROFILE "Downloads\customer-360-revenue-growth-analytics")
    Write-Host ""
    exit 1
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$powerbiDir = Join-Path $root "powerbi"
$docsDir = Join-Path $root "docs"
$qaDir = Join-Path $root "reports\qa"
$imagesDir = Join-Path $root "images\powerbi"
$backupRoot = Join-Path $root "backups"
$backupDir = Join-Path $backupRoot ("final_delivery_" + $timestamp)
$script:LogFile = Join-Path $qaDir ("final_delivery_" + $timestamp + ".log")
$summaryFile = Join-Path $qaDir "FINAL_DELIVERY_STATUS.txt"

$script:Repairs = 0
$script:Warnings = 0
$script:Errors = 0

foreach ($dir in @($docsDir, $qaDir, $imagesDir, $backupRoot, $backupDir)) {
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

Write-Host ""
Write-Host "============================================================"
Write-Host " CUSTOMER 360 - FINAL VS CODE DELIVERY"
Write-Host "============================================================"
Write-Host ""
Log "INFO" ("Project root: " + $root)

# ------------------------------------------------------------
# 1. CLOSE POWER BI
# ------------------------------------------------------------

$pbis = @(Get-Process -Name "PBIDesktop" -ErrorAction SilentlyContinue)

if ($pbis.Count -gt 0) {
    Log "INFO" "Closing Power BI Desktop before source edits."

    foreach ($p in $pbis) {
        try {
            $null = $p.CloseMainWindow()
        }
        catch {
        }
    }

    Start-Sleep -Seconds 4

    $remaining = @(Get-Process -Name "PBIDesktop" -ErrorAction SilentlyContinue)

    if ($remaining.Count -gt 0) {
        foreach ($p in $remaining) {
            try {
                Stop-Process -Id $p.Id -Force -ErrorAction Stop
            }
            catch {
            }
        }

        Log "REPAIRED" "Power BI Desktop force-closed after graceful close did not finish."
    }
    else {
        Log "OK" "Power BI Desktop closed cleanly."
    }
}

# ------------------------------------------------------------
# 2. DISCOVER PBIP / REPORT / MODEL
# ------------------------------------------------------------

if (-not (Test-Path -LiteralPath $powerbiDir)) {
    Log "ERROR" "Power BI project folder missing."
    exit 1
}

$pbip = Get-ChildItem -LiteralPath $powerbiDir -Filter "*.pbip" -File -ErrorAction SilentlyContinue | Select-Object -First 1
$reportDir = Get-ChildItem -LiteralPath $powerbiDir -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*.Report" } | Select-Object -First 1
$modelDir = Get-ChildItem -LiteralPath $powerbiDir -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*.SemanticModel" } | Select-Object -First 1

if ($null -eq $pbip) {
    Log "ERROR" "PBIP file not found."
    exit 1
}

if ($null -eq $reportDir) {
    Log "ERROR" "PBIR report folder not found."
    exit 1
}

if ($null -eq $modelDir) {
    Log "ERROR" "Semantic model folder not found."
    exit 1
}

$pagesDir = Join-Path $reportDir.FullName "definition\pages"

if (-not (Test-Path -LiteralPath $pagesDir)) {
    Log "ERROR" "PBIR pages folder not found."
    exit 1
}

Log "OK" ("PBIP: " + $pbip.FullName)
Log "OK" ("Report: " + $reportDir.FullName)
Log "OK" ("Model: " + $modelDir.FullName)

# ------------------------------------------------------------
# 3. BACKUP BEFORE CHANGES
# ------------------------------------------------------------

try {
    Copy-Item -LiteralPath $powerbiDir -Destination (Join-Path $backupDir "powerbi") -Recurse -Force -ErrorAction Stop

    if (Test-Path -LiteralPath (Join-Path $root "README.md")) {
        Copy-Item -LiteralPath (Join-Path $root "README.md") -Destination $backupDir -Force
    }

    if (Test-Path -LiteralPath (Join-Path $root ".gitignore")) {
        Copy-Item -LiteralPath (Join-Path $root ".gitignore") -Destination $backupDir -Force
    }

    Log "OK" ("Backup created: " + $backupDir)
}
catch {
    Log "ERROR" ("Backup failed: " + $_.Exception.Message)
    exit 1
}

# ------------------------------------------------------------
# 4. NORMALIZE TEXT FILES
# ------------------------------------------------------------

$textExtensions = @(".json", ".pbip", ".pbir", ".tmdl", ".md", ".txt")

$textFiles = @(Get-ChildItem -LiteralPath $powerbiDir -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $textExtensions -contains $_.Extension.ToLower() })

foreach ($file in $textFiles) {
    try {
        if ($file.Length -eq 0) {
            Log "WARNING" ("Zero-byte file found: " + $file.FullName)
            continue
        }

        $text = [System.IO.File]::ReadAllText($file.FullName)

        if ($text.Length -gt 0 -and [int][char]$text[0] -eq 65279) {
            $text = $text.Substring(1)
            Log "REPAIRED" ("Removed BOM marker: " + $file.FullName)
        }

        $nul = [string][char]0

        if ($text.Contains($nul)) {
            $text = $text.Replace($nul, "")
            Log "REPAIRED" ("Removed NUL character(s): " + $file.FullName)
        }

        Write-NoBom -Path $file.FullName -Text $text
    }
    catch {
        Log "WARNING" ("Could not normalize: " + $file.FullName)
    }
}

# ------------------------------------------------------------
# 5. COLOUR SYSTEM
# ------------------------------------------------------------

$darkText = "#172033"
$white = "#FFFFFF"
$outspace = "#111827"

$chartPalette = @(
    "#2563EB",
    "#7C3AED",
    "#059669",
    "#EA580C",
    "#DB2777",
    "#0891B2",
    "#CA8A04",
    "#4F46E5"
)

$borderPalette = @(
    "#BFDBFE",
    "#DDD6FE",
    "#A7F3D0",
    "#FED7AA",
    "#FBCFE8",
    "#A5F3FC",
    "#FDE68A",
    "#C7D2FE"
)

# ------------------------------------------------------------
# 6. STYLE PBIR PAGES AND VISUALS
# ------------------------------------------------------------

$pageFiles = @(Get-ChildItem -LiteralPath $pagesDir -Filter "page.json" -File -Recurse -ErrorAction SilentlyContinue)

$pageNames = @()
$pageCount = 0
$visualCount = 0

foreach ($pageFile in $pageFiles) {
    if (-not (Test-JsonFile -Path $pageFile.FullName)) {
        Log "ERROR" ("Invalid page JSON before styling: " + $pageFile.FullName)
        continue
    }

    $page = [System.IO.File]::ReadAllText($pageFile.FullName) | ConvertFrom-Json
    $pageName = [string]$page.displayName

    if ([string]::IsNullOrWhiteSpace($pageName)) {
        $pageName = [string]$page.name
    }

    $pageNames += $pageName
    $pageAccent = Get-PageAccent -Name $pageName
    $pageCanvas = Get-PageCanvas -Name $pageName
    $pastels = Get-PagePastels -Name $pageName

    if ($null -eq $page.objects) {
        $page | Add-Member -MemberType NoteProperty -Name objects -Value ([PSCustomObject]@{}) -Force
    }

    # Keep page styling conservative.
    Set-OrAddProperty -Object $page.objects -Name "background" -Value @(
        @{
            properties = @{
                color = ColorExpr -Hex $pageCanvas
                transparency = DecimalExpr -Value 0
            }
        }
    )

    Set-OrAddProperty -Object $page.objects -Name "outspace" -Value @(
        @{
            properties = @{
                color = ColorExpr -Hex $outspace
                transparency = DecimalExpr -Value 0
            }
        }
    )

    $pageJson = $page | ConvertTo-Json -Depth 100
    Write-NoBom -Path $pageFile.FullName -Text ($pageJson + [Environment]::NewLine)

    $visualsDir = Join-Path $pageFile.Directory.FullName "visuals"

    if (-not (Test-Path -LiteralPath $visualsDir)) {
        $pageCount++
        continue
    }

    $visualFiles = @(Get-ChildItem -LiteralPath $visualsDir -Filter "visual.json" -File -Recurse -ErrorAction SilentlyContinue)
    $index = 0

    foreach ($vf in $visualFiles) {
        if (-not (Test-JsonFile -Path $vf.FullName)) {
            Log "WARNING" ("Skipping invalid visual JSON: " + $vf.FullName)
            continue
        }

        $rootVisual = [System.IO.File]::ReadAllText($vf.FullName) | ConvertFrom-Json

        if ($null -eq $rootVisual.visual) {
            continue
        }

        $visual = $rootVisual.visual
        $visualType = [string]$visual.visualType
        $paletteIndex = $index % $chartPalette.Count
        $accent = $chartPalette[$paletteIndex]
        $border = $borderPalette[$paletteIndex]
        $background = $pastels[$paletteIndex]

        if ($null -eq $visual.visualContainerObjects) {
            $visual | Add-Member -MemberType NoteProperty -Name visualContainerObjects -Value ([PSCustomObject]@{}) -Force
        }

        $vco = $visual.visualContainerObjects

        if ($visualType -eq "textbox") {
            Set-OrAddProperty -Object $vco -Name "visualHeader" -Value @(
                @{
                    properties = @{
                        show = BoolExpr -Value $false
                    }
                }
            )
        }
        else {
            Set-OrAddProperty -Object $vco -Name "background" -Value (BackgroundObject -Color $background -Transparency 0)
            Set-OrAddProperty -Object $vco -Name "border" -Value (BorderObject -Color $border -Radius 12 -Width 1)
            Set-OrAddProperty -Object $vco -Name "padding" -Value (PaddingObject -Padding 8)
            Set-OrAddProperty -Object $vco -Name "visualHeader" -Value @(
                @{
                    properties = @{
                        show = BoolExpr -Value $false
                    }
                }
            )

            if ($null -ne $vco.title) {
                $title = @($vco.title)[0]

                if ($null -ne $title) {
                    if ($null -eq $title.properties) {
                        $title | Add-Member -MemberType NoteProperty -Name properties -Value ([PSCustomObject]@{}) -Force
                    }

                    Set-OrAddProperty -Object $title.properties -Name "show" -Value (BoolExpr -Value $true)
                    Set-OrAddProperty -Object $title.properties -Name "fontColor" -Value (ColorExpr -Hex $darkText)
                    Set-OrAddProperty -Object $title.properties -Name "fontSize" -Value (DecimalExpr -Value 12)
                    Set-OrAddProperty -Object $title.properties -Name "fontFamily" -Value (StringExpr -Value "Segoe UI Semibold")
                }
            }
        }

        if ($null -eq $visual.objects) {
            $visual | Add-Member -MemberType NoteProperty -Name objects -Value ([PSCustomObject]@{}) -Force
        }

        $objects = $visual.objects

        $barTypes = @(
            "clusteredBarChart",
            "clusteredColumnChart",
            "barChart",
            "columnChart",
            "hundredPercentStackedBarChart",
            "hundredPercentStackedColumnChart",
            "stackedBarChart",
            "stackedColumnChart"
        )

        if ($barTypes -contains $visualType) {
            Set-OrAddProperty -Object $objects -Name "dataPoint" -Value @(
                @{
                    properties = @{
                        fill = ColorExpr -Hex $accent
                    }
                }
            )
        }

        if ($visualType -eq "lineChart" -or $visualType -eq "areaChart") {
            Set-OrAddProperty -Object $objects -Name "dataPoint" -Value @(
                @{
                    properties = @{
                        fill = ColorExpr -Hex $accent
                    }
                }
            )
        }

        if ($visualType -eq "tableEx" -or $visualType -eq "pivotTable") {
            Set-OrAddProperty -Object $objects -Name "columnHeaders" -Value @(
                @{
                    properties = @{
                        backColor = ColorExpr -Hex $pageAccent
                        fontColor = ColorExpr -Hex $white
                        bold = BoolExpr -Value $true
                    }
                }
            )
        }

        $json = $rootVisual | ConvertTo-Json -Depth 100
        Write-NoBom -Path $vf.FullName -Text ($json + [Environment]::NewLine)

        $visualCount++
        $index++
    }

    $pageCount++
    Log "REPAIRED" ("Styled page: " + $pageName)
}

# ------------------------------------------------------------
# 7. VALIDATE ALL PBIR JSON AFTER STYLING
# ------------------------------------------------------------

$jsonFiles = @(Get-ChildItem -LiteralPath $powerbiDir -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Extension.ToLower() -in @(".json", ".pbip", ".pbir") })
$invalidJson = @()

foreach ($file in $jsonFiles) {
    if (-not (Test-JsonFile -Path $file.FullName)) {
        $invalidJson += $file.FullName
    }
}

if ($invalidJson.Count -gt 0) {
    Log "ERROR" ("JSON validation failed in " + $invalidJson.Count + " file(s).")
    Log "INFO" "Rolling back Power BI source to the pre-delivery backup."

    try {
        Remove-Item -LiteralPath $powerbiDir -Recurse -Force
        Copy-Item -LiteralPath (Join-Path $backupDir "powerbi") -Destination $powerbiDir -Recurse -Force
        Log "REPAIRED" "Power BI source rolled back successfully."
    }
    catch {
        Log "ERROR" "Rollback failed."
    }

    $status = "REVIEW REQUIRED"
}
else {
    Log "OK" "All PBIP, PBIR, and JSON files parse successfully."
    $status = "PASS"
}

# ------------------------------------------------------------
# 8. CREATE FINAL PORTFOLIO README
# ------------------------------------------------------------

$readmePath = Join-Path $root "README.md"

$pageListText = ""

foreach ($p in $pageNames) {
    $pageListText += "- " + $p + [Environment]::NewLine
}

$readme = @"
# Customer 360 & Revenue Growth Analytics

## Overview

Customer 360 & Revenue Growth Analytics is an end-to-end business intelligence portfolio project focused on customer behaviour, commercial performance, revenue growth, and marketing efficiency.

The solution uses a Power BI Project (PBIP) structure with PBIR report files and a TMDL semantic model, making the project source-control friendly and suitable for professional analytics engineering workflows.

## Business Questions

The project is designed to support questions such as:

- How is revenue performing?
- Which customers and segments drive value?
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
- PowerShell
- Git
- GitHub

## Dashboard Pages

$pageListText
## Marketing Performance

The marketing section uses synthetic campaign data for portfolio demonstration.

Headline marketing KPIs:

- Total spend: GBP 40,000
- Attributed revenue: GBP 166,000
- Marketing profit: GBP 126,000
- Acquisitions: 2,430
- ROAS: 4.15x
- Blended CPA: GBP 16.46
- Marketing ROI: 315.0%

Key campaign findings:

- Email Retargeting has the strongest ROAS.
- Google Search produces the highest absolute revenue.
- Affiliate is highly efficient relative to most other channels.
- Display Prospecting has the weakest ROAS and highest CPA.

## Dashboard Design

The report uses a colourful but professional visual system:

- Executive views: blue
- Customer views: purple
- Revenue views: green
- Marketing views: orange
- Product views: pink
- Channel views: cyan

The styling uses soft page canvases, high-contrast KPI cards, restrained borders, and consistent typography.

## Quality Assurance

The project includes automated validation for:

- PBIP structure
- PBIR JSON parsing
- UTF8 source files
- report page preservation
- visual preservation
- semantic model source files
- Git status
- final portfolio packaging

QA evidence is stored under:

`reports/qa/`

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

## Screenshots

Dashboard screenshots are stored in:

`images/powerbi/`

## Author

Oluwatosin Oluwaseun Mulero

Data Analyst | Data Scientist

Skills demonstrated include SQL, Python, Power BI, DAX, data modelling, customer analytics, revenue analysis, marketing analytics, dashboard design, data quality validation, and Git-based analytics development.
"@

Write-NoBom -Path $readmePath -Text ($readme + [Environment]::NewLine)
Log "REPAIRED" "README.md finalized."

# ------------------------------------------------------------
# 9. CREATE RECRUITER SUMMARY
# ------------------------------------------------------------

$recruiterPath = Join-Path $docsDir "RECRUITER_PROJECT_SUMMARY.md"

$recruiterText = @"
# Recruiter Project Summary

## Project

Customer 360 & Revenue Growth Analytics

## What this project demonstrates

- End-to-end analytics delivery
- Customer and revenue analysis
- Marketing performance measurement
- KPI development
- DAX measures
- Semantic modelling
- Power BI dashboard engineering
- PBIP / PBIR / TMDL development
- Visual Studio Code workflow
- Git source control
- Automated QA

## Business Value

The solution converts customer, revenue, and campaign-level data into decision-support reporting that enables users to compare performance, identify efficient channels, and monitor headline commercial KPIs.

## Portfolio Positioning

Relevant to roles including:

- Data Analyst
- Business Intelligence Analyst
- Power BI Analyst
- Reporting Analyst
- Insights Analyst
- Customer Data Analyst
- Commercial Data Analyst
- Data Scientist
"@

Write-NoBom -Path $recruiterPath -Text ($recruiterText + [Environment]::NewLine)
Log "REPAIRED" "Recruiter project summary created."

# ------------------------------------------------------------
# 10. GITIGNORE
# ------------------------------------------------------------

$gitignorePath = Join-Path $root ".gitignore"

$requiredIgnore = @(
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
    "Thumbs.db"
)

$ignoreLines = @()

if (Test-Path -LiteralPath $gitignorePath) {
    $ignoreLines = @([System.IO.File]::ReadAllLines($gitignorePath))
}

foreach ($line in $requiredIgnore) {
    if ($ignoreLines -notcontains $line) {
        $ignoreLines += $line
    }
}

Write-NoBom -Path $gitignorePath -Text (($ignoreLines -join [Environment]::NewLine) + [Environment]::NewLine)
Log "REPAIRED" ".gitignore finalized."

# ------------------------------------------------------------
# 11. GIT INIT / COMMIT
# ------------------------------------------------------------

$git = Get-Command git -ErrorAction SilentlyContinue
$gitCommitted = $false
$gitPushed = $false
$remoteExists = $false

if ($null -ne $git) {
    Push-Location $root

    if (-not (Test-Path -LiteralPath (Join-Path $root ".git"))) {
        try {
            git init | Out-Null
            Log "REPAIRED" "Git repository initialized."
        }
        catch {
            Log "WARNING" "Could not initialize Git repository."
        }
    }

    try {
        git add -A

        $statusLines = @(git status --porcelain)

        if ($statusLines.Count -gt 0) {
            $commitMessage = "Complete Customer 360 portfolio dashboard"
            git commit -m $commitMessage | Out-Null

            if ($LASTEXITCODE -eq 0) {
                $gitCommitted = $true
                Log "OK" "Final Git commit created."
            }
            else {
                Log "WARNING" "Git commit did not complete. Check Git user.name and user.email configuration."
            }
        }
        else {
            Log "OK" "No uncommitted Git changes remain."
            $gitCommitted = $true
        }
    }
    catch {
        Log "WARNING" ("Git commit stage failed: " + $_.Exception.Message)
    }

    try {
        $origin = git remote get-url origin 2>$null

        if (-not [string]::IsNullOrWhiteSpace($origin)) {
            $remoteExists = $true
            Log "OK" ("Git remote detected: " + $origin)

            git push -u origin HEAD

            if ($LASTEXITCODE -eq 0) {
                $gitPushed = $true
                Log "OK" "Git push completed."
            }
            else {
                Log "WARNING" "Git push was not completed. Authentication or branch permissions may be required."
            }
        }
        else {
            Log "WARNING" "No Git origin remote is configured. Local commit is preserved."
        }
    }
    catch {
        Log "WARNING" "No usable Git origin remote was found."
    }

    Pop-Location
}
else {
    Log "WARNING" "Git is not installed or is not available on PATH."
}

# ------------------------------------------------------------
# 12. OPEN POWER BI
# ------------------------------------------------------------

if ($status -eq "PASS") {
    try {
        Start-Process -FilePath $pbip.FullName -ErrorAction Stop
        Log "OK" "Power BI launch command sent."
    }
    catch {
        try {
            Invoke-Item -LiteralPath $pbip.FullName -ErrorAction Stop
            Log "OK" "Power BI launched using Windows file association."
        }
        catch {
            Log "WARNING" ("Power BI could not be launched automatically. Open: " + $pbip.FullName)
        }
    }
}

# ------------------------------------------------------------
# 13. ATTEMPT AUTOMATED SCREENSHOT CAPTURE
# ------------------------------------------------------------

$screenshotsCaptured = 0

if ($status -eq "PASS") {
    try {
        Start-Sleep -Seconds 12

        $proc = Get-Process -Name "PBIDesktop" -ErrorAction SilentlyContinue |
            Where-Object { $_.MainWindowHandle -ne 0 } |
            Select-Object -First 1

        if ($null -ne $proc) {
            Add-Type -AssemblyName System.Windows.Forms

            $pageTotal = $pageNames.Count

            if ($pageTotal -lt 1) {
                $pageTotal = 1
            }

            for ($i = 0; $i -lt $pageTotal; $i++) {
                $safeName = "page_" + ("{0:D2}" -f ($i + 1))

                if ($i -lt $pageNames.Count) {
                    $candidate = $pageNames[$i] -replace '[^A-Za-z0-9]+', '_'
                    $candidate = $candidate.Trim("_")

                    if (-not [string]::IsNullOrWhiteSpace($candidate)) {
                        $safeName = ("{0:D2}" -f ($i + 1)) + "_" + $candidate.ToLower()
                    }
                }

                $png = Join-Path $imagesDir ($safeName + ".png")

                if (Capture-Window -Handle $proc.MainWindowHandle -OutputPath $png) {
                    $screenshotsCaptured++
                    Log "OK" ("Screenshot captured: " + $png)
                }
                else {
                    Log "WARNING" ("Could not capture screenshot for page index " + ($i + 1))
                }

                if ($i -lt ($pageTotal - 1)) {
                    [System.Windows.Forms.SendKeys]::SendWait("^{PGDN}")
                    Start-Sleep -Seconds 2
                }
            }
        }
        else {
            Log "WARNING" "Power BI window was not ready for automated screenshots."
        }
    }
    catch {
        Log "WARNING" ("Automated screenshot stage skipped: " + $_.Exception.Message)
    }
}

# ------------------------------------------------------------
# 14. UPDATE README SCREENSHOT SECTION IF PNG FILES EXIST
# ------------------------------------------------------------

$pngFiles = @(Get-ChildItem -LiteralPath $imagesDir -Filter "*.png" -File -ErrorAction SilentlyContinue | Sort-Object Name)

if ($pngFiles.Count -gt 0) {
    $existingReadme = [System.IO.File]::ReadAllText($readmePath)

    $gallery = [Environment]::NewLine + "## Dashboard Gallery" + [Environment]::NewLine + [Environment]::NewLine

    foreach ($png in $pngFiles) {
        $relative = "images/powerbi/" + $png.Name
        $label = [System.IO.Path]::GetFileNameWithoutExtension($png.Name).Replace("_", " ")
        $gallery += "### " + $label + [Environment]::NewLine + [Environment]::NewLine
        $gallery += "![" + $label + "](" + $relative + ")" + [Environment]::NewLine + [Environment]::NewLine
    }

    if ($existingReadme -notmatch "## Dashboard Gallery") {
        Write-NoBom -Path $readmePath -Text ($existingReadme.TrimEnd() + [Environment]::NewLine + $gallery)
        Log "REPAIRED" "Dashboard gallery added to README."
    }
}

# ------------------------------------------------------------
# 15. SECOND GIT COMMIT FOR SCREENSHOTS
# ------------------------------------------------------------

if ($null -ne $git) {
    Push-Location $root

    try {
        git add -A

        $pending = @(git status --porcelain)

        if ($pending.Count -gt 0) {
            git commit -m "Add final dashboard screenshots and portfolio documentation" | Out-Null

            if ($LASTEXITCODE -eq 0) {
                Log "OK" "Screenshot/documentation commit created."
            }

            if ($remoteExists) {
                git push

                if ($LASTEXITCODE -eq 0) {
                    $gitPushed = $true
                    Log "OK" "Latest portfolio changes pushed."
                }
            }
        }
    }
    catch {
        Log "WARNING" "Final Git screenshot commit/push stage could not complete."
    }

    Pop-Location
}

# ------------------------------------------------------------
# 16. FINAL QA
# ------------------------------------------------------------

$finalInvalidJson = @()

$jsonFiles = @(Get-ChildItem -LiteralPath $powerbiDir -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Extension.ToLower() -in @(".json", ".pbip", ".pbir") })

foreach ($file in $jsonFiles) {
    if (-not (Test-JsonFile -Path $file.FullName)) {
        $finalInvalidJson += $file.FullName
    }
}

if ($finalInvalidJson.Count -gt 0) {
    $status = "REVIEW REQUIRED"
}

$summary = @"
============================================================
CUSTOMER 360 - FINAL DELIVERY STATUS
============================================================

STATUS:
$status

PROJECT:
$root

BACKUP:
$backupDir

PAGES DETECTED:
$pageCount

VISUALS STYLED:
$visualCount

SCREENSHOTS CAPTURED:
$screenshotsCaptured

INVALID JSON REMAINING:
$($finalInvalidJson.Count)

REPAIRS:
$script:Repairs

WARNINGS:
$script:Warnings

ERRORS:
$script:Errors

GIT COMMIT READY:
$gitCommitted

GIT REMOTE EXISTS:
$remoteExists

GIT PUSH COMPLETED:
$gitPushed

README:
$readmePath

RECRUITER SUMMARY:
$recruiterPath

SCREENSHOT FOLDER:
$imagesDir

============================================================
"@

Write-NoBom -Path $summaryFile -Text $summary

Write-Host ""
Write-Host $summary

try {
    Start-Process -FilePath "explorer.exe" -ArgumentList $qaDir
}
catch {
}

Write-Host ""
Write-Host "============================================================"
Write-Host " FINAL VS CODE DELIVERY FINISHED"
Write-Host "============================================================"
Write-Host ""
Write-Host "If STATUS is PASS, the local portfolio build is complete."
Write-Host "If Git push is False, your project is still committed locally."
Write-Host "A push can only succeed when an existing remote and valid Git credentials are available."
Write-Host "============================================================"
'''

cmd = r'''@echo off
setlocal
title Customer 360 Final VS Code Delivery

set "SCRIPT=%~dp0customer360_final_delivery.ps1"

if not exist "%SCRIPT%" (
    echo ERROR: customer360_final_delivery.ps1 is missing.
    echo.
    pause
    exit /b 1
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"

echo.
echo Final delivery script finished.
pause
'''

instructions = r'''CUSTOMER 360 FINAL DELIVERY
===========================

Use this package from VS Code / Windows.

Recommended:
1. Extract this ZIP.
2. Open the Customer 360 project folder in VS Code.
3. Save any Power BI work.
4. Either:
   - Run the PS1 from the VS Code PowerShell terminal, or
   - Double-click RUN_FINAL_DELIVERY.cmd.

Direct VS Code command:
powershell -NoProfile -ExecutionPolicy Bypass -File ".\customer360_final_delivery.ps1"

The script:
- closes Power BI before editing source files;
- creates a full backup;
- applies colourful page and visual styling;
- validates PBIR/PBIP JSON;
- finalizes README.md;
- creates docs/RECRUITER_PROJECT_SUMMARY.md;
- finalizes .gitignore;
- initializes/commits Git if available;
- pushes only when an existing origin remote is configured;
- opens Power BI;
- attempts automatic dashboard screenshots;
- adds screenshots to README when capture succeeds;
- creates reports/qa/FINAL_DELIVERY_STATUS.txt.

Important:
No script can guarantee Git push without an existing remote and valid credentials.
No script can guarantee Power BI window screenshots if Windows blocks foreground
automation, but screenshot failure does not corrupt the report.
'''

ps1_path = base / "customer360_final_delivery.ps1"
cmd_path = base / "RUN_FINAL_DELIVERY.cmd"
txt_path = base / "README_FIRST.txt"

ps1_path.write_text(ps1, encoding="ascii")
cmd_path.write_text(cmd, encoding="ascii")
txt_path.write_text(instructions, encoding="ascii")

# Sanity checks that specifically protect against the previous encoding/parser issue.
assert all(ord(ch) < 128 for ch in ps1)
assert all(ord(ch) < 128 for ch in cmd)

zip_path = Path("/mnt/data/customer360_final_vs_code_delivery.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(ps1_path, ps1_path.name)
    z.write(cmd_path, cmd_path.name)
    z.write(txt_path, txt_path.name)

print("Created:", zip_path)
print("PowerShell ASCII-safe:", all(ord(ch) < 128 for ch in ps1))
print("Launcher ASCII-safe:", all(ord(ch) < 128 for ch in cmd))
print("Files:", [p.name for p in base.iterdir()])



from pathlib import Path
import textwrap, zipfile, py_compile, hashlib, json, os, re

out = Path("/mnt/data/customer360_python_final")
out.mkdir(parents=True, exist_ok=True)

script = r'''from __future__ import annotations

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
'''

script_path = out / "customer360_FINAL_BUILD.py"
script_path.write_text(script, encoding="ascii")

# Validate Python syntax.
compile(script, str(script_path), "exec")

launcher = r'''@echo off
setlocal
title Customer 360 Final Python Build

cd /d "%USERPROFILE%\Downloads\customer-360-revenue-growth-analytics"

if not exist "customer360_FINAL_BUILD.py" (
    echo ERROR: customer360_FINAL_BUILD.py is not in the project root.
    echo.
    pause
    exit /b 1
)

python "customer360_FINAL_BUILD.py"

echo.
echo Build finished.
pause
'''
launcher_path = out / "RUN_FROM_PROJECT_ROOT.cmd"
launcher_path.write_text(launcher, encoding="ascii")

readme = r'''CUSTOMER 360 - FINAL BUILD
==========================

This package replaces the earlier PowerShell repair scripts.

WHY:
The old PowerShell script contained corrupted mojibake characters such as
the broken dash/quote sequences that caused parser errors. This build uses
Python instead, executed from VS Code, so that failure mode is removed.

USE:
1. Download customer360_FINAL_BUILD.py.
2. Copy it into:
   C:\Users\OLUWATOSIN OLUWASEUN\Downloads\customer-360-revenue-growth-analytics
3. Open that project folder in VS Code.
4. Open a new VS Code terminal.
5. Run:

   python .\customer360_FINAL_BUILD.py

The script creates a backup before modifying the Power BI project.
It validates JSON and rolls back Power BI source changes if styling creates
invalid JSON.

The final report is:
reports\qa\FINAL_PYTHON_BUILD_STATUS.txt
'''
readme_path = out / "README_FIRST.txt"
readme_path.write_text(readme, encoding="ascii")

zip_path = Path("/mnt/data/customer360_FINAL_BUILD_PACKAGE.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for p in (script_path, launcher_path, readme_path):
        z.write(p, p.name)

sha = hashlib.sha256(script_path.read_bytes()).hexdigest()

print("Created:", script_path)
print("ZIP:", zip_path)
print("Python syntax validation: PASS")
print("ASCII-only:", all(b < 128 for b in script_path.read_bytes()))
print("SHA256:", sha)


code = r'''
from __future__ import annotations
import json, os, re, shutil, subprocess, sys, time
from datetime import datetime
from pathlib import Path

PROJECT_NAME = "customer-360-revenue-growth-analytics"
REPO_NAME = PROJECT_NAME
REPO_VISIBILITY = "private"
REPO_DESCRIPTION = "Customer 360 and Revenue Growth Analytics portfolio built with Power BI, DAX, PBIP, PBIR, TMDL, Python, SQL and Git."

def run(cmd, cwd=None, timeout=300, capture=True):
    print("$", " ".join(map(str, cmd)))
    try:
        p = subprocess.run(
            [str(x) for x in cmd],
            cwd=str(cwd) if cwd else None,
            text=True,
            capture_output=capture,
            timeout=timeout,
            shell=False,
        )
        if capture:
            if p.stdout.strip():
                print(p.stdout.strip())
            if p.stderr.strip():
                print(p.stderr.strip())
        return p.returncode, (p.stdout.strip() if capture else ""), (p.stderr.strip() if capture else "")
    except Exception as e:
        print("[ERROR]", e)
        return 999, "", str(e)

def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def find_root():
    cwd = Path.cwd()
    if (cwd / "powerbi").exists():
        return cwd
    d = Path.home() / "Downloads" / PROJECT_NAME
    if d.exists():
        return d
    raise SystemExit(f"Project not found. Open {PROJECT_NAME} in VS Code and run again.")

def valid_json(path: Path):
    try:
        json.loads(path.read_text(encoding="utf-8-sig"))
        return True
    except Exception:
        return False

def slug(s: str):
    s = re.sub(r"[^A-Za-z0-9]+", "_", s.strip()).strip("_").lower()
    return s or "page"

root = find_root()
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
powerbi = root / "powerbi"
docs = root / "docs"
qa = root / "reports" / "qa"
images = root / "images" / "powerbi"
scripts = root / "scripts"
vscode = root / ".vscode"
backups = root / "backups"
for p in [docs, qa, images, scripts, vscode, backups]:
    p.mkdir(parents=True, exist_ok=True)

log_path = qa / f"stage6_{timestamp}.log"
status_path = qa / "FINAL_STAGE6_STATUS.txt"
warnings, errors = [], []

def log(level, msg):
    line = f"[{level}] {msg}"
    print(line)
    with log_path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")
    if level == "WARNING": warnings.append(msg)
    if level == "ERROR": errors.append(msg)

print("\n" + "="*60)
print(" CUSTOMER 360 - STAGE 6 VS CODE DELIVERY")
print("="*60 + "\n")
log("INFO", f"Project root: {root}")

# 1. Validate finished Power BI project
pbips = list(powerbi.glob("*.pbip"))
reports = list(powerbi.glob("*.Report"))
models = list(powerbi.glob("*.SemanticModel"))
if not pbips or not reports or not models:
    raise SystemExit("Missing PBIP, Report, or SemanticModel component.")
pbip, report_dir, model_dir = pbips[0], reports[0], models[0]
pages_dir = report_dir / "definition" / "pages"
pages_json = pages_dir / "pages.json"
if not pages_dir.exists():
    raise SystemExit("PBIR pages directory missing.")

json_like = [p for p in powerbi.rglob("*") if p.is_file() and p.suffix.lower() in {".json",".pbip",".pbir"}]
bad = [p for p in json_like if not valid_json(p)]
if bad:
    for p in bad: log("ERROR", f"Invalid JSON: {p}")
    raise SystemExit("Stage 6 stopped because Power BI JSON is invalid.")
log("OK", f"Power BI JSON valid: {len(json_like)} files")

# 2. Page inventory in report order
page_map = {}
for pf in pages_dir.rglob("page.json"):
    try:
        obj = json.loads(pf.read_text(encoding="utf-8-sig"))
        page_map[str(obj.get("name", pf.parent.name))] = str(obj.get("displayName") or obj.get("name") or pf.parent.name)
    except Exception:
        pass
page_ids = []
if pages_json.exists() and valid_json(pages_json):
    try:
        meta = json.loads(pages_json.read_text(encoding="utf-8-sig"))
        page_ids = [str(x) for x in meta.get("pageOrder", [])]
    except Exception:
        pass
ordered_pages = [page_map[i] for i in page_ids if i in page_map]
for k,v in page_map.items():
    if v not in ordered_pages: ordered_pages.append(v)
log("OK", f"Pages detected: {len(ordered_pages)}")
for x in ordered_pages: log("INFO", f"Page: {x}")

# 3. Final docs
page_lines = "\n".join(f"- {x}" for x in ordered_pages)
readme = f"""# Customer 360 & Revenue Growth Analytics

## Overview
End-to-end business intelligence portfolio project covering customer behaviour, retention, acquisition, product performance, forecasting, experimentation and marketing efficiency.

The solution uses Power BI Project (PBIP), PBIR report source, a TMDL semantic model, Python, SQL, DAX, Visual Studio Code and Git.

## Dashboard Pages
{page_lines}

## Marketing Performance
The marketing page uses synthetic campaign data for portfolio demonstration.

- Total marketing spend: GBP 40,000
- Attributed revenue: GBP 166,000
- Marketing profit: GBP 126,000
- Acquisitions: 2,430
- Overall ROAS: 4.15x
- Blended CPA: GBP 16.46
- Marketing ROI: 315.0%

## Design System
- Executive: blue
- Customer and retention: purple
- Revenue: green
- Marketing: orange
- Product: pink
- Channel: cyan

## Technology
- Power BI
- DAX
- PBIP / PBIR / TMDL
- Python
- SQL
- Power Query
- Git and GitHub
- Visual Studio Code

## Quality Assurance
Automated checks validate Power BI JSON, project structure, source files, documentation and Git state. QA outputs are stored in `reports/qa/`.

<!-- DASHBOARD_GALLERY_START -->
## Dashboard Gallery

Final screenshots are stored in `images/powerbi/`.

<!-- DASHBOARD_GALLERY_END -->

## Author
Oluwatosin Oluwaseun Mulero

Data Analyst | Data Scientist
"""
write_text(root / "README.md", readme)

write_text(docs / "RECRUITER_PROJECT_SUMMARY.md", f"""# Recruiter Project Summary

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
- Forecasting and experimentation
- Marketing performance measurement
- KPI development
- DAX
- Semantic modelling
- Power BI dashboard engineering
- PBIP / PBIR / TMDL
- Python and SQL
- Git source control
- Automated QA
""")

write_text(docs / "GITHUB_PUBLISH_CHECKLIST.md", """# GitHub Publish Checklist
- [x] PBIP detected
- [x] PBIR detected
- [x] Semantic model detected
- [x] JSON validation passed
- [x] README finalized
- [x] Recruiter summary created
- [x] Screenshot folder created
- [x] VS Code project tasks created
- [ ] Screenshots visually verified
- [ ] GitHub remote/push verified
""")

write_text(docs / "POWER_BI_SCREENSHOT_GUIDE.md", "\n".join(
    ["# Power BI Screenshot Guide", "", "Save screenshots in `images/powerbi/`.", ""]
    + [f"- `{i:02d}_{slug(name)}.png` - {name}" for i,name in enumerate(ordered_pages,1)]
) + "\n")
log("OK", "Portfolio documentation created/updated")

# 4. VS Code workspace automation
tasks = {
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Customer 360 - Stage 6 Publish",
            "type": "shell",
            "command": "python",
            "args": ["${workspaceFolder}/scripts/stage6_publish.py"],
            "group": {"kind": "build", "isDefault": True},
            "problemMatcher": []
        },
        {
            "label": "Customer 360 - Open Power BI",
            "type": "shell",
            "command": "powershell",
            "args": ["-NoProfile","-Command",f'Start-Process "{pbip}"'],
            "problemMatcher": []
        }
    ]
}
write_text(vscode / "tasks.json", json.dumps(tasks, indent=2) + "\n")
write_text(vscode / "settings.json", json.dumps({
    "files.encoding":"utf8",
    "files.eol":"\n",
    "python.terminal.activateEnvironment": True,
    "terminal.integrated.cwd":"${workspaceFolder}"
}, indent=2) + "\n")
log("OK", ".vscode tasks/settings created")

# 5. Gitignore
gitignore = root / ".gitignore"
existing = gitignore.read_text(encoding="utf-8-sig").splitlines() if gitignore.exists() else []
needed = [".pbi/","**/.pbi/","*.abf","*.tmp","*.lock","backups/","__pycache__/","*.pyc",".venv/","venv/",".DS_Store","Thumbs.db"]
for item in needed:
    if item not in existing: existing.append(item)
write_text(gitignore, "\n".join(existing).rstrip() + "\n")

# 6. Power BI launch and screenshot attempt
def install(pkg):
    rc,_,_ = run([sys.executable,"-m","pip","install",pkg,"--quiet"], cwd=root, timeout=300)
    return rc == 0

def screenshot_attempt():
    if os.name != "nt":
        return 0
    try:
        import pyautogui
    except Exception:
        if not install("pyautogui"):
            log("WARNING","Could not install pyautogui; screenshot automation skipped.")
            return 0
        import pyautogui
    try:
        os.startfile(str(pbip))
    except Exception as e:
        log("WARNING", f"Could not open Power BI automatically: {e}")
        return 0

    log("INFO","Waiting for Power BI to load before screenshot attempt...")
    time.sleep(20)
    # Move to first tab, then capture screen and advance pages.
    try:
        for _ in range(max(len(ordered_pages),1)+2):
            pyautogui.hotkey("ctrl","pageup")
            time.sleep(0.5)
        count = 0
        for idx, name in enumerate(ordered_pages,1):
            time.sleep(2)
            target = images / f"{idx:02d}_{slug(name)}.png"
            pyautogui.screenshot(str(target))
            if target.exists() and target.stat().st_size > 1000:
                count += 1
                log("OK", f"Screenshot captured: {target.name}")
            if idx < len(ordered_pages):
                pyautogui.hotkey("ctrl","pagedown")
        pyautogui.hotkey("ctrl","s")
        return count
    except Exception as e:
        log("WARNING", f"Screenshot automation could not finish: {e}")
        return 0

screenshots = screenshot_attempt()

# 7. Rebuild gallery from screenshots present
pngs = sorted(images.glob("*.png"))
gallery = ["<!-- DASHBOARD_GALLERY_START -->","## Dashboard Gallery",""]
if pngs:
    for p in pngs:
        title = p.stem.replace("_"," ").title()
        gallery += [f"### {title}","",f"![{title}](images/powerbi/{p.name})",""]
else:
    gallery += ["Final screenshots will be added here.",""]
gallery += ["<!-- DASHBOARD_GALLERY_END -->"]
readme_path = root / "README.md"
text = readme_path.read_text(encoding="utf-8-sig")
start = text.find("<!-- DASHBOARD_GALLERY_START -->")
end = text.find("<!-- DASHBOARD_GALLERY_END -->")
if start >= 0 and end >= 0:
    end += len("<!-- DASHBOARD_GALLERY_END -->")
    text = text[:start] + "\n".join(gallery) + text[end:]
write_text(readme_path, text)

# 8. Git / GitHub
git = shutil.which("git")
if not git:
    raise SystemExit("Git is not installed or not on PATH.")
if not (root / ".git").exists():
    rc,_,err = run([git,"init"], cwd=root)
    if rc != 0: raise SystemExit(f"git init failed: {err}")
run([git,"branch","-M","main"], cwd=root)

# GitHub CLI
gh = shutil.which("gh")
if not gh and os.name == "nt":
    winget = shutil.which("winget")
    if winget:
        log("INFO","Installing GitHub CLI with winget...")
        run([winget,"install","--id","GitHub.cli","-e","--source","winget","--accept-source-agreements","--accept-package-agreements"], timeout=300)
        candidates = [Path(r"C:\Program Files\GitHub CLI\gh.exe"), Path.home()/"AppData"/"Local"/"Programs"/"GitHub CLI"/"gh.exe"]
        gh = next((str(p) for p in candidates if p.exists()), shutil.which("gh"))

if gh:
    rc,_,_ = run([gh,"auth","status","--hostname","github.com"], timeout=60)
    if rc != 0:
        log("INFO","GitHub login is required. Complete the browser login opened by GitHub CLI.")
        rc,_,err = run([gh,"auth","login","--hostname","github.com","--git-protocol","https","--web"], timeout=900)
        if rc != 0:
            log("WARNING", f"GitHub login not completed: {err}")
    rc, username, _ = run([gh,"api","user","--jq",".login"], timeout=60)
    username = username.strip() if rc == 0 else ""
    if username:
        run([git,"config","user.name","Oluwatosin Oluwaseun Mulero"], cwd=root)
        rc,email,_ = run([git,"config","--get","user.email"], cwd=root)
        if not email.strip():
            run([git,"config","user.email",f"{username}@users.noreply.github.com"], cwd=root)
        run([gh,"auth","setup-git"], timeout=60)
else:
    username = ""
    log("WARNING","GitHub CLI unavailable. Git will still be committed locally.")

run([git,"add","-A"], cwd=root)
rc, pending, _ = run([git,"status","--porcelain"], cwd=root)
if pending.strip():
    rc,_,err = run([git,"commit","-m","Finalize Customer 360 analytics portfolio"], cwd=root, timeout=120)
    if rc != 0:
        raise SystemExit(f"Git commit failed: {err}")
    log("OK","Final Git commit created")
else:
    log("OK","No uncommitted changes remain")

remote_url = ""
if gh and username:
    rc, origin, _ = run([git,"remote","get-url","origin"], cwd=root)
    origin = origin.strip()
    repo_full = f"{username}/{REPO_NAME}"
    if not origin:
        rc, url, _ = run([gh,"repo","view",repo_full,"--json","url","--jq",".url"], timeout=60)
        if rc == 0 and url.strip():
            remote_url = url.strip()
            run([git,"remote","add","origin",f"https://github.com/{repo_full}.git"], cwd=root)
        else:
            vis = "--public" if REPO_VISIBILITY == "public" else "--private"
            rc, out, err = run([gh,"repo","create",REPO_NAME,vis,"--source",str(root),"--remote","origin","--description",REPO_DESCRIPTION], cwd=root, timeout=180)
            if rc != 0:
                log("WARNING", f"GitHub repository creation failed: {err}")
            else:
                log("OK", f"GitHub repository created as {REPO_VISIBILITY}")
    rc, origin, _ = run([git,"remote","get-url","origin"], cwd=root)
    if rc == 0 and origin.strip():
        remote_url = origin.strip()
        rc,_,err = run([git,"push","-u","origin","main"], cwd=root, timeout=300)
        if rc == 0:
            log("OK","GitHub push completed")
        else:
            log("WARNING", f"GitHub push failed; local commit is safe: {err}")

# 9. Final status
rc, status_out, _ = run([git,"status","--short"], cwd=root)
clean = not status_out.strip()
status = "PASS" if not errors and len(bad) == 0 else "REVIEW REQUIRED"
report = f"""============================================================
CUSTOMER 360 - FINAL STAGE 6 STATUS
============================================================

STATUS: {status}

PROJECT:
{root}

POWER BI PAGES:
{len(ordered_pages)}

POWER BI JSON ERRORS:
{len(bad)}

SCREENSHOTS PRESENT:
{len(list(images.glob("*.png")))}

SCREENSHOTS AUTO-CAPTURED THIS RUN:
{screenshots}

GIT WORKING TREE CLEAN:
{clean}

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

SCREENSHOTS:
{images}

============================================================
"""
write_text(status_path, report)
print("\n" + report)

# Save a copy of this script under scripts for repeat runs.
try:
    src = Path(__file__).resolve()
    dst = scripts / "stage6_publish.py"
    if src != dst:
        shutil.copy2(src, dst)
except Exception:
    pass

if os.name == "nt":
    try: os.startfile(str(qa))
    except Exception: pass

print("STAGE 6 COMPLETE")
'''
compile(code, "<stage6>", "exec")
print("syntax ok", len(code.splitlines()))



code2 = code.replace(
'''    log("INFO","Waiting for Power BI to load before screenshot attempt...")
    time.sleep(20)
    # Move to first tab, then capture screen and advance pages.
    try:
        for _ in range(max(len(ordered_pages),1)+2):
            pyautogui.hotkey("ctrl","pageup")
            time.sleep(0.5)
        count = 0
        for idx, name in enumerate(ordered_pages,1):
            time.sleep(2)
            target = images / f"{idx:02d}_{slug(name)}.png"
            pyautogui.screenshot(str(target))
            if target.exists() and target.stat().st_size > 1000:
                count += 1
                log("OK", f"Screenshot captured: {target.name}")
            if idx < len(ordered_pages):
                pyautogui.hotkey("ctrl","pagedown")
        pyautogui.hotkey("ctrl","s")
        return count
    except Exception as e:
        log("WARNING", f"Screenshot automation could not finish: {e}")
        return 0
''',
'''    log("INFO","Waiting for Power BI to load before screenshot attempt...")
    time.sleep(12)
    try:
        try:
            import pygetwindow as gw
        except Exception:
            install("pygetwindow")
            import pygetwindow as gw

        window = None
        deadline = time.time() + 60
        while time.time() < deadline and window is None:
            candidates = []
            for title in gw.getAllTitles():
                if title and ("Power BI" in title or PROJECT_NAME.lower() in title.lower()):
                    candidates.extend(gw.getWindowsWithTitle(title))
            candidates = [w for w in candidates if getattr(w, "width", 0) > 500 and getattr(w, "height", 0) > 400]
            if candidates:
                window = candidates[0]
                break
            time.sleep(2)

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
            time.sleep(2)

        for _ in range(max(len(ordered_pages),1)+2):
            pyautogui.hotkey("ctrl","pageup")
            time.sleep(0.5)

        count = 0
        for idx, name in enumerate(ordered_pages,1):
            time.sleep(2)
            target = images / f"{idx:02d}_{slug(name)}.png"
            if window is not None:
                region = (max(window.left,0), max(window.top,0), window.width, window.height)
                shot = pyautogui.screenshot(region=region)
                shot.save(str(target))
            else:
                pyautogui.screenshot(str(target))

            if target.exists() and target.stat().st_size > 1000:
                count += 1
                log("OK", f"Screenshot captured: {target.name}")

            if idx < len(ordered_pages):
                pyautogui.hotkey("ctrl","pagedown")

        pyautogui.hotkey("ctrl","s")
        time.sleep(3)
        return count

    except Exception as e:
        log("WARNING", f"Screenshot automation could not finish: {e}")
        return 0
'''
)
compile(code2, "<stage6>", "exec")
print("syntax ok", len(code2.splitlines()))
