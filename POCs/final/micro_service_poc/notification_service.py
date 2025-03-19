from fastapi import FastAPI, HTTPException

app = FastAPI()


# In a real service, this would integrate with an email/SMS gateway
@app.post("/notifications/send")
async def send_notification(notification: dict):
    user_id = notification.get("user_id")
    message = notification.get("message")

    if not user_id or not message:
        raise HTTPException(status_code=400, detail="user_id and message are required")

    print(f"Sending notification to {user_id}: {message}")  # Mock sending
    return {"status": "sent", "user_id": user_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8004)
