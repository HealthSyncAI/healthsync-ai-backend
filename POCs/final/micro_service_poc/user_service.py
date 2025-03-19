# user_service.py
from fastapi import FastAPI, HTTPException

app = FastAPI()

# Mock database (replace with PostgreSQL in a real implementation)
users_db = {
    "user1": {"user_id": "user1", "role": "patient", "name": "Alice"},
    "user2": {"user_id": "user2", "role": "doctor", "name": "Dr. Bob"},
}


@app.get("/users/{user_id}")
def get_user(user_id: str):
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/users/add")
def add_user(user: dict):
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    if users_db.get(user_id) is not None:
        raise HTTPException(status_code=409, detail="User already exists")

    users_db[user_id] = user
    return {"message": f"User {user_id} has added"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
