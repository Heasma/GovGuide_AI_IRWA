import asyncio
import json
import uuid
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.nlp.activity_extractor import extract_business_activity
from app.nlp.intent_classifier import classify_intent, classify_intents

queries = [
    ("1", "enna enna business license inga edulkkalam"),
    ("2", "What business licenses are available?"),
    ("3", "show me all available business licenses"),
    ("4", "I want to start a restaurant. Which license do I need?"),
    ("5", "I want to start a dress shop. Which license do I need?"),
    ("6", "I want to start a business. Which license do I need?"),
    ("7", "ennaku licence edukanum"),
]

async def run():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register and login to get auth token
        email = f"catalog_runner_{uuid.uuid4().hex[:6]}@example.com"
        pwd = "Password123!"
        reg = await client.post("/api/v1/auth/register", json={"email": email, "password": pwd})
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        for code, q in queries:
            primary_intent = classify_intent(q)
            all_intents = classify_intents(q)
            act = extract_business_activity(q)
            resp = await client.post(
                "/api/v1/query",
                json={"query": q, "session_id": str(uuid.uuid4())},
                headers=headers,
            )
            data = resp.json()
            print(f"=== TEST CASE {code}: \"{q}\" ===")
            print(f"Primary Intent: {primary_intent.value if hasattr(primary_intent, 'value') else primary_intent}")
            print(f"All Classified Intents: {[it.value if hasattr(it, 'value') else it for it in all_intents]}")
            print(f"Business Activity: {act.activity_type.value} (is_generic: {act.is_generic_or_ambiguous})")
            print("HTTP Status:", resp.status_code)
            print("Confidence Score:", data.get("confidence_score"))
            print("Confidence Label:", data.get("confidence_label"))
            print("Caveats:", data.get("caveats"))
            print("Explanation:", data.get("explanation"))
            sources = data.get("sources", [])
            print(f"Sources ({len(sources)}):")
            for s in sources:
                print(f"  - [{s.get('source_id')}] {s.get('title')}: {s.get('url')}")
            print("--- ANSWER ---")
            print(str(data.get("answer")))
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    asyncio.run(run())
