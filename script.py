import os
import re
import json
import time
import requests
import urllib.parse
from datetime import datetime
from google import genai

HISTORY_FILE = "history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not read history file: {e}")
            return []
    return []

def save_history(history):
    # Keep only the last 30 entries to keep file size lightweight
    trimmed_history = history[-30:]
    with open(HISTORY_FILE, "w") as f:
        json.dump(trimmed_history, f, indent=2)

def draft_post():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Critical Error: GEMINI_API_KEY is missing from GitHub Secrets.")
        
    client = genai.Client(api_key=api_key)
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Load past topics to build exclusion context
    history = load_history()
    recent_topics = [f"- {entry.get('topic_summary')}" for entry in history[-15:]]
    history_context = "\n".join(recent_topics) if recent_topics else "None (this is the first post)."

    prompt = f"""
    Act as a pragmatic, highly competent Full-Stack Web Developer writing an honest, engaging LinkedIn post.
    Today's Date: {today_str}

    Target Audience: Founders, CEOs, and Tech Leads of small IT agencies and boutique web dev studios (1 to 15 employees).

    RECENTLY COVERED TOPICS (STRICTLY DO NOT REPEAT OR USE SIMILAR ANGLES):
    {history_context}

    INSTRUCTIONS FOR TOPIC SELECTION:
    Pick ONE specific, realistic scenario or lesson based on one of these core content pillars:
    1. Async Communication & Founder Time-Saving (e.g., Loom videos, clear PRs, Slack updates, managing up).
    2. Code Quality vs. Shipping Speed (e.g., refactoring vs. launching, handling technical debt, pragmatism).
    3. Remote Culture, Ownership, & Hiring (e.g., green/red flags in developer interviews, onboarding into a small team, what makes a dev a true partner vs. just a coder).
    4. Modern Web Stacks & Latest Tech (e.g., evaluating new frameworks vs. sticking to stable tech, APIs, Next.js, AI coding assistants).
    5. Developer Operations & Experience (e.g., CI/CD, testing, staging environments, debugging bottlenecks).
    6. Market Trends & Agency Growth (e.g., shifting client demands, scaling small web apps, the difference between freelance coders and dedicated remote team members).

    Make today's specific angle unique and original. 

    TONE & VOICE RULES (STRICTLY ENFORCE HUMAN STYLE):
    - Write like a real developer having a genuine conversation or sharing a lesson learned on the job.
    - Sound grounded, practical, and direct. Avoid sounding like a marketing blog or motivational speaker.
    - STRICTLY BANNED AI WORDS: Do NOT use "delve", "testament", "realm", "landscape", "game-changer", "unleash", "foster", "elevate", "seamless", "revolutionize", "tapestry", "empower", "passionate", "beacon", "mastery".

    FORMATTING RULES:
    - Length: ~120 to 150 words.
    - Structure: Short, natural paragraphs with conversational flow.
    - NO HASHTAGS.
    - End with a grounded, direct question asking agency founders about how they handle this in their teams.

    CRITICAL INSTRUCTIONS AT THE END:
    On a new line write:
    TOPIC_SUMMARY: [Provide a 1-sentence summary of the core lesson/topic covered in this post]
    On another new line write:
    IMAGE_PROMPT: [Insert a 5 to 10 word visual description of a realistic developer workspace setup]
    """
    
    for attempt in range(3):
        try:
            response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
            return response.text, history
        except Exception as e:
            print(f"Server busy, retrying in 15 seconds... (Attempt {attempt+1}/3)")
            time.sleep(15)
            if attempt == 2:
                raise RuntimeError(f"Gemini API failed after 3 attempts: {e}")

def parse_and_save(post_text, history):
    # Parse TOPIC_SUMMARY for memory tracking
    summary_match = re.search(r'TOPIC_SUMMARY:\s*(.*?)(?=\n|IMAGE_PROMPT:|$)', post_text, flags=re.IGNORECASE | re.DOTALL)
    topic_summary = summary_match.group(1).strip() if summary_match else "General Web Development Best Practices"

    # Clean the post text (remove TOPIC_SUMMARY line from the final post)
    cleaned_post = re.sub(r'TOPIC_SUMMARY:.*?\n', '', post_text, flags=re.IGNORECASE)

    # Save to history file
    today_str = datetime.now().strftime("%Y-%m-%d")
    history.append({
        "date": today_str,
        "topic_summary": topic_summary
    })
    save_history(history)

    return cleaned_post

def send_discord(post_text):
    split_text = re.split(r'IMAGE_PROMPT:\s*', post_text, flags=re.IGNORECASE)
    
    if len(split_text) > 1:
        main_post = split_text[0].strip()
        img_prompt_text = split_text[1].strip()[:100] 
    else:
        main_post = post_text.strip()
        img_prompt_text = "A clean developer setup with dual monitors showing web code"
    
    if len(main_post) > 1900:
        main_post = main_post[:1900] + "... [Truncated to fit Discord limits]"

    encoded_img_prompt = urllib.parse.quote(img_prompt_text)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_img_prompt}?width=1080&height=1080&nologo=true"
    
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("Critical Error: DISCORD_WEBHOOK_URL is missing from GitHub Secrets.")
    
    payload = {
        "content": f"🎯 **Human-Style Tech Draft** 🎯\n\n{main_post}",
        "embeds": [{"image": {"url": image_url}}]
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        print("Successfully sent draft to Discord!")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send to Discord: {e}")

if __name__ == "__main__":
    raw_draft, current_history = draft_post()
    if raw_draft:
        clean_draft = parse_and_save(raw_draft, current_history)
        send_discord(clean_draft)
