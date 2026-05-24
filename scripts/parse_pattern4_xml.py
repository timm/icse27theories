#!/usr/bin/env python3
"""Parse pattern4.jar XML output(s) into a patterned-files CSV.

Scans data/helix/derived/pattern4/*.xml and produces an aggregated
CSV. The module name comes from the XML filename stem; the source
prefix is `<module>/src/main/java/`.

Output: data/helix/derived/pattern4/patterned_files.csv
  columns: file_pathname, pattern_type, role, module
"""

import csv, glob, os, sys, xml.etree.ElementTree as ET

XML_GLOB = "data/helix/derived/pattern4/*.xml"
OUT_CSV  = "data/helix/derived/pattern4/patterned_files.csv"


def class_to_path(cls, module):
    """`org.apache.helix.X$Inner` + module → `<module>/src/main/java/.../X.java`."""
    outer = cls.split("$", 1)[0]
    return f"{module}/src/main/java/" + outer.replace(".", "/") + ".java"


def parse_xml(path):
    module = os.path.splitext(os.path.basename(path))[0]
    rows = []
    root = ET.parse(path).getroot()
    for pat in root.findall("pattern"):
        ptype = pat.get("name", "?")
        for inst in pat.findall("instance"):
            for role in inst.findall("role"):
                cls = (role.get("element") or "").split("::", 1)[0]
                if not cls:
                    continue
                rows.append({
                    "file_pathname": class_to_path(cls, module),
                    "pattern_type":  ptype,
                    "role":          role.get("name", ""),
                    "module":        module,
                })
    return rows


def main():
    paths = sorted(glob.glob(XML_GLOB))
    if not paths:
        print(f"no XMLs found at {XML_GLOB}", file=sys.stderr)
        return 1

    all_rows = []
    for p in paths:
        rows = parse_xml(p)
        print(f"  {os.path.basename(p):40s} {len(rows)} role-rows")
        all_rows.extend(rows)

    # Dedupe on (file, pattern_type, role)
    seen = {}
    for r in all_rows:
        key = (r["file_pathname"], r["pattern_type"], r["role"])
        seen[key] = r
    deduped = list(seen.values())

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["file_pathname", "pattern_type",
                                          "role", "module"])
        w.writeheader()
        w.writerows(deduped)
    unique_files = len(set(r["file_pathname"] for r in deduped))
    print(f"Wrote {OUT_CSV} ({len(deduped)} rows, {unique_files} unique files)")


if __name__ == "__main__":
    sys.exit(main())
