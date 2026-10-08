import asyncio
import json
import uuid
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.nlp.activity_extractor import extract_business_activity

queries = [
    ("A", "I want to start a restaurant. Which license do I need?"),
    ("B", "I want to start a dress shop. Which license do I need?"),
    ("C", "I want to open a clothing store."),
    ("D", "I want to start XYZABC123 business. Which license should I get?"),
    ("E", "I want to start a business. Which license do I need?"),
    ("F", "ennaku licence edukanum"),
]

async def run():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register and login to get auth token
        email = f"test_runner_{uuid.uuid4().hex[:6]}@example.com"
        pwd = "Password123!"
        reg = await client.post("/api/v1/auth/register", json={"email": email, "password": pwd})
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        for code, q in queries:
            act = extract_business_activity(q)
            resp = await client.post(
                "/api/v1/query",
                json={"query": q, "session_id": str(uuid.uuid4())},
                headers=headers,
            )
            data = resp.json()
            print(f"=== TEST {code}: \"{q}\" ===")
            print(f"Detected Business Activity: {act.activity_type.value} (text: '{act.extracted_text}', is_food: {act.is_food_related}, is_generic: {act.is_generic_or_ambiguous})")
            print("Status Code:", resp.status_code)
            print("Answer:\n" + str(data.get("answer")))
            print("Confidence Score:", data.get("confidence_score"))
            print("Confidence Label:", data.get("confidence_label"))
            print("Caveats:", data.get("caveats"))
            print("Explanation:", data.get("explanation"))
            print("Sources count:", len(data.get("sources", [])))
            for s in data.get("sources", []):
                print(f"  - [{s.get('source_id')}] {s.get('title')}: {s.get('url')}")
            print("Is Demo:", data.get("is_demo"))
            print("Is Conversational:", data.get("is_conversational"))
            print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    asyncio.run(run())
