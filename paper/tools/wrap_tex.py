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
\hypersetup{
  pdftitle={How Many Metastable States Did You Actually Find? Sampling Budget as a Confound},
  pdfauthor={Jaiveer Bassi},
  pdfsubject={Sampling-budget sensitivity of component counts in molecular-simulation embeddings},
  pdfkeywords={molecular dynamics, dimensionality reduction, Gaussian mixtures, model selection, sampling budget}
}

% ORCID badge next to the author name. orcidlink draws the official mark and
% hyperlinks it; the fallback keeps the paper compilable on a TeX installation
% that does not have the package, since a missing logo should not stop a build.
\IfFileExists{orcidlink.sty}{\usepackage{orcidlink}}{%
  \newcommand{\orcidlink}[1]{}%
}

\captionsetup{font=small,labelfont=bf}
\setlength{\tabcolsep}{4pt}

\newcommand{\ORCID}{0009-0006-3633-3220}

\title{\textbf{How Many Metastable States Did You Actually Find?\\
\large Sampling Budget as a Confound in Dimensionality-Reduction Analyses of
Molecular Simulation}}

\author{Jaiveer Bassi\,\orcidlink{\ORCID} \\
Independent Researcher, USA \\
\texttt{jaiveerbassi@yahoo.com} \\
{\footnotesize ORCID: \href{https://orcid.org/\ORCID}{\ORCID}}}
\date{}

\begin{document}
\maketitle
"""

POST = r"""
\section*{Data availability}

All result files underlying every number and figure in this paper are in the
accompanying GitHub repository
\href{https://github.com/imjbassi/state-count-sampling-bias}{\texttt{state-count-sampling-bias}},
under \texttt{results/}: \texttt{sweep.csv} and \texttt{sweep\_prinz.csv} (960
conditions each), \texttt{alanine\_sweep\_100ns.csv} (480 conditions),
\texttt{alanine\_sweep\_100ns\_seed1.csv} (432 conditions),
\texttt{tica\_lag\_ablation.csv} (300 conditions) and
\texttt{dim\_ablation.csv} (540 conditions), and
\texttt{iid\_equilibrium\_control.csv} (160 conditions). The superseded 5~ns alanine pilot
sweeps are retained in the same directory for provenance and are identified as
such in \texttt{results/NOTE.md}. The alanine starting structure, complete
simulation protocol, random-seed controls and derived result tables are
included. The exact production trajectories are not currently archived in the
repository because each DCD is about 28.8~MB. Both exact 100~ns production
trajectories, their matching 50,000,000-step logs, the topology, locked
environments, result tables, analysis-source snapshot and SHA-256 manifest are
preserved in the versioned Zenodo dataset at the all-versions DOI
\url{https://doi.org/10.5281/zenodo.22754433}. An independent replay of all 480
seed-0 conditions matched every scientific result column exactly; only
machine-runtime timing was excluded. Rerunning molecular dynamics reproduces
the protocol but is not expected to produce bitwise-identical trajectories
across hardware and software stacks.

\section*{Code availability}

All code is in the same repository under the MIT License. \texttt{run\_all.sh}
writes a fresh, non-resuming reproduction to a separate output directory and
includes the synthetic sweeps and registered ablations; \texttt{src/alanine.py} runs the
molecular dynamics and its sweep; \texttt{src/figures.py} and
\texttt{src/figures\_alanine.py} regenerate every figure from the result CSVs.

\section*{Competing interests}

The author declares no competing interests.

\section*{Funding}

This research received no external funding.

\section*{Author contributions}

Jaiveer Bassi: conceptualization, methodology, software, formal analysis,
investigation, visualization, writing---original draft, and writing---review
and editing.

\section*{Use of AI tools}

OpenAI ChatGPT and Codex were used to assist with manuscript editing,
consistency checking, software review, statistical cross-checking, and LaTeX
build troubleshooting. The author independently reviewed and takes
responsibility for the scientific reasoning, computations, references, and
final text.

\bibliographystyle{unsrt}
\bibliography{refs}

\end{document}
"""

io.open(OUT, "w", encoding="utf-8", newline="\n").write(PRE + "\n" + body + POST)
print(f"wrote {OUT}")
