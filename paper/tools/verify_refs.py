"""Check every reference in the manuscript against Crossref.

Sends each full entry to Crossref's bibliographic query, then compares the
year / volume / first page I wrote against what Crossref returns. Flags
anything that disagrees or that cannot be matched at all.
"""
import io, re, sys, json, time, urllib.parse, urllib.request

MANU = sys.argv[1]
text = io.open(MANU, encoding="utf-8").read().split("## 10. References")[1]

entries = re.findall(r"^\[(\d+)\]\s+(.*?)(?=^\[\d+\]|\Z)", text, re.M | re.S)
print(f"parsed {len(entries)} entries\n")


def flat(s):
    return re.sub(r"\s+", " ", s).replace("*", "").strip()


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def crossref(q):
    url = ("https://api.crossref.org/works?rows=3&select=title,DOI,volume,page,"
           "issued,container-title,type&query.bibliographic="
           + urllib.parse.quote(q))
    req = urllib.request.Request(url, headers={
        "User-Agent": "sampling-audit-refcheck/1.0 (mailto:jaiveerbassi@yahoo.com)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["message"]["items"]


problems = []
for num, raw in entries:
    ent = flat(raw)
    my_year = re.search(r"(\d{4})\.\s*$", ent)
    my_year = my_year.group(1) if my_year else None
    my_vol = re.search(r",\s*(\d+)\(", ent) or re.search(r"\*,\s*(\d+):", ent)
    my_vol = my_vol.group(1) if my_vol else None
    my_pg = re.search(r":\s*(\d+)", ent)
    my_pg = my_pg.group(1) if my_pg else None

    try:
        items = crossref(ent)
    except Exception as e:
        print(f"[{num}] QUERY FAILED: {e}")
        problems.append((num, "query failed", ent[:70]))
        continue
    if not items:
        print(f"[{num}] NO MATCH")
        problems.append((num, "no crossref match", ent[:70]))
        continue

    it = items[0]
    ct = (it.get("container-title") or [""])[0]
    cr_title = (it.get("title") or [""])[0]
    cr_year = str((it.get("issued", {}).get("date-parts") or [[None]])[0][0])
    cr_vol = it.get("volume")
    cr_pg = (it.get("page") or "").split("-")[0]

    # is the returned record plausibly the same work?
    title_in_entry = norm(cr_title)[:40] and norm(cr_title)[:40] in norm(ent)
    bad = []
    if not title_in_entry:
        bad.append(f"title? crossref says '{cr_title[:60]}'")
    if my_year and cr_year and my_year != cr_year:
        bad.append(f"year {my_year} != {cr_year}")
    if my_vol and cr_vol and my_vol != str(cr_vol):
        bad.append(f"vol {my_vol} != {cr_vol}")
    if my_pg and cr_pg and my_pg != cr_pg:
        bad.append(f"page {my_pg} != {cr_pg}")

    status = "OK  " if not bad else "CHECK"
    print(f"[{num}] {status} {cr_title[:58]}")
    print(f"        doi={it.get('DOI')}  {ct[:50]}")
    if bad:
        for b in bad:
            print(f"        -> {b}")
        problems.append((num, "; ".join(bad), cr_title[:60]))
    time.sleep(0.3)

print("\n" + "=" * 70)
print(f"{len(entries) - len(problems)}/{len(entries)} clean, {len(problems)} to check")
for n, why, what in problems:
    print(f"  [{n}] {why}")
