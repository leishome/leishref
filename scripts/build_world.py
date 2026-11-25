"""Build leishref-web/world.json (land path + country centroids) from Natural Earth 110m.

Usage: python scripts/build_world.py ne_110m_admin_0_countries.geojson [leishref-web/world.json]

Source: https://github.com/nvkelso/natural-earth-vector (public domain). Equirectangular
projection, 1000 units wide; latitudes below -58 (Antarctica) are cropped.
"""

import json
import sys

W, LAT_MIN, LAT_MAX = 1000.0, -58.0, 84.0
K = W / 360.0
H = round((LAT_MAX - LAT_MIN) * K)

#: Places the 110m file lacks as a country of their own.
EXTRA = {"French Guiana": (-53.1, 3.9)}


def proj(lon, lat):
    return round((lon + 180) * K, 1), round((LAT_MAX - lat) * K, 1)


def ring_area(ring):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]))) / 2


def main(src, out="leishref-web/world.json"):
    path, centroids = [], {}
    for f in json.load(open(src))["features"]:
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        outers = [p[0] for p in polys]
        for ring in outers:
            pts = [proj(*c) for c in ring if LAT_MIN <= c[1]]
            if len(pts) > 2:
                path.append("M" + "L".join(f"{x:g} {y:g}" for x, y in pts) + "Z")
        big = max(outers, key=ring_area)
        lons, lats = [c[0] for c in big], [c[1] for c in big]
        centroids[f["properties"]["ADMIN"]] = proj((min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2)
    for name, (lon, lat) in EXTRA.items():
        centroids[name] = proj(lon, lat)
    json.dump({"w": W, "h": H, "land": "".join(path), "centroids": centroids}, open(out, "w"), separators=(",", ":"))
    print(f"{len(centroids)} places, {len(path)} rings -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
