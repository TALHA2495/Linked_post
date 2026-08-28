import os
import re
import time
import random
import requests
import urllib.parse
from google import genai

def draft_post():
    # Validates that the API key exists to prevent cryptic tracebacks
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Critical Error: GEMINI_API_KEY is missing from GitHub Secrets.")
        
    client = genai.Client(api_key=api_key)
    
    # Expanded topic list for better long-term variety
    topics = [
        "Web development frameworks and trends", 
        "Software engineering best practices", 
        "Life and struggles as a Computer Science student", 
        "IT career growth and networking tips",
        "The reality of debugging and coding daily"
    ]
    daily_topic = random.choice(topics)
    
    prompt = f"""
    Write a highly engaging, 150-word LinkedIn post about: {daily_topic}.
    Target Audience: IT professionals, software developers, and CS students.
    Format: Short paragraphs. No hashtags. End with a specific question for the audience.
    
    CRITICAL INSTRUCTION:
    At the very end of your response, on a new line, write exactly: 
    IMAGE_PROMPT: [Insert a 5 to 10 word visual description for a related aesthetic image here]
    """
    
    # Retry mechanism for temporary server overloads
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
    # Regex handles AI casing inconsistencies (e.g., "Image Prompt:", "IMAGE_PROMPT:", "image prompt:")
    split_text = re.split(r'IMAGE_PROMPT:\s*', post_text, flags=re.IGNORECASE)
    
    if len(split_text) > 1:
        main_post = split_text[0].strip()
        img_prompt_text = split_text[1].strip()
        # Truncates the image prompt to 100 characters in case the AI generated a massive paragraph
        img_prompt_text = img_prompt_text[:100] 
    else:
        main_post = post_text.strip()
        img_prompt_text = "A software developer coding with glowing screens aesthetic"
    
    # Discord enforces a strict 2000 character limit for messages
    if len(main_post) > 1900:
        main_post = main_post[:1900] + "... [Truncated to fit Discord limits]"

    encoded_img_prompt = urllib.parse.quote(img_prompt_text)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_img_prompt}?width=1080&height=1080&nologo=true"
    
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("Critical Error: DISCORD_WEBHOOK_URL is missing from GitHub Secrets.")
    
    payload = {
        "content": f"🚀 **Daily Tech Draft** 🚀\n\n{main_post}",
        "embeds": [
            {
                "image": {
                    "url": image_url
                }
            }
        ]
    }
    
    # Added a 10-second timeout to prevent the script from hanging indefinitely
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        print("Successfully sent to Discord!")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send to Discord: {e}")

if __name__ == "__main__":
    draft = draft_post()
    if draft:
        send_discord(draft)
