import pandas as pd
from pathlib import Path
from collections import Counter

SUPP = Path(r"D:\User\IRWA_project\data\supplementary")
SUPP.mkdir(parents=True, exist_ok=True)

BACP_DEPT  = "City of Chicago -- Department of Business Affairs and Consumer Protection (BACP)"
BACP_ADDR  = "City Hall, 121 N. LaSalle Street, Room 800, Chicago, IL 60602"
BACP_PHONE = "312-74-GOBIZ (312-744-6249)"
BACP_EMAIL = "businesslicense@cityofchicago.org"
BACP_HOURS = "Monday-Friday 8:00 AM - 5:00 PM"
BACP_URL   = "https://www.chicago.gov/city/en/depts/bacp.html"
PORTAL_URL = "https://www.chicago.gov/BusinessDirect"
VDATE      = "2026-08-19"

lt_df = pd.read_csv(SUPP / "license_types.csv", dtype=str)
print(f"Loaded {len(lt_df)} license types")
print("DONE")
