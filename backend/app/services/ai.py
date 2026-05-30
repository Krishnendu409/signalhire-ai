import json
import logging
import asyncio
from functools import lru_cache
from google import genai
from google.genai import types
from google.api_core.exceptions import GoogleAPICallError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-2.5-flash-preview-05-20"
# Thinking budget controls extra reasoning tokens in Gemini 2.5 Flash; 768 balances
# extraction consistency improvements with latency/cost for JD and resume parsing.
THINKING_BUDGET = 768


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    return genai.Client(api_key=settings.gemini_api_key)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((GoogleAPICallError, ConnectionError, TimeoutError)),
)
async def gemini_generate(
    prompt: str,
    system: str = "You are an expert recruiter and talent analyst.",
    temperature: float = 0.1,
) -> dict:
    """
    Call Gemini 2.5 Flash and return the parsed JSON response.
    Uses asyncio.to_thread to avoid blocking the event loop.
    """
    response = await asyncio.to_thread(
        _get_client().models.generate_content,
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            response_mime_type="application/json",
            thinking_config=types.ThinkingConfig(thinking_budget=THINKING_BUDGET),
        ),
        contents=[prompt],
    )
    return json.loads(response.text)


# ---------- Prompt Templates ----------

JD_PARSE_SYSTEM = """You are an expert hiring strategist. Analyze the job description and extract structured data. Always respond with valid JSON only."""

JD_PARSE_PROMPT = """Extract the following fields from the job description:

- title: string
- seniority: "junior" | "mid" | "senior" | "lead" | "principal"
- required_hard_skills: list of strings
- required_soft_skills: list of strings
- must_have_experience: string description
- nice_to_have: list of strings
- hidden_competencies: list of inferred skills not explicitly mentioned (e.g., stakeholder management, scaling teams)
- domain_knowledge: string

Return JSON:
{{
  "title": "...",
  "seniority": "...",
  "required_hard_skills": [...],
  "required_soft_skills": [...],
  "must_have_experience": "...",
  "nice_to_have": [...],
  "hidden_competencies": [...],
  "domain_knowledge": "..."
}}

Job Description:
{jd_text}"""

RESUME_PARSE_SYSTEM = """You are an elite resume parser. Extract structured data from the text. Always respond with valid JSON only."""

RESUME_PARSE_PROMPT = """Extract a JSON object from the resume text below with exactly these fields:

- full_name: string
- current_title: string
- summary: 2-3 sentence professional summary
- contact: {{"email": "", "phone": ""}}
- experiences: list of objects {{"title": "", "company": "", "start_date": "", "end_date": "", "bullets": [""]}}
- education: list of objects {{"degree": "", "institution": "", "year": ""}}
- skills: list of objects {{"name": "", "type": "hard/soft", "confidence": 0.0, "source_section": "experience/skills/certification/projects/education", "context": ""}}
- certifications: list of names
- projects: list of objects {{"name": "", "description": "", "technologies": []}}
- career_gaps: list of objects {{"start": "", "end": "", "reason": ""}}
- trajectory_events: list of objects {{"type": "promotion/lateral/break", "date": "", "details": ""}}

Rules for skills:
- Set confidence: 1.0 if mentioned in experience section with concrete usage; 0.6 if in projects or education; 0.2 if only in a skills list.
- For "familiar with" or "basic knowledge of" -> reduce confidence to 0.3 and note in context.
- Detect negation ("no experience with", "have not worked with") -> set confidence to 0.0 and flag.
- Extract version numbers (e.g., "Angular 17", "Python 3.10").
- Do NOT confuse programming languages with general terms (e.g., "Go" language vs "go-to-market").

Resume text:
{resume_text}"""

RERANK_SYSTEM = """You are an elite recruiter who scores candidates on multiple dimensions with extreme precision."""

RERANK_PROMPT = """You will evaluate a candidate for a job on a scale of 0-100 for each dimension.

Job Requirements: {job_req_json}
Candidate Profile: {candidate_json}

Dimensions:
- semantic_relevance: Overall fit to the job's core responsibilities and competencies.
- experience_depth: Years and level of relevant experience.
- career_trajectory: Evaluate the career progression: Fast Climber (rapid promotions, increasing scope), Stable Performer (long tenures, deep expertise), Chaotic Hopper (frequent short stints without progression). Score higher for Fast Climber and Stable Performer, lower for Chaotic Hopper. Also note the archetype.
- project_relevance: Similarity of past projects to the job's likely tasks.
- behavioral_indicators: Evidence of leadership, collaboration, problem-solving.
- domain_alignment: Familiarity with the industry/domain.
- adaptability: Evidence of learning new skills quickly, adjacent skill transferability.

Additionally detect:
- adjacent_skills: list of skills the candidate has that compensate for missing required hard skills (e.g., has Docker/AWS but lacks Kubernetes).
- missing_skills: required hard skills from the job that are absent or weak.

Return JSON:
{{
  "semantic_relevance": {{"score": int, "note": "string"}},
  "experience_depth": {{"score": int, "note": "string"}},
  "career_trajectory": {{"score": int, "note": "string", "archetype": "fast_climber/stable_performer/chaotic_hopper/mixed"}},
  "project_relevance": {{"score": int, "note": "string"}},
  "behavioral_indicators": {{"score": int, "note": "string"}},
  "domain_alignment": {{"score": int, "note": "string"}},
  "adaptability": {{"score": int, "note": "string"}},
  "adjacent_skills": ["string"],
  "missing_skills": ["string"]
}}"""

EXPLAIN_SYSTEM = """You are an AI recruiting assistant that builds trust through transparent, evidence-based explanations."""

EXPLAIN_PROMPT = """Create a detailed, verifiable explanation for why this candidate matches the job.

Job Requirements: {job_req_json}
Candidate Profile: {candidate_json}
Dimension Scores: {scores_json}

Output JSON:
{{
  "top_strengths": ["string", ...],
  "missing_skills": ["string", ...],
  "adjacent_skills": ["string", ...],
  "risk_factors": ["string", ...],
  "overall_assessment": "paragraph summary",
  "extracted_evidence": [
    {{
      "claim": "string",
      "evidence": "verbatim resume snippet",
      "mapped_requirement": "string",
      "confidence": 0.0,
      "source_section": "experience/projects/summary/skills/education"
    }}
  ]
}}"""


# ---------- Public AI Pipeline ----------

class AIPipeline:
    @staticmethod
    async def parse_jd(raw_text: str) -> dict:
        """Run JD understanding engine using Gemini 2.5 Flash."""
        prompt = JD_PARSE_PROMPT.format(jd_text=raw_text)
        return await gemini_generate(prompt, system=JD_PARSE_SYSTEM)

    @staticmethod
    async def parse_resume(text: str) -> dict:
        """Extract structured data from resume text."""
        # Pass full resume text; Gemini 2.5 Flash supports long context windows.
        prompt = RESUME_PARSE_PROMPT.format(resume_text=text)
        return await gemini_generate(prompt, system=RESUME_PARSE_SYSTEM)

    @staticmethod
    async def rerank_candidate(job_req: dict, candidate_parsed: dict) -> dict:
        """Score a candidate on all dimensions."""
        prompt = RERANK_PROMPT.format(
            job_req_json=json.dumps(job_req, indent=2),
            candidate_json=json.dumps(candidate_parsed, indent=2),
        )
        return await gemini_generate(prompt, system=RERANK_SYSTEM)

    @staticmethod
    async def generate_explanation(
        job_req: dict,
        candidate_parsed: dict,
        scores: dict,
    ) -> dict:
        """Generate evidence-backed explanation."""
        prompt = EXPLAIN_PROMPT.format(
            job_req_json=json.dumps(job_req, indent=2),
            candidate_json=json.dumps(candidate_parsed, indent=2),
            scores_json=json.dumps(scores, indent=2),
        )
        response = await gemini_generate(prompt, system=EXPLAIN_SYSTEM)
        evidence = response.get("extracted_evidence", [])
        normalized = []
        for item in evidence:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "claim": str(item.get("claim", "")).strip(),
                    "evidence": str(item.get("evidence", "")).strip(),
                    "mapped_requirement": str(item.get("mapped_requirement", "")).strip(),
                    "confidence": float(item.get("confidence", 0.0)),
                    "source_section": str(item.get("source_section", "unknown")).strip() or "unknown",
                }
            )
        response["extracted_evidence"] = normalized
        return response