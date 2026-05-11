from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
import re

app = FastAPI()

# Load SHL catalog
url = "https://tcp-us-prod-rnd.shl.com/voiceRater/shl-ai-hiring/shl_product_catalog.json"

response = requests.get(url)

text_data = response.text

# Clean invalid characters
clean_text = re.sub(r'[\x00-\x1F\x7F]', '', text_data)

catalog = json.loads(clean_text)

# Request schema
class ChatRequest(BaseModel):
    messages: list

# Ignore common useless words
stop_words = [
    "i", "need", "want", "assessment", "test",
    "developer", "for", "a", "an", "the",
    "role", "job"
]

# Health endpoint
@app.get("/health")
def health():
    return {"status": "ok"}

# Chat endpoint
@app.post("/chat")
def chat(data: ChatRequest):

    # Read FULL conversation history
    user_message = " ".join(
        [msg["content"] for msg in data.messages]
    ).lower()

    recommendations = []

    # OFF-TOPIC REFUSAL
    off_topic_words = [
        "weather",
        "football",
        "movie",
        "politics"
    ]

    for word in off_topic_words:

        if word in user_message:

            return {
                "reply": "I can only assist with SHL assessment recommendations and related queries.",
                "recommendations": [],
                "end_of_conversation": False
            }

    # COMPARE FEATURE
    if "compare" in user_message:

        return {
            "reply": "Comparison feature is currently basic. Please specify two SHL assessments to compare.",
            "recommendations": [],
            "end_of_conversation": False
        }

    # Extract useful words
    query_words = []

    for word in user_message.split():

        if word not in stop_words and len(word) > 2:
            query_words.append(word)

    # If query too vague
    if len(query_words) == 0:

        return {
            "reply": "Please specify the role, skills, seniority level, or assessment type you are hiring for.",
            "recommendations": [],
            "end_of_conversation": False
        }

    # Search SHL catalog
    for item in catalog:

        item_text = str(item).lower()

        score = 0

        for word in query_words:

            if word in item_text:
                score += 1

        # Relevant match
        if score > 0:

            recommendations.append({
                "score": score,
                "name": item.get("name", "Unknown"),
                "url": item.get("link", ""),
                "test_type": "Assessment"
            })

    # Sort by relevance
    recommendations = sorted(
        recommendations,
        key=lambda x: x["score"],
        reverse=True
    )

    # Keep top 5
    recommendations = recommendations[:5]

    # Remove score field
    final_recommendations = []

    for item in recommendations:

        final_recommendations.append({
            "name": item["name"],
            "url": item["url"],
            "test_type": item["test_type"]
        })

    # Return recommendations
    if final_recommendations:

        return {
            "reply": "Here are recommended SHL assessments.",
            "recommendations": final_recommendations,
            "end_of_conversation": False
        }

    # No matches found
    return {
        "reply": "I could not find matching SHL assessments. Please refine the role or required skills.",
        "recommendations": [],
        "end_of_conversation": False
    }