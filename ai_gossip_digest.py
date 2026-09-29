#!/usr/bin/env python3
"""
AI Morning Gossip Digest
-------------------------
Searches a curated list of verified AI-news sources for what happened in the
last 24-48 hours, asks Claude to write it up as a fun "gossip column" style
digest, and emails it to you.

Runs standalone (python ai_gossip_digest.py) or on a schedule via
GitHub Actions (see .github/workflows/daily-ai-gossip.yml).

Required environment variables (set as GitHub Actions secrets, or in a
local .env / your shell, when running manually):
    GEMINI_API_KEY         - your Google AI Studio API key
    GMAIL_ADDRESS          - the Gmail address to send FROM
    GMAIL_APP_PASSWORD     - a 16-character Gmail "app password" (not your
                             normal password — see README.md for how to get one)
    RECIPIENT_EMAIL        - the email address to send the digest TO
                             (defaults to GMAIL_ADDRESS if not set)
"""

import os
import sys
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", GMAIL_ADDRESS)

# Model to use for generation. "gemini-2.5-flash" is fast/cheap and supports
# Google Search grounding, which is what lets this actually search the web
# instead of answering from memory. Swap to "gemini-2.5-pro" for higher
# quality at higher cost if you want.
MODEL = "gemini-3.8-flash"

# Curated list of verified/trustworthy AI-news sources. The model is told to
# restrict its search to these domains. Edit this list to taste.
VERIFIED_SOURCES = [
    "openai.com/blog",
    "openai.com/news",
    "anthropic.com/news",
    "deepmind.google/discover",
    "ai.meta.com/blog",
    "blog.google/technology/ai",
    "microsoft.com/en-us/ai/blog",
    "reuters.com",
    "bloomberg.com",
    "techcrunch.com",
    "theverge.com",
    "wired.com",
    "arstechnica.com",
    "technologyreview.com",
    "arxiv.org",
    "nature.com",
]

SYSTEM_PROMPT = """You are a witty tech-industry insider writing a daily private
email newsletter called "The AI Morning Gossip" for one reader who works in
AI/startups. Your job: search the web for what genuinely happened in the
world of AI in roughly the last 24-48 hours, using ONLY the domains you're
given as sources, and write it up like juicy-but-accurate industry gossip —
sharp, fun, a little cheeky — while staying 100% factually accurate. Never
invent facts, quotes, or events. If you're not sure something is confirmed,
say so plainly instead of hyping it.

Structure the email in this order, using the section headers exactly:

1. "☕ TODAY'S HEADLINE" — the single biggest AI story of the day, 2-3
   sentences, gossip tone but factual.
2. "🔥 THE DRAMA" — any controversies, lawsuits, leadership shakeups, spats
   between labs/companies, or surprising reversals. Skip if genuinely none.
3. "🚀 WHAT SHIPPED" — new models, products, papers, or features released.
   Bullet points, one line each, with the source.
4. "💥 WHO GOT DISRUPTED" — real-world industries, companies, or jobs
   visibly affected by AI this cycle (layoffs attributed to AI, an industry
   adopting/reacting to AI, market moves, regulation, etc).
5. "📎 QUICK HITS" — 3-5 short one-line mentions of smaller but notable
   items, each with its source.

End with a one-line sign-off in the gossip-columnist voice.

Keep the whole email skimmable in under 3 minutes. Always name the source
(e.g. "per TechCrunch", "per OpenAI's blog") next to each claim so the
reader can trust it. Do not fabricate a story just to fill a section —
it's fine for a section to be short or say 'quiet day on this front.'"""


def build_user_prompt() -> str:
    today = datetime.date.today().strftime("%A, %B %d, %Y")
    sources_list = "\n".join(f"- {s}" for s in VERIFIED_SOURCES)
    return f"""Today is {today}.

Search the web for AI news from roughly the last 24-48 hours. Restrict
yourself to information that traces back to these verified sources
(search things like "site:{{domain}}" style queries against this list, or
general queries and then only use results from these domains):

{sources_list}

Now write today's edition of The AI Morning Gossip following the structure
and voice you were given."""


def generate_digest() -> str:
    if not GEMINI_API_KEY:
        sys.exit("Missing GEMINI_API_KEY environment variable.")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{MODEL}:generateContent"
    )

    resp = requests.post(
        url,
        headers={
            "x-goog-api-key": GEMINI_API_KEY,
            "content-type": "application/json",
        },
        json={
            # system_instruction plays the same role as Anthropic's "system"
            # param above: persistent behavior/voice instructions.
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            # "contents" is Gemini's equivalent of "messages" — a list of
            # turns, each with a role and one or more "parts" of content.
            "contents": [
                {"role": "user", "parts": [{"text": build_user_prompt()}]}
            ],
            # This is the Gemini equivalent of Anthropic's web_search tool —
            # "grounding" lets the model run real Google searches before
            # answering, instead of relying on what it already knows.
            "tools": [{"google_search": {}}],
            "generationConfig": {"maxOutputTokens": 2500},
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()

    # Gemini's response shape: data["candidates"][0]["content"]["parts"] is a
    # list of parts (usually just one for a plain-text answer). We join all
    # of them in case the model split its answer across multiple parts.
    try:
        parts = data["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError):
        sys.exit(f"Unexpected response shape from Gemini API: {data}")

    digest = "\n".join(p.get("text", "") for p in parts).strip()

    if not digest:
        sys.exit(f"No text content returned from API. Raw response: {data}")

    return digest


def send_email(body: str) -> None:
    if not (GMAIL_ADDRESS and GMAIL_APP_PASSWORD and RECIPIENT_EMAIL):
        sys.exit(
            "Missing one of GMAIL_ADDRESS / GMAIL_APP_PASSWORD / RECIPIENT_EMAIL "
            "environment variables."
        )

    today = datetime.date.today().strftime("%b %d, %Y")
    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = RECIPIENT_EMAIL
    msg["Subject"] = f"☕ The AI Morning Gossip — {today}"
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())

    print(f"Sent digest to {RECIPIENT_EMAIL}")


def main() -> None:
    print("Generating today's digest...")
    digest = generate_digest()
    print("\n--- DIGEST PREVIEW ---\n")
    print(digest)
    print("\n----------------------\n")
    print("Sending email...")
    send_email(digest)


if __name__ == "__main__":
    main()
