# Resume — Waseem Raza, QA Automation Engineer

LaTeX source and PDF build of the one-page ATS resume for **Waseem Raza** (QA Automation Engineer, New Delhi, India), plus the plain-text mirror, the reproducible ATS scorer, and the NotebookLM slide-deck prompt for the same content.

## Files

| File | Purpose |
| --- | --- |
| `resume.tex` | Primary ATS build: single column, no graphics/tables/columns, plain-text contact block with visible LinkedIn/GitHub URLs (also hyperlinked). Includes Projects, Certifications and a Personal Details section (date of birth, nationality, marital status) as in the source resume. |
| `resume_v2.tex` | Variant build for application portals that strip hyperlinks and penalise personal data: same content, contact details as unlinked plain text, and no Personal Details section. |
| `resume.pdf`, `resume_v2.pdf` | Compiled PDFs, one page each (build outputs, regenerate with `pdflatex`). |
| `pdf_content.txt` | Plain-text mirror of the resume, in layout order, for pasting into portals that ask for resume text. |
| `ats_score.py` | Reproducible ATS scorer: parses the PDF (pypdf + pdfminer.six), then scores 8 weighted axes out of 100. |
| `NoteboolLmPrompt.md` | Prompt fed to NotebookLM to generate the 12-slide deck of the same resume. |

## ATS score

```
python3 ats_score.py resume.pdf resume_v2.pdf      # needs pypdf + pdfminer.six
```

| Axis | Weight | Before | After (`resume`) | After (`resume_v2`) |
| --- | --- | --- | --- | --- |
| Parseability & file structure | 15 | 15.00 | 15.00 | 15.00 |
| Contact & identity fields | 10 | 6.00 | 10.00 | 10.00 |
| Standard section headings | 10 | 7.14 | 10.00 | 8.57 |
| Dates, chronology & tenure | 10 | 10.00 | 10.00 | 10.00 |
| Experience section completeness | 10 | 9.00 | 10.00 | 10.00 |
| Hard-skill keyword coverage | 30 | 18.84 | 29.65 | 29.65 |
| Impact & action-verb language | 10 | 5.50 | 10.00 | 10.00 |
| Education, certifications & projects | 5 | 3.00 | 5.00 | 5.00 |
| **Total** | **100** | **74.48** | **99.65** | **98.22** |

`resume_v2` scores lower only because its Personal Details section is absent (the Languages line lives there) — a deliberate trade-off for portals that reject personal data.

How the score is produced — and what it is not:

- It is a **documented rubric plus a real parser** (`pdfminer.six`, the library several resume parsers are built on), not a vendor score such as Jobscan's. The number is reproducible from the script in this repository.
- The keyword axis is weighted against the hard-skill set of a real QA-automation posting (QEdge "QA Automation Engineer – Selenium", plus the Vodafone VOIS QA-automation posting) and **only scores skills the candidate can legitimately claim**. JD skills the candidate does not claim anywhere (Cucumber/BDD, REST Assured, JUnit, TestRail/Zephyr, Allure/Extent Reports, Sauce Labs/BrowserStack, JMeter, Docker, GitLab CI, GitHub Actions, ISTQB, Python, JavaScript) are reported as gaps and excluded from scoring rather than being claimed.
- No numeric-achievement axis is scored: neither source resume contains a metric, and inventing one would be fabrication. Impact is scored through action-verb density and explicit responsibility scope.
- Formatting rules enforced in the `.tex` (and rewarded by the parse axis): single column, no tables or images, contact details in body text, conventional section headings, `Mon YYYY` date ranges, en-dash bullets, and `\DisableLigatures` so that "fi"/"ff" ligatures never extract as `U+FB01` and break keyword matching.

## Content provenance

Both source documents are the candidate's own: a **scanned one-page PDF with no extractable text layer** (`Resume.pdf`) and an earlier **text-rendered export** (`WaseemRazaResume17stSep.pdf`). Every value below was recovered from those documents by OCR (two engines) plus pixel/ink analysis, and cross-checked against public data wherever a pixel-level read was ambiguous:

- Email `waseem.razain@gmail.com` and employer `DigiExcel Pvt Ltd` — confirmed from the GitHub account [raza-automation](https://github.com/raza-automation) commit metadata and profile.
- Employer `i3Infosoft` (Noida, India) — confirmed against the company's own website.
- Name, title, email, phone, LinkedIn URL (`linkedin.com/in/waseem-raza-in`), GitHub URL and the education block — independently confirmed by both source documents.
- Projects: the **TP-Link (B2B) loyalty platform** entry covers the live application the candidate tests (`https://tp-link-v2.apps.dgexcel.cloud/`, a DigiExcel-hosted partner portal for TP-Link India Pvt. Ltd.). Every module, role and validation surface named in that entry is one the shipped app actually exposes: partner registration with dependent state/city dropdowns and PAN/GSTIN/pincode fields, the scheme–rebate–claim routes (`schemes/participants`, `claims/.../submit`, `rebate-programs/.../targets`, `.../upload-sales`), the partner/sales-person/RSM/admin roles with admin MFA setup and audit logs, the push (OneSignal)/WhatsApp/email notification channels, the sales-trend, product-performance, city-wise and vertical-wise reports, and the mobile-first PWA shell. The **Pharmacy Website** project, the tool lists (`Java, Selenium, TestNG, Maven, Postman, MySQL, JIRA, MS Excel`), the certifications and the additional skills come from the earlier export and describe the same employers.

No employment, education, certification, tool or metric appears in these files that is not present in one of the two source documents, and no figure was invented to raise the score.

One deliberate omission: the earlier export lists a `Sr. Representative, Operations — Concentrix Daksh Services India Private Limited (2013 – 2022)` role alongside a `2013 – 2019` gap, while the current scan lists `i3Infosoft (Aug 2019 – Jun 2022)`. Both cannot be presented as-is without a contradiction, so the Concentrix entry is left out pending confirmation of the true employment history.

## Building the PDF

Requires a LaTeX distribution with `pdflatex` (TeX Live base + recommended packages are enough).

```bash
pdflatex -interaction=nonstopmode -halt-on-error resume.tex
pdflatex -interaction=nonstopmode -halt-on-error resume_v2.tex
```

Both compile in a single pass and must produce **one-page** PDFs. See `WALKTHROUGH.md` for the exact package list and the WSL/Ubuntu install path.

## Overleaf

1. Create a new project in Overleaf.
2. Upload `resume.tex` (and `resume_v2.tex` if you want both variants).
3. Click **Recompile** and download the generated PDF.

## Credits

The ATS-oriented `article`-class layout (the `\sectionheader` / `\jobentry` macros) is inherited from the MIT-licensed [dphang/resume](https://github.com/dphang/resume) template.
