"""Structural checks on main.tex, standing in for a compile.

No TeX distribution is installed here, so this catches the errors that would
otherwise only surface on the user's first pdflatex run: unbalanced braces or
environments, unescaped specials, missing graphics, and undefined refs.
"""
import io, os, re, sys
from collections import Counter

TEX, ROOT = sys.argv[1], sys.argv[2]
t = io.open(TEX, encoding="utf-8").read()
bad = 0

# --- environments -----------------------------------------------------------
op = Counter(re.findall(r"\\begin\{([^}]+)\}", t))
cl = Counter(re.findall(r"\\end\{([^}]+)\}", t))
for k in set(op) | set(cl):
    if op[k] != cl[k]:
        print(f"UNBALANCED env {k}: {op[k]} begin / {cl[k]} end")
        bad += 1
print(f"environments balanced : {len(set(op) | set(cl))} kinds")

# --- braces -----------------------------------------------------------------
d = 0
for ch in re.sub(r"\\[{}]", "", t):
    d += (ch == "{") - (ch == "}")
print(f"brace balance         : {d}")
if d:
    bad += 1

# --- graphics ---------------------------------------------------------------
gp = re.search(r"\\graphicspath\{\{([^}]*)\}\}", t)
base = os.path.normpath(os.path.join(os.path.dirname(TEX), gp.group(1))) if gp \
    else os.path.dirname(TEX)
missing = []
for img in re.findall(r"\\includegraphics\[[^\]]*\]\{([^}]+)\}", t):
    if not os.path.exists(os.path.join(base, img)):
        missing.append(img)
print(f"graphics referenced   : {len(re.findall(r'includegraphics', t))}"
      f"  missing: {len(missing)}")
for m in missing:
    print(f"   MISSING {m}")
    bad += 1

# --- refs / labels ----------------------------------------------------------
labels = set(re.findall(r"\\label\{([^}]+)\}", t))
refs = set(re.findall(r"\\ref\{([^}]+)\}", t))
print(f"labels {len(labels)}  refs {len(refs)}")
for r in sorted(refs - labels):
    print(f"   UNDEFINED ref {r}")
    bad += 1
for l in sorted(labels - refs):
    print(f"   note: label never referenced: {l}")

# --- unescaped specials -----------------------------------------------------
# '&' is the column separator inside tabular and must stay bare; '%' starting a
# line is a comment. Only flag the cases that would actually break a build.
stripped = re.sub(r"\$[^$]*\$", "", t)
stripped = re.sub(r"\\begin\{tabular\}.*?\\end\{tabular\}", "", stripped, flags=re.S)
n_spec = 0
for ln in stripped.split("\n"):
    if ln.lstrip().startswith("%"):
        continue
    for m in re.finditer(r"(?<!\\)([&#])|(?<!\\)%(?=\S)", ln):
        print(f"   UNESCAPED {m.group(0)!r} in: {ln.strip()[:80]}")
        n_spec += 1
print(f"unescaped specials    : {n_spec}")
bad += n_spec

# --- bib --------------------------------------------------------------------
bib = os.path.join(os.path.dirname(TEX), "refs.bib")
keys = set(re.findall(r"@\w+\{([^,]+),", io.open(bib, encoding="utf-8").read()))
cited = set()
for c in re.findall(r"\\cite\{([^}]*)\}", t):
    cited.update(x.strip() for x in c.split(","))
print(f"bib entries {len(keys)}  cited {len(cited)}")
for c in sorted(cited - keys):
    print(f"   CITED BUT NOT IN BIB: {c}")
    bad += 1

print("\n" + ("LINT CLEAN" if not bad else f"{bad} PROBLEM(S)"))
