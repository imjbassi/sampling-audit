"""Convert the manuscript body to LaTeX deterministically.

Written rather than pandoc'd because pandoc is not actually installed here (the
chocolatey shim is dangling) and because a narrow converter for exactly this
document's constructs is auditable: verify_tex.py then checks that every number
in the markdown survived into the .tex.

Handles: headings, bold/emph, pipe tables -> booktabs, em-dashes, arrows, and
LaTeX escaping that leaves \\cite{} alone. Figure floats are injected at named
anchors.
"""
import io, re, sys

BODY, OUT = sys.argv[1], sys.argv[2]

# ---------------------------------------------------------------- table captions
TABLE_META = [
    ("tab:rho", "Spearman rank correlation between log sampling budget and "
     "BIC-selected state count, for each system, sampling mode and projection "
     "method. Brackets are bootstrap 95\\% confidence intervals over the 20 "
     "seeds. No interval approaches zero."),
    ("tab:ceiling", "Ceiling-hit rate: the fraction of conditions in which the "
     "criterion selected the largest state count the search allowed "
     "($k_{\\max} = 15$). Where this is non-negligible the reported count is "
     "right-censored, so the inflation reported elsewhere is understated. ICL "
     "is the only criterion that never reaches the ceiling."),
    ("tab:critrho", "Budget correlation under each selection criterion: "
     "Spearman $\\rho$ between log sampling budget and selected state count. "
     "Entries marked ``--'' are conditions in which the criterion returned the "
     "same count at every budget, leaving the correlation undefined."),
    ("tab:coverage", "The coverage-matched control. BIC budget correlations "
     "under genuinely short trajectories and under uniform thinning of one long "
     "reference trajectory. Intervals overlap in all six comparisons, so holding "
     "landscape coverage fixed does not remove the effect."),
    ("tab:lagablation", "TICA lag ablation on the Prinz potential: oracle-$k$ "
     "recovery as a function of sampling budget and lag (10 seeds, subsample "
     "mode, 300 conditions). Recovery falls monotonically as lag grows at fixed "
     "budget, and the budget needed to reach any given level rises with lag."),
    ("tab:oraclegap", "Recovery at the criterion-selected state count against "
     "recovery given the true state count, at $n = 32{,}000$ in \\texttt{short} "
     "mode. The gap localises how much of the error belongs to the selection "
     "step rather than to the projection."),
    ("tab:ninepairs", "All nine method--system pairs. Every pair declines from "
     "its peak to the largest budget tested; the size of the decline tracks how "
     "much budget remains after TICA's warm-up completes, and is otherwise "
     "uniformly large for PCA and VAE."),
    ("tab:warmup", "Why TICA's decline varies by system. Warm-up completion is "
     "read from the oracle-$k$ column; what remains of the sweep after it "
     "determines how much ordinary selection-driven degradation can occur."),
    ("tab:efflag", "TICA under coverage-matched subsampling on alanine "
     "dipeptide. Thinning to $n$ frames from a 100,000-frame reference imposes a "
     "stride of $100{,}000/n$, so the effective physical lag shrinks as the "
     "budget grows. Projection quality tracks the effective lag, not the budget."),
    ("tab:basins", "Mean number of the three ground-truth basins visited by "
     "contiguous leading blocks of the 100~ns trajectory. Under coverage-matched "
     "subsampling all three are visited at every budget."),
]

# ---------------------------------------------------------------- figure floats
FIGS = [
    ("anchor", "ref{fig:landscape} shows", "fig:landscape", "figures/fig1_landscape.pdf",
     "\\textwidth", "figure*",
     "Ground truth for the Müller--Brown potential: (a) the energy surface "
     "with its three minima, (b) basin assignment by steepest-descent quenching, "
     "(c) one sampled trajectory coloured by true basin. Basin labels never come "
     "from a fitted model."),
    ("anchor", "ref{fig:embeddings} shows", "fig:embeddings",
     "figures/fig2_embedding_grid.pdf", "\\textwidth", "figure*",
     "Embeddings of the Müller--Brown system across projection method (rows) "
     "and sampling budget (columns), coloured by true basin. The underlying "
     "landscape is identical in every panel; only the number of saved frames "
     "differs."),
    ("after_table", 0, "fig:inflation", "figures/fig3_state_inflation_bic.pdf",
     "\\columnwidth", "figure",
     "BIC-selected state count against sampling budget, with bootstrap "
     "confidence intervals over seeds. The dotted line is the true state count. "
     "Counts rise monotonically while the landscape is unchanged."),
    ("after_table", 2, "fig:criteria", "figures/fig4_criteria.pdf",
     "\\textwidth", "figure*",
     "The same trend under all five selection criteria. BIC inflates "
     "monotonically; AIC is saturated at every budget rather than trending; ICL "
     "alone stays in an interpretable range; silhouette and elbow gap are "
     "insensitive to budget and to landscape alike."),
    ("after_table", 5, "fig:recovery", "figures/fig5_recovery.pdf",
     "\\textwidth", "figure*",
     "Recovery at the selected state count against recovery given the true state "
     "count. Selected-$k$ recovery peaks at an intermediate budget and then "
     "declines while oracle-$k$ recovery is flat or rising: more data makes the "
     "standard pipeline's answer worse. Degenerate conditions, in which fewer "
     "basins were visited than exist, are excluded."),
    ("after_table", 3, "fig:coverage", "figures/fig6_coverage.pdf",
     "\\columnwidth", "figure",
     "Budget correlation with and without coverage matching. The effect survives "
     "holding landscape exploration fixed, which places it in the estimator "
     "rather than in what the trajectory visited."),
    ("after_table", 8, "fig:efflag", "figures_alanine/fig7_tica_effective_lag.pdf",
     "\\textwidth", "figure*",
     "Thinning a trajectory rescales TICA's lag. (a) Warm-up against sampling "
     "budget for both modes. (b) The same points against the effective lag "
     "$\\tau_{\\mathrm{eff}} = L\\,(N/n)\\,\\Delta t$: every subsample point "
     "above the dihedral transition timescale sits near 0.25 and everything "
     "below it jumps to roughly 0.95, so lag alone accounts for that curve. The "
     "\\texttt{short} points sit at a fixed 10~ps and still span 0.15 to 0.96, "
     "so their spread is sample size alone."),
]

UNI = [("\u2014", "---"), ("\u2013", "--"), ("\u2248", "$\\approx$"),
       ("\u00d7", "$\\times$"), ("\u2192", "$\\rightarrow$"),
       ("\u03c1", "$\\rho$"), ("\u03c4", "$\\tau$"), ("\u00b5", "$\\mu$")]


def inline(s):
    """Escape LaTeX specials and apply markdown inline formatting."""
    holds = []

    def hold(m):
        holds.append(m.group(0))
        return f"\x00{len(holds)-1}\x00"

    def hold_str(txt):
        holds.append(txt)
        return f"\x00{len(holds)-1}\x00"

    s = re.sub(r"\\(?:cite|ref)\{[^}]*\}", hold, s)
    # These expand to math ($\approx$ and friends). They must be held, not
    # inserted raw: the escaping pass below would otherwise escape the dollar
    # signs they introduce and emit a literal "\$\approx\$".
    for a, b in UNI:
        if a in s:
            s = s.replace(a, hold_str(b))
    s = s.replace("\\", "\x01")
    for ch in "&%#_${}":
        s = s.replace(ch, "\\" + ch)
    s = s.replace("\x01", "\\textbackslash{}")
    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
    s = re.sub(r"(?<![\w*])\*([^*]+?)\*(?![\w*])", r"\\emph{\1}", s)
    s = re.sub(r"`([^`]+)`", r"\\texttt{\1}", s)
    s = s.replace(" -- ", "---").replace(" -> ", " $\\rightarrow$ ")
    s = re.sub(r'"([^"]+)"', r"``\1''", s)
    return re.sub(r"\x00(\d+)\x00", lambda m: holds[int(m.group(1))], s)


def make_table(rows, idx):
    label, cap = TABLE_META[idx]
    head, body = rows[0], rows[1:]
    ncol = len(head)
    spec = "l" + "c" * (ncol - 1)
    # Every table here carries either wide numeric cells (confidence intervals)
    # or wide labels, and none fits a 3.4in column: the four-column warm-up
    # table silently overflowed into the neighbouring column's body text when
    # this was decided by column count.
    env = "table*"
    out = [f"\\begin{{{env}}}[t]", "\\centering", "\\small",
           f"\\caption{{{cap}}}", f"\\label{{{label}}}",
           f"\\begin{{tabular}}{{{spec}}}", "\\toprule",
           " & ".join(f"\\textbf{{{inline(c)}}}" for c in head) + " \\\\",
           "\\midrule"]
    for r in body:
        r = (r + [""] * ncol)[:ncol]
        out.append(" & ".join(inline(c) for c in r) + " \\\\")
    out += ["\\bottomrule", "\\end{tabular}", f"\\end{{{env}}}"]
    return "\n".join(out)


def figure(label, path, width, env, cap):
    return "\n".join([
        f"\\begin{{{env}}}[t]", "\\centering",
        f"\\includegraphics[width={width}]{{{path}}}",
        f"\\caption{{{cap}}}", f"\\label{{{label}}}", f"\\end{{{env}}}"])


src = io.open(BODY, encoding="utf-8").read().split("\n")
out, i, tbl_i = [], 0, 0
pending_after_table = {}
for spec in FIGS:
    if spec[0] == "after_table":
        pending_after_table.setdefault(spec[1], []).append(spec)

in_abstract = False
started = False          # have we reached the Abstract yet?
deferred = []            # figure floats waiting for the paragraph to end
while i < len(src):
    line = src[i]

    # pipe table
    if line.startswith("|") and i + 1 < len(src) and \
       re.fullmatch(r"[|\-: ]+", src[i + 1] or "x"):
        rows = []
        j = i
        while j < len(src) and src[j].startswith("|"):
            if not re.fullmatch(r"[|\-: ]+", src[j]):
                rows.append([c.strip() for c in src[j].strip("|").split("|")])
            j += 1
        out.append(make_table(rows, tbl_i))
        for spec in pending_after_table.get(tbl_i, []):
            out.append(figure(spec[2], spec[3], spec[4], spec[5], spec[6]))
        tbl_i += 1
        i = j
        continue

    if line.startswith("## "):
        t = line[3:].strip()
        if t.lower() == "abstract":
            out.append("\\begin{abstract}")
            in_abstract = True
            started = True
        else:
            if in_abstract:
                out.append("\\end{abstract}")
                in_abstract = False
            out.append("\\section{%s}" % inline(re.sub(r"^\d+\.\s*", "", t)))
        i += 1
        continue
    if line.startswith("### "):
        # The line directly under the H1 is the paper's subtitle, not a
        # section. It already appears inside \title, so emitting it here too
        # produced a stray "0.1" subsection above the abstract.
        if not started:
            i += 1
            continue
        out.append("\\subsection{%s}" %
                   inline(re.sub(r"^\d+\.\d+\s*", "", line[4:].strip())))
        i += 1
        continue
    if line.startswith("# "):
        i += 1
        continue

    # bullet / numbered lists. Items may be separated by blank lines (the
    # Recommendations are) and wrap onto indented continuation lines, so the
    # list ends only when a blank line is followed by something that is
    # neither a marker nor a continuation.
    m = re.match(r"(\s*)(-|\d+\.)\s+(.*)", line)
    if m and not line.startswith("|"):
        env = "itemize" if m.group(2) == "-" else "enumerate"
        items, j = [], i
        while j < len(src):
            ln = src[j]
            mk = re.match(r"\s*(?:-|\d+\.)\s+(.*)", ln)
            if mk:
                items.append([mk.group(1)])
            elif ln.startswith((" ", "\t")) and ln.strip():
                items[-1].append(ln.strip())
            elif not ln.strip():
                k = j + 1
                while k < len(src) and not src[k].strip():
                    k += 1
                if k < len(src) and (re.match(r"\s*(?:-|\d+\.)\s+", src[k])
                                     or src[k].startswith((" ", "\t"))):
                    j = k
                    continue
                break
            else:
                break
            j += 1
        out.append(f"\\begin{{{env}}}")
        for it in items:
            out.append("\\item " + inline(" ".join(it)))
        out.append(f"\\end{{{env}}}")
        i = j
        continue

    out.append(inline(line))
    # A float emitted in the middle of a paragraph splits that paragraph in
    # the output, so hold it until the paragraph actually ends.
    for spec in FIGS:
        if spec[0] == "anchor" and spec[1] in line:
            deferred.append(spec)
    if not line.strip() and deferred:
        for spec in deferred:
            out.append(figure(spec[2], spec[3], spec[4], spec[5], spec[6]))
        out.append("")
        deferred = []
    i += 1

if in_abstract:
    out.append("\\end{abstract}")

doc = "\n".join(out).strip() + "\n"

# ---- whole-document typography ---------------------------------------------
# These have to run across the finished text, not line by line: the manuscript
# wraps at 78 columns, so quoted phrases routinely straddle a newline and the
# per-line pass cannot see both ends of them.
doc, nq = re.subn(r'"([^"]+?)"', r"``\1''", doc, flags=re.S)

# The prose spells the rank correlation as the word "rho". In a typeset paper
# it should be the symbol. Never touch an existing \rho, and never touch the
# inside of a \ref/\label/\cite argument -- the label tab:rho lives there, and
# rewriting it produces \ref{tab:$\rho$}, which is a fatal TeX error rather
# than a visible typo.
_held = []


def _hold_arg(m):
    _held.append(m.group(0))
    return f"\x02{len(_held)-1}\x02"


doc = re.sub(r"\\(?:ref|label|cite)\{[^}]*\}", _hold_arg, doc)
doc, nr = re.subn(r"(?<![\\\w])rho(?![\w])", r"$\\rho$", doc)
doc = re.sub(r"\x02(\d+)\x02", lambda m: _held[int(m.group(1))], doc)

io.open(OUT, "w", encoding="utf-8", newline="\n").write(doc)
print(f"multi-line quotes fixed: {nq}   'rho' -> symbol: {nr}")
print(f"tables: {tbl_i}   figures: {len(FIGS)}")
print(f"wrote {OUT}")
