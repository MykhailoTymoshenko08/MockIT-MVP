import os
import json
import time
import fitz
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from openai import OpenAI

app = FastAPI(title="Recruitment Suite: MockIT & Speed-Dating")


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY", "default_key_to_prevent_crash"),
)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        return "".join(page.get_text() for page in doc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF reading error: {str(e)}")

def parse_ai_json(raw_text: str):
    """Smart JSON extraction: saves the day if AI adds extra text to the response"""
    text = raw_text.strip()
    start = min([text.find('{'), text.find('[')] + [float('inf')])
    end = max(text.rfind('}'), text.rfind(']'))
    
    if start != float('inf') and end != -1:
        return json.loads(text[int(start):end+1])
    return json.loads(text) 

def call_openrouter_with_retry(prompt: str, max_retries: int = 3):
    delay = 2 
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="nvidia/nemotron-3-super-120b-a12b:free",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                timeout=45.0 
            )
            return parse_ai_json(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Waiting {delay} seconds before the next attempt...")
                time.sleep(delay)
                delay *= 2
            else:
                raise Exception(f"All 3 attempts exhausted. Server is overloaded.")

@app.post("/analyze/")
async def analyze_cv(role: str = Form(...), file: UploadFile = File(...)):
    cv_text = extract_text_from_pdf(await file.read())
    
    prompt = f"""Analyze the CV for the position of '{role}'. Resume text: {cv_text[:1500]}. 
    Generate 5 interview questions. Format - ONLY JSON array: [{{"question": "...", "expected_answer": "...", "red_flags": "..."}}]"""
    
    try:
        data = call_openrouter_with_retry(prompt)
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": f"AI Error (Analysis): {str(e)}"}

@app.post("/screening/")
async def generate_screening(role: str = Form(...), file: UploadFile = File(...)):
    cv_text = extract_text_from_pdf(await file.read())
    
    prompt = f"""You are an IT recruiter. Write a message to a candidate for the '{role}' position (resume: {cv_text[:1500]}).
    Format - ONLY JSON: {{"message": "Message text", "internal_notes": "Note for HR"}}."""
    
    try:
        data = call_openrouter_with_retry(prompt)
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": f"AI Error (Screening): {str(e)}"}