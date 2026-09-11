"""Regenerate paper/main.tex from paper/manuscript.md, then check it.

    python paper/tools/build.py            # convert + verify
    python paper/tools/build.py --bib      # also rebuild refs.bib from Crossref

Run from the repository root.

The conversion is one-way. If you start editing main.tex directly -- which is
the natural thing to do once the paper is in review -- retire manuscript.md
rather than editing both, because this script overwrites main.tex wholesale.

There is deliberately no pandoc dependency: the converter in md2tex.py handles
exactly the constructs this manuscript uses, and verify_tex.py then proves that
every numeric token in the markdown survived into the LaTeX. That check is the
point of the whole arrangement -- the numbers are the paper.
"""
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
    if r.returncode and script not in ("verify_tex.py",):
        sys.exit(f"{script} failed ({r.returncode})")
    return r.returncode


if "--bib" in sys.argv:
    run("build_bib.py", MANU, BIB, MAP)
    run("clean_bib.py", BIB)

run("prep_md.py", MANU, MAP, BODY_MD)
run("md2tex.py", BODY_MD, BODY_TEX)
run("wrap_tex.py", BODY_TEX, TEX)
run("verify_tex.py", BODY_MD, BODY_TEX)
run("check_cites.py", TEX, MAP)
run("lint_tex.py", TEX, ROOT)

for f in (BODY_MD, BODY_TEX):
    if os.path.exists(f):
        os.remove(f)

print(f"\nmain.tex rebuilt. To produce the PDF (needs a TeX distribution):")
print("  cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main")
