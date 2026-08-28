import os
import requests
from google import genai
import urllib.parse
import random

def draft_post():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    
    # Randomizes the topic every day so your posts stay fresh
    topics = ["Web development frameworks", "Software engineering best practices", "Life as a Computer Science student", "IT career growth tips"]
    daily_topic = random.choice(topics)
    
    prompt = f"""
    Write a highly engaging, 150-word LinkedIn post about: {daily_topic}.
    Target Audience: IT professionals, software developers, and CS students.
    Format: Short paragraphs. End with a specific question for the audience.
    At the very end of your response, on a new line, write exactly: 
    IMAGE_PROMPT: [Insert a 5 to 10 word visual description for a related aesthetic image here]
    """
    
    response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
    return response.text

def send_discord(post_text):
    # Separates the post text from the image prompt
    if "IMAGE_PROMPT:" in post_text:
        parts = post_text.split("IMAGE_PROMPT:")
        main_post = parts[0].strip()
        img_prompt_text = parts[1].strip()
    else:
        main_post = post_text
        img_prompt_text = "A software developer coding with glowing screens aesthetic"
        
    # Generates a free AI image using Pollinations AI
    encoded_img_prompt = urllib.parse.quote(img_prompt_text)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_img_prompt}?width=1080&height=1080&nologo=true"
    
    webhook_url = os.environ["DISCORD_WEBHOOK_URL"]
    
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
    requests.post(webhook_url, json=payload)

if __name__ == "__main__":
    draft = draft_post()
    send_discord(draft)
