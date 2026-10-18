#!/usr/bin/env python3
"""Rubric-based ATS score for a resume PDF.

Two layers:
  1. Parse simulation - reads the PDF with pdfminer.six (the library several
     resume parsers/ATS front-ends use) and reports what a machine can see.
  2. Weighted rubric   - 8 axes, 100 points total.

Keyword axis is scored against the hard-skill set of a QA Automation Engineer
JD (QEdge "QA Automation Engineer - Selenium" posting + Vodafone VOIS posting)
intersected with what the candidate can legitimately claim. JD skills the
candidate does not claim are reported separately as gaps and are not scored.
"""
import re
import sys
import json
from collections import OrderedDict

from pypdf import PdfReader
from pdfminer.high_level import extract_text as pdfminer_text

# ---------------------------------------------------------------- keyword set
# (pattern, weight, label) - weight 3 core, 2 high, 1 supporting
KEYWORDS = [
    (r"selenium", 3, "Selenium"),
    (r"\bjava\b", 3, "Java"),
    (r"testng", 3, "TestNG"),
    (r"automation (?:test )?framework|hybrid framework|framework design", 3, "Automation framework"),
    (r"ci/cd|continuous integration", 3, "CI/CD"),
    (r"api testing", 3, "API testing"),
    (r"manual testing", 3, "Manual testing"),
    (r"test cases?", 3, "Test cases"),
    (r"test plans?", 3, "Test plans"),
    (r"regression testing", 3, "Regression testing"),
    (r"\bagile\b", 3, "Agile"),
    (r"\bscrum\b", 3, "Scrum"),
    (r"\bjira\b", 3, "JIRA"),
    (r"\bgit\b|github", 3, "Git/GitHub"),
    (r"appium", 2, "Appium"),
    (r"\bmaven\b", 2, "Maven"),
    (r"postman", 2, "Postman"),
    (r"page object model|\bpom\b", 2, "Page Object Model"),
    (r"jenkins", 2, "Jenkins"),
    (r"mobile (?:application |app )?testing|apk|\bios\b", 2, "Mobile testing (APK/iOS)"),
    (r"functional testing", 2, "Functional testing"),
    (r"smoke testing", 2, "Smoke testing"),
    (r"sanity testing", 2, "Sanity testing"),
    (r"integration testing", 2, "Integration testing"),
    (r"\bsql\b|mysql", 2, "SQL/MySQL"),
    (r"xpath", 2, "XPath"),
    (r"css (?:selector|expression)", 2, "CSS selectors"),
    (r"defect|bug", 2, "Defect reporting"),
    (r"compatibilit", 2, "Cross-browser/compatibility testing"),
    (r"accessibilit", 2, "Accessibility testing"),
    (r"script", 2, "Test script development"),
    (r"test case design|writing test cases|test case preparation", 1, "Test case design"),
    (r"\bstlc\b|software testing life cycle|\bsdlc\b", 1, "STLC/SDLC"),
    (r"sprint", 1, "Sprint planning"),
    (r"requirement (?:analysis|gathering)", 1, "Requirement analysis"),
    (r"test (?:strategy|report|summary|documentation)", 1, "Test strategy/reporting"),
    (r"e-?commerce", 1, "E-commerce domain"),
    (r"healthcare", 1, "Healthcare domain"),
    (r"ms ?excel|excel", 1, "MS Excel"),
    (r"traceability", 1, "Traceability matrix"),
    (r"playwright", 2, "Playwright"),
    (r"typescript", 1, "TypeScript"),
    (r"github actions", 1, "GitHub Actions"),
    (r"quality assurance|\bqa\b", 1, "Quality assurance"),
]

# JD skills the candidate does not claim anywhere in their own materials
JD_GAPS = ["Cucumber/BDD", "REST Assured", "JUnit", "TestRail/Zephyr", "Allure/Extent Reports",
           "Sauce Labs/BrowserStack/LambdaTest", "JMeter/Locust", "Docker", "GitLab CI",
           "ISTQB certification", "JavaScript", "Python"]

ACTION_VERBS = ["design", "develop", "execute", "maintain", "collaborat", "integrat", "create",
                "enhance", "perform", "participat", "identif", "report", "troubleshoot",
                "validate", "verify", "track", "write", "build", "manage", "conduct", "prepare",
                "analyze", "document", "review", "ensure", "log", "record", "own", "lead", "drive",
                "test", "cover", "script", "automate"]

STANDARD_HEADINGS = ["summary", "professional summary", "skills", "technical skills",
                     "experience", "work experience", "professional experience",
                     "projects", "project experience", "education", "certifications",
                     "languages", "personal details"]

CONTACT_PATTERNS = OrderedDict([
    ("email", r"[\w.+-]+@[\w-]+\.[\w.]+"),
    ("phone", r"\+?\d[\d\s-]{8,}\d"),
    ("linkedin", r"linkedin\.com/\S+"),
    ("github", r"github\.com/\S+"),
])

BULLET_RE = r"^[-*\u2022\u2013\u2014]+\s"
BULLET_STRIP = " -*\u2022\u2013\u2014\u00a0"
DATE_RE = re.compile(r"(?:0?[1-9]|1[0-2])/\d{4}|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}|\b\d{4}\b", re.I)
DATE_PAIR_RE = re.compile(r"((?:0?[1-9]|1[0-2])/\d{4}|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4})\s*[-–to]+\s*((?:0?[1-9]|1[0-2])/\d{4}|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}|present|current)", re.I)


def pdf_facts(pdf_path):
    r = PdfReader(pdf_path)
    page_imgs = 0
    fonts = set()
    for p in r.pages:
        res = p.get("/Resources", {})
        xo = res.get("/XObject") or {}
        for k, v in xo.items():
            try:
                if v.get_object().get("/Subtype") == "/Image":
                    page_imgs += 1
            except Exception:
                pass
        for f in (res.get("/Font") or {}):
            fonts.add(str(f))
    return len(r.pages), page_imgs, fonts


def score(pdf_path, verbose=True):
    text_pypdf = "\n".join(p.extract_text() or "" for p in PdfReader(pdf_path).pages)
    text_pm = pdfminer_text(pdf_path)
    text = text_pypdf if len(text_pypdf.strip()) > len(text_pm.strip()) else text_pm
    low = re.sub(r"\s+", " ", text).lower()
    low_lines = re.sub(r"\s+", " ", text).lower()  # ATS normalizers collapse newlines before phrase matching
    pages, images, fonts = pdf_facts(pdf_path)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    res = OrderedDict()

    # 1. parseability (15)
    p = 15.0
    notes = []
    if len(text.strip()) < 200:
        p -= 8; notes.append("little/no extractable text")
    if images:
        p -= min(6, images * 3); notes.append(f"{images} image object(s) on page")
    if len(fonts) > 6:
        p -= 1.5; notes.append(f"{len(fonts)} distinct font objects (possible columns/design text runs)")
    pipe_lines = [l for l in lines if "|" in l]
    if len(pipe_lines) >= 5 or "\t" in text:
        p -= 1.0; notes.append(f"table-like separators ({len(pipe_lines)} lines containing '|')")
    if not fonts:
        p -= 3; notes.append("no embedded fonts (text may be outlined/vector)")
    if re.search(r"^\s*\d\s*$", text, re.M):
        pass
    if not re.search(r"[-*\u2022\u2013\u2014]", text):
        p -= 1; notes.append("no standard bullet glyphs")
    res["Parseability & file structure (15)"] = (max(0, p), notes or ["clean: text layer, no images, no tables"])

    # 2. contact & identity (10)
    p = 0
    notes = []
    for name, pat in CONTACT_PATTERNS.items():
        if re.search(pat, low):
            p += 2
        else:
            notes.append(f"missing {name}")
    first_line = lines[0] if lines else ""
    if re.match(r"^[A-Z][A-Za-z.]*(\s+[A-Z][A-Za-z.]*){1,3}$", first_line):
        p += 2
    else:
        notes.append("name not the first line of the body text")
    if re.search(r"qa automation engineer", low):
        p += 0  # informational only
    res["Contact & identity fields (10)"] = (p, notes or ["name, email, phone, LinkedIn, GitHub all in body text"])

    # 3. standard section headings (10)
    groups = OrderedDict([
        ("summary", r"professional summary|^summary\b|\bsummary\b"),
        ("skills", r"technical skills|\bskills\b"),
        ("experience", r"professional experience|work experience|\bexperience\b"),
        ("projects", r"^projects\b|\bproject experience\b|\bprojects\b"),
        ("education", r"\beducation\b"),
        ("certifications", r"\bcertifications?\b|\bcertificates?\b"),
        ("languages", r"\blanguages?\b"),
    ])
    optional = {"personal": r"\bpersonal details\b|\bpersonal information\b"}
    hit = [k for k, pat in groups.items() if re.search(pat, low, re.M)]
    opt_hit = [k for k, pat in optional.items() if re.search(pat, low, re.M)]
    p = round(10 * len(hit) / len(groups), 2)
    notes = [f"missing heading: {k}" for k in groups if k not in hit]
    if not notes:
        notes = [f"all {len(groups)} scored headings present" + (f" (+{len(opt_hit)} optional)" if opt_hit else "")]
    res["Standard section headings (10)"] = (p, notes)

    # 4. dates & chronology (10)
    pairs = DATE_PAIR_RE.findall(text)
    dense_dates = len(DATE_RE.findall(text))
    p = 0.0
    notes = []
    if pairs:
        p += 6
    else:
        notes.append("no parseable start-end date ranges found")
    if re.search(r"present|current", low) and pairs:
        p += 2
    else:
        notes.append("no 'Present' role")
    if dense_dates >= 3:
        p += 2
    else:
        notes.append("few dates overall")
    fmts = set()
    for a, b in pairs:
        fmts.add("mon-yyyy" if re.match(r"[a-z]", a, re.I) else "mm/yyyy")
    if len(fmts) > 1:
        p -= 1; notes.append(f"mixed date formats: {sorted(fmts)}")
    res["Dates, chronology & tenure (10)"] = (p, notes or [f"{len(pairs)} date range(s) parsed, 'Present' role present"])

    # 5. experience completeness (10)
    roles = len(pairs)
    bullets = len([l for l in lines if re.match(BULLET_RE, l)])
    p = 0.0
    notes = []
    p += min(6, roles * 3)
    if roles == 0:
        notes.append("no role with dates detected")
    p += min(4, bullets / 4)
    if bullets < 8:
        notes.append(f"only {bullets} bullet lines")
    res["Experience section completeness (10)"] = (round(min(10, p), 2),
                                                    notes or [f"{roles} dated role(s), {bullets} bullets"])

    # 6. keyword coverage (30)
    got = gotw = totw = 0
    matched, missing = [], []
    for pat, w, label in KEYWORDS:
        totw += w
        if re.search(pat, low):
            gotw += w; matched.append(label)
        else:
            missing.append(label)
    p = round(30 * gotw / totw, 2)
    res["Hard-skill keyword coverage (30)"] = (p, [f"missing: {', '.join(missing)}"] if missing else ["full coverage of the JD skill set"])

    # 7. impact / action language (10)
    bl = [l for l in lines if re.match(BULLET_RE, l)]
    started = sum(1 for b in bl if any(b.lower().lstrip(BULLET_STRIP).startswith(v) for v in ACTION_VERBS))
    p = 0.0
    notes = []
    if bl:
        p += 6 * started / len(bl)
        if started < len(bl):
            notes.append(f"{len(bl)-started}/{len(bl)} bullets do not open with a strong action verb")
    else:
        notes.append("no bullets")
    if re.search(r"\bi\b|\bmy\b", low):
        p -= 1; notes.append("first-person pronouns present")
    scope = len(re.findall(r"hybrid|end-to-end|across|multiple|each|all modules|functional, integration", low))
    p += min(4, scope)
    res["Impact & action-verb language (10)"] = (round(max(0, min(10, p)), 2), notes or ["all bullets lead with action verbs"])

    # 8. education / certifications / projects (5)
    p = 0.0
    notes = []
    if re.search(r"bachelor", low): p += 2
    else: notes.append("no degree")
    if re.search(r"university|college|institute", low): p += 1
    else: notes.append("no institution")
    if re.search(r"certification|certificate", low): p += 1
    else: notes.append("no certifications section")
    if re.search(r"^projects?|project experience", text, re.M | re.I): p += 1
    else: notes.append("no projects section")
    res["Education, certifications & projects (5)"] = (p, notes or ["degree, institution, certifications and projects all present"])

    total = round(sum(v[0] for v in res.values()), 2)
    if verbose:
        print(f"===== ATS score: {pdf_path}")
        print(f"pages={pages} images={images} fonts={len(fonts)} text_chars={len(text.strip())} "
              f"date_ranges={len(pairs)} bullets={bullets}")
        for k, (v, n) in res.items():
            print(f"  {v:6.2f}  {k}")
            for x in n[:6]:
                print(f"          - {x}")
        print(f"  ------")
        print(f"  {total:6.2f}  TOTAL (out of 100)")
        print(f"  matched keywords ({len(matched)}): {', '.join(matched)}")
        all_missing = [l for _, _, l in KEYWORDS if l in missing]
        print(f"  missing keywords ({len(all_missing)}): {', '.join(all_missing)}")
        print(f"  JD skills not claimed anywhere (not scored): {', '.join(JD_GAPS)}")
    return total, res


if __name__ == "__main__":
    for f in sys.argv[1:]:
        score(f)
        print()
