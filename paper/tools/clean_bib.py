"""Repair publisher BibTeX quirks.

Springer's record for Mueller & Brown (1979) carries a bad byte where the
umlaut should be, which arrives as U+FFFD. Page ranges also come back with
Unicode en-dashes, which BibTeX wants as '--'.
"""
import io, sys

P = sys.argv[1]
t = io.open(P, encoding="utf-8").read()

before_fffd = t.count("�")
t = t.replace("M�ller, Klaus", 'M{\\"u}ller, Klaus')

before_dash = t.count("–")
t = t.replace("–", "--")

io.open(P, "w", encoding="utf-8", newline="\n").write(t)
print(f"replacement chars fixed : {before_fffd - t.count(chr(0xFFFD))}")
print(f"en-dashes normalised    : {before_dash}")
print(f"remaining U+FFFD        : {t.count(chr(0xFFFD))}")
