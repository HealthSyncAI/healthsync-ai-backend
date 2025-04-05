import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI()


HUGGING_FACE_API_URL = "https://your-huggingface-endpoint"
HUGGING_FACE_API_KEY = "your_api_key"


async def call_huggingface_api(prompt: str):
    headers = {"Authorization": f"Bearer {HUGGING_FACE_API_KEY}"}
    data = {"inputs": prompt}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                HUGGING_FACE_API_URL, headers=headers, json=data
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Chatbot service unavailable")
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Chatbot API Error: {e.response.text}",
            )


@app.post("/chatbot/ask")
async def ask_chatbot(question: dict):
    user_question = question.get("question")
    if not user_question:
        raise HTTPException(status_code=400, detail="Question is required")



    chatbot_response = {
        "generated_text": f"Mock response for: {user_question}"
    }

    return {"response": chatbot_response}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
