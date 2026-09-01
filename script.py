import os
import re
import time
import requests
import urllib.parse
from datetime import datetime
from google import genai

def draft_post():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Critical Error: GEMINI_API_KEY is missing from GitHub Secrets.")
        
    client = genai.Client(api_key=api_key)
    
    # Uses today's date as a unique seed so the AI never generates the same scenario twice
    today_str = datetime.now().strftime("%A, %B %d, %Y")
    
    prompt = f"""
    Act as a pragmatic, highly competent Full-Stack Web Developer writing an honest, engaging LinkedIn post.
    Today's Date: {today_str}

    Target Audience: Founders, CEOs, and Tech Leads of small IT agencies and boutique web dev studios (1 to 15 employees).

    INSTRUCTIONS FOR TOPIC SELECTION:
    Pick ONE specific, realistic scenario or lesson based on one of these core content pillars:
    1. Async Communication & Founder Time-Saving (e.g., Loom videos, clear PRs, Slack updates, managing up).
    2. Code Quality vs. Shipping Speed (e.g., refactoring vs. launching, handling technical debt, pragmatism).
    3. Remote Culture & Ownership (e.g., proactive problem solving, taking initiative, asking clarifying questions).
    4. Modern Web Stacks & Architecture (e.g., Next.js, APIs, state management, database bottlenecks).
    5. Developer Operations & Developer Experience (e.g., CI/CD, testing, staging environments, debugging).

    Make today's specific angle unique and original. Do NOT repeat broad or generic advice.

    TONE & VOICE RULES (STRICTLY ENFORCE HUMAN STYLE):
    - Write like a real developer having a genuine conversation or sharing a lesson learned on the job.
    - Sound grounded, practical, and direct. Avoid sounding like a marketing blog or motivational speaker.
    - STRICTLY BANNED AI WORDS: Do NOT use "delve", "testament", "realm", "landscape", "game-changer", "unleash", "foster", "elevate", "seamless", "revolutionize", "tapestry", "empower", "passionate", "beacon", "mastery".
    - Use real-world dev context (e.g., PR reviews, async updates, Loom walkthroughs, refactoring, edge cases, clear Git commits).

    FORMATTING RULES:
    - Length: ~120 to 150 words.
    - Structure: Short, natural paragraphs with conversational flow.
    - NO HASHTAGS.
    - End with a grounded, direct question asking agency founders about how they handle this in their teams.

    CRITICAL INSTRUCTION:
    At the very end of your response, on a new line, write exactly: 
    IMAGE_PROMPT: [Insert a 5 to 10 word visual description of a realistic, aesthetic developer workspace setup]
    """
    
    # 3-attempt retry loop for API stability
    for attempt in range(3):
        try:
            response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
            return response.text
        except Exception as e:
            print(f"Server busy, retrying in 15 seconds... (Attempt {attempt+1}/3)")
            time.sleep(15)
            if attempt == 2:
                raise RuntimeError(f"Gemini API failed after 3 attempts: {e}")

def send_discord(post_text):
    split_text = re.split(r'IMAGE_PROMPT:\s*', post_text, flags=re.IGNORECASE)
    
    if len(split_text) > 1:
        main_post = split_text[0].strip()
        img_prompt_text = split_text[1].strip()[:100] 
    else:
        main_post = post_text.strip()
        img_prompt_text = "A clean developer setup with dual monitors showing web code and a warm desk lamp"
    
    if len(main_post) > 1900:
        main_post = main_post[:1900] + "... [Truncated to fit Discord limits]"

    encoded_img_prompt = urllib.parse.quote(img_prompt_text)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_img_prompt}?width=1080&height=1080&nologo=true"
    
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("Critical Error: DISCORD_WEBHOOK_URL is missing from GitHub Secrets.")
    
    payload = {
        "content": f"🎯 **Human-Style Tech Draft** 🎯\n\n{main_post}",
        "embeds": [
            {
                "image": {
                    "url": image_url
                }
            }
        ]
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        print("Successfully sent draft to Discord!")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send to Discord: {e}")

if __name__ == "__main__":
    draft = draft_post()
    if draft:
        send_discord(draft)
