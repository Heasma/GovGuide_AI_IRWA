"""
GovGuide AI -- Dataset Profiling Script
Phase 1: Profiling ONLY -- no cleaning, no transformation, no DB writes.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR      = PROJECT_ROOT / "data" / "raw"
VAL_DIR      = PROJECT_ROOT / "data" / "validation"
DATASET_NAME = "Business_Licenses_-_Current_Active_20260819.csv"
CSV_PATH     = RAW_DIR / DATASET_NAME

VAL_DIR.mkdir(parents=True, exist_ok=True)


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_encoding(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            with open(path, "r", encoding=enc, errors="strict") as f:
                f.read(65536)
            return enc
        except Exception:
            continue
    return "latin-1"


def detect_delimiter(path: Path, encoding: str) -> str:
    with open(path, "r", encoding=encoding) as f:
        sample = f.read(4096)
    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        return ","


def try_parse_dates(series: pd.Series) -> dict:
    parsed     = pd.to_datetime(series, errors="coerce", )
    total      = len(series)
    non_null   = int(series.notna().sum())
    successful = int(parsed.notna().sum())
    return {
        "total"              : int(total),
        "non_null_original"  : non_null,
        "successfully_parsed": successful,
        "parse_rate_pct"     : round(successful / total * 100, 2) if total else 0,
        "invalid_count"      : non_null - successful,
        "min_date"           : str(parsed.min()) if successful else None,
        "max_date"           : str(parsed.max()) if successful else None,
        "missing_count"      : int(total - non_null),
    }


def is_likely_date_col(series: pd.Series, name: str) -> bool:
    keywords = ["DATE", "TIME", "CREATED", "ISSUED", "EXPIR", "START", "CHANGE"]
    if any(k in name.upper() for k in keywords):
        return True
    sample = series.dropna().astype(str).head(20)
    hits = sum(1 for v in sample if pd.notna(pd.to_datetime(v, errors="coerce", )))
    return hits > len(sample) * 0.6


def is_likely_location_col(name: str) -> bool:
    keywords = ["ADDRESS", "CITY", "STATE", "ZIP", "WARD", "COMMUNITY",
                "NEIGHBORHOOD", "LATITUDE", "LONGITUDE", "LOCATION",
                "PRECINCT", "POLICE", "SSA"]
    return any(k in name.upper() for k in keywords)


def categorize_dtype(series: pd.Series, name: str) -> str:
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if is_likely_date_col(series, name):
        return "date"
    if is_likely_location_col(name):
        return "location"
    if series.nunique() <= 50:
        return "categorical"
    return "text"


print("=" * 70)
print("GovGuide AI -- Dataset Profiling Script")
print(f"Started : {datetime.now().isoformat()}")
print("=" * 70)

print(f"\n[1] Detecting encoding/delimiter for: {CSV_PATH.name}")
encoding    = detect_encoding(CSV_PATH)
delimiter   = detect_delimiter(CSV_PATH, encoding)
file_sha256 = sha256_of_file(CSV_PATH)
print(f"    Encoding  : {encoding}")
print(f"    Delimiter : {repr(delimiter)}")
print(f"    SHA-256   : {file_sha256}")

print("\n[2] Loading CSV ...")
df = pd.read_csv(CSV_PATH, encoding=encoding, sep=delimiter, dtype=str, low_memory=False)
n_rows, n_cols = df.shape
print(f"    Shape : {n_rows:,} rows x {n_cols} columns")

print("\n[3] Columns:")
for i, col in enumerate(df.columns):
    print(f"    {i:>2}: {col}")

# Missing values
print("\n[4] Missing values ...")
missing_count = df.isnull().sum()
missing_pct   = (df.isnull().sum() / n_rows * 100).round(2)
pd.DataFrame({
    "column"       : df.columns,
    "missing_count": missing_count.values,
    "missing_pct"  : missing_pct.values,
    "non_null"     : (n_rows - missing_count).values,
}).to_csv(VAL_DIR / "missing_values.csv", index=False)
print(f"    Saved -> {VAL_DIR / 'missing_values.csv'}")

# Unique values
print("\n[5] Unique values ...")
pd.DataFrame([{
    "column"      : col,
    "unique_count": int(df[col].nunique(dropna=True)),
    "sample"      : str(df[col].dropna().unique()[:5].tolist()),
} for col in df.columns]).to_csv(VAL_DIR / "unique_values.csv", index=False)
print(f"    Saved -> {VAL_DIR / 'unique_values.csv'}")

# Numeric summary
print("\n[6] Numeric summaries ...")
NUM_CANDIDATES = [
    "LICENSE ID", "ACCOUNT NUMBER", "SITE NUMBER", "LICENSE CODE",
    "LICENSE NUMBER", "WARD", "PRECINCT", "POLICE DISTRICT",
    "COMMUNITY AREA", "SSA", "LATITUDE", "LONGITUDE",
]
num_rows = []
for col in NUM_CANDIDATES:
    if col not in df.columns:
        continue
    s = pd.to_numeric(df[col], errors="coerce")
    if s.notna().sum() == 0:
        continue
    num_rows.append({
        "column": col,
        "count" : int(s.count()),
        "mean"  : round(float(s.mean()), 6),
        "std"   : round(float(s.std()), 6) if s.count() > 1 else None,
        "min"   : round(float(s.min()), 6),
        "p25"   : round(float(s.quantile(0.25)), 6),
        "median": round(float(s.median()), 6),
        "p75"   : round(float(s.quantile(0.75)), 6),
        "max"   : round(float(s.max()), 6),
        "missing": int(s.isna().sum()),
    })
pd.DataFrame(num_rows).to_csv(VAL_DIR / "numeric_summary.csv", index=False)
print(f"    Saved -> {VAL_DIR / 'numeric_summary.csv'}")

# Duplicates
print("\n[7] Duplicates ...")
n_full_dups = int(df.duplicated().sum())
print(f"    Complete duplicate rows: {n_full_dups}")
dup_summary: dict[str, Any] = {"complete_duplicate_rows": n_full_dups}
ID_COLS = {"ID": "ID (composite)", "LICENSE ID": "LICENSE ID",
           "LICENSE NUMBER": "LICENSE NUMBER", "ACCOUNT NUMBER": "ACCOUNT NUMBER"}
dup_records = []
for col, label in ID_COLS.items():
    if col not in df.columns:
        continue
    vc   = df[col].value_counts()
    dups = vc[vc > 1]
    print(f"    {label}: dup_values={len(dups)}, extra_rows={int(dups.sum()-len(dups))}")
    dup_summary[col] = {"duplicate_values": int(len(dups)),
                        "extra_rows": int(dups.sum() - len(dups))}
    if len(dups) > 0:
        t = dups.head(5).reset_index()
        t.columns = ["value", "count"]
        t["column"] = col
        dup_records.append(t)
dup_df = pd.concat(dup_records, ignore_index=True) if dup_records else pd.DataFrame(columns=["column","value","count"])
dup_df.to_csv(VAL_DIR / "duplicate_summary.csv", index=False)
print(f"    Saved -> {VAL_DIR / 'duplicate_summary.csv'}")

# Date analysis
print("\n[8] Date columns ...")
date_analysis: dict[str, Any] = {}
for col in df.columns:
    if is_likely_date_col(df[col], col):
        s = try_parse_dates(df[col])
        date_analysis[col] = s
        print(f"    {col}: parse_rate={s['parse_rate_pct']}%  min={s['min_date']}  max={s['max_date']}")

# Location analysis
print("\n[9] Location columns ...")
location_analysis: dict[str, Any] = {}
for col in df.columns:
    if not is_likely_location_col(col):
        continue
    info: dict[str, Any] = {
        "missing_count": int(df[col].isna().sum()),
        "missing_pct"  : round(df[col].isna().mean() * 100, 2),
        "unique_count" : int(df[col].nunique()),
        "sample_values": df[col].dropna().unique()[:5].tolist(),
    }
    if "LATITUDE" in col.upper():
        s = pd.to_numeric(df[col], errors="coerce")
        info["invalid_lat"] = int(((s < -90) | (s > 90)).sum())
        info["lat_range"] = f"[{round(float(s.min()),5)}, {round(float(s.max()),5)}]" if s.notna().any() else None
    if "LONGITUDE" in col.upper():
        s = pd.to_numeric(df[col], errors="coerce")
        info["invalid_lon"] = int(((s < -180) | (s > 180)).sum())
        info["lon_range"] = f"[{round(float(s.min()),5)}, {round(float(s.max()),5)}]" if s.notna().any() else None
    if col == "CITY":
        info["city_counts"] = df[col].dropna().value_counts().head(10).to_dict()
    if col == "STATE":
        info["state_counts"] = df[col].dropna().value_counts().to_dict()
    if col == "WARD":
        info["ward_count"] = int(df[col].nunique())
    location_analysis[col] = info
    print(f"    {col}: missing={info['missing_count']} ({info['missing_pct']}%)  unique={info['unique_count']}")

# Per-column profile
print("\n[10] Per-column profile ...")
column_profiles = []
for col in df.columns:
    s = df[col]
    column_profiles.append({
        "column"       : col,
        "pandas_dtype" : str(s.dtype),
        "semantic_type": categorize_dtype(s, col),
        "total_records": n_rows,
        "non_null"     : n_rows - int(s.isna().sum()),
        "missing_count": int(s.isna().sum()),
        "missing_pct"  : round(s.isna().mean() * 100, 2),
        "unique_count" : int(s.nunique(dropna=True)),
        "sample_values": s.dropna().unique()[:5].tolist(),
    })

# Full JSON profile
profile_json: dict[str, Any] = {
    "profiling_metadata": {
        "generated_at"  : datetime.now().isoformat(),
        "script"        : "data/profiling/profile_dataset.py",
        "dataset_file"  : DATASET_NAME,
        "dataset_sha256": file_sha256,
        "encoding"      : encoding,
        "delimiter"     : delimiter,
    },
    "shape"                  : {"rows": n_rows, "columns": n_cols},
    "columns"                : [c["column"] for c in column_profiles],
    "column_profiles"        : column_profiles,
    "duplicate_analysis"     : dup_summary,
    "date_field_analysis"    : date_analysis,
    "location_field_analysis": location_analysis,
    "sample_records"         : df.head(5).to_dict(orient="records"),
}

with open(VAL_DIR / "dataset_profile.json", "w", encoding="utf-8") as f:
    json.dump(profile_json, f, indent=2, default=str)
print(f"    Saved -> {VAL_DIR / 'dataset_profile.json'}")

# Markdown quality report
print("\n[11] Markdown quality report ...")
MEANINGS = {
    "ID": "Composite unique record ID (ACCOUNT_NO-LICENSE_TERM_START_YEAR)",
    "LICENSE ID": "Numeric license identifier -- primary numeric key",
    "ACCOUNT NUMBER": "Business account number -- groups all licenses per entity",
    "SITE NUMBER": "Location index for multi-site business accounts",
    "LEGAL NAME": "Registered legal/corporate name of the business",
    "DOING BUSINESS AS NAME": "Trade/DBA name (may differ from legal name)",
    "ADDRESS": "Street address of the licensed premises",
    "CITY": "City (expected: CHICAGO for all or most records)",
    "STATE": "US state abbreviation (expected: IL)",
    "ZIP CODE": "US ZIP code of the licensed premises",
    "WARD": "Chicago City Council ward number",
    "PRECINCT": "Election precinct within the ward",
    "WARD PRECINCT": "Composite WARD-PRECINCT identifier",
    "POLICE DISTRICT": "CPD district number covering the premises",
    "COMMUNITY AREA": "Chicago community area number (1-77)",
    "COMMUNITY AREA NAME": "Human-readable community area name",
    "NEIGHBORHOOD": "Sub-community neighborhood name",
    "LICENSE CODE": "Numeric license category code",
    "LICENSE DESCRIPTION": "Human-readable license type description",
    "BUSINESS ACTIVITY ID": "Activity code(s) -- may be pipe-delimited",
    "BUSINESS ACTIVITY": "Activity description(s) -- may be pipe-delimited",
    "LICENSE NUMBER": "Official license number issued to the business",
    "APPLICATION TYPE": "Application type: ISSUE / RENEW / C_LOC / etc.",
    "APPLICATION CREATED DATE": "Date the application was created",
    "APPLICATION REQUIREMENTS COMPLETE": "Date all requirements were satisfied",
    "PAYMENT DATE": "Date the license fee was paid",
    "CONDITIONAL APPROVAL": "Conditional approval flag (Y/N/blank)",
    "LICENSE TERM START DATE": "Start date of the current license period",
    "LICENSE TERM EXPIRATION DATE": "Expiration date of the current license period",
    "LICENSE APPROVED FOR ISSUANCE": "Date approved for issuance",
    "DATE ISSUED": "Date the license was formally issued",
    "LICENSE STATUS": "License status code (AAI = Active After Issuance)",
    "LICENSE STATUS CHANGE DATE": "Date of most recent status change",
    "SSA": "Special Service Area number (Chicago tax district)",
    "LATITUDE": "WGS84 latitude of geocoded address",
    "LONGITUDE": "WGS84 longitude of geocoded address",
    "LOCATION": "WKT POINT geometry (lon lat)",
}

md = ["# GovGuide AI -- Dataset Quality Report", ""]
md += [
    f"**Dataset**: `{DATASET_NAME}`  ",
    f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
    f"**Rows**: {n_rows:,}  ",
    f"**Columns**: {n_cols}  ",
    f"**SHA-256**: `{file_sha256}`  ",
    f"**Encoding**: {encoding}  ",
    f"**Delimiter**: `{repr(delimiter)}`  ",
    "", "---", "",
    "## Column Quality Summary", "",
    "| # | Column | Type | Missing % | Non-Null | Unique | Sample | Potential Meaning |",
    "|---|--------|------|-----------|----------|--------|--------|-------------------|",
]
for i, cp in enumerate(column_profiles, 1):
    sample = "; ".join(str(v)[:35] for v in cp["sample_values"][:3])
    meaning = MEANINGS.get(cp["column"], "-- Needs domain confirmation")
    md.append(f"| {i} | `{cp['column']}` | {cp['semantic_type']} | {cp['missing_pct']}% | {cp['non_null']:,} | {cp['unique_count']:,} | {sample} | {meaning} |")

md += ["", "---", "", "## Duplicate Analysis", ""]
md.append(f"- **Complete duplicate rows**: {n_full_dups}")
for col, label in ID_COLS.items():
    if col in dup_summary and isinstance(dup_summary[col], dict):
        d = dup_summary[col]
        md.append(f"- **{label}**: {d['duplicate_values']} values appear >1 times ({d['extra_rows']} extra rows)")
md += ["", "> NOTE: Duplicates are NOT deleted. ACCOUNT NUMBER repeating = multiple licenses per business (expected).", "",
       "---", "", "## Date Field Analysis", "",
       "| Column | Parse Rate | Min Date | Max Date | Missing |",
       "|--------|-----------|---------|---------|---------|"]
for col, s in date_analysis.items():
    md.append(f"| `{col}` | {s['parse_rate_pct']}% | {s['min_date']} | {s['max_date']} | {s['missing_count']} |")

md += ["", "---", "", "## Location Field Analysis", "",
       "| Column | Missing | Missing% | Unique | Notes |",
       "|--------|---------|----------|--------|-------|"]
for col, info in location_analysis.items():
    notes = []
    if "invalid_lat" in info:
        notes.append(f"invalid_lat={info['invalid_lat']}")
    if "invalid_lon" in info:
        notes.append(f"invalid_lon={info['invalid_lon']}")
    if "city_counts" in info:
        notes.append("top_cities: " + ", ".join(list(info["city_counts"].keys())[:3]))
    if "state_counts" in info:
        notes.append("states: " + ", ".join(list(info["state_counts"].keys())[:3]))
    md.append(f"| `{col}` | {info['missing_count']} | {info['missing_pct']}% | {info['unique_count']} | {'; '.join(notes) or '--'} |")

md += ["", "---", "", "## Sample Records (first 3)", "", "```"]
for record in df.head(3).to_dict(orient="records"):
    md.append(json.dumps(record, default=str, ensure_ascii=False))
md += ["```", ""]

with open(VAL_DIR / "dataset_quality_report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(md))
print(f"    Saved -> {VAL_DIR / 'dataset_quality_report.md'}")

print("\n" + "=" * 70)
print("PROFILING COMPLETE")
print("=" * 70)
print(f"  Rows            : {n_rows:,}")
print(f"  Columns         : {n_cols}")
print(f"  Full duplicates : {n_full_dups}")
print(f"  Date columns    : {len(date_analysis)}")
print(f"  Location columns: {len(location_analysis)}")
print(f"\n  Raw CSV intact  : {CSV_PATH}")
print(f"  SHA-256         : {file_sha256}")
print(f"\nFinished: {datetime.now().isoformat()}")

