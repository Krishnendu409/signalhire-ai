import json
import time
import httpx
import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings


# ---------- Low-level LLM callers ----------

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
)
async def deepseek_chat(
    prompt: str,
    system: str = "You are an expert recruiter and talent analyst.",
    temperature: float = 0.1,
) -> dict:
    """Call DeepSeek API and return parsed JSON response."""
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": temperature,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60.0,
        )
        if resp.status_code == 402:
            raise Exception("DeepSeek API balance exhausted. Please top up your account or switch to Ollama.")
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)


async def ollama_chat(
    prompt: str,
    system: str = "You are an expert recruiter and talent analyst.",
    model: str = "qwen2.5:7b",
    temperature: float = 0.1,
) -> dict:
    """Fallback to local Ollama when DeepSeek is unavailable or for offline dev."""
    client = openai.AsyncOpenAI(
        base_url=settings.ollama_base_url,
        api_key="ollama",
    )
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=temperature,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        if "500" in str(e):
            raise Exception(f"Ollama error: {e}. Tip: Ensure you have run 'ollama pull {model}'")
        raise e


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
  "extracted_evidence": [{{"claim": "string", "evidence": "verbatim resume snippet"}}]
}}"""


# ---------- Public AI Pipeline ----------

class AIPipeline:
    @staticmethod
    async def parse_jd(raw_text: str) -> dict:
        """Run JD understanding engine with multiple fallbacks."""
        prompt = JD_PARSE_PROMPT.format(jd_text=raw_text)
        try:
            return await deepseek_chat(prompt, system=JD_PARSE_SYSTEM)
        except Exception as e:
            print(f"DeepSeek JD Parse failed: {e}. Trying Ollama...")
            try:
                return await ollama_chat(prompt, system=JD_PARSE_SYSTEM)
            except Exception as e2:
                print(f"Ollama JD Parse failed: {e2}. Using heuristic fallback.")
                return {
                    "title": "Unparsed Role",
                    "seniority": "mid",
                    "required_hard_skills": [],
                    "required_soft_skills": [],
                    "must_have_experience": "JD parsing failed. Manual review required.",
                    "nice_to_have": [],
                    "hidden_competencies": [],
                    "domain_knowledge": "N/A"
                }

    @staticmethod
    async def parse_resume(text: str) -> dict:
        """Extract structured data from resume text with multiple fallbacks."""
        prompt = RESUME_PARSE_PROMPT.format(resume_text=text[:8000])
        try:
            return await deepseek_chat(prompt, system=RESUME_PARSE_SYSTEM)
        except Exception as e:
            print(f"DeepSeek Resume Parse failed: {e}. Trying Ollama...")
            try:
                return await ollama_chat(prompt, system=RESUME_PARSE_SYSTEM)
            except Exception as e2:
                print(f"Ollama Resume Parse failed: {e2}. Using heuristic fallback.")
                return {
                    "full_name": "Unknown Candidate",
                    "current_title": "Unknown Title",
                    "summary": "Resume parsing failed due to AI provider unavailability.",
                    "contact": {"email": "", "phone": ""},
                    "experiences": [],
                    "education": [],
                    "skills": [],
                    "certifications": [],
                    "projects": [],
                    "career_gaps": [],
                    "trajectory_events": []
                }

    @staticmethod
    async def rerank_candidate(job_req: dict, candidate_parsed: dict) -> dict:
        """Score a candidate on all dimensions with heuristic fallback."""
        prompt = RERANK_PROMPT.format(
            job_req_json=json.dumps(job_req, indent=2),
            candidate_json=json.dumps(candidate_parsed, indent=2),
        )
        try:
            return await deepseek_chat(prompt, system=RERANK_SYSTEM)
        except Exception:
            try:
                return await ollama_chat(prompt, system=RERANK_SYSTEM)
            except Exception:
                # Heuristic scoring (very basic)
                return {
                    "semantic_relevance": {"score": 50, "note": "Heuristic fallback (AI unavailable)"},
                    "experience_depth": {"score": 50, "note": "N/A"},
                    "career_trajectory": {"score": 50, "note": "N/A", "archetype": "stable_performer"},
                    "project_relevance": {"score": 50, "note": "N/A"},
                    "behavioral_indicators": {"score": 50, "note": "N/A"},
                    "domain_alignment": {"score": 50, "note": "N/A"},
                    "adaptability": {"score": 50, "note": "N/A"},
                    "adjacent_skills": [],
                    "missing_skills": []
                }

    @staticmethod
    async def generate_explanation(
        job_req: dict,
        candidate_parsed: dict,
        scores: dict,
    ) -> dict:
        """Generate evidence-backed explanation with template fallback."""
        prompt = EXPLAIN_PROMPT.format(
            job_req_json=json.dumps(job_req, indent=2),
            candidate_json=json.dumps(candidate_parsed, indent=2),
            scores_json=json.dumps(scores, indent=2),
        )
        try:
            return await deepseek_chat(prompt, system=EXPLAIN_SYSTEM)
        except Exception:
            try:
                return await ollama_chat(prompt, system=EXPLAIN_SYSTEM)
            except Exception:
                return {
                    "top_strengths": ["Data present in profile"],
                    "missing_skills": ["Unable to determine (AI Offline)"],
                    "adjacent_skills": [],
                    "risk_factors": ["System fallback mode active"],
                    "overall_assessment": "This candidate was evaluated using heuristic rules because the AI reasoning engine was unavailable. Please review the resume manually for precise fit.",
                    "extracted_evidence": [{"claim": "Evaluation Mode", "evidence": "System Fallback"}]
                }