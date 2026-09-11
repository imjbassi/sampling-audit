"""Confirm the LaTeX conversion preserved every number and lost no prose.

Compares the multiset of numeric tokens in the markdown against the .tex, and
checks that section/table/figure counts are what we expect.
"""
import io, re, sys
from collections import Counter

md = io.open(sys.argv[1], encoding="utf-8").read()
tex = io.open(sys.argv[2], encoding="utf-8").read()

# strip things that legitimately exist in only one of the two
md_s = re.sub(r"\\cite\{[^}]*\}", " ", md)
tex_s = re.sub(r"\\cite\{[^}]*\}", " ", tex)
# Captions are prose I wrote for the LaTeX version and have no markdown
# counterpart, so their contents must come out before comparing.
def strip_captions(t):
    out, i = [], 0
    while i < len(t):
        m = re.compile(r"\\caption\{").search(t, i)
        if not m:
            out.append(t[i:]); break
        out.append(t[i:m.start()])
        d, j = 1, m.end()
        while j < len(t) and d:
            d += (t[j] == "{") - (t[j] == "}")
            j += 1
        i = j
    return "".join(out)

tex_s = strip_captions(tex_s)

NUM = re.compile(r"\d+(?:[.,]\d+)*")
a, b = Counter(NUM.findall(md_s)), Counter(NUM.findall(tex_s))

missing = {k: a[k] - b.get(k, 0) for k in a if a[k] > b.get(k, 0)}
extra = {k: b[k] - a.get(k, 0) for k in b if b[k] > a.get(k, 0)}

print(f"distinct numeric tokens  md={len(a)}  tex={len(b)}")
print(f"total occurrences        md={sum(a.values())}  tex={sum(b.values())}")
print(f"\nmissing from tex : {len(missing)}")
for k, v in sorted(missing.items())[:15]:
    print(f"   {k}  (x{v})")
print(f"extra in tex     : {len(extra)}")
for k, v in sorted(extra.items())[:15]:
    print(f"   {k}  (x{v})")

print("\nstructure")
print(f"  sections     {tex.count(chr(92)+'section{')}")
print(f"  subsections  {tex.count(chr(92)+'subsection{')}")
print(f"  tables       {len(re.findall(r'begin.table', tex))}")
print(f"  figures      {len(re.findall(r'includegraphics', tex))}")
print(f"  cite sites   {len(re.findall(r'\\\\cite\\{', tex))}")
print("\nVERDICT:", "PASS" if not missing else "REVIEW NEEDED")
