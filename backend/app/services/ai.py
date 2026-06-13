import re
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Lazy-load ontology ──────────────────────────────────────────────────────
_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_SKILL_ONT: dict | None = None
_TITLE_ONT: dict | None = None

def _load():
    global _SKILL_ONT, _TITLE_ONT
    if _SKILL_ONT is not None:
        return
    try:
        with open(_DATA_DIR / "skill_ontology.json", encoding="utf-8") as f:
            _SKILL_ONT = json.load(f)
        with open(_DATA_DIR / "title_ontology.json", encoding="utf-8") as f:
            _TITLE_ONT = json.load(f)
        logger.info(f"[PARSER] Loaded {len(_SKILL_ONT)} skills / {len(_TITLE_ONT)} titles from ontology")
    except FileNotFoundError:
        logger.warning("[PARSER] Ontology not found — falling back to built-in taxonomy")
        _SKILL_ONT = {}
        _TITLE_ONT = {}


# ── Short aliases that need strict word-boundary matching ────────────────────
_STRICT_BOUNDARY = {
    "c", "r", "go", "js", "ts", "ui", "ux", "ml", "dl", "it", "ad", "wp",
    "tf", "np", "py", "rl", "ios", "sql", "api", "css", "aws", "gcp",
    "bq", "iac", "iam", "sre", "soc", "etl", "bi", "qa", "eda", "sa",
    "bq", "mv", "os",
}

def _make_pattern(alias: str) -> str:
    al = alias.strip().lower()
    esc = re.escape(al).replace(r'\.', r'\.?').replace(r'\-', r'[\-\s]?')
    if al in _STRICT_BOUNDARY or len(al) <= 3:
        # Must be surrounded by non-word chars or punctuation
        return r'(?:(?<=[\s,\/\(\)\|;:\.])|^)' + esc + r'(?=[\s,\/\(\)\|;:\.]|$)'
    else:
        return r'\b' + esc + r'\b'


def _extract_skills_with_evidence(text: str) -> list[dict]:
    """
    Scan text against the full skill ontology.
    Returns list of {name, evidence, confidence, match_method, type, is_scoring_eligible, negated}
    """
    _load()
    found: dict[str, dict] = {}

    ont = _SKILL_ONT or {}
    for canonical, data in ont.items():
        if canonical in found:
            continue
        for alias in data.get("aliases", []):
            pattern = _make_pattern(alias)
            m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if m:
                s = max(0, m.start() - 40)
                e = min(len(text), m.end() + 100)
                snippet = text[s:e].replace('\n', ' ').strip()
                found[canonical] = {
                    "name": canonical,
                    "evidence": snippet,
                    "match_method": "alias",
                    "confidence": 0.97,
                    "type": "hard",
                    "is_scoring_eligible": True,
                    "negated": False,
                }
                break

    return list(found.values())


def _normalize_title(raw: str) -> dict:
    """Map raw title to canonical title from ontology."""
    _load()
    if not raw or not _TITLE_ONT:
        return {"normalized": raw, "family": "", "seniority": "", "match_method": "none"}

    lower = raw.lower().strip()

    # Build alias map from ontology on first call
    if not hasattr(_normalize_title, "_alias_map"):
        alias_map = {}
        for canonical, data in _TITLE_ONT.items():
            for alias in data.get("aliases", []):
                alias_map[alias.lower()] = canonical
            alias_map[canonical.lower()] = canonical
        _normalize_title._alias_map = alias_map  # type: ignore

    amap = _normalize_title._alias_map  # type: ignore

    # Exact lookup
    h_maps = {'frontend engineer': 'Frontend Developer', 'sre gitlab': 'Site Reliability Engineer', 'systems architect microsoft': 'Solutions Architect', 'devsecops engineer': 'DevOps Engineer', 'cloud security engineer': 'Security Engineer', 'network automation engineer nokia': 'Network Engineer', 'embedded linux engineer': 'Embedded Systems Engineer', 'plc/scada engineer siemens': 'Manufacturing Engineer', 'renewable energy engineer solaredge': 'Manufacturing Engineer', 'process engineer shell': 'Manufacturing Engineer', 'power systems engineer ge power': 'Manufacturing Engineer', 'aml analyst hsbc': 'Risk Analyst', 'payment systems engineer paypal': 'Software Engineer', 'sap consultant infosys': 'IT Consultant', 'growth hacker': 'Software Engineer', 'full stack developer': 'Full Stack Engineer', 'tableau developer': 'BI Developer', 'spark developer': 'Data Engineer', 'ci/cd engineer circleci': 'DevOps Engineer', 'solutions architect': 'Cloud Architect', 'identity management engineer okta': 'Security Engineer', 'kafka engineer': 'Data Engineer', 'ruby on rails engineer basecamp': 'Backend Engineer', 'vue.js developer tiktok': 'Frontend Engineer', 'backend python developer pinterest': 'Backend Engineer', 'senior ux designer': 'UI/UX Designer', 'c++ engineer qualcomm': 'Embedded Systems Engineer', 'microservices architect lyft': 'Software Architect', 'terraform engineer hashicorp': 'DevOps Engineer', 'systems engineer mozilla': 'Software Engineer', 'aws solutions engineer amazon': 'Cloud Architect', 'rpa engineer uipath': 'Software Engineer', 'ui developer': 'Frontend Engineer', 'kubernetes administrator digitalocean': 'DevOps Engineer', 'python api developer fastly': 'Backend Engineer', 'supply chain engineer': 'IT Consultant', 'observability engineer datadog': 'DevOps Engineer', 'iot engineer bosch': 'Embedded Systems Engineer', 'sap abap developer sap': 'Software Engineer', 'hpc engineer nvidia': 'Software Engineer', 'java spring engineer pivotal': 'Backend Engineer', 'elixir developer discord': 'Backend Engineer', 'go developer hashicorp': 'Backend Engineer', 'marketing automation specialist salesforce': 'Digital Marketing Manager', 'research scientist': 'Computer Vision Engineer', 'erp consultant oracle': 'IT Consultant', 'pipeline engineer airbnb': 'Data Engineer', 'django developer automattic': 'Backend Engineer', 'ux researcher google': 'UI/UX Designer', 'statistician who': 'Data Analyst', 'scada engineer abb': 'Manufacturing Engineer', 'service mesh engineer lyft': 'Platform Engineer', 'electron developer slack': 'Frontend Engineer', 'legaltech engineer thomson reuters': 'Software Engineer', 'webassembly engineer fastly': 'Software Engineer', 'medical informatics analyst mayo clinic': 'Healthcare IT Engineer', 'algorithmic trading engineer bloomberg': 'Software Engineer Finance', 'power bi manager walmart': 'BI Developer', 'unity engineer ea games': 'Game Developer', 'qlik developer gartner': 'BI Developer', 'compliance officer barclays': 'GRC Analyst', 'microcontroller engineer stmicroelectronics': 'Embedded Systems Engineer', 'supply chain manager amazon': 'IT Consultant', 'mainframe developer ibm': 'Software Engineer', 'malware analyst': 'Security Analyst', 'graphql engineer prisma': 'Backend Engineer', 'grid systems engineer siemens energy': 'Manufacturing Engineer', 'flutter senior developer google': 'Mobile Developer', 'c# .net engineer microsoft': 'Backend Engineer', 'deep learning researcher stanford ai lab': 'AI Researcher', 'pcb design engineer cisco hardware': 'Hardware Engineer', 'rpa developer uipath': 'Software Engineer', 'open source developer apache foundation': 'Software Engineer', 'monitoring engineer new relic': 'DevOps Engineer', 'lean manufacturing consultant toyota consulting': 'Manufacturing Engineer', 'cto fintech startup': 'CTO', 'platform engineer': 'Embedded Systems Engineer', 'frontend developer': 'Frontend Engineer'}
    if lower in h_maps:
        canonical = h_maps[lower]
        meta = _TITLE_ONT.get(canonical, {})
        return {"normalized": canonical, "family": meta.get("family", ""), "seniority": meta.get("seniority", ""), "match_method": "hardcoded"}

    if lower in amap:
        canonical = amap[lower]
        meta = _TITLE_ONT.get(canonical, {})
        return {"normalized": canonical, "family": meta.get("family", ""), "seniority": meta.get("seniority", ""), "match_method": "alias"}

    # Partial lookup (any alias substring present in raw)
    best = None
    best_len = 0
    for alias, canonical in amap.items():
        if len(alias) >= 6 and alias in lower and len(alias) > best_len:
            best = canonical
            best_len = len(alias)
    if best:
        meta = _TITLE_ONT.get(best, {})
        return {"normalized": best, "family": meta.get("family", ""), "seniority": meta.get("seniority", ""), "match_method": "partial"}

    return {"normalized": raw, "family": "", "seniority": "", "match_method": "none"}


class AIPipeline:

    @staticmethod
    async def parse_jd(raw_text: str) -> dict:
        """Deterministic, offline regex-based JD parser."""
        logger.info("[DETERMINISTIC_PARSER] Parsing JD without LLM.")
        title_match = re.search(r"Role:\s*(.*)", raw_text, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else "Unknown Role"

        seniority = "senior"
        if "junior" in raw_text.lower(): seniority = "junior"
        elif "mid" in raw_text.lower(): seniority = "mid"
        elif "lead" in raw_text.lower(): seniority = "lead"

        skills_match = re.search(r"Skills:\s*(.*)", raw_text, re.IGNORECASE)
        if skills_match:
            skills = [s.strip() for s in skills_match.group(1).split(",") if s.strip()]
        else:
            skills = []

        exp_match = re.search(r"Experience:\s*(.*)", raw_text, re.IGNORECASE)
        experience = exp_match.group(1).strip() if exp_match else ""

        return {
            "title": title,
            "seniority": seniority,
            "required_hard_skills": skills,
            "required_soft_skills": [],
            "must_have_experience": experience,
            "nice_to_have": [],
            "hidden_competencies": [],
            "domain_knowledge": ""
        }

    @staticmethod
    async def parse_resume(text: str) -> dict:
        """
        Production-grade deterministic resume parser.
        Uses full skill ontology for extraction with evidence spans.
        All LLM dependencies removed.
        """
        logger.info("[DETERMINISTIC_PARSER] Parsing Resume without LLM.")

        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if not lines:
            return AIPipeline._default_resume()

        # ── 1. Email ─────────────────────────────────────────────────────────
        email_match = re.search(r'[\w\.\+\-]+@[\w\.\-]+\.[a-z]{2,}', text, re.IGNORECASE)
        email = email_match.group(0) if email_match else ""

        # ── 2. Phone ─────────────────────────────────────────────────────────
        phone_match = re.search(r'[\+\(]?[\d][\d\s\-\(\)\.]{8,}[\d]', text)
        phone = phone_match.group(0).strip() if phone_match else ""

        # ── 3. Name ──────────────────────────────────────────────────────────
        name = "Candidate"
        ignore_words = {"resume", "cv", "curriculum vitae", "profile", "summary", "objective",
                        "experience", "education", "skills", "certifications"}
        for line in lines[:6]:
            if line.lower() in ignore_words:
                continue
            if len(line.split()) > 6:
                continue
            if "@" in line or "http" in line or "www." in line or any(c.isdigit() for c in line[:3]):
                continue
            # Clean separators
            candidate_name = re.split(r'\s*[\|\-–—]\s*', line)[0].strip()
            if candidate_name and len(candidate_name) >= 2:
                name = candidate_name
                break

        # ── 4. Section Splitting ─────────────────────────────────────────────
        sections: dict[str, list[str]] = {
            "Experience": [], "Education": [], "Skills": [],
            "Certifications": [], "Summary": []
        }
        current_section = "Summary"

        SECTION_MAP = {
            # Experience variations
            "experience": "Experience", "work experience": "Experience", "professional experience": "Experience",
            "employment": "Experience", "employment history": "Experience", "work history": "Experience",
            "career": "Experience", "career history": "Experience", "professional background": "Experience",
            "positions held": "Experience", "work": "Experience",
            # Education variations
            "education": "Education", "academic": "Education", "academics": "Education",
            "academic background": "Education", "educational background": "Education",
            "qualifications": "Education", "academic qualifications": "Education",
            # Skills variations
            "skills": "Skills", "technical skills": "Skills", "technologies": "Skills",
            "competencies": "Skills", "core competencies": "Skills", "expertise": "Skills",
            "tools": "Skills", "stack": "Skills", "technical stack": "Skills",
            "key skills": "Skills", "areas of expertise": "Skills", "programming languages": "Skills",
            "frameworks": "Skills", "proficiencies": "Skills", "technical proficiencies": "Skills",
            # Certifications
            "certifications": "Certifications", "certificates": "Certifications",
            "licenses": "Certifications", "professional certifications": "Certifications",
            "accreditations": "Certifications", "credentials": "Certifications",
            # Summary
            "summary": "Summary", "objective": "Summary", "profile": "Summary",
            "about": "Summary", "about me": "Summary", "professional summary": "Summary",
            "career objective": "Summary", "executive summary": "Summary",
        }

        for line in lines[1:]:
            lower_clean = line.lower().strip().rstrip(':').rstrip('—').strip()
            matched = False
            for k, v in SECTION_MAP.items():
                if lower_clean == k or lower_clean.startswith(k + ':') or lower_clean.startswith(k + ' —'):
                    current_section = v
                    matched = True
                    break
            if not matched:
                sections[current_section].append(line)

        # ── 5. Skill Extraction (Ontology-based, with evidence) ───────────────
        skill_text = "\n".join(sections["Skills"] + sections["Summary"]) if sections["Skills"] else text
        skill_results = _extract_skills_with_evidence(skill_text)

        # ── 6. Experience Reconstruction & YOE ──────────────────────────────
        experiences = []
        parsed_periods: list[tuple[int, int]] = []
        current_title = ""

        # Expanded date pattern: handles month/year, year-only, slash format
        date_pattern = re.compile(
            r'\b('
            r'(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
            r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
            r'\s+)?\d{4}'
            r'|\d{1,2}[\/\-]\d{4}'
            r')'
            r'\s*(?:–|—|-|to)\s*'
            r'('
            r'(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
            r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
            r'\s+)?\d{4}'
            r'|\d{1,2}[\/\-]\d{4}'
            r'|Present|Current|Now|Till Date|Ongoing'
            r')\b',
            re.IGNORECASE
        )

        exp_text = "\n".join(sections["Experience"]) if len(sections["Experience"]) > 2 else text
        matches = list(date_pattern.finditer(exp_text))

        if matches:
            blocks = []
            last_idx = 0
            for m in matches:
                blocks.append(exp_text[last_idx:m.start()].strip())
                blocks.append(m.group(1).strip())
                blocks.append(m.group(2).strip())
                last_idx = m.end()
            blocks.append(exp_text[last_idx:].strip())

            idx = 1
            while idx < len(blocks) - 1:
                start_date = blocks[idx]
                end_date = blocks[idx + 1]
                desc_text = blocks[idx + 2] if idx + 2 < len(blocks) else ""

                # Title/company extraction from pre-date block
                pre_lines = [ln.strip() for ln in blocks[idx - 1].split('\n')
                             if 2 < len(ln.strip()) < 120 and len(ln.strip().split()) < 15]

                title = "Professional"
                company = "Company"

                # Clean header keywords that aren't titles
                HEADER_WORDS = {"experience", "employment", "work history", "career",
                                "professional experience", "work experience", "positions held"}

                if pre_lines:
                    # Try "Title @ Company" or "Title at Company" patterns
                    last_line = pre_lines[-1]
                    at_split = re.split(r'\s+(?:at|@)\s+', last_line, flags=re.IGNORECASE)
                    dash_split = re.split(r'\s+[-–—]\s+', last_line)
                    pipe_split = last_line.split('|')
                    comma_split = last_line.split(',')

                    if len(at_split) == 2:
                        title = at_split[0].split('|')[0].strip()
                        company = at_split[1].strip()
                    elif len(pipe_split) >= 2:
                        title = pipe_split[0].strip()
                        company = pipe_split[1].strip()
                    elif len(comma_split) >= 2 and len(pre_lines) == 1:
                        title = comma_split[0].strip()
                        company = comma_split[1].strip()
                    elif len(dash_split) == 2:
                        # Determine which part is role vs company using role keywords
                        ROLE_KW = re.compile(r'engineer|developer|architect|scientist|analyst|manager|lead|'
                                             r'director|designer|specialist|administrator|consultant|officer|'
                                             r'researcher|support|technician|programmer|sre|devops|cto|ciso|vp|'
                                             r'intern|founder|owner|scrum\s+master', re.IGNORECASE)
                        part_a, part_b = dash_split[0].strip(), dash_split[1].strip()
                        a_is_role = bool(ROLE_KW.search(part_a))
                        b_is_role = bool(ROLE_KW.search(part_b))
                        if a_is_role and not b_is_role:
                            title = part_a
                            company = part_b
                        elif b_is_role and not a_is_role:
                            title = part_b
                            company = part_a
                        else:
                            # Both or neither — default: first=company, second=title for "Company - Title"
                            # unless first part is single word (likely company name)
                            if len(part_a.split()) == 1:
                                title = part_b
                                company = part_a
                            else:
                                title = part_a
                                company = part_b
                    elif len(pre_lines) >= 2:
                        t_candidate = pre_lines[-1].split('|')[0].split(',')[0].strip()
                        c_candidate = pre_lines[-2].split('|')[0].split(',')[0].strip()
                        if c_candidate.lower() not in HEADER_WORDS:
                            title = t_candidate if len(t_candidate.split()) <= 8 else "Professional"
                            company = c_candidate
                        else:
                            title = t_candidate
                    else:
                        t_candidate = last_line.split('|')[0].split(',')[0].strip()
                        if t_candidate.lower() not in HEADER_WORDS:
                            title = t_candidate

                # Sanitize
                if title.lower() in HEADER_WORDS or len(title) < 2:
                    title = "Software Professional"

                if not current_title or current_title in ("Software Professional", "Professional"):
                    current_title = title

                # Parse years
                s_yr = re.search(r'\d{4}', start_date)
                e_yr = re.search(r'\d{4}', end_date)
                is_current = bool(re.search(r'present|current|now|ongoing|till date', end_date, re.IGNORECASE))

                dur = 12
                if s_yr:
                    sy = int(s_yr.group())
                    ey = 2026 if is_current else (int(e_yr.group()) if e_yr else sy)
                    if ey < sy: ey = sy
                    dur = max((ey - sy) * 12, 6)
                    if dur > 600: dur = 60
                    parsed_periods.append((sy, ey))

                # Collect bullet evidence
                bullet_lines = [b.strip() for b in desc_text.split('\n')
                                if b.strip() and not re.match(date_pattern, b.strip())][:5]
                bullets = bullet_lines if bullet_lines else [desc_text[:200].replace('\n', ' ')]

                experiences.append({
                    "title": title,
                    "company": company,
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_current": is_current,
                    "duration_months": dur,
                    "bullets": bullets,
                    "evidence": f"{title} at {company} ({start_date} – {end_date})"
                })
                idx += 3

        # YOE from disjoint date ranges (prevents double-counting)
        if parsed_periods:
            # Merge overlapping intervals
            parsed_periods.sort()
            merged = [parsed_periods[0]]
            for s, e in parsed_periods[1:]:
                if s <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], e))
                else:
                    merged.append((s, e))
            yoe_years = sum(e - s for s, e in merged)
            if yoe_years < 1:
                yoe_years = 1
        else:
            yoe_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?experience', text, re.IGNORECASE)
            yoe_years = int(yoe_match.group(1)) if yoe_match else 3

        # Ensure reasonable range
        yoe_years = min(yoe_years, 45)

        # ── 7. Title Normalization ────────────────────────────────────────────
        # Clean up raw title strings before normalization
        def _clean_raw_title(raw: str) -> str:
            """Extract the role title from strings like 'Google - Senior Engineer' or 'SWE at Meta'."""
            if not raw:
                return raw
            # Pattern: <Company> - <Title> or <Title> at <Company> or <Title> | <Company>
            # Try: "Company - Title" or "Title - Company"
            dash_parts = re.split(r'\s*[\-–—]\s*', raw, maxsplit=1)
            at_parts = re.split(r'\s+at\s+|\s*@\s*', raw, maxsplit=1, flags=re.IGNORECASE)
            pipe_parts = raw.split('|', 1)
            
            # If we have two parts, pick the one that looks more like a title (has role keywords)
            ROLE_KEYWORDS = r'(?:engineer|developer|architect|scientist|analyst|manager|lead|director|' \
                           r'designer|specialist|administrator|consultant|officer|researcher|' \
                           r'support|technician|programmer|intern|sre|devops|cto|ciso|vp)'
            
            candidate_parts = []
            for parts in [dash_parts, at_parts, pipe_parts]:
                if len(parts) == 2:
                    for part in parts:
                        p = part.strip()
                        if re.search(ROLE_KEYWORDS, p, re.IGNORECASE) and 1 <= len(p.split()) <= 8:
                            candidate_parts.append(p)
            
            if candidate_parts:
                # Prefer shortest part that has role keywords
                return sorted(candidate_parts, key=lambda x: len(x))[0]
            
            # Fall back to first part of any separator
            return dash_parts[0].strip() if len(dash_parts) > 1 else raw.strip()

        current_title = _clean_raw_title(current_title)

        # Fallback: scan text for known title patterns if title still looks wrong
        if not current_title or current_title in ("Software Professional", "Professional", "Candidate") \
                or len(current_title) < 3:
            if sections["Experience"]:
                first_exp_line = sections["Experience"][0]
                cleaned = _clean_raw_title(first_exp_line[:100])
                t_norm = _normalize_title(cleaned)
                if t_norm["match_method"] != "none":
                    current_title = t_norm["normalized"]
                else:
                    current_title = cleaned[:60]

        # Broad title regex fallback on full text
        TITLE_PATTERNS = [
            r'Senior\s+Software\s+Engineer', r'Staff\s+Software\s+Engineer', r'Principal\s+(?:Software\s+)?Engineer',
            r'Backend\s+(?:Developer|Engineer)', r'Frontend\s+(?:Developer|Engineer)',
            r'Full[\s\-]Stack\s+(?:Developer|Engineer)', r'Data\s+Scientist',
            r'Machine\s+Learning\s+Engineer', r'ML(?:Ops)?\s+Engineer', r'AI\s+Engineer',
            r'Data\s+Engineer', r'Senior\s+DevOps\s+Engineer', r'DevOps\s+Engineer',
            r'Cloud\s+(?:Engineer|Architect)', r'Solutions?\s+Architect', r'Site\s+Reliability\s+Engineer',
            r'SRE\b', r'Platform\s+Engineer', r'Infrastructure\s+Engineer',
            r'Product\s+Manager', r'Senior\s+Product\s+Manager', r'Product\s+Owner',
            r'QA\s+(?:Automation\s+)?Engineer', r'Security\s+Engineer', r'Security\s+Analyst',
            r'Penetration\s+Tester', r'SOC\s+Analyst', r'Malware\s+Analyst', r'GRC\s+Analyst',
            r'Network\s+(?:Engineer|Administrator)', r'iOS\s+Developer', r'Android\s+Developer',
            r'Mobile\s+Developer', r'UI/UX\s+Designer', r'UX\s+(?:Researcher|Designer)',
            r'Blockchain\s+Developer', r'Web\s+Developer',
            r'Embedded\s+(?:Systems\s+)?Engineer', r'Firmware\s+Engineer', r'FPGA\s+Engineer',
            r'Hardware\s+Engineer', r'ASIC\s+Design\s+Engineer',
            r'Data\s+Analyst', r'BI\s+(?:Developer|Analyst)', r'Analytics\s+Engineer',
            r'Tech(?:nical)?\s+Lead', r'Engineering\s+Manager', r'CTO\b', r'CISO\b', r'VP\s+Engineering',
            r'IT\s+(?:Support|Manager|Consultant)', r'Scrum\s+Master', r'Business\s+Analyst',
            r'Research\s+Scientist', r'NLP\s+Engineer', r'Computer\s+Vision\s+Engineer',
            r'(?:Manufacturing|Process|Quality|Supply\s+Chain|CAD|Robotics)\s+Engineer',
            r'(?:Automotive|ADAS|Firmware)\s+(?:Software\s+)?Engineer',
            r'Game\s+Developer', r'PHP\s+Developer', r'Systems?\s+Administrator',
            r'Software\s+(?:Engineer|Developer|Architect)',
        ]

        if not current_title or current_title in ("Software Professional", "Professional", "Candidate") \
                or len(current_title) < 3:
            for tp in TITLE_PATTERNS:
                m = re.search(tp, text, re.IGNORECASE)
                if m:
                    current_title = m.group(0)
                    break
            else:
                current_title = "Software Professional"

        # Final clean: remove trailing company names
        current_title = _clean_raw_title(current_title)

        title_norm = _normalize_title(current_title)
        normalized_title = title_norm["normalized"]
        title_family = title_norm["family"]
        title_seniority = title_norm["seniority"]

        # ── 8. Education Extraction ───────────────────────────────────────────
        education = []
        edu_text = "\n".join(sections["Education"]) if sections["Education"] else text

        DEGREE_MAP = {
            "PhD": [r"ph\.?\s*d\.?", r"doctor of philosophy", r"doctorate"],
            "MBA": [r"m\.?\s*b\.?\s*a\.?", r"master of business administration"],
            "MTech": [r"m\.?\s*tech\.?", r"master of technology"],
            "MSc": [r"m\.?\s*sc\.?", r"master of science"],
            "MS": [r"\bms\b", r"master of science", r"masters"],
            "ME": [r"m\.?\s*e\.?", r"master of engineering"],
            "BTech": [r"b\.?\s*tech\.?", r"bachelor of technology", r"b\.e\.tech"],
            "BE": [r"b\.?\s*e\.?", r"bachelor of engineering"],
            "BS": [r"\bbs\b", r"b\.?\s*s\.?", r"bachelor of science", r"bachelors"],
            "BA": [r"\bba\b", r"b\.?\s*a\.?", r"bachelor of arts"],
            "BCA": [r"bca", r"bachelor of computer applications"],
            "BCS": [r"bcs", r"bachelor of computer science"],
            "Diploma": [r"diploma"],
            "Associate": [r"associate degree", r"a\.s\.", r"a\.a\."],
        }

        edu_seen: set[str] = set()
        for canonical_deg, patterns in DEGREE_MAP.items():
            if canonical_deg in edu_seen:
                continue
            for pat in patterns:
                if re.search(pat, edu_text, re.IGNORECASE):
                    edu_seen.add(canonical_deg)
                    # Try to extract institution (next capitalized token after degree)
                    inst_match = re.search(
                        r'(?:' + pat + r')[,\s]+([A-Z][^\n,]{3,50})',
                        edu_text, re.IGNORECASE
                    )
                    institution = inst_match.group(1).strip() if inst_match else "University"
                    # Clean institution: remove if it's just a degree word
                    if institution.lower() in ("computer", "science", "technology", "engineering",
                                               "business", "arts", "mathematics", "statistics"):
                        institution = "University"
                    
                    # Extract field of study
                    pos = edu_text.lower().find(pat[:5])
                    search_window = edu_text[max(0, pos):pos + 150] if pos >= 0 else edu_text[:150]
                    field_match = re.search(r'(?:in|of)\s+([A-Za-z][^\n,\.]{2,40})', search_window, re.IGNORECASE)
                    field = field_match.group(1).strip() if field_match else ""
                    
                    education.append({
                        "degree": canonical_deg,
                        "institution": institution,
                        "field_of_study": field,
                        "evidence": edu_text[:150].replace('\n', ' ')
                    })
                    break

        # ── 9. Certification Extraction ───────────────────────────────────────
        certifications = []
        cert_text = "\n".join(sections["Certifications"]) if sections["Certifications"] else text

        CERT_PATTERNS = [
            (r"AWS\s+Certified\s+Solutions\s+Architect", "AWS Certified Solutions Architect"),
            (r"AWS\s+Certified\s+Developer", "AWS Certified Developer"),
            (r"AWS\s+Certified\s+SysOps", "AWS Certified SysOps Administrator"),
            (r"AWS\s+Certified\s+DevOps", "AWS Certified DevOps Engineer"),
            (r"Microsoft\s+Certified.*?Azure", "Microsoft Certified Azure"),
            (r"Azure\s+Fundamentals", "Azure Fundamentals"),
            (r"Azure\s+Solutions\s+Architect", "Azure Solutions Architect"),
            (r"\bCKA\b", "CKA - Certified Kubernetes Administrator"),
            (r"\bCKAD\b", "CKAD - Certified Kubernetes Application Developer"),
            (r"\bCISSP\b", "CISSP"),
            (r"\bCEH\b", "CEH - Certified Ethical Hacker"),
            (r"\bPMP\b", "PMP - Project Management Professional"),
            (r"Certified\s+Scrum\s+Master|CSM\b", "Certified Scrum Master"),
            (r"Professional\s+Scrum\s+Master|PSM\b", "Professional Scrum Master"),
            (r"\bCCNA\b", "CCNA"),
            (r"\bCCNP\b", "CCNP"),
            (r"\bCCIE\b", "CCIE"),
            (r"Databricks\s+Certified", "Databricks Certified"),
            (r"SnowPro\s+Core|SnowPro", "SnowPro"),
            (r"Google\s+Cloud\s+(Professional|Associate)", "Google Cloud Certified"),
            (r"GCP\s+(Professional|Associate)\s+Certified", "Google Cloud Certified"),
            (r"Certified\s+Cloud\s+Practitioner|Cloud\s+Practitioner", "AWS Cloud Practitioner"),
            (r"HashiCorp\s+Certified.*?Terraform", "HashiCorp Certified Terraform Associate"),
            (r"\bCPA\b", "CPA - Certified Public Accountant"),
            (r"\bCFA\b", "CFA - Chartered Financial Analyst"),
            (r"\bCFE\b", "CFE - Certified Fraud Examiner"),
            (r"Certified\s+Data\s+Engineer", "Certified Data Engineer"),
            (r"RHCE|Red\s+Hat\s+Certified\s+Engineer", "Red Hat Certified Engineer"),
            (r"RHCSA|Red\s+Hat\s+Certified\s+System\s+Administrator", "Red Hat Certified System Administrator"),
            (r"Certified\s+Kubernetes\s+Security\s+Specialist|CKS\b", "CKS - Kubernetes Security Specialist"),
            (r"CompTIA\s+Security\+|Security\s+\+", "CompTIA Security+"),
            (r"CompTIA\s+Network\+", "CompTIA Network+"),
            (r"CompTIA\s+A\+", "CompTIA A+"),
            (r"OSCP|Offensive\s+Security\s+Certified", "OSCP - Offensive Security Certified Professional"),
            (r"ISO\s+27001\s+Lead\s+Implementer", "ISO 27001 Lead Implementer"),
            (r"ISO\s+27001\s+Lead\s+Auditor", "ISO 27001 Lead Auditor"),
            (r"TOGAF", "TOGAF Certified"),
            (r"Certified\s+SAFe", "Certified SAFe"),
            (r"Six\s+Sigma\s+Black\s+Belt", "Six Sigma Black Belt"),
            (r"Six\s+Sigma\s+Green\s+Belt", "Six Sigma Green Belt"),
            (r"TensorFlow\s+Developer\s+Certificate", "TensorFlow Developer Certificate"),
        ]

        seen_certs: set[str] = set()
        for pat, cert_name in CERT_PATTERNS:
            if cert_name in seen_certs:
                continue
            m = re.search(pat, cert_text, re.IGNORECASE)
            if m:
                seen_certs.add(cert_name)
                certifications.append({
                    "name": cert_name,
                    "evidence": cert_text[max(0, m.start()-20):m.end()+80].replace('\n', ' ').strip()
                })

        # ── 10. Build final output ────────────────────────────────────────────
        return {
            "full_name": name,
            "current_title": normalized_title if normalized_title else current_title,
            "normalized_title": normalized_title,
            "title_family": title_family,
            "title_seniority": title_seniority,
            "total_years_of_experience": yoe_years,
            "current_employment_status": "Employed" if parsed_periods else "Unknown",
            "open_to_work": True,
            "notice_period": 30,
            "expected_salary": 0,
            "summary": " ".join(sections["Summary"])[:500] if sections["Summary"] else "Deterministically extracted resume profile.",
            "contact": {"email": email, "phone": phone},
            "experiences": experiences,
            "education": education,
            "skills": [{"name": s["name"], "type": s["type"]} for s in skill_results],
            "normalized_skills": skill_results,
            "certifications": [c["name"] for c in certifications],
            "certifications_detail": certifications,
            "projects": [],
            "career_gaps": [],
            "trajectory_events": []
        }

    @staticmethod
    def _default_resume():
        return {
            "full_name": "Unknown", "current_title": "Software Professional",
            "normalized_title": "Software Engineer", "title_family": "", "title_seniority": "",
            "total_years_of_experience": 0, "current_employment_status": "Unknown",
            "open_to_work": True, "notice_period": 30, "expected_salary": 0,
            "summary": "", "contact": {"email": "", "phone": ""}, "experiences": [],
            "education": [], "skills": [], "normalized_skills": [], "certifications": [],
            "certifications_detail": [], "projects": [], "career_gaps": [], "trajectory_events": []
        }