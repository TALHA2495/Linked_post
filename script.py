import os
import re
import time
import random
import requests
import urllib.parse
from google import genai

def draft_post():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Critical Error: GEMINI_API_KEY is missing from GitHub Secrets.")
        
    client = genai.Client(api_key=api_key)
    
    # Grounded, highly realistic topics tailored for founders of small web dev teams (1–15 people)
    topics = [
        "Why the best developer on a 10-person team is usually the one who asks clarifying questions before writing code",
        "How sending a 2-minute Loom video with your PR saves agency founders hours of testing",
        "The real difference between code that just works and code a small team can actually maintain a year later",
        "Why small agency founders don't need 'hero coders'—they need developers who own outcomes",
        "How proactive async updates on Slack prevent founder micro-management before it even starts"
    ]
    daily_topic = random.choice(topics)
    
    prompt = f"""
    Write a LinkedIn post as a pragmatic, hands-on Full-Stack Web Developer sharing an honest workplace insight.

    Topic: {daily_topic}
    Audience: Founders, CEOs, and Tech Leads of small IT agencies and boutique dev studios (1 to 15 employees).

    TONE & VOICE RULES (STRICTLY ENFORCE HUMAN STYLE):
    - Write like a real developer having a genuine conversation over coffee or dropping an honest thought on LinkedIn.
    - Sound grounded, practical, and direct. Avoid sounding like a marketing blog, motivational speaker, or textbook.
    - STRICTLY BANNED AI WORDS: Do NOT use "delve", "testament", "realm", "landscape", "game-changer", "unleash", "foster", "elevate", "seamless", "revolutionize", "tapestry", "empower", "passionate", "beacon", "mastery".
    - Use real-world dev context (e.g., PR reviews, async updates, Loom walkthroughs, refactoring, edge cases, clear Git commits).
    - Show strong cultural fit: highlight taking initiative, respecting founder time, and writing clean, readable web code.

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
    # Regex handles casing variations gracefully
    split_text = re.split(r'IMAGE_PROMPT:\s*', post_text, flags=re.IGNORECASE)
    
    if len(split_text) > 1:
        main_post = split_text[0].strip()
        img_prompt_text = split_text[1].strip()[:100] 
    else:
        main_post = post_text.strip()
        img_prompt_text = "A clean developer setup with dual monitors showing web code and a warm desk lamp"
    
    # Enforce Discord limits
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
