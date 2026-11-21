# Project Idea Generator (LLM Mini Project, PS 49)

**Problem statement:** Students struggle to pick project topics. This app generates 5 project ideas, with
tools, build modules and difficulty, from a chosen domain, skill level and available time.

Built by Himank Maheshwari (Roll No. 49), MIT-ADT Pune. Python · Streamlit · Gemini API (`gemini-3.5-flash`).

## How it works
1. The student picks a **domain**, **skill level** (Beginner / Intermediate / Advanced) and **time** (1-12 weeks).
2. `ideas.py` fills a prompt template with those three inputs and asks Gemini for a JSON array of 5 ideas.
3. The reply is parsed and checked (fenced or extra text is stripped; one retry if unreadable).
4. `app.py` shows each idea as a card: title, difficulty badge, time, description, tools, modules, demo outcome.

## Run it
```bash
pip install -r requirements.txt
cp .env.example .env        # then put your free key from https://aistudio.google.com/apikey in .env
streamlit run app.py
```
You can also paste the key into the sidebar instead of using `.env`. The `.env` file is git-ignored.

## Test (no API key needed)
```bash
python -m unittest test_ideas.py
```

## Files
| File | Purpose |
|---|---|
| `app.py` | Streamlit UI (inputs, cards, download button) |
| `ideas.py` | Prompt, Gemini call, JSON parsing and validation |
| `test_ideas.py` | Unit tests using a fake LLM |
| `requirements.txt` | Python dependencies |

## Screenshots
Add 1-2 screenshots of the app here (e.g. `screenshots/output1.png`).
