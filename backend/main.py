import os
import json
import time
import fitz
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from openai import OpenAI

# initializing the core app for the recruitment suite
app = FastAPI(title="Recruitment Suite: MockIT & Speed-Dating")

# setup openrouter client with a fallback key to avoid startup crashes
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY", "default_key_to_prevent_crash"),
)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """extracts raw text content from uploaded pdf bytes using pymupdf"""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        return "".join(page.get_text() for page in doc)
    except Exception as e:
        # standard 400 error if the file is corrupted or unreadable
        raise HTTPException(status_code=400, detail=f"PDF reading error: {str(e)}")

def parse_ai_json(raw_text: str):
    """safely extracts json content even if the model includes conversational fluff"""
    text = raw_text.strip()
    # finding indices of brackets to isolate the json block
    start = min([text.find('{'), text.find('[')] + [float('inf')])
    end = max(text.rfind('}'), text.rfind(']'))
    
    if start != float('inf') and end != -1:
        return json.loads(text[int(start):end+1])
    return json.loads(text) 

def call_openrouter_with_retry(prompt: str, max_retries: int = 3):
    """handles model requests with exponential backoff for stability"""
    delay = 2 
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="nvidia/nemotron-3-super-120b-a12b:free",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1, # low temperature for more consistent json structure
                timeout=45.0 
            )
            return parse_ai_json(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                # wait and scale the delay before retrying
                print(f"Waiting {delay} seconds before the next attempt...")
                time.sleep(delay)
                delay *= 2
            else:
                # final fail state if all retries fail
                raise Exception(f"All 3 attempts exhausted. Server is overloaded.")

@app.post("/analyze/")
async def analyze_cv(role: str = Form(...), file: UploadFile = File(...)):
    """endpoint to process a cv and generate specific interview questions"""
    cv_text = extract_text_from_pdf(await file.read())
    
    # limited to 1500 chars to stay within context windows and reduce latency
    prompt = f"""Analyze the CV for the position of '{role}'. Resume text: {cv_text[:1500]}. 
    Generate 5 interview questions. Format - ONLY JSON array: [{{"question": "...", "expected_answer": "...", "red_flags": "..."}}]"""
    
    try:
        data = call_openrouter_with_retry(prompt)
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": f"AI Error (Analysis): {str(e)}"}

@app.post("/screening/")
async def generate_screening(role: str = Form(...), file: UploadFile = File(...)):
    """generates a personalized recruiter reach-out message based on cv data"""
    cv_text = extract_text_from_pdf(await file.read())
    
    prompt = f"""You are an IT recruiter. Write a message to a candidate for the '{role}' position (resume: {cv_text[:1500]}).
    Format - ONLY JSON: {{"message": "Message text", "internal_notes": "Note for HR"}}."""
    
    try:
        # calling the same retry logic to ensure high success rate for the outreach
        data = call_openrouter_with_retry(prompt)
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": f"AI Error (Screening): {str(e)}"}