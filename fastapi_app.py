from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

MODEL_NAME = "gemini-2.5-pro-preview-03-25"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
BRIGHTDATA_API_KEY = os.getenv("BRIGHTDATA_API_KEY")
BRIGHTDATA_DATASET_ID = os.getenv("BRIGHTDATA_DATASET_ID")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

def ask_gemini(prompt: str) -> str:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    return getattr(response, "text", "")

def search_brightdata(query: str) -> str:
    url = f"https://api.brightdata.com/dca/{BRIGHTDATA_DATASET_ID}"
    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"query": query}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        return f"Error fetching data from BrightData: {e}"

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    user_message = req.message.strip()
    keywords = ["search", "find", "lookup", "web"]
    if any(word in user_message.lower() for word in keywords):
        web_data = search_brightdata(user_message)
        summary = ask_gemini(f"Summarize this information: {web_data}")
        return {"response": summary}
    else:
        reply = ask_gemini(user_message)
        return {"response": reply}

@app.post("/summarize")
async def summarize_endpoint(req: ChatRequest):
    summary = ask_gemini(f"Summarize this: {req.message}")
    return {"summary": summary}
