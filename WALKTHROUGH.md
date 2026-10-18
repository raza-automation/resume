# Resume PDF Generation Walkthrough

How to compile `resume.tex` and `resume_v2.tex` into PDFs, including the package set that is actually required and the failure modes seen on a minimal TeX Live install.

## Required packages

Both documents use a deliberately tiny, ATS-friendly package set:

| Package | Used for | Debian/Ubuntu package |
| --- | --- | --- |
| `geometry` | page margins (0.45 in) | `texlive-latex-base` |
| `hyperref` | clickable email/URL links (`hidelinks` — no coloured boxes) | `texlive-latex-recommended` |
| `microtype` | `\DisableLigatures` — see *ATS-specific settings* below | `texlive-latex-recommended` |
| `enumitem` | en-dash bullet label and list spacing | `texlive-latex-extra` |

`hyperref` pulls in `letltxmacro` (also `texlive-latex-extra` on older releases), so a TeX Live install that stops at `texlive-latex-base` fails on `enumitem.sty` first and on `letltxmacro.sty` second. Installing `texlive-latex-extra` resolves both.

## ATS-specific settings

These are the parts of the preamble that exist purely for machine parsing. Changing them changes the ATS score, and some of them change the page count.

| Setting | Why |
| --- | --- |
| `\usepackage{microtype}` + `\DisableLigatures{encoding = OT1, family = *}` | In OT1, `fi`/`ff`/`ffl` are single font glyphs that PDF text extraction returns as `U+FB01`/`U+FB00`, so "Certifications", "findings" or "identifying" stop matching the plain ASCII keywords an ATS looks for. Disabling ligatures restores plain `f`+`i` in the extracted text while looking identical in print. Side effect: `--` no longer becomes an en dash, which is why bullets are set with `label={\textendash}` and date ranges with `\textendash`. |
| Contact block as body text | Location, email, phone, LinkedIn and GitHub are ordinary text lines, not a header/footer or text box, and the LinkedIn/GitHub URLs are printed as visible text so a parser that ignores link annotations still sees them. |
| `margin=0.45in`, `itemsep=0pt`, `\sectionheader` at `\normalsize` | Fits the full content (summary, six skill groups, both roles, two projects, education, certifications, personal details) onto **one page**. Loosening any of them spills the tail sections onto a second page. |
| Conventional headings | `Professional Summary`, `Technical Skills`, `Professional Experience`, `Projects`, `Education`, `Certifications`, `Personal Details` — the exact strings ATS section mapping expects. |

Verify the result after any change:

```bash
python3 ats_score.py resume.pdf resume_v2.pdf   # parses the PDF and prints the 8-axis score
pdfinfo resume.pdf | grep Pages                 # must stay at 1
```



```bash
# one-time setup (Ubuntu 20.04 verified)
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended

# build
pdflatex -interaction=nonstopmode -halt-on-error resume.tex
pdflatex -interaction=nonstopmode -halt-on-error resume_v2.tex
```

Each document compiles in a single pass — there is no bibliography, cross-reference, or index. Expected result: exit status `0` and one-page PDFs.

If `enumitem.sty` is reported missing and installing `texlive-latex-extra` is not an option, drop the single style file into your user tree instead:

```bash
mkdir -p ~/texmf/tex/latex/enumitem
curl -L -o ~/texmf/tex/latex/enumitem/enumitem.sty \
  https://mirrors.ctan.org/macros/latex/contrib/enumitem/enumitem.sty
texhash ~/texmf   # optional; kpathsea picks up ~/texmf automatically
```

Note that the `enumitem` on CTAN also needs `letltxmacro.sty` (oberdiek bundle) when `hyperref` is loaded.

## Build on Windows (MiKTeX or TeX Live)

```powershell
pdflatex -interaction=nonstopmode -halt-on-error resume.tex
pdflatex -interaction=nonstopmode -halt-on-error resume_v2.tex
```

MiKTeX installs missing packages on demand; TeX Live users should run `tlmgr install enumitem letltxmacro`.

## Keeping the source files out of the build directory

`pdflatex` writes `resume.aux`, `resume.log`, and `resume.out` next to the source. These are throwaway build artifacts — delete them (or compile with `-output-directory=build`) before committing.

## Alternative: Overleaf

1. Go to https://www.overleaf.com and create a free account.
2. Create a new project and upload `resume.tex` (and `resume_v2.tex`).
3. Click **Recompile** to generate the PDF and download it.

Overleaf ships a full TeX Live, so no package installation is needed there.

## CI

`.github/workflows/build-resume.yml` compiles both documents with `xu-cheng/latex-action` on every push to `master`/`main` that touches a `.tex` file, renames the outputs to `Waseem_Raza_Resume.pdf` / `Waseem_Raza_Resume_v2.pdf`, uploads them as artifacts, and commits them back to the repository on pushes to `master`. Tagging a release attaches both PDFs to the release.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `File 'enumitem.sty' not found` | base TeX Live only | install `texlive-latex-extra` (or the single CTAN file) |
| `File 'letltxmacro.sty' not found` | `hyperref` dependency not installed | install `texlive-latex-extra` |
| `pdflatex: command not found` | no TeX distribution on `PATH` | install TeX Live/MiKTeX, or compile on Overleaf |
| PDF missing links | `hyperref` not loaded or driver mismatch | keep `\usepackage[hidelinks]{hyperref}` and compile with `pdflatex` |
| Resume spills onto a second page | content grew or spacing was loosened | tighten `margin`, `\sectionheader` `\vspace`, or `itemsep`; or drop the weakest bullet — verify with `pdfinfo resume.pdf` |
| ATS cannot match "Certifications"/"identifying" | `fi`/`ff` ligature glyphs (`U+FB01`) in the extracted text | keep `microtype` + `\DisableLigatures{encoding = OT1, family = *}` in the preamble |
| Bullets extract as `--` instead of `–` | `\DisableLigatures` also disables the OT1 `--` ligature | keep `label={\textendash}` in `\setlist[itemize]` |
