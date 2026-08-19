import pandas as pd, json
from pathlib import Path

RAW = Path(r"D:\User\IRWA_project\data\raw\Business_Licenses_-_Current_Active_20260819.csv")
OUT = Path(r"D:\User\IRWA_project\data\supplementary")
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(RAW, dtype=str, low_memory=False)

grp = df.groupby(["LICENSE CODE","LICENSE DESCRIPTION"])
rows = []
for (code, desc), group in grp:
    acts = group["BUSINESS ACTIVITY"].dropna().unique()[:3].tolist()
    act_ids = group["BUSINESS ACTIVITY ID"].dropna().unique()[:3].tolist()
    rows.append({
        "license_code": code,
        "license_description": desc,
        "record_count": len(group),
        "sample_business_activity": " | ".join(acts[:2]) if acts else "",
        "sample_activity_ids": " | ".join(act_ids[:2]) if act_ids else "",
    })

rows.sort(key=lambda x: x["license_code"])
out_df = pd.DataFrame(rows)
out_df.to_csv(OUT / "license_types.csv", index=False)
print(f"Saved {len(rows)} license types to {OUT / 'license_types.csv'}")
for r in rows:
    print(f"  {r['license_code']:6s}  {r['record_count']:6d}  {r['license_description']}")
