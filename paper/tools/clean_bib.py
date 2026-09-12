"""Repair publisher BibTeX quirks.

The characters this file matches on are written as escapes, not as literals.
An editor or shell that re-encodes the file would otherwise silently destroy
them and the repairs would stop firing without failing.

  U+FFFD  Springer's record for Mueller & Brown (1979) carries a bad byte
          where the umlaut belongs, which arrives as a replacement character.
  U+2013  Page ranges come back with Unicode en-dashes; BibTeX wants '--'.
  months  Crossref writes month=June, but BibTeX's standard styles define only
          the three-letter abbreviations, so anything else raises
          "string name undefined".
  pages   Schwarz (1978) has no page range in Crossref, and OpenAlex's 15-18
          is wrong. Project Euclid, the publisher of record, gives
          Ann. Statist. 6(2):461-464.
"""
import io, re, sys

REPLACEMENT = "�"
ENDASH = "–"

P = sys.argv[1]
t = io.open(P, encoding="utf-8").read()

before_fffd = t.count(REPLACEMENT)
t = t.replace("M" + REPLACEMENT + "ller, Klaus", 'M{\\"u}ller, Klaus')

before_dash = t.count(ENDASH)
t = t.replace(ENDASH, "--")

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
n_month = 0
for m in MONTHS:
    pat = "month=" + m
    n_month += t.count(pat)
    t = t.replace(pat, "month=" + m[:3].lower())

# `unsrt` lowercases titles, which turns OpenMM into "Openmm", ff14SB into
# "ff14sb", MDTraj into "Mdtraj" and Born into "born". BibTeX leaves anything
# inside braces alone, so protect exactly the words that must keep their case:
# tokens with a capital inside them, all-caps acronyms, and proper nouns that
# look like ordinary words. Hyphenated words are judged segment by segment, so
# "Auto-Encoding" and "Non-Native" are left to be lowercased like their
# neighbours while "t-SNE" is protected.
PROPER = {"Bayes", "Bayesian", "Born", "Markov", "Gaussian", "Langevin",
          "Rand", "Ramachandran", "Monte", "Carlo", "Boltzmann", "Fourier",
          "Spearman", "Euclidean"}


def _needs_protection(core):
    for seg in core.split("-"):
        letters = [c for c in seg if c.isalpha()]
        if len(letters) >= 2 and all(c.isupper() for c in letters):
            return True                      # SNE, RAVE, NTL9, ICL
        if any(c.isupper() for c in seg[1:]):
            return True                      # OpenMM, MDTraj, ff14SB, GBn2
    return core in PROPER


def protect_title(title):
    out = []
    for tok in title.split(" "):
        core = tok.strip(".,:;()[]")
        if core and "{" not in tok and _needs_protection(core):
            tok = tok.replace(core, "{" + core + "}", 1)
        out.append(tok)
    return " ".join(out)


n_prot = 0
def _protect_match(m):
    global n_prot
    inner = m.group(2)
    new = protect_title(inner)
    if new != inner:
        n_prot += 1
    return m.group(1) + new + "}"


t = re.sub(r"(title\s*=\s*\{)([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",
           _protect_match, t, flags=re.I)

n_pages = 0
if re.search(r"@\w+\{schwarz1978,", t) and not re.search(
        r"schwarz1978,(?:[^@]*?)pages", t, re.S):
    t = re.sub(r"(@\w+\{schwarz1978,)", r"\1\n  pages={461--464},", t, count=1)
    n_pages += 1

io.open(P, "w", encoding="utf-8", newline="\n").write(t)
print(f"replacement chars fixed : {before_fffd - t.count(REPLACEMENT)}")
print(f"en-dashes normalised    : {before_dash}")
print(f"month names abbreviated : {n_month}")
print(f"schwarz1978 pages added : {n_pages}")
print(f"titles case-protected   : {n_prot}")
print(f"remaining U+FFFD        : {t.count(REPLACEMENT)}")
