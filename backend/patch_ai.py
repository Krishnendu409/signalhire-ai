import re

with open('app/services/ai.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove fallbacks in parsing
content = content.replace('name = "Candidate"', 'name = None')
content = content.replace('title = t_candidate if len(t_candidate.split()) <= 8 else "Professional"', 'title = t_candidate if len(t_candidate.split()) <= 8 else ""')
content = content.replace('title = "Software Professional"', 'title = ""')

# Replace the current_title block at line 401
content = content.replace('if not current_title or current_title in ("Software Professional", "Professional"):', 'if not current_title:')

# Replace the broad fallback block (lines 489-512)
old_fallback = """        # Fallback: scan text for known title patterns if title still looks wrong
        if not current_title or current_title in ("Software Professional", "Professional", "Candidate") \\
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
        if not current_title or len(current_title) < 3:
            for exp in experiences:
                if exp.get('title') and exp.get('title') not in ("Professional", "Employee", "Software Professional", "Unknown Role", "Candidate"):
                    current_title = exp['title']
                    break
        
        current_title = _clean_raw_title(current_title)
        
        # If it still ends up as fallback, clear it.
        if current_title in ("Professional", "Employee", "Software Professional", "Unknown Role", "Candidate"):
            current_title = ""

        title_norm = _normalize_title(current_title)
        normalized_title = title_norm["normalized"]
        title_family = title_norm["family"]
        title_seniority = title_norm["seniority"]"""

new_fallback = """        # Title extraction rebuild based on priority: headline -> latest role -> summary -> ontology inference
        raw_title = None
        normalized_title = None
        title_confidence = 0

        # Try to extract title directly from early text lines (headline)
        headline_title = ""
        for line in lines[:8]:
            if line.strip() == name: continue
            cleaned = _clean_raw_title(line[:100])
            tn = _normalize_title(cleaned)
            if tn["match_method"] != "none":
                headline_title = tn["normalized"]
                break

        # Priority 1: Headline
        if headline_title:
            raw_title = headline_title
            title_confidence = 90
        # Priority 2: Latest Role
        elif experiences and experiences[0].get('title'):
            raw_title = experiences[0].get('title')
            title_confidence = 80
        # Priority 3: Summary
        elif sections["Summary"]:
            summary_text = " ".join(sections["Summary"])
            tn = _normalize_title(summary_text[:200])
            if tn["match_method"] != "none":
                raw_title = tn["normalized"]
                title_confidence = 70
        # Priority 4: Ontology Inference
        if not raw_title and skill_results:
            top_cat = max([s.get("category") for s in skill_results if s.get("category")], default="", key=lambda c: sum(1 for x in skill_results if x.get("category") == c))
            if top_cat:
                raw_title = f"{top_cat} Specialist"
                title_confidence = 50

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
            
        current_title = raw_title"""

if old_fallback in content:
    content = content.replace(old_fallback, new_fallback)
else:
    print("Could not find old_fallback block!")

# Replace return dict in parse_resume
old_ret = """        return {
            "full_name": name,
            "current_title": normalized_title if normalized_title else current_title,
            "normalized_title": normalized_title,
            "title_family": title_family,
            "title_seniority": title_seniority,"""
new_ret = """        return {
            "full_name": name,
            "current_title": normalized_title if normalized_title else raw_title,
            "raw_title": raw_title,
            "normalized_title": normalized_title,
            "title_confidence": title_confidence,
            "title_family": title_family,
            "title_seniority": title_seniority,"""
content = content.replace(old_ret, new_ret)

# Replace parse_jd domain
old_jd_domain = """        # 5. Domain
        domains = ["finance", "healthcare", "automotive", "telecom", "manufacturing", "retail", "e-commerce", "aerospace", "defense", "energy", "solar", "rf", "vlsi", "embedded", "sales", "marketing", "supply chain", "clinical"]
        domain = ""
        for d in domains:
            if re.search(r'\\b' + d + r'\\b', raw_text, re.IGNORECASE):
                domain = d.capitalize()
                break
                
        return {
            "title": title,
            "seniority": seniority,
            "required_hard_skills": hard,
            "required_soft_skills": soft,
            "must_have_experience": experience,
            "certifications": certs,
            "domain_knowledge": domain
        }"""
new_jd_domain = """        # 5. Domain Inference via Ontology
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
        }"""
content = content.replace(old_jd_domain, new_jd_domain)

# Modify explanations
old_expl_1 = """        if sm.get("score", 0) > 80: overall = "Excellent candidate with strong alignment to job requirements."
        elif sm.get("score", 0) < 50: overall = "Candidate lacks several core competencies required for the role."

        evidence = []
        if matched: evidence.append({"claim": "Skill Match", "evidence": f"Found skills: {', '.join(matched)}"})
        evidence.append({"claim": "Experience", "evidence": f"{yoe} years derived from resume dates."})"""
new_expl_1 = """        req_yoe = scores.get("experience_match", {}).get("required_years", 0)
        domain = scores.get("domain_match", {}).get("required_domain", "")

        overall = f"Matched: {', '.join(matched[:5]) if matched else 'None'} | Missing: {', '.join(missing[:5]) if missing else 'None'} | YOE: {yoe} vs required {req_yoe} | Domain: {domain}"

        evidence = []
        if matched: evidence.append({"claim": "Skill Match", "evidence": f"Found skills: {', '.join(matched)}"})
        evidence.append({"claim": "Experience", "evidence": f"{yoe} years vs required {req_yoe} years."})
        evidence.append({"claim": "Domain", "evidence": f"Matched in domain: {domain}" if scores.get("domain_match", {}).get("score", 0) > 0 else "No domain match found."})"""
content = content.replace(old_expl_1, new_expl_1)

with open('app/services/ai.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch applied")
