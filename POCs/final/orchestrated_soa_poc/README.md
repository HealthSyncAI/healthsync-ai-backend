```angular2html
pip install -r requirements.txt
```
```angular2html
uvicorn orchestrator:app --reload --port 8000
uvicorn auth_service:app --reload --port 8001
uvicorn appointment_service:app --reload --port 8002
uvicorn symptom_service:app --reload --port 8003
uvicorn notification_service:app --reload --port 8004
```

```angular2html
curl -X POST -H "Content-Type: application/json" -d '{"patient_id": 1, "symptom": "fever", "appointment_time": "2024-03-16 10:00"}' http://localhost:8000/schedule_appointment
```