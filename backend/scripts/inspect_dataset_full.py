import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

csv_path = Path('D:/User/IRWA_project/data/raw/Business_Licenses_-_Current_Active_20260819.csv')

with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
    reader = csv.DictReader(f)
    columns = list(reader.fieldnames)
    rows = list(reader)

total_rows = len(rows)
total_cols = len(columns)

null_counts = defaultdict(int)
unique_counts = {}
inferred_types = {}

def infer_type(values):
    non_null = [v for v in values if v.strip()]
    if not non_null:
        return 'UNKNOWN'
    
    is_int = True
    is_float = True
    is_date = True
    
    for v in non_null[:1000]:
        if is_int:
            try:
                int(v)
            except ValueError:
                is_int = False
        if is_float:
            try:
                float(v)
            except ValueError:
                is_float = False
        if is_date:
            try:
                datetime.strptime(v, '%m/%d/%Y')
            except ValueError:
                is_date = False
                
    if is_int:
        return 'INTEGER'
    if is_float:
        return 'FLOAT'
    if is_date:
        return 'DATE (MM/DD/YYYY)'
    return 'TEXT / STRING'

for col in columns:
    col_vals = [r[col] for r in rows]
    unique_counts[col] = len(set(v.strip() for v in col_vals if v.strip()))
    inferred_types[col] = infer_type(col_vals)
    for r in rows:
        val = r[col].strip()
        if not val or val.lower() in ('none', 'null', 'nan'):
            null_counts[col] += 1

print(f"=== DATASET BASIC DIMENSIONS ===")
print(f"Total Rows: {total_rows}")
print(f"Total Columns: {total_cols}")
print(f"\n=== COLUMN DETAILS ===")
print(f"{'No.':<4} | {'Column Name':<38} | {'Inferred Type':<20} | {'Null Count':<10} | {'Null %':<8} | {'Unique Count':<12}")
print("-" * 105)
for i, col in enumerate(columns, 1):
    nc = null_counts[col]
    pct = (nc / total_rows) * 100
    uc = unique_counts[col]
    itype = inferred_types[col]
    print(f"{i:<4} | {col:<38} | {itype:<20} | {nc:<10} | {pct:<7.2f}% | {uc:<12}")

# Primary Key & Duplicate Analysis
id_counts = Counter(r['ID'].strip() for r in rows)
lic_id_counts = Counter(r['LICENSE ID'].strip() for r in rows)
acc_site_counts = Counter((r['ACCOUNT NUMBER'].strip(), r['SITE NUMBER'].strip()) for r in rows)
full_row_hashes = Counter(tuple(r[c].strip() for c in columns) for r in rows)

dup_ids = {k: v for k, v in id_counts.items() if v > 1}
dup_lic_ids = {k: v for k, v in lic_id_counts.items() if v > 1}
dup_rows = {k: v for k, v in full_row_hashes.items() if v > 1}

print(f"\n=== PRIMARY KEY & DUPLICATE ANALYSIS ===")
print(f"Total distinct 'ID' values: {len(id_counts)} (Duplicates: {len(dup_ids)})")
print(f"Total distinct 'LICENSE ID' values: {len(lic_id_counts)} (Duplicates: {len(dup_lic_ids)})")
print(f"Total distinct (ACCOUNT NUMBER, SITE NUMBER) pairs: {len(acc_site_counts)}")
print(f"Exact full duplicate rows: {len(dup_rows)}")

# Categorical Distributions
print(f"\n=== CATEGORICAL DISTRIBUTIONS ===")
for cat in ['LICENSE STATUS', 'APPLICATION TYPE', 'LICENSE STATUS CHANGE DATE', 'STATE', 'CITY']:
    if cat in columns:
        cnt = Counter(r[cat].strip() for r in rows if r[cat].strip())
        print(f"\nTop values for '{cat}':")
        for val, count in cnt.most_common(10):
            pct = (count / total_rows) * 100
            print(f"  - {val!r}: {count} ({pct:.2f}%)")

print(f"\nTotal distinct 'LICENSE DESCRIPTION' categories: {unique_counts['LICENSE DESCRIPTION']}")
lic_desc_cnt = Counter(r['LICENSE DESCRIPTION'].strip() for r in rows if r['LICENSE DESCRIPTION'].strip())
print("Top 10 License Descriptions:")
for val, count in lic_desc_cnt.most_common(10):
    pct = (count / total_rows) * 100
    print(f"  - {val!r}: {count} ({pct:.2f}%)")

# Date Validation
print(f"\n=== DATE COLUMNS ANALYSIS ===")
date_cols = ['APPLICATION CREATED DATE', 'APPLICATION REQUIREMENTS COMPLETE', 'PAYMENT DATE', 
             'LICENSE TERM START DATE', 'LICENSE TERM EXPIRATION DATE', 'DATE ISSUED', 'LICENSE STATUS CHANGE DATE']

for dc in date_cols:
    dates = []
    malformed = []
    for r in rows:
        v = r[dc].strip()
        if v:
            try:
                d = datetime.strptime(v, '%m/%d/%Y')
                dates.append(d)
            except ValueError:
                malformed.append(v)
    min_d = min(dates).strftime('%Y-%m-%d') if dates else 'N/A'
    max_d = max(dates).strftime('%Y-%m-%d') if dates else 'N/A'
    print(f"{dc:<35} | Valid: {len(dates):<6} | Nulls: {null_counts[dc]:<6} | Malformed: {len(malformed):<4} | Min: {min_d} | Max: {max_d}")

# Spatial / Coordinates
print(f"\n=== GEOSPATIAL / COORDINATE ANALYSIS ===")
lat_valid, lon_valid, null_coords, out_of_bounds, parse_errors = 0, 0, 0, 0, 0
for r in rows:
    lat_s = r.get('LATITUDE', '').strip()
    lon_s = r.get('LONGITUDE', '').strip()
    if not lat_s or not lon_s:
        null_coords += 1
    else:
        try:
            lat = float(lat_s)
            lon = float(lon_s)
            # Illinois / Chicago bounds
            if 41.60 <= lat <= 42.10 and -87.95 <= lon <= -87.50:
                lat_valid += 1
                lon_valid += 1
            else:
                out_of_bounds += 1
        except ValueError:
            parse_errors += 1

print(f"Valid Chicago Coordinates: {lat_valid} ({lat_valid/total_rows*100:.2f}%)")
print(f"Null Coordinates: {null_coords} ({null_coords/total_rows*100:.2f}%)")
print(f"Out of Chicago Bounds: {out_of_bounds} ({out_of_bounds/total_rows*100:.2f}%)")
print(f"Coordinate Parse Errors: {parse_errors}")

# Logical consistency check
exp_before_start = 0
for r in rows:
    sd_s = r['LICENSE TERM START DATE'].strip()
    ed_s = r['LICENSE TERM EXPIRATION DATE'].strip()
    if sd_s and ed_s:
        try:
            sd = datetime.strptime(sd_s, '%m/%d/%Y')
            ed = datetime.strptime(ed_s, '%m/%d/%Y')
            if ed < sd:
                exp_before_start += 1
        except ValueError:
            pass
print(f"\nRecords where Expiration Date < Start Date: {exp_before_start}")
