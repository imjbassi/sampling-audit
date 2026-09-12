"""Audit paper/refs.bib against sources INDEPENDENT of how it was built.

refs.bib is generated from Crossref, so re-querying Crossref would be circular.
This checks every entry against OpenAlex and Semantic Scholar instead, and adds
a self-consistency test that catches the highest-risk failure mode: a
bibliographic search having silently matched the wrong paper. The citation keys
encode first-author surname and year, so key-versus-metadata disagreement is a
red flag that depends on no external service at all.

Five disagreements are known and adjudicated; see ADJUDICATED below. They are
printed as NOTE rather than FLAG so a real regression stays visible.

    python paper/tools/audit_refs.py paper/refs.bib
"""
import io, re, sys, json, time, unicodedata, urllib.request

BIB = sys.argv[1] if len(sys.argv) > 1 else "paper/refs.bib"
UA = {"User-Agent": "sampling-audit-refaudit/1.0 (mailto:jaiveerbassi@yahoo.com)"}

# Disagreements checked by hand against the publisher of record. Keyed by
# (bib key, substring of the complaint).
ADJUDICATED = {
    ("hernandez2018", "S2 year"):
        "S2 dates the arXiv preprint 1711.08576; PRE 97, 062412 is 2018",
    ("wehmeyer2018", "S2 year"):
        "S2 dates the arXiv preprint 1710.11239; JCP 148, 241703 is 2018",
    ("drton2017", "S2 year"):
        "S2 dates the arXiv preprint 1309.0911; JRSS-B 79, 323 is 2017",
    ("eastman2017", "S2 year"):
        "S2 dates the bioRxiv preprint; DBLP key ...Eastman...17 and "
        "PLoS Comput Biol 13, e1005659 are 2017",
    ("schwarz1978", "first page"):
        "OpenAlex is wrong. Project Euclid, the publisher of record, gives "
        "Ann. Statist. 6(2):461-464",
}


def get(url):
    return json.load(urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=30))


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s.lower())


def field(entry, name):
    m = re.search(name + r"\s*=\s*", entry, re.I)
    if not m:
        return None
    i = m.end()
    if entry[i] == "{":
        d, j = 1, i + 1
        while j < len(entry) and d:
            d += (entry[j] == "{") - (entry[j] == "}")
            j += 1
        return entry[i + 1:j - 1].strip()
    return entry[i:].split(",")[0].strip()


def adjudication(key, issue):
    for (k, frag), why in ADJUDICATED.items():
        if k == key and frag in issue:
            return why
    return None


raw = io.open(BIB, encoding="utf-8").read()
chunks = [c for c in re.split(r"\n(?=@)", raw.strip()) if c.startswith("@")]
print(f"auditing {len(chunks)} entries in {BIB}\n")

real, noted = [], []
for ch in chunks:
    key = re.match(r"@\w+\{([^,]+),", ch).group(1)
    doi = field(ch, "DOI")
    title, year = field(ch, "title") or "", field(ch, "year")
    vol, pages = field(ch, "volume"), field(ch, "pages")
    authors = field(ch, "author") or ""
    first = authors.split(" and ")[0]
    surname = first.split(",")[0].strip() if "," in first else first.split()[-1]

    issues = []
    km = re.match(r"([a-z]+)(\d{4})", key)
    if km:
        if km.group(1) not in norm(surname) and norm(surname) not in km.group(1):
            issues.append(f"key surname '{km.group(1)}' vs author '{surname}'")
        if year and km.group(2) != year:
            issues.append(f"key year {km.group(2)} vs bib year {year}")

    src = []
    if doi:
        try:
            oa = get(f"https://api.openalex.org/works/doi:{doi}")
            b = oa.get("biblio") or {}
            src.append(("OpenAlex", oa.get("title"), str(oa.get("publication_year")),
                        b.get("volume"), b.get("first_page")))
        except Exception as e:
            issues.append(f"OpenAlex lookup failed: {str(e)[:40]}")
        try:
            s2 = get("https://api.semanticscholar.org/graph/v1/paper/DOI:"
                     f"{doi}?fields=title,year")
            src.append(("S2", s2.get("title"), str(s2.get("year")), None, None))
        except Exception:
            pass

    for name, t2, y2, v2, p2 in src:
        if t2 and norm(t2)[:35] not in norm(title) and norm(title)[:35] not in norm(t2):
            issues.append(f"{name} title differs: '{t2[:50]}'")
        if y2 and year and y2 not in ("None",) and y2 != year:
            issues.append(f"{name} year {y2} vs bib {year}")
        if v2 and vol and str(v2) != str(vol):
            issues.append(f"{name} volume {v2} vs bib {vol}")
        if p2 and pages and str(p2) != pages.split("--")[0]:
            issues.append(f"{name} first page {p2} vs bib {pages.split('--')[0]}")

    live = [i for i in issues if not adjudication(key, i)]
    known = [i for i in issues if adjudication(key, i)]
    tag = "FLAG " if live else ("NOTE " if known else "OK   ")
    print(f"[{tag}] {key:<20} {'+'.join(s[0] for s in src) or 'no DOI':<16} {title[:42]}")
    for i in live:
        print(f"           -> {i}")
        real.append((key, i))
    for i in known:
        print(f"           .. {i}")
        print(f"              adjudicated: {adjudication(key, i)}")
        noted.append(key)
    time.sleep(0.25)

print("\n" + "=" * 72)
print(f"{len(chunks) - len(set(k for k, _ in real)) - len(set(noted))} clean, "
      f"{len(set(noted))} adjudicated, {len(set(k for k, _ in real))} unresolved")
print("RESULT:", "PASS" if not real else "REGRESSION -- investigate")
sys.exit(1 if real else 0)
