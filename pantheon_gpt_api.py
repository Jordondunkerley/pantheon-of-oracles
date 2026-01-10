from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os

app = FastAPI()

API_SECRET = os.getenv("PANTHEON_GPT_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("PANTHEON_GPT_MODEL", "gpt-4o-mini")

client = OpenAI(api_key=OPENAI_API_KEY)

class OracleUpdate(BaseModel):
    command: str
    oracle_name: str
    action: str
    metadata: dict

@app.post("/gpt/update-oracle")
async def update_oracle(data: OracleUpdate, request: Request):
    token = request.headers.get("Authorization")
    if token != f"Bearer {API_SECRET}":
        raise HTTPException(status_code=403, detail="Unauthorized")

    print(f"Received GPT update: {data.dict()}")

    # Call the configured GPT model to process the update
    prompt = (
        f"Oracle: {data.oracle_name}\n"
        f"Command: {data.command}\n"
        f"Action: {data.action}\n"
        f"Metadata: {data.metadata}"
    )

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
        )
        gpt_message = completion.choices[0].message["content"].strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "status": "success",
        "message": f"{data.oracle_name} will be {data.action}",
        "model": MODEL_NAME,
        "gpt_response": gpt_message,
    }
