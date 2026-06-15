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
    Scan text against the full skill ontology and N-Grams.
    Returns list of {name, evidence, confidence, match_method, type, is_scoring_eligible, negated}
    """
    _load()
    found: dict[str, dict] = {}

    ont = _SKILL_ONT or {}
    lower_txt = text.lower()
    
    COMPOUND_SKILLS = {
        "machine learning", "deep learning", "learning-to-rank", "vector databases",
        "computer vision", "natural language processing", "project management",
        "supply chain", "root cause analysis", "microsoft office", "power bi",
        "tableau", "data analysis", "neural networks", "software engineering",
        "agile methodologies", "scrum master", "artificial intelligence", "ci/cd",
        "continuous integration", "continuous deployment", "data science",
        "amazon web services", "google cloud platform", "object oriented programming",
        "restful apis", "microservices architecture", "test driven development",
        "react native", "node.js", "kubernetes", "docker", "sql server",
        "postgresql", "mongodb", "elasticsearch", "redis", "kafka", "rabbitmq"
    }

    for comp in COMPOUND_SKILLS:
        if comp in lower_txt:
            idx = lower_txt.find(comp)
            snippet = text[max(0, idx-40):min(len(text), idx+len(comp)+100)].replace('\n', ' ').strip()
            found[comp.title()] = {
                "name": comp.title(),
                "evidence": snippet,
                "match_method": "n-gram",
                "confidence": 0.95,
                "type": "hard",
                "is_scoring_eligible": True,
                "negated": False
            }

    for canonical, data in ont.items():
        if canonical in found:
            continue
        for alias in data.get("aliases", []):
            if alias.lower() not in lower_txt:
                continue
            pattern = _make_pattern(alias)
            if len(alias) <= 3 and alias.lower() in ['c', 'r', 'sta', 'ads', 'c++']:
                m = re.search(pattern, text, re.MULTILINE)  # Case sensitive for short tokens
            else:
                m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if m:
                s = max(0, m.start() - 40)
                e = min(len(text), m.end() + 100)
                snippet = text[s:e].replace('\n', ' ').strip()
                found[canonical] = {
                    "name": canonical,
                    "evidence": snippet,
                    "match_method": "alias",
                    "confidence": 0.90,
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
import datetime

ROLE_KEYWORDS = re.compile(
    r'(?:engineer|developer|architect|scientist|analyst|manager|lead|director|'
    r'designer|specialist|administrator|consultant|officer|researcher|support|'
    r'technician|programmer|sre|devops|cto|ciso|vp|intern|founder|owner|scrum\s+master)', 
    re.IGNORECASE
)

def _is_role_title(text: str) -> bool:
    import re
    invalid_patterns = [
        r'(?i)seeking\s+a', r'(?i)to\s+obtain', r'(?i)professional\s+summary',
        r'(?i)career\s+objective', r'(?i)objective:', r'(?i)summary:', r'(?i)seeking\s+an'
    ]
    for p in invalid_patterns:
        if re.search(p, text):
            return False
    if len(text) > 100:
        return False
    return bool(ROLE_KEYWORDS.search(text))

def _parse_dates(start_str: str, end_str: str):
    s_yr_match = re.search(r'\d{4}', start_str)
    e_yr_match = re.search(r'\d{4}', end_str)
    is_current = bool(re.search(r'(?i)present|current|now|ongoing|till date', end_str))
    
    sy = int(s_yr_match.group()) if s_yr_match else None
    current_year = datetime.datetime.now().year
    ey = current_year if is_current else (int(e_yr_match.group()) if e_yr_match else sy)
    
    if sy is None:
        return 0, False, None, None
    if ey is None:
        ey = sy
    if ey < sy:
        ey = sy
        
    months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    sm = 1
    em = 12 if not is_current else datetime.datetime.now().month
    
    for i, m in enumerate(months):
        if re.search(rf'(?i)\b{m}', start_str): sm = i + 1
        if re.search(rf'(?i)\b{m}', end_str): em = i + 1
            
    sm_match = re.search(r'(\d{1,2})[\/\-]\d{4}', start_str)
    if sm_match: sm = int(sm_match.group(1))
    em_match = re.search(r'(\d{1,2})[\/\-]\d{4}', end_str)
    if em_match: em = int(em_match.group(1))

    duration_months = max(1, (ey - sy) * 12 + (em - sm))
    start_abs_months = sy * 12 + sm
    end_abs_months = ey * 12 + em
    return duration_months, is_current, start_abs_months, end_abs_months

def _reconstruct_career_history(exp_lines: list[str], full_text: str):
    date_pattern = re.compile(
        r'\b((?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+)?\d{4}|\d{1,2}[\/\-]\d{4})\s*(?:–|—|-|to)\s*((?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+)?\d{4}|\d{1,2}[\/\-]\d{4}|Present|Current|Now|Till Date|Ongoing)\b',
        re.IGNORECASE
    )
    
    exp_text = "\n".join(exp_lines) if len(exp_lines) > 2 else full_text
    matches = list(date_pattern.finditer(exp_text))
    
    career_history = []
    raw_blocks = []
    
    if not matches:
        # Fallback to line-by-line parsing if no dates found
        for line in exp_lines:
            line = line.strip()
            if not line: continue
            if _is_role_title(line):
                inline_split = re.split(r'\s+[-–—\|@,]\s+|\s+at\s+', line, flags=re.IGNORECASE)
                if len(inline_split) >= 2:
                    a_role = _is_role_title(inline_split[0])
                    t_val = inline_split[0].strip() if a_role else inline_split[-1].strip()
                    c_val = inline_split[-1].strip() if a_role else inline_split[0].strip()
                    career_history.append({
                        "title": t_val,
                        "company": c_val,
                        "start_date": "", "end_date": "", "is_current": False, "duration_months": 0, "start_abs_months": None, "end_abs_months": None, "bullets": [],
                        "confidence": 0.6, "evidence": ["Role keyword inline match"]
                    })
                else:
                    career_history.append({
                        "title": line,
                        "company": "",
                        "start_date": "", "end_date": "", "is_current": False, "duration_months": 0, "start_abs_months": None, "end_abs_months": None, "bullets": [],
                        "confidence": 0.5, "evidence": ["Role keyword match"]
                    })
        return career_history, 0, 0, 0, 0, 0, 0.0, 0, []
        
    last_idx = 0
    blocks = []
    for m in matches:
        blocks.append(exp_text[last_idx:m.start()].strip())
        blocks.append(m.group(1).strip())
        blocks.append(m.group(2).strip())
        last_idx = m.end()
    blocks.append(exp_text[last_idx:].strip())
    
    current_company = "Unknown Company"
    parsed_periods = []
    inversion_count = 0
    idx = 1
    
    while idx < len(blocks) - 1:
        start_date = blocks[idx]
        end_date = blocks[idx + 1]
        desc_text = blocks[idx + 2] if idx + 2 < len(blocks) else ""
        pre_text = blocks[idx - 1]
        
        raw_blocks.append({
            "pre_date_text": pre_text,
            "start_date": start_date,
            "end_date": end_date,
            "desc_text": desc_text[:200]
        })
        
        pre_lines = [ln.strip() for ln in pre_text.split('\n') if 2 < len(ln.strip()) < 120]
        title, company = "", ""
        HEADER_WORDS = {"experience", "employment", "work history", "career", "professional experience", "work experience", "positions held"}
        pre_lines = [l for l in pre_lines if l.lower() not in HEADER_WORDS]
        
        if pre_lines:
            line1 = pre_lines[-1]
            line2 = pre_lines[-2] if len(pre_lines) >= 2 else ""
            
            inline_split = re.split(r'\s+[-–—\|@,]\s+|\s+at\s+', line1, flags=re.IGNORECASE)
            
            if len(inline_split) >= 2:
                part_a = inline_split[0].strip()
                part_b = inline_split[-1].strip()
                a_role = _is_role_title(part_a)
                b_role = _is_role_title(part_b)
                if a_role and not b_role: title, company = part_a, part_b
                elif b_role and not a_role: 
                    title, company = part_b, part_a
                    inversion_count += 1
                else: title, company = (part_a, part_b) if a_role else (part_b, part_a)
            elif line2:
                l1_role = _is_role_title(line1)
                l2_role = _is_role_title(line2)
                if l1_role and not l2_role: title, company = line1, line2
                elif l2_role and not l1_role: 
                    title, company = line2, line1
                    inversion_count += 1
                else: title, company = line1, line2
            else:
                title = line1
        
        if company and company != "Unknown Company": current_company = company
        elif not company: company = current_company
            
        dur_months, is_current, start_abs_months, end_abs_months = _parse_dates(start_date, end_date)
        if start_abs_months and end_abs_months: parsed_periods.append((start_abs_months, end_abs_months))
            
        bullet_lines = [b.strip() for b in desc_text.split('\n') if b.strip() and not re.match(date_pattern, b.strip())][:5]
        
        title_val = title if title and title != "Unknown Title" else ""
        company_val = company if company and company != "Unknown Company" else ""
        
        # Confidence and evidence
        evidence = []
        conf = 0.5
        if title_val:
            if _is_role_title(title_val):
                conf += 0.2
                evidence.append(f"Title matched ontology: {title_val}")
            else:
                conf += 0.1
                evidence.append(f"Title found: {title_val}")
        if company_val:
            conf += 0.2
            evidence.append(f"Company found: {company_val}")
        if start_abs_months and end_abs_months:
            conf += 0.1
            evidence.append(f"Valid dates: {start_date} - {end_date}")
        conf = min(1.0, conf)

        career_history.append({
            "title": title_val,
            "company": company_val,
            "start_date": start_date,
            "end_date": end_date,
            "is_current": is_current,
            "duration_months": dur_months,
            "start_abs_months": start_abs_months,
            "end_abs_months": end_abs_months,
            "bullets": bullet_lines,
            "confidence": conf,
            "evidence": evidence
        })
        idx += 3
        
    total_months = 0
    if parsed_periods:
        parsed_periods.sort()
        merged = [parsed_periods[0]]
        for s, e in parsed_periods[1:]:
            if s <= merged[-1][1]: merged[-1] = (merged[-1][0], max(merged[-1][1], e))
            else: merged.append((s, e))
        total_months = sum(e - s for s, e in merged)
    total_years = max(0, total_months / 12)
    
    # Domain-aware relevant years logic
    relevant_months = 0
    rel_periods = []
    for exp in career_history:
        if _is_role_title(exp['title']) and exp.get('start_abs_months') and exp.get('end_abs_months'):
            rel_periods.append((exp['start_abs_months'], exp['end_abs_months']))
    if rel_periods:
        rel_periods.sort()
        merged_rel = [rel_periods[0]]
        for s, e in rel_periods[1:]:
            if s <= merged_rel[-1][1]: merged_rel[-1] = (merged_rel[-1][0], max(merged_rel[-1][1], e))
            else: merged_rel.append((s, e))
        relevant_months = sum(e - s for s, e in merged_rel)
    relevant_years = max(0, relevant_months / 12)
    
    leadership_years = sum(max(1, exp['duration_months'] // 12) for exp in career_history if re.search(r'(?i)lead|manager|director|vp|chief|head', exp['title']))
    
    companies_seen = {}
    promotion_count = 0
    # Reversed goes from oldest to newest if career_history is newest first
    for exp in reversed(career_history):
        c = exp['company'].lower()
        t = exp['title'].lower()
        if c in companies_seen: 
            # Same company seen earlier, if different title, it's a promotion
            if companies_seen[c] != t:
                promotion_count += 1
        companies_seen[c] = t
        
    company_count = len(companies_seen)
    career_velocity = round(promotion_count / max(1, total_years) * 10, 1)
    
    return career_history, total_years, relevant_years, leadership_years, promotion_count, company_count, career_velocity, inversion_count, raw_blocks


class AIPipeline:

    @staticmethod
    async def parse_jd(raw_text: str) -> dict:
        """Deterministic ontology-driven JD parser."""
        logger.info("[DETERMINISTIC_PARSER] Parsing JD without LLM.")
        
        # 1. Title Extraction
        t_norm = _normalize_title(raw_text)
        if t_norm["match_method"] != "none":
            title = t_norm["normalized"]
        else:
            m = re.search(r'(Engineer|Developer|Manager|Analyst|Scientist|Architect|Associate|Director|VP|Lead)', raw_text, re.IGNORECASE)
            if m:
                m_full = re.search(r'([a-zA-Z\s]{0,20}' + m.group(1) + r')', raw_text, re.IGNORECASE)
                title = m_full.group(1).strip() if m_full else m.group(1)
            else:
                title = ""
        
        seniority = "mid"
        lower_txt = raw_text.lower()
        if "senior" in lower_txt: seniority = "senior"
        elif "junior" in lower_txt: seniority = "junior"
        elif "lead" in lower_txt or "manager" in lower_txt: seniority = "lead"
        
        # 2. Skills
        extracted = _extract_skills_with_evidence(raw_text)
        hard = [s["name"] for s in extracted if s["type"] == "hard"]
        soft = [s["name"] for s in extracted if s["type"] == "soft"]
        
        # 3. Experience
        exp_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?experience', raw_text, re.IGNORECASE)
        experience = exp_match.group(1) + " years" if exp_match else ""
        if not experience:
            if seniority == "senior": experience = "5 years"
            elif seniority == "lead": experience = "8 years"
            elif seniority == "junior": experience = "1 year"
            else: experience = "3 years"
        
        # 4. Certifications
        certs = []
        for s in extracted:
            if s["name"].endswith("Certified") or "Certification" in s["name"]:
                certs.append(s["name"])
                
        # 5. Domain Inference via Ontology
        domain_counts = {}
        for s in extracted:
            if s.get("type") == "hard" and "category" in s:
                cat = s["category"]
                domain_counts[cat] = domain_counts.get(cat, 0) + 1
        
        domain = ""
        domain_confidence = 0
        supporting_evidence = []
        if domain_counts:
            best_domain = max(domain_counts.items(), key=lambda x: x[1])
            domain = best_domain[0]
            domain_confidence = min(100, int((best_domain[1] / max(1, len(hard))) * 100))
            supporting_evidence = [s["name"] for s in extracted if s.get("category") == domain]

        missing_extractions = {}
        if not title: missing_extractions["title"] = "No matching title found in ontology or regex"
        if not hard: missing_extractions["skills"] = "No hard skills matched in ontology"
        if not domain: missing_extractions["domain"] = "No domain inferred from extracted skills"

        return {
            "title": title,
            "seniority": seniority,
            "required_hard_skills": hard,
            "required_soft_skills": soft,
            "preferred_skills": [],
            "must_have_experience": experience,
            "certifications": certs,
            "domain": domain,
            "domain_knowledge": domain,
            "domain_confidence": domain_confidence,
            "supporting_evidence": supporting_evidence[:5],
            "missing_extractions": missing_extractions
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
        name = None
        name_confidence = 0.0
        ignore_words = {"resume", "cv", "curriculum vitae", "profile", "summary", "objective",
                        "experience", "education", "skills", "certifications", "page", "portfolio"}
        
        name_candidates = []
        for i, line in enumerate(lines[:50]):
            cl = line.strip()
            if not cl: continue
            words = cl.split()
            if len(words) > 5 or len(words) < 1: continue
            
            lower_cl = cl.lower()
            if lower_cl in ignore_words or lower_cl.startswith("page"): continue
            if "@" in cl or "http" in cl or "www." in cl or any(c.isdigit() for c in cl): continue
            
            candidate_name = re.split(r'\s*[\|\-–—]\s*', cl)[0].strip()
            if len(candidate_name) < 2: continue
            
            score = 100 - (i * 5)
            
            if email_match and abs(text.find(email_match.group(0)) - text.find(candidate_name)) < 200:
                score += 20
            if phone_match and abs(text.find(phone_match.group(0)) - text.find(candidate_name)) < 200:
                score += 20
                
            if candidate_name.isupper():
                score += 15
            elif candidate_name.istitle():
                score += 10
                
            name_candidates.append((candidate_name, score))
            
        if name_candidates:
            name_candidates.sort(key=lambda x: x[1], reverse=True)
            name = name_candidates[0][0]
            name_confidence = min(100, max(0, name_candidates[0][1])) / 100.0

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
                if lower_clean == k:
                    current_section = v
                    matched = True
                    break
                elif lower_clean.startswith(k + ':') or lower_clean.startswith(k + ' —'):
                    current_section = v
                    matched = True
                    # Append the rest of the line to the section!
                    rest = line[line.lower().find(k) + len(k) + 1:].strip()
                    if rest.startswith('-') or rest.startswith('—'):
                        rest = rest[1:].strip()
                    if rest:
                        sections[current_section].append(rest)
                    break

            if not matched:
                sections[current_section].append(line)

        # ── 5. Skill Extraction (Ontology-based, with evidence) ───────────────
        skill_text = "\n".join(sections["Skills"] + sections["Summary"]) if sections["Skills"] else text
        skill_results = _extract_skills_with_evidence(skill_text)

        # ── 6. Experience Reconstruction & YOE ──────────────────────────────
        career_history, total_years, relevant_years, leadership_years, promotion_count, company_count, career_velocity, inversion_count, raw_blocks = _reconstruct_career_history(sections["Experience"], text)
        
        if total_years < 1:
            yoe_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?experience', text, re.IGNORECASE)
            total_years = int(yoe_match.group(1)) if yoe_match else 3
            
        yoe_years = min(total_years, 45)
        current_title = career_history[0]["title"] if career_history else ""

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

        # Priority 1: Headline
        headline_title = ""
        for line in lines[:15]:
            if line.strip() == name: continue
            cleaned = _clean_raw_title(line[:100])
            tn = _normalize_title(cleaned)
            if tn["match_method"] != "none":
                headline_title = tn["normalized"]
                break

        raw_title = None
        normalized_title = None
        title_confidence = 0.0

        if headline_title:
            raw_title = headline_title
            title_confidence = 0.90
        elif career_history and career_history[0].get('title'):
            raw_title = career_history[0].get('title')
            title_confidence = 0.85
        elif sections["Summary"]:
            summary_text = " ".join(sections["Summary"])
            tn = _normalize_title(summary_text[:200])
            if tn["match_method"] != "none":
                raw_title = tn["normalized"]
                title_confidence = 0.70

        if not raw_title and skill_results:
            top_cat = max([s.get("category") for s in skill_results if s.get("category")], default="", key=lambda c: sum(1 for x in skill_results if x.get("category") == c))
            if top_cat:
                raw_title = f"{top_cat} Specialist"
                title_confidence = 0.50

        if raw_title:
            title_norm = _normalize_title(raw_title)
            normalized_title = title_norm["normalized"]
            title_family = title_norm["family"]
            title_seniority = title_norm["seniority"]
        else:
            raw_title = None
            normalized_title = None
            title_family = ""
            title_seniority = ""
            
        current_title = raw_title

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
            "current_title": normalized_title if normalized_title else raw_title,
            "raw_title": raw_title,
            "normalized_title": normalized_title,
            "title_confidence": title_confidence,
            "title_family": title_family,
            "title_seniority": title_seniority,
            "total_years_of_experience": yoe_years,
            "current_employment_status": "Employed" if career_history and career_history[0].get("is_current") else "Unknown",
            "open_to_work": True,
            "notice_period": 30,
            "expected_salary": 0,
            "summary": " ".join(sections["Summary"])[:500] if sections["Summary"] else "Deterministically extracted resume profile.",
            "contact": {"email": email, "phone": phone},
            "career_history": career_history,
            "raw_experience_blocks": raw_blocks,
            "education": education,
            "skills": [{"name": s["name"], "type": s["type"]} for s in skill_results],
            "normalized_skills": skill_results,
            "certifications": [c["name"] for c in certifications],
            "certifications_detail": certifications,
            "projects": [],
            "career_gaps": [],
            "trajectory_events": [],
            "name_confidence": name_confidence,
            "title_confidence": title_confidence,
            "skill_confidence": min(1.0, len(skill_results) / 20.0),
            "overall_confidence": round((name_confidence + title_confidence + min(1.0, len(skill_results) / 20.0)) / 3.0, 2),
            "career_graph": {
                "total_years": total_years,
                "relevant_years": relevant_years,
                "leadership_years": leadership_years,
                "promotion_count": promotion_count,
                "company_count": company_count,
                "career_velocity": career_velocity,
                "inversion_count": inversion_count
            }
        }

    @staticmethod
    async def rerank_candidate(job_req: dict, candidate_parsed: dict) -> dict:
        """Evidence-based candidate evaluation."""
        # 1. Skill Match
        req_skills = set(s.lower().strip() for s in job_req.get("required_hard_skills", []))
        cand_skills = set(s.get("name", "").lower().strip() for s in candidate_parsed.get("skills", []))
        if req_skills:
            matched = list(req_skills.intersection(cand_skills))
            missing = list(req_skills - cand_skills)
            skill_score = int((len(matched) / len(req_skills)) * 100)
            skill_match = {"score": skill_score, "matched": matched, "missing": missing}
        else:
            skill_match = {"score": 100, "matched": list(cand_skills)[:5], "missing": []}

        # 2. Title Match
        req_title = job_req.get("title", "").lower()
        cand_title = candidate_parsed.get("normalized_title", "").lower() or candidate_parsed.get("current_title", "").lower()
        if not req_title: title_match = {"score": 100, "required": "", "candidate": cand_title, "match_type": "none"}
        elif req_title == cand_title: title_match = {"score": 100, "required": req_title, "candidate": cand_title, "match_type": "exact"}
        elif req_title in cand_title or cand_title in req_title: title_match = {"score": 80, "required": req_title, "candidate": cand_title, "match_type": "partial"}
        else: title_match = {"score": 40, "required": req_title, "candidate": cand_title, "match_type": "none"}

        # 3. Experience Match
        cand_yoe = candidate_parsed.get("total_years_of_experience", 0)
        req_exp_str = job_req.get("must_have_experience", "")
        exp_match = re.search(r'\d+', req_exp_str)
        req_yoe = int(exp_match.group(0)) if exp_match else 0
        if req_yoe == 0: exp_score = {"score": 100, "required_years": 0, "candidate_years": cand_yoe, "status": "no_requirement"}
        elif cand_yoe >= req_yoe: exp_score = {"score": min(100, 80 + int((cand_yoe - req_yoe) * 5)), "required_years": req_yoe, "candidate_years": cand_yoe, "status": "exceeds"}
        else: exp_score = {"score": max(0, int((cand_yoe / req_yoe) * 100)), "required_years": req_yoe, "candidate_years": cand_yoe, "status": "shortfall"}

        # 4. Domain Match
        req_domain = job_req.get("domain_knowledge", "").lower()
        if req_domain:
            found = [exp.get("company", "Unknown") for exp in candidate_parsed.get("career_history", []) if req_domain in exp.get("company", "").lower() or req_domain in str(exp.get("bullets", [])).lower()]
            domain_match = {"score": 100 if found else 0, "required_domain": req_domain, "found_in": list(set(found))}
        else:
            domain_match = {"score": 100, "required_domain": "None", "found_in": []}

        # 5. Education Match
        edu_score = 100 if candidate_parsed.get("education") else 60
        education_match = {"score": edu_score, "degrees": [e.get("degree") for e in candidate_parsed.get("education", [])]}

        # 6. Certification Match
        cert_score = 100 if candidate_parsed.get("certifications") else 60
        cert_match = {"score": cert_score, "certifications": candidate_parsed.get("certifications", [])}

        # 7. Project Match
        proj_score = 100 if candidate_parsed.get("projects") else 70
        proj_match = {"score": proj_score, "projects_found": len(candidate_parsed.get("projects", []))}

        # 8. Career Progression
        traj = candidate_parsed.get("_trajectory", {})
        archetype = traj.get("archetype", "unknown")
        traj_score = {"fast_climber": 100, "stable_performer": 80, "chaotic_hopper": 40}.get(archetype, 60)
        career_progression = {"score": traj_score, "archetype": archetype, "details": traj.get("details", "")}

        # 9. Recency
        exps = candidate_parsed.get("career_history", [])
        latest = exps[0] if exps else {}
        is_current = latest.get("is_current", False)
        recency = {"score": 100 if is_current else 60, "latest_role": latest.get("title", ""), "is_current": is_current}

        # 10. Transferable Skills Intelligence
        _TRANSFERABILITY_MAP = {
            "react": {"vue": {"risk": "Low", "reason": "Both are component-based JS frameworks."}, "angular": {"risk": "Medium", "reason": "Different architecture but similar frontend concepts."}, "svelte": {"risk": "Low", "reason": "Component-based architecture."}},
            "python": {"ruby": {"risk": "Low", "reason": "Both are dynamic scripting languages."}, "java": {"risk": "Medium", "reason": "Different paradigms but strong OOP foundation."}},
            "aws": {"gcp": {"risk": "Low", "reason": "Equivalent cloud infrastructure concepts."}, "azure": {"risk": "Low", "reason": "Equivalent cloud concepts."}},
            "sql": {"nosql": {"risk": "Medium", "reason": "Different data models but general database familiarity."}, "postgresql": {"risk": "Low", "reason": "Direct SQL dialect."}},
            "c++": {"c": {"risk": "Low", "reason": "Same family of systems languages."}, "rust": {"risk": "Medium", "reason": "Memory management paradigms differ."}},
            "machine learning": {"data analysis": {"risk": "High", "reason": "Foundational statistics but lacks model building."}, "deep learning": {"risk": "Low", "reason": "Advanced ML application."}},
            "kubernetes": {"docker swarm": {"risk": "Medium", "reason": "Container orchestration concepts transfer."}},
            "node.js": {"express": {"risk": "Low", "reason": "Express is a Node.js framework."}},
            "java": {"c#": {"risk": "Low", "reason": "Very similar syntax and OOP paradigms."}}
        }
        
        transferable_found = []
        adaptation_risks = []
        for m_skill in missing:
            m_lower = m_skill.lower()
            if m_lower in _TRANSFERABILITY_MAP:
                for alt_skill, alt_data in _TRANSFERABILITY_MAP[m_lower].items():
                    if alt_skill in cand_skills:
                        transferable_found.append({
                            "missing_requirement": m_skill,
                            "candidate_skill": alt_skill,
                            "adaptation_risk": alt_data["risk"],
                            "reasoning": alt_data["reason"]
                        })
                        adaptation_risks.append(alt_data["risk"])
                        break

        if "High" in adaptation_risks: overall_risk = "High"
        elif "Medium" in adaptation_risks: overall_risk = "Medium"
        elif "Low" in adaptation_risks: overall_risk = "Low"
        else: overall_risk = "None"

        adj_score = 50 + (len(transferable_found) * 15)
        adj_score = min(100, adj_score)

        adjacency = {
            "score": adj_score, 
            "adjacent_skills": [t["candidate_skill"] for t in transferable_found],
            "transferable_intelligence": transferable_found,
            "overall_adaptation_risk": overall_risk
        }

        return {
            "skill_match": skill_match,
            "title_match": title_match,
            "experience_match": exp_score,
            "education_match": education_match,
            "certification_match": cert_match,
            "project_match": proj_match,
            "domain_match": domain_match,
            "career_progression": career_progression,
            "recency": recency,
            "adjacency": adjacency
        }

    @staticmethod
    async def generate_explanation(job_req: dict, candidate_parsed: dict, scores: dict) -> dict:
        """Deterministic evidence-backed explanation generator."""
        sm = scores.get("skill_match", {})
        missing = sm.get("missing", [])
        matched = sm.get("matched", [])
        
        yoe = candidate_parsed.get("total_years_of_experience", 0)
        strengths = []
        if matched: strengths.append(f"Strong match for core skills: {', '.join(matched[:3])}")
        strengths.append(f"{yoe} years of professional experience.")
        
        req_yoe = scores.get("experience_match", {}).get("required_years", 0)
        domain = scores.get("domain_match", {}).get("required_domain", "")

        overall = f"Matched: {', '.join(matched[:5]) if matched else 'None'} | Missing: {', '.join(missing[:5]) if missing else 'None'} | YOE: {yoe} vs required {req_yoe} | Domain: {domain}"

        evidence = []
        if matched: evidence.append({"claim": "Skill Match", "evidence": f"Found skills: {', '.join(matched)}"})
        evidence.append({"claim": "Experience", "evidence": f"{yoe} years vs required {req_yoe} years."})
        evidence.append({"claim": "Domain", "evidence": f"Matched in domain: {domain}" if scores.get("domain_match", {}).get("score", 0) > 0 else "No domain match found."})
        
        return {
            "top_strengths": strengths,
            "missing_skills": missing,
            "adjacent_skills": scores.get("adjacency", {}).get("adjacent_skills", []),
            "risk_factors": ["Career trajectory needs manual review."] if scores.get("career_progression", {}).get("score", 0) < 50 else [],
            "overall_assessment": overall,
            "extracted_evidence": evidence
        }

    @staticmethod
    def _default_resume():
        return {
            "full_name": "", "current_title": "",
            "normalized_title": "", "title_family": "", "title_seniority": "",
            "total_years_of_experience": 0, "current_employment_status": "Unknown",
            "open_to_work": True, "notice_period": 30, "expected_salary": 0,
            "summary": "", "contact": {"email": "", "phone": ""}, "career_history": [], "raw_experience_blocks": [],
            "education": [], "skills": [], "normalized_skills": [], "certifications": [],
            "certifications_detail": [], "projects": [], "career_gaps": [], "trajectory_events": []
        }