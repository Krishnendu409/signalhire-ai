import logging
from typing import List, Dict, Any

logger = logging.getLogger("signalhire.comparison")

class ComparisonService:
    @staticmethod
    def compare_candidates(candidates_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not candidates_data:
            return {}

        all_skills = {}
        for c in candidates_data:
            c_id = str(c.get("id"))
            skills = c.get("parsed_data", {}).get("skills", [])
            skill_names = set(s.get("name", "").lower() for s in skills if s.get("name"))
            all_skills[c_id] = skill_names

        common_skills = set.intersection(*all_skills.values()) if all_skills else set()
        union_skills = set.union(*all_skills.values()) if all_skills else set()
        
        unique_strengths = {}
        missing_skills = {}
        for c_id, skills in all_skills.items():
            others_skills = set()
            for o_id, o_skills in all_skills.items():
                if o_id != c_id:
                    others_skills.update(o_skills)
            unique = skills - others_skills
            unique_strengths[c_id] = list(unique)
            missing = union_skills - skills
            missing_skills[c_id] = list(missing)

        experience_comparison = {}
        for c in candidates_data:
            c_id = str(c.get("id"))
            yoe = c.get("parsed_data", {}).get("experience_years", 0)
            experience_comparison[c_id] = {"years": yoe}

        career_trajectory = {}
        leadership_delta = {}
        domain_overlap = {}
        transferable_skills_overlap = {}
        
        for c in candidates_data:
            c_id = str(c.get("id"))
            history = c.get("parsed_data", {}).get("career_history", [])
            career_trajectory[c_id] = history
            
            # Simple leadership heuristic
            lead_years = sum(max(1, h.get("duration_months", 12)//12) for h in history if "lead" in h.get("title", "").lower() or "manager" in h.get("title", "").lower())
            leadership_delta[c_id] = lead_years
            
            domain_overlap[c_id] = ["software", "tech"] # dummy for now
            transferable_skills_overlap[c_id] = [] # dummy

        return {
            "candidates": candidates_data,
            "skill_overlap": list(common_skills),
            "shared_skills": list(common_skills),
            "unique_skills": unique_strengths,
            "unique_strengths": unique_strengths,
            "missing_skills": missing_skills,
            "experience_comparison": experience_comparison,
            "experience_delta": experience_comparison,
            "leadership_delta": leadership_delta,
            "domain_overlap": domain_overlap,
            "transferable_skills_overlap": transferable_skills_overlap,
            "career_trajectory": career_trajectory
        }
