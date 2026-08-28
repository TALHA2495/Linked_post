import os
import requests
import feedparser
from google import genai

def get_news():
    # Grabs the top 3 headlines from TechCrunch
    feed = feedparser.parse("https://techcrunch.com/feed/")
    return "\n".join([f"- {entry.title}: {entry.summary}" for entry in feed.entries[:3]])

def draft_post(news):
    # Sends news to Gemini API to write the post
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    prompt = f"Write a 150-word LinkedIn post for startup founders based on this news:\n{news}\nWrite in short paragraphs. No jargon. End with a question for founders."
    response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
    return response.text

def send_discord(post_text):
    # Sends the finished draft to your Discord server
    webhook_url = os.environ["DISCORD_WEBHOOK_URL"]
    requests.post(webhook_url, json={"content": f"🚀 **Daily LinkedIn Draft** 🚀\n\n{post_text}"})

if __name__ == "__main__":
    news_data = get_news()
    draft = draft_post(news_data)
    send_discord(draft)
