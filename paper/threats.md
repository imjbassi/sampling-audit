# Threats to validity

Written before the results section, deliberately. Each entry names the
objection a hostile-but-fair reviewer would raise, the current mitigation, and
what is still exposed. Anything still exposed goes in the paper's limitations
section in the paper's own words — not hidden.

---

### T1. "This is a known property of BIC, not a finding about DR."

The strongest objection. Under model misspecification the log-likelihood gain
from an extra Gaussian component scales with *n* while BIC's penalty scales
with log *n*, so BIC selects more components as *n* grows regardless of the
data-generating process.

**Mitigation.** Five selection criteria on every condition (`selection.py`).
ICL adds an explicit entropy penalty on component overlap; silhouette is
likelihood-free; elbow gap is assumption-light. The claim is made only to the
extent it survives all of them.

**Still exposed.** If the effect appears under BIC/AIC but vanishes under ICL
and silhouette, the honest paper is a *different* paper: "the standard
criterion inflates state counts with budget; here is what to use instead."
That is still a good paper. Write it if that is what the data says. Do not
force the original framing.

---

### T2. "Your ground truth is a toy potential and a fake nonlinear lift."

**Mitigation.** Two independent potentials with different dimensionality and
different basin counts, plus the alanine dipeptide validation where ground
truth comes from backbone dihedrals — chemistry, not construction.

**Still exposed.** Alanine dipeptide is still small and fast-mixing. The result
is not demonstrated on a slow-folding protein, and should not be claimed for
one. State the scope explicitly.

---

### T3. "More data means more VAE training, so you confounded your own variable."

**Mitigation.** `VAEEmbedder(fixed_steps=...)` trains for a constant number of
gradient steps regardless of dataset size. This is on by default in the sweep.

**Still exposed.** A fixed step budget slightly *under*-trains large datasets
relative to normal practice. Report the fixed-epoch variant as an ablation and
show the direction of the difference rather than only the convenient setting.

---

### T4. "You bootstrap over seeds but frames are autocorrelated."

**Mitigation.** That is exactly why the seed is the replicate and no CI is
computed over frames. Stated explicitly in `analyze.py` and in the methods.

**Still exposed.** Independent seeds share the same lift and the same
potential, so they are replicates of the sampling process, not of the system.
Say so.

---

### T5. "Reported k is censored at kmax."

**Mitigation.** Ceiling-hit rate reported per condition (Table 4).

**Still exposed.** Where the rate is high the effect size is understated and
the rank correlation is attenuated. Do not quote a mean k as if it were
uncensored; quote it as a lower bound.

---

### T6. "Prior work already benchmarked these methods."

**Mitigation.** Prior comparisons vary the method at fixed data; this varies the
data at fixed ground truth. Say this in one sentence in the introduction and
cite the prior work generously.

**Still exposed.** The gap is genuinely narrow. The paper's value rests on the
control design, not on novelty of the methods. Lead with the control.

---

### T7. "Two components is an arbitrary embedding dimension."

**Mitigation.** Two is the dimension used for the free-energy-surface figures
this paper is about, which is why it is the default.

**Still exposed.** Not yet swept. Add an appendix ablation over
`n_components ∈ {2, 3, 5}` before submission; if the effect is dimension-
dependent, that belongs in the paper.

---

### T8. Self-audit.

The paper argues that conclusions can be artifacts of an uncontrolled nuisance
variable. It would be self-undermining to publish results from too few seeds.
Run the full seed count before writing any number into the manuscript, and if a
preliminary trend does not survive seed expansion, report that it did not —
as happened in the previous project, and as the argument here demands.
