"""Public-domain code lists -> clean, specialty-tagged tables for the synthetic claims.

Sources (both public domain US government code sets, retrieved via GitHub mirrors because
cms.gov is blocked on our network):
- ICD-10-CM April 2025 order file (CMS/CDC), mirror: stabgan/ICD-10-CM-code-April-2025-CSV-FILE-ENHANCED
- HCPCS Level II list, mirror: Rahul-Soundararajan/hcpcs-data-pipeline (Main_List_HCPCS.csv)
CPT is NOT used: its descriptors are AMA-copyrighted.

    python -m data.pipeline.codes
Outputs data/processed/icd10cm_billable.csv, hcpcs_level2.csv, specialty_codes.json, codes_log.json
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
OUT = Path("data/processed")

# Specialty -> (ICD-10-CM prefixes, HCPCS prefixes). Clinical plausibility only; not medical guidance.
# ICD-10-CM by prefix; HCPCS by description keywords (prefixes mixed in dialysis supplies for cardiology).
SPECIALTIES = {
    "orthopedics": (["M17", "M16", "M23", "M51", "M54", "M75", "S82", "S72", "S83"],
                    r"knee orthosis|hip orthosis|crutch|cane,|walker|continuous passive motion|lumbar-sacral orthosis"),
    "cardiology": (["I10", "I20", "I21", "I25", "I48", "I50", "R00"],
                   r"cardiac|defibrillator|electrocardiogram|ecg|cardiovascular|pacemaker"),
    "sleep_medicine": (["G47"], r"positive airway pressure|cpap|bi-level|nasal interface|full face mask|oral interface"),
}


def parse_icd(path: Path) -> pd.DataFrame:
    """CMS order-file layout: order(5) sp code(7) sp billable(1) sp short(60) sp long(rest)."""
    rows = []
    for line in path.read_text(encoding="latin-1").splitlines():
        if len(line) < 16:
            continue
        rows.append({"order": line[0:5].strip(), "code": line[6:13].strip(), "billable": line[14:15] == "1",
                     "short": line[16:76].strip(), "long": line[77:].strip()})
    df = pd.DataFrame(rows)
    df["code_dotted"] = df["code"].map(lambda c: c if len(c) <= 3 else f"{c[:3]}.{c[3:]}")
    return df


def parse_hcpcs(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    df.columns = [c.strip().lower() for c in df.columns]
    df["code"] = df["code"].str.strip().str.upper()
    df["description"] = df["description"].fillna("").str.replace(r"\s+", " ", regex=True).str.strip()
    return df


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    icd = parse_icd(RAW / "icd10cm-order-April-2025.txt")
    hc = parse_hcpcs(RAW / "hcpcs_main_list.csv")
    log = {"icd_rows": len(icd), "icd_billable": int(icd["billable"].sum()), "hcpcs_rows_raw": len(hc)}
    hc_valid = hc[hc["code"].str.match(r"^[A-V]\d{4}$", na=False) & (hc["description"] != "")]
    log["hcpcs_invalid_or_blank_dropped"] = len(hc) - len(hc_valid)
    dup = hc_valid["code"].duplicated()
    log["hcpcs_duplicate_codes_dropped"] = int(dup.sum())
    hc_valid = hc_valid[~dup]
    log["hcpcs_rows_clean"] = len(hc_valid)
    bill = icd[icd["billable"]][["code", "code_dotted", "short", "long"]]
    bill.to_csv(OUT / "icd10cm_billable.csv", index=False)
    hc_valid[["code", "description", "group_code", "category_name"]].to_csv(OUT / "hcpcs_level2.csv", index=False)

    spec = {}
    for name, (icd_p, hc_rx) in SPECIALTIES.items():
        di = bill[bill["code"].str.startswith(tuple(icd_p))]
        dh = hc_valid[hc_valid["description"].str.contains(hc_rx, case=False, regex=True)]
        # keep descriptions short and readable for the UI; drop "unspecified" when better options exist
        di = di[~di["long"].str.contains("unspecified", case=False)] if (~di["long"].str.contains("unspecified", case=False)).sum() > 20 else di
        spec[name] = {"icd10cm": di.head(60)[["code_dotted", "long"]].values.tolist(),
                      "hcpcs": dh.head(40)[["code", "description"]].values.tolist()}
        log[f"{name}_icd"] = len(spec[name]["icd10cm"])
        log[f"{name}_hcpcs"] = len(spec[name]["hcpcs"])
    (OUT / "specialty_codes.json").write_text(json.dumps(spec, indent=1))
    (OUT / "codes_log.json").write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))
    assert all(re.match(r"^[A-Z]\d", c) for c, _ in spec["orthopedics"]["icd10cm"][:5])


if __name__ == "__main__":
    main()
