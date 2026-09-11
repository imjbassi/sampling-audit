"""Wrap the converted body in a complete, compilable main.tex."""
import io, sys

BODY, OUT = sys.argv[1], sys.argv[2]
body = io.open(BODY, encoding="utf-8").read()

PRE = r"""% Generated from paper/manuscript.md -- edit the markdown, then re-run
% the conversion, or adopt this file as the source of truth and retire the
% markdown. Do not edit both.
\documentclass[twocolumn]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{graphicx}
% main.tex lives in paper/, the figure directories live at the repository root
\graphicspath{{../}}
\usepackage{natbib}
\usepackage{times}
\usepackage{url}
\usepackage[margin=0.75in]{geometry}
\usepackage{caption}
\usepackage{booktabs}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage[hidelinks]{hyperref}

\captionsetup{font=small,labelfont=bf}
\setlength{\tabcolsep}{4pt}

\title{\textbf{How Many Metastable States Did You Actually Find?\\
\large Sampling Budget as a Confound in Dimensionality-Reduction Analyses of
Molecular Simulation}}

\author{Jaiveer Bassi \\
College of Science, Engineering, and Technology \\
Grand Canyon University, Phoenix, Arizona, USA \\
\texttt{jaiveerbassi@yahoo.com}}
\date{}

\begin{document}
\maketitle
"""

POST = r"""
\section*{Data availability}

All result files underlying every number and figure in this paper are in the
accompanying repository at \url{https://github.com/imjbassi/sampling-audit},
under \texttt{results/}: \texttt{sweep.csv} and \texttt{sweep\_prinz.csv} (960
conditions each), \texttt{alanine\_sweep\_100ns.csv} (480 conditions),
\texttt{tica\_lag\_ablation.csv} (300 conditions) and
\texttt{dim\_ablation.csv} (540 conditions). The superseded 5~ns alanine pilot
sweeps are retained in the same directory for provenance and are identified as
such in \texttt{results/NOTE.md}. Raw trajectories are not distributed because
they are large and exactly reproducible from the simulation script; the
alanine dipeptide starting structure is included.

\section*{Code availability}

All code is in the same repository under the MIT License. \texttt{run\_all.sh}
reproduces the synthetic sweeps end to end; \texttt{src/alanine.py} runs the
molecular dynamics and its sweep; \texttt{src/figures.py} and
\texttt{src/figures\_alanine.py} regenerate every figure from the result CSVs.

\section*{Competing interests}

The author declares no competing interests.

\bibliographystyle{unsrt}
\bibliography{refs}

\end{document}
"""

io.open(OUT, "w", encoding="utf-8", newline="\n").write(PRE + "\n" + body + POST)
print(f"wrote {OUT}")
