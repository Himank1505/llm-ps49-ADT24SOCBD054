"""Core logic for the Project Idea Generator (PS 49): prompt building, LLM call, parsing.

The UI (app.py) only calls generate_ideas(); everything that can be tested without a
browser lives here.
"""
import json
import os
import re

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
NUM_IDEAS = 5
DIFFICULTIES = ("Easy", "Medium", "Hard")
REQUIRED_KEYS = ("title", "description", "tools", "modules", "difficulty")

PROMPT_TEMPLATE = """You are a friendly academic mentor helping a final-year engineering student choose a project topic.

Student profile:
- Domain: {domain}
- Skill level: {level}
- Time available: {weeks} week(s)

Task: suggest exactly {n} DIFFERENT project ideas for this student.

Rules:
1. Every idea must be realistically finishable by this student in {weeks} week(s) at the "{level}" level.
   A Beginner gets simple, well-documented tools; an Advanced student may get harder ideas.
2. The ideas must be clearly different from each other (different problem, not variations of one app).
3. "difficulty" must be exactly one of: Easy, Medium, Hard, and must be consistent with the skill level
   and the time available (do not label a 1-week idea "Hard" for a Beginner).
4. "tools" lists 3-5 concrete tools / libraries / services (e.g. Python, Streamlit, scikit-learn).
5. "modules" lists 3-5 short build steps or components in the order a student would build them.
6. "description" is 2 sentences: what the project does and who it helps.

Return ONLY a JSON array of {n} objects, no markdown, no commentary. Each object must have exactly these keys:
"title" (string), "description" (string), "tools" (array of strings), "modules" (array of strings),
"difficulty" (string), "estimated_time" (string, e.g. "10 days"), "outcome" (string, one line on what the student can demo).
"""


def build_prompt(domain: str, level: str, weeks: int, n: int = NUM_IDEAS) -> str:
    """Fill the prompt template with the student's three inputs."""
    return PROMPT_TEMPLATE.format(domain=domain.strip(), level=level, weeks=weeks, n=n)


def _extract_json(text: str):
    """Parse the model reply even if it wrapped the JSON in ``` fences or added extra text."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("["), text.rfind("]")
        if start != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise


def _clean_idea(raw: dict) -> dict:
    """Keep only the fields the UI needs and make sure they have the right types."""
    def as_list(v):
        if isinstance(v, str):
            return [p.strip() for p in re.split(r"[,;\n]", v) if p.strip()]
        return [str(x).strip() for x in (v or []) if str(x).strip()]

    difficulty = str(raw.get("difficulty", "Medium")).strip().capitalize()
    if difficulty not in DIFFICULTIES:
        difficulty = "Medium"
    return {
        "title": str(raw["title"]).strip(),
        "description": str(raw["description"]).strip(),
        "tools": as_list(raw["tools"]),
        "modules": as_list(raw["modules"]),
        "difficulty": difficulty,
        "estimated_time": str(raw.get("estimated_time", "")).strip(),
        "outcome": str(raw.get("outcome", "")).strip(),
    }


def parse_ideas(text: str) -> list:
    """Turn the raw LLM reply into a list of cleaned idea dicts (raises ValueError if unusable)."""
    data = _extract_json(text)
    if isinstance(data, dict):  # some models return {"ideas": [...]}
        data = next((v for v in data.values() if isinstance(v, list)), [])
    ideas = []
    for item in data:
        if isinstance(item, dict) and all(k in item for k in REQUIRED_KEYS):
            ideas.append(_clean_idea(item))
    if not ideas:
        raise ValueError("The model reply did not contain any usable ideas.")
    return ideas


def call_llm(prompt: str, api_key: str) -> str:
    """Send the prompt to Gemini and return the raw text reply."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.9,                       # higher = more varied ideas
            response_mime_type="application/json",  # ask Gemini for JSON directly
        ),
    )
    return response.text or ""


def generate_ideas(domain: str, level: str, weeks: int, api_key: str, llm=call_llm) -> list:
    """Full pipeline: build prompt -> call LLM -> parse. Retries once if the reply is not valid."""
    prompt = build_prompt(domain, level, weeks)
    last_error = None
    for _ in range(2):
        reply = llm(prompt, api_key)
        try:
            return parse_ideas(reply)
        except (ValueError, json.JSONDecodeError, KeyError) as e:
            last_error = e
    raise ValueError(f"Could not read the model's reply after 2 tries: {last_error}")


def ideas_to_markdown(ideas: list, domain: str, level: str, weeks: int) -> str:
    """Plain-text export of the ideas, for the download button."""
    lines = [f"# Project ideas: {domain} ({level}, {weeks} week(s))", ""]
    for i, idea in enumerate(ideas, 1):
        lines += [
            f"## {i}. {idea['title']}  [{idea['difficulty']}]",
            idea["description"],
            f"- Estimated time: {idea['estimated_time']}",
            f"- Tools: {', '.join(idea['tools'])}",
            f"- Modules: {' -> '.join(idea['modules'])}",
            f"- Demo outcome: {idea['outcome']}",
            "",
        ]
    return "\n".join(lines)
