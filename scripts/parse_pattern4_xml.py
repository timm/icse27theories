#!/usr/bin/env python3
"""Parse pattern4.jar XML output into a patterned-files CSV.

For each pattern instance, extract the class name from each role's
`element` attribute (format: `pkg.Class::method...`) and map to its
source file path under helix-core/src/main/java/.

Output: data/helix/derived/pattern4/patterned_files.csv
  columns: file_pathname, pattern_type, role
"""

import csv, os, sys, xml.etree.ElementTree as ET

XML_PATH    = "data/helix/derived/pattern4/helix-core.xml"
OUT_CSV     = "data/helix/derived/pattern4/patterned_files.csv"
SRC_PREFIX  = "helix-core/src/main/java/"


def class_to_path(cls):
    """`org.apache.helix.X$Inner` -> `helix-core/src/main/java/org/apache/helix/X.java`."""
    outer = cls.split("$", 1)[0]
    return SRC_PREFIX + outer.replace(".", "/") + ".java"


def main():
    if not os.path.exists(XML_PATH):
        print(f"missing {XML_PATH}", file=sys.stderr)
        return 1

    root = ET.parse(XML_PATH).getroot()
    rows = []
    for pat in root.findall("pattern"):
        ptype = pat.get("name", "?")
        for inst in pat.findall("instance"):
            for role in inst.findall("role"):
                cls = (role.get("element") or "").split("::", 1)[0]
                if not cls:
                    continue
                rows.append({
                    "file_pathname": class_to_path(cls),
                    "pattern_type":  ptype,
                    "role":          role.get("name", ""),
                })

    rows = list({(r["file_pathname"], r["pattern_type"], r["role"]): r
                 for r in rows}.values())  # dedupe

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f,
                           fieldnames=["file_pathname", "pattern_type", "role"])
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {OUT_CSV} ({len(rows)} rows, "
          f"{len(set(r['file_pathname'] for r in rows))} unique files)")


if __name__ == "__main__":
    sys.exit(main())
