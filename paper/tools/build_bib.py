"""Build paper/refs.bib from publisher metadata, not by hand.

For each reference, resolve its DOI via Crossref, then pull the publisher's own
BibTeX through doi.org content negotiation. Four entries are not in Crossref
(ICLR, JMLR and Sankhya are not indexed) and are written out explicitly after
being confirmed by hand; they are listed in MANUAL below.

Emits refs.bib plus refmap.json, which maps the manuscript's [n] markers onto
citation keys for the LaTeX conversion.
"""
import io, re, sys, json, time, urllib.parse, urllib.request

MANU, OUT_BIB, OUT_MAP = sys.argv[1], sys.argv[2], sys.argv[3]

KEYS = {
    1: "muller1979", 2: "prinz2011", 3: "amadei1993", 4: "perezhernandez2013",
    5: "schwantes2013", 6: "kingma2014", 7: "hernandez2018", 8: "wehmeyer2018",
    9: "ribeiro2018", 10: "glielmo2021", 11: "husic2018", 12: "chodera2014",
    13: "scherer2015", 14: "grossfield2009", 15: "schwarz1978", 16: "akaike1974",
    17: "biernacki2000", 18: "keribin2000", 19: "drton2017", 20: "rousseeuw1987",
    21: "hubert1985", 22: "vandermaaten2008", 23: "wattenberg2016",
    24: "eastman2017", 25: "maier2015", 26: "nguyen2013", 27: "zhang2019",
    28: "mcgibbon2015", 29: "wu2026",
}

# Not in Crossref; each verified against the publisher/author page directly.
MANUAL = {
6: """@inproceedings{kingma2014,
  author    = {Kingma, Diederik P. and Welling, Max},
  title     = {Auto-Encoding Variational {B}ayes},
  booktitle = {2nd International Conference on Learning Representations
               (ICLR 2014), Conference Track Proceedings},
  address   = {Banff, AB, Canada},
  year      = {2014},
  eprint    = {1312.6114},
  archivePrefix = {arXiv},
  primaryClass  = {stat.ML},
}""",
18: """@article{keribin2000,
  author  = {Keribin, Christine},
  title   = {Consistent Estimation of the Order of Mixture Models},
  journal = {Sankhy\\={a}: The Indian Journal of Statistics, Series A},
  volume  = {62},
  number  = {1},
  pages   = {49--66},
  year    = {2000},
}""",
22: """@article{vandermaaten2008,
  author  = {van der Maaten, Laurens and Hinton, Geoffrey},
  title   = {Visualizing Data using {t-SNE}},
  journal = {Journal of Machine Learning Research},
  volume  = {9},
  number  = {86},
  pages   = {2579--2605},
  year    = {2008},
  url     = {https://jmlr.org/papers/v9/vandermaaten08a.html},
}""",
}

UA = {"User-Agent": "sampling-audit-refcheck/1.0 (mailto:jaiveerbassi@yahoo.com)"}
text = io.open(MANU, encoding="utf-8").read().split("## 10. References")[1]
entries = dict((int(n), re.sub(r"\s+", " ", b).replace("*", "").strip())
               for n, b in re.findall(r"^\[(\d+)\]\s+(.*?)(?=^\[\d+\]|\Z)",
                                      text, re.M | re.S))


def get(url, headers):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=headers), timeout=30).read().decode("utf-8")


out, failed = [], []
for n in sorted(entries):
    key = KEYS[n]
    if n in MANUAL:
        out.append(MANUAL[n])
        print(f"[{n:>2}] manual   {key}")
        continue
    try:
        items = json.loads(get(
            "https://api.crossref.org/works?rows=1&select=DOI&query.bibliographic="
            + urllib.parse.quote(entries[n]), UA))["message"]["items"]
        doi = items[0]["DOI"]
        bib = get(f"https://doi.org/{doi}",
                  {**UA, "Accept": "application/x-bibtex; charset=utf-8"}).strip()
        # normalise the publisher's key to ours
        bib = re.sub(r"^(@\w+\s*\{)[^,]*,", r"\g<1>" + key + ",", bib, count=1)

        # JCP, PRE and similar identify articles by article number rather than
        # a page range. Crossref carries that as `article-number`, which the
        # BibTeX rendering drops entirely -- leaving the entry with no locator
        # at all, so a reader cannot find the paper. Put it in `pages`.
        if not re.search(r"pages\s*=", bib, re.I):
            meta = json.loads(get(f"https://api.crossref.org/works/{doi}", UA))["message"]
            artno = meta.get("article-number") or (
                meta.get("page") if meta.get("page") else None)
            if artno:
                bib = re.sub(r"\n?\}\s*$", f",\n  pages = {{{artno}}}\n}}", bib)
                print(f"     + pages={artno} (from article-number)")
        out.append(bib)
        print(f"[{n:>2}] crossref {key:<20} {doi}")
    except Exception as e:
        print(f"[{n:>2}] FAILED   {key}: {e}")
        failed.append(n)
    time.sleep(0.4)

io.open(OUT_BIB, "w", encoding="utf-8", newline="\n").write("\n\n".join(out) + "\n")
io.open(OUT_MAP, "w", encoding="utf-8", newline="\n").write(
    json.dumps({str(k): v for k, v in KEYS.items()}, indent=2))
print(f"\nwrote {OUT_BIB} ({len(out)}/{len(entries)} entries)")
if failed:
    print("FAILED:", failed)
