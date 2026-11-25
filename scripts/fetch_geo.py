"""Backfill ``country`` / ``geo_loc_name`` into catalog entries from their NCBI BioSample.

Usage: python scripts/fetch_geo.py [--write]

Dry run by default: prints what would be added. With --write, inserts the lines after
the ``strain:`` (or ``species:``) line of each metadata.yaml, leaving the rest untouched.
Needs the NCBI ``datasets`` binary and network access.
"""

import json
import subprocess
import sys

import yaml

from leishref.metadata import CATALOG_DIR, METADATA_FILE
from leishref.ncbi import country_from_geo_loc_name, geo_loc_name_from_biosample


def biosample_places(accessions):
    places = {}
    for i in range(0, len(accessions), 50):
        p = subprocess.run(
            ["datasets", "summary", "genome", "accession", *accessions[i : i + 50]],
            capture_output=True,
            text=True,
            timeout=300,
            check=True,
        )
        for r in json.loads(p.stdout).get("reports", []):
            name = geo_loc_name_from_biosample(r.get("assembly_info", {}).get("biosample"))
            if name:
                places[r["accession"]] = name
    return places


def insert_geo(text, geo_loc_name, country=None):
    lines = text.splitlines(keepends=True)
    country = country or country_from_geo_loc_name(geo_loc_name)
    fields = {"country": country, "geo_loc_name": geo_loc_name}
    new = yaml.safe_dump({k: v for k, v in fields.items() if v}, allow_unicode=True, sort_keys=False)
    for key in ("strain:", "species:"):
        for i, line in enumerate(lines):
            if line.startswith(key):
                return "".join(lines[: i + 1]) + new + "".join(lines[i + 1 :])
    raise ValueError("no species line")


#: Country codes used in WHO strain designations (MHOM/BR/75/M2904), for the codes the catalog holds.
WHO_COUNTRIES = {
    "BR": "Brazil", "COL": "Colombia", "ES": "Spain", "GT": "Guatemala", "IN": "India", "IL": "Israel", "SD": "Sudan",
    "ET": "Ethiopia", "KE": "Kenya", "IR": "Iran", "TN": "Tunisia", "PE": "Peru", "PA": "Panama", "FR": "France",
}  # fmt: skip


def country_from_who_code(strain):
    """Country named by a WHO strain code like ``MHOM/BR/75/M2904``, or None."""
    parts = (strain or "").split("/")
    return WHO_COUNTRIES.get(parts[1]) if len(parts) >= 4 and parts[0].isalpha() else None


def add_country(path, country):
    path.write_text(insert_geo(path.read_text(), None, country))


def infer_countries(write=False):
    """Fill entries still lacking a country: from the WHO code of the strain, else from another
    entry of the same species and strain (a scaffold or custom assembly of a known isolate)."""
    entries = []
    for path in sorted(CATALOG_DIR.rglob(METADATA_FILE)):
        data = yaml.safe_load(path.read_text())
        entries.append((path, data))
    known = {
        (d.get("species"), d.get("strain")): d["country"] for _, d in entries if d.get("country") and d.get("strain")
    }
    n = 0
    for path, d in entries:
        if d.get("country"):
            continue
        country = country_from_who_code(d.get("strain")) or known.get((d.get("species"), d.get("strain")))
        if country:
            n += 1
            print(f"{d['identifier']}\t{country}\t(inferred)")
            if write:
                add_country(path, country)
    print(f"{n} countries inferred", file=sys.stderr)


def main(write=False):
    files = sorted(p for p in CATALOG_DIR.rglob(METADATA_FILE) if "ncbi" in p.relative_to(CATALOG_DIR).parts[0])
    entries = {}
    for path in files:
        data = yaml.safe_load(path.read_text())
        if data.get("accession", "").startswith("GC") and not data.get("country"):
            entries[data["accession"]] = path
    places = biosample_places(sorted(entries))
    for acc, name in places.items():
        print(f"{acc}\t{name}")
        if write:
            entries[acc].write_text(insert_geo(entries[acc].read_text(), name))
    print(
        f"{len(places)} of {len(entries)} entries have a location" + (" (written)" if write else " (dry run)"),
        file=sys.stderr,
    )
    infer_countries(write)


if __name__ == "__main__":
    main("--write" in sys.argv)
