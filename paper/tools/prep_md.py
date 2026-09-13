"""Prepare manuscript.md for pandoc: [n] -> \\cite{key}, drop the ref list.

Every bracket replacement is printed so it can be audited -- the manuscript is
full of bracketed confidence intervals like [+0.85, +0.91], which must NOT be
touched. Only brackets whose contents are bare integers in 1..29 are citations.
"""
import io, re, sys, json

MANU, REFMAP, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
keys = json.load(io.open(REFMAP, encoding="utf-8"))
src = io.open(MANU, encoding="utf-8").read()

body, refs = src.split("## 10. References")

# audit: show every bracketed thing so nothing is silently converted
all_br = set(re.findall(r"\[([^\]\[]{1,40})\]", body))
cite_br = {b for b in all_br
           if re.fullmatch(r"[\d,\s]+", b) and
           all(1 <= int(x) <= 29 for x in b.split(",") if x.strip())}
print(f"distinct bracket contents: {len(all_br)}")
print(f"  treated as citations   : {len(cite_br)}")
skipped = sorted(all_br - cite_br)
print(f"  left alone             : {len(skipped)}")
for s in skipped[:6]:
    print(f"      e.g. [{s}]")

n = 0


def repl(m):
    global n
    inner = m.group(1)
    if not re.fullmatch(r"[\d,\s]+", inner):
        return m.group(0)
    nums = [x.strip() for x in inner.split(",") if x.strip()]
    if not all(x.isdigit() and 1 <= int(x) <= 29 for x in nums):
        return m.group(0)
    n += 1
    return "\\cite{" + ",".join(keys[x] for x in nums) + "}"


body = re.sub(r"\[([^\]\[]{1,40})\]", repl, body)
print(f"\ncitations rewritten: {n}")

# Cross-references: the prose names figures and tables as plain text
# ("Figure 3", "Fig. 4", "Table 1"). LaTeX should number them itself.
FIGREF = {1: "fig:landscape", 2: "fig:embeddings", 3: "fig:inflation",
          4: "fig:criteria", 5: "fig:recovery", 6: "fig:coverage",
          7: "fig:efflag", 8: "fig:rama"}
# Table mentions are matched on surrounding context, not on the number they
# happen to carry: the numbers in the prose were written against a numbering
# the document never actually had (it cited a "Table 4" that did not exist).
# LaTeX numbers the floats itself, so each site is bound to a label by meaning.
TABSITES = [
    ("tightly bounded (Table 1):", "tab:rho"),
    ("of Prinz conditions (Table 4). Where the cap", "tab:ceiling"),
    ("of Prinz conditions (Table 4) --", "tab:ceiling"),
    ("Table 1 (silhouette/PCA:", "tab:critrho"),
    ("understated (Table 4):", "tab:ceiling"),
    ("endpoint comparison in Table 3,", "tab:oraclegap"),
    ("(Table 8). Sampling budgets", "tab:basins"),
]

f = t = 0


def figrepl(m):
    global f
    k = int(m.group(2))
    if k not in FIGREF:
        return m.group(0)
    f += 1
    return "Figure~\\ref{%s}" % FIGREF[k]


body = re.sub(r"(Figure|Fig\.)\s+(\d+)", figrepl, body)

for ctx, label in TABSITES:
    assert body.count(ctx) == 1, f"table site {ctx!r} found {body.count(ctx)}x"
    body = body.replace(ctx, re.sub(r"Table\s+\d+", "Table~\\\\ref{%s}" % label, ctx))
    t += 1

# Four tables are introduced by a colon rather than by name. That reads fine in
# markdown, where the table sits immediately below, but LaTeX floats move, so
# each needs an explicit reference.
TABINTRO = [
    ("are closely similar in magnitude:", "tab:coverage"),
    ("The independent-sample result is:", "tab:iid"),
    ("quality with the selection step removed -- as a function of both:", "tab:lagablation"),
    ("associated with how many budget doublings remain:", "tab:warmup"),
    ("quality tracks it closely:", "tab:efflag"),
    ("randomness that the eight sweep seeds\nvary.", "tab:crossseed"),
]
for ctx, label in TABINTRO:
    assert body.count(ctx) == 1, f"table intro {ctx[:40]!r} found {body.count(ctx)}x"
    # keep whatever punctuation ended the lead-in -- some are colons
    # introducing the table, some are full sentences before it
    body = body.replace(ctx, ctx[:-1] + " (Table~\\ref{%s})" % label + ctx[-1])
    t += 1

leftover = re.findall(r"Table\s+\d+", body)
print(f"figure refs linked : {f}")
print(f"table refs linked  : {t}")
print(f"unlinked 'Table N' : {len(leftover)} {leftover}")

io.open(OUT, "w", encoding="utf-8", newline="\n").write(body.rstrip() + "\n")
print(f"wrote {OUT}")
