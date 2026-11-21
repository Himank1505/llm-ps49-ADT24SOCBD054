"""Project Idea Generator (PS 49) - Streamlit UI.

Run:  streamlit run app.py
"""
import os

import streamlit as st
from dotenv import load_dotenv

from ideas import MODEL, generate_ideas, ideas_to_markdown

load_dotenv()  # reads GEMINI_API_KEY from a local .env file (never committed to GitHub)

st.set_page_config(page_title="Project Idea Generator", page_icon="💡", layout="wide")

DOMAINS = [
    "Web Development", "Machine Learning / AI", "Generative AI / LLMs", "Data Science & Analytics",
    "Cybersecurity", "IoT & Embedded Systems", "Mobile Apps", "Cloud & DevOps",
    "Game Development", "Blockchain", "Other (type your own)",
]
BADGE = {"Easy": ":green-badge[Easy]", "Medium": ":orange-badge[Medium]", "Hard": ":red-badge[Hard]"}

# ---------------------------------------------------------------- sidebar: API key
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Gemini API key", type="password", value=os.getenv("GEMINI_API_KEY", ""),
                            help="Free key from https://aistudio.google.com/apikey. Kept only in this session.")
    st.caption(f"Model: `{MODEL}`")
    st.markdown("**How it works**\n\n1. Pick domain, skill level and time.\n2. The app builds a prompt.\n"
                "3. Gemini returns 5 ideas as JSON.\n4. Ideas are shown as cards.")

# ---------------------------------------------------------------- inputs
st.title("💡 Project Idea Generator")
st.write("Stuck choosing a project topic? Tell me your domain, skill level and time, and get 5 ideas "
         "with tools, modules and difficulty.")

c1, c2, c3 = st.columns(3)
with c1:
    domain_choice = st.selectbox("Domain", DOMAINS)
    domain = st.text_input("Your domain", placeholder="e.g. Healthcare, Agriculture, Education") \
        if domain_choice == "Other (type your own)" else domain_choice
with c2:
    level = st.radio("Skill level", ["Beginner", "Intermediate", "Advanced"], horizontal=True)
with c3:
    weeks = st.select_slider("Time available (weeks)", options=list(range(1, 13)), value=2)

if st.button("Generate 5 ideas", type="primary"):
    if not domain.strip():
        st.warning("Please enter a domain.")
    elif not api_key.strip():
        st.warning("Please paste your Gemini API key in the sidebar.")
    else:
        try:
            with st.spinner("Thinking up ideas..."):
                st.session_state["ideas"] = generate_ideas(domain, level, weeks, api_key.strip())
                st.session_state["meta"] = (domain, level, weeks)
        except Exception as e:  # network error, bad key, quota, unreadable reply ...
            st.session_state.pop("ideas", None)
            st.error(f"Could not generate ideas: {e}")

# ---------------------------------------------------------------- output cards
ideas = st.session_state.get("ideas")
if ideas:
    d, l, w = st.session_state["meta"]
    st.subheader(f"Ideas for **{d}** · {l} · {w} week(s)")
    for row_start in range(0, len(ideas), 3):
        cols = st.columns(3)
        for col, idea in zip(cols, ideas[row_start:row_start + 3]):
            with col, st.container(border=True):
                st.markdown(f"### {idea['title']}")
                st.markdown(f"{BADGE[idea['difficulty']]} &nbsp; ⏱ {idea['estimated_time']}")
                st.write(idea["description"])
                st.markdown("**Tools:** " + " · ".join(f"`{t}`" for t in idea["tools"]))
                st.markdown("**Modules:**")
                for i, m in enumerate(idea["modules"], 1):
                    st.markdown(f"{i}. {m}")
                if idea["outcome"]:
                    st.caption(f"🎯 Demo outcome: {idea['outcome']}")
    st.download_button("Download ideas (.md)", ideas_to_markdown(ideas, d, l, w),
                       file_name="project_ideas.md", mime="text/markdown")
