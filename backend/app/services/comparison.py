import logging
from typing import List, Dict, Any

logger = logging.getLogger("signalhire.comparison")

class ComparisonService:
    @staticmethod
    def compare_candidates(candidates_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not candidates_data:
            return {}

        # 1. Skill Overlap & Unique Strengths
        all_skills = {}
        for c in candidates_data:
            c_id = str(c.get("id"))
            skills = c.get("parsed_data", {}).get("skills", [])
            skill_names = set(s.get("name", "").lower() for s in skills if s.get("name"))
            all_skills[c_id] = skill_names

        common_skills = set.intersection(*all_skills.values()) if all_skills else set()
        
        unique_strengths = {}
        for c_id, skills in all_skills.items():
            others_skills = set()
            for o_id, o_skills in all_skills.items():
                if o_id != c_id:
                    others_skills.update(o_skills)
            unique = skills - others_skills
            unique_strengths[c_id] = list(unique)

        # 2. Experience Delta
        experience_comparison = {}
        for c in candidates_data:
            c_id = str(c.get("id"))
            yoe = c.get("parsed_data", {}).get("experience_years", 0)
            experience_comparison[c_id] = {"years": yoe}

        # 3. Career Trajectory
        career_trajectory = {}
        for c in candidates_data:
            c_id = str(c.get("id"))
            history = c.get("parsed_data", {}).get("career_history", [])
            career_trajectory[c_id] = history

        return {
            "candidates": candidates_data,
            "skill_overlap": list(common_skills),
            "unique_strengths": unique_strengths,
            "missing_skills": {},  # Would be relative to JD, but we don't have JD here
            "experience_comparison": experience_comparison,
            "career_trajectory": career_trajectory
        }
