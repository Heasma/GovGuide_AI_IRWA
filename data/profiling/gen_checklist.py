"""Generate data_collection_checklist.md from the template CSV."""
import pandas as pd
from pathlib import Path

SUPP = Path(r"D:\User\IRWA_project\data\supplementary")
df = pd.read_csv(SUPP / "government_services_template.csv", dtype=str)

def is_done(val):
    return str(val).strip() not in ("", "NOT_AVAILABLE", "nan", "None")

def chk(val):
    return "Y" if is_done(val) else "-"

CONF_MAP = {"VERIFIED": "V", "PARTIALLY_VERIFIED": "P",
            "REQUIRES_MANUAL_VERIFICATION": "M", "NOT_FOUND": "X"}

FIELDS = [
    ("service_name",             "Service name"),
    ("eligibility_summary",      "Eligibility"),
    ("required_documents",       "Required documents"),
    ("application_steps",        "Application procedure"),
    ("application_portal_url",   "Application URL"),
    ("fee_amount",               "Fees"),
    ("estimated_processing_time","Processing time"),
    ("renewal_steps",            "Renewal procedure"),
    ("government_department",    "Responsible department"),
    ("phone",                    "Contact information"),
    ("official_url",             "Official source URL"),
    ("legal_reference",          "Legal reference"),
    ("source_confidence",        "Verification status"),
]

lines = []
lines.append("# GovGuide AI -- Phase 2 Data Collection Checklist")
lines.append("")
lines.append("**Date**: 2026-08-19  ")
lines.append("**Total License Types**: 56  ")
lines.append("")
lines.append("## Overall Completion")
lines.append("")
lines.append("| Information Category | Completed | Remaining | % |")
lines.append("|---------------------|-----------|-----------|---|")
for col, label in FIELDS:
    done = df[col].apply(is_done).sum()
    rem = 56 - done
    pct = 100 * done // 56
    lines.append(f"| {label} | {done} | {rem} | {pct}% |")

total_fields = len(FIELDS)
total_done = sum(df[col].apply(is_done).sum() for col, _ in FIELDS)
total_possible = total_fields * 56
pct_overall = 100 * total_done // total_possible
lines.append("")
lines.append(f"**Overall field completion: {total_done}/{total_possible} ({pct_overall}%)**")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## Per-License Type Checklist")
lines.append("")
lines.append("**Column key**: SN=Service Name, EL=Eligibility, RD=Required Docs, AP=Procedure,")
lines.append("URL=App URL, FE=Fees, PT=Processing Time, RN=Renewal, DP=Dept, CO=Contact,")
lines.append("SR=Source URL, LR=Legal Ref, CF=Confidence")
lines.append("")
lines.append("| Code | License Type | SN | EL | RD | AP | URL | FE | PT | RN | DP | CO | SR | LR | CF |")
lines.append("|------|--------------|----|----|----|-----|----|----|----|----|----|----|----|----|-----|")

for _, r in df.iterrows():
    code = r["license_code"]
    desc = r["license_description"][:28]
    conf = CONF_MAP.get(str(r["source_confidence"]).strip(), "?")
    row = (
        f"| {code:6s} | {desc:28s} "
        f"| {chk(r['service_name'])} "
        f"| {chk(r['eligibility_summary'])} "
        f"| {chk(r['required_documents'])} "
        f"| {chk(r['application_steps'])} "
        f"| {chk(r['application_portal_url'])} "
        f"| {chk(r['fee_amount'])} "
        f"| {chk(r['estimated_processing_time'])} "
        f"| {chk(r['renewal_steps'])} "
        f"| {chk(r['government_department'])} "
        f"| {chk(r['phone'])} "
        f"| {chk(r['official_url'])} "
        f"| {chk(r['legal_reference'])} "
        f"| {conf} |"
    )
    lines.append(row)

lines.append("")
lines.append("**Legend**: Y=Verified | -=NOT_AVAILABLE | V=VERIFIED | P=PARTIALLY_VERIFIED | M=REQUIRES_MANUAL_VERIFICATION")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## High-Priority Manual Verification Queue")
lines.append("")
lines.append("License types with high record counts requiring urgent data collection:")
lines.append("")
lines.append("| License Code | License Type | Record Count | Priority |")
lines.append("|-------------|-------------|-------------|---------|")

needs_manual = df[df["source_confidence"] == "REQUIRES_MANUAL_VERIFICATION"].copy()
needs_manual["record_count_n"] = pd.to_numeric(needs_manual["record_count"], errors="coerce")
needs_manual = needs_manual.sort_values("record_count_n", ascending=False).head(15)
PRIORITY = ["CRITICAL","HIGH","HIGH","MEDIUM","MEDIUM","MEDIUM","LOW","LOW","LOW","LOW","LOW","LOW","LOW","LOW","LOW"]
for i, (_, r) in enumerate(needs_manual.iterrows()):
    lines.append(f"| {r['license_code']} | {r['license_description']} | {r['record_count']} | {PRIORITY[min(i, len(PRIORITY)-1)]} |")

lines.append("")
lines.append("---")
lines.append("")
lines.append("## Official Sources to Visit (Manual Collection)")
lines.append("")
lines.append("1. **Chicago Business Direct** (PRIMARY): https://www.chicago.gov/BusinessDirect")
lines.append("2. **BACP Department**: https://www.chicago.gov/city/en/depts/bacp.html")
lines.append("3. **Chicago Municipal Code**: https://www.chicityclerk.com/about-city-government-chicago-city-council/municipal-code")
lines.append("4. **Chicago Zoning Ordinance**: https://codelibrary.amlegal.com/codes/chicago/latest/chicagozoning_il/0-0-0-48006")
lines.append("5. **Illinois DCFS** (childcare): https://www.illinois.gov/sites/dcfs/")
lines.append("6. **IL Liquor Control Commission** (liquor): https://www.illinois.gov/agencies/liquor-control-commission")

out_path = SUPP / "data_collection_checklist.md"
out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"Written: {out_path}")
print(f"Overall completion: {pct_overall}%")
