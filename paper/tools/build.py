"""Regenerate paper/main.tex from paper/manuscript.md, then check it.

    python paper/tools/build.py            # convert + verify
    python paper/tools/build.py --audit    # also re-audit refs.bib (network)
    python paper/tools/build.py --bib      # also rebuild refs.bib, then audit

Run from the repository root.

The conversion is one-way. If you start editing main.tex directly -- which is
the natural thing to do once the paper is in review -- retire manuscript.md
rather than editing both, because this script overwrites main.tex wholesale.

There is deliberately no pandoc dependency: the converter in md2tex.py handles
exactly the constructs this manuscript uses, and verify_tex.py then proves that
every numeric token in the markdown survived into the LaTeX. That check is the
point of the whole arrangement -- the numbers are the paper.
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.path.dirname(HERE)
ROOT = os.path.dirname(PAPER)

MANU = os.path.join(PAPER, "manuscript.md")
BIB = os.path.join(PAPER, "refs.bib")
TEX = os.path.join(PAPER, "main.tex")
MAP = os.path.join(HERE, "refmap.json")
BODY_MD = os.path.join(HERE, "_body.md")
BODY_TEX = os.path.join(HERE, "_body.tex")


def run(script, *args):
    cmd = [sys.executable, os.path.join(HERE, script), *map(str, args)]
    print(f"\n$ {script} {' '.join(map(str, args[:2]))}")
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode:
        sys.exit(f"{script} failed ({r.returncode})")
    return r.returncode


if "--bib" in sys.argv:
    run("build_bib.py", MANU, BIB, MAP)
    run("clean_bib.py", BIB)

if "--bib" in sys.argv or "--audit" in sys.argv:
    # Independent of Crossref, which is what refs.bib is built from.
    run("audit_refs.py", BIB)

run("prep_md.py", MANU, MAP, BODY_MD)
run("md2tex.py", BODY_MD, BODY_TEX)
run("wrap_tex.py", BODY_TEX, TEX)
run("verify_tex.py", BODY_MD, BODY_TEX)
run("check_cites.py", TEX, MAP)
run("lint_tex.py", TEX, ROOT)

for f in (BODY_MD, BODY_TEX):
    if os.path.exists(f):
        os.remove(f)

print("\nmain.tex rebuilt.")


def find_tex(prog):
    """Locate a TeX binary. MiKTeX installs per-user and does not always put
    itself on PATH, so fall back to its default location before giving up."""
    from shutil import which
    p = which(prog)
    if p:
        return p
    for base in (os.path.expandvars(r"%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64"),
                 r"C:\Program Files\MiKTeX\miktex\bin\x64",
                 "/usr/bin", "/usr/local/bin", "/Library/TeX/texbin"):
        cand = os.path.join(base, prog + (".exe" if os.name == "nt" else ""))
        if os.path.exists(cand):
            return cand
    return None


if "--pdf" in sys.argv:
    pdflatex, bibtex = find_tex("pdflatex"), find_tex("bibtex")
    if not pdflatex:
        sys.exit("pdflatex not found. Install a TeX distribution (MiKTeX or "
                 "TeX Live), or open paper/main.tex in Overleaf.")
    # pdflatex, bibtex, then twice more so citations and cross-references
    # settle; bibtex is skipped if absent so the run still yields a PDF.
    seq = [pdflatex, bibtex, pdflatex, pdflatex]
    for i, exe in enumerate(seq, 1):
        if exe is None:
            continue
        args = ([exe, "-interaction=nonstopmode", "main.tex"]
                if exe == pdflatex else [exe, "main"])
        r = subprocess.run(args, cwd=PAPER, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        print(f"  pass {i}: {os.path.basename(exe)} -> exit {r.returncode}")

    log = os.path.join(PAPER, "main.log")
    if os.path.exists(log):
        text = io.open(log, encoding="utf-8", errors="replace").read()
        print(f"\n  undefined references/citations : {text.count('undefined')}")
        print(f"  overfull boxes                 : {text.count('Overfull')}")
    pdf = os.path.join(PAPER, "main.pdf")
    print(f"\n{pdf}  ({os.path.getsize(pdf) / 1e6:.1f} MB)" if os.path.exists(pdf)
          else "\nno PDF produced -- see paper/main.log")
else:
    print("Add --pdf to also build the PDF.")
