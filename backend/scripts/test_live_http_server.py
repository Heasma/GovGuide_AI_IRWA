import asyncio
import json
import uuid
import sys
import os
import httpx

queries = [
    ("A", "enna enna business licence inga edukkalam"),
    ("B", "enna enna business license inga edulkkalam"),
    ("C", "enna enna licence inga edukkalam"),
    ("D", "what business licenses are available"),
    ("E", "naan restaurant open panna poren enna licence venum?"),
    ("F", "naan dress shop start panna poren"),
    ("G", "naan business start panna poren enna license venum?"),
    ("H", "ennaku licence edukanum"),
]

async def run():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=30.0) as client:
        # Register and login to get auth token
        email = f"live_http_runner_{uuid.uuid4().hex[:6]}@example.com"
        pwd = "Password123!"
        reg = await client.post("/api/v1/auth/register", json={"email": email, "password": pwd})
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        print("\n" + "=" * 80)
        print("GOVGUIDE AI — LIVE SERVER VALIDATION (http://127.0.0.1:8000/api/v1/query)")
        print("=" * 80 + "\n")

        for code, q in queries:
            resp = await client.post(
                "/api/v1/query",
                json={"query": q, "session_id": str(uuid.uuid4())},
                headers=headers,
            )
            data = resp.json()
            print(f"=== TEST CASE {code}: \"{q}\" ===")
            print(f"HTTP Status:        {resp.status_code}")
            print(f"Confidence Score:   {data.get('confidence_score')}")
            print(f"Confidence Label:   {data.get('confidence_label')}")
            print(f"Explanation:        {data.get('explanation')}")
            print(f"Sources Count:      {len(data.get('sources', []))}")
            for s in data.get("sources", []):
                print(f"  - [{s.get('source_id')}] {s.get('title')}: {s.get('url')}")
            print("--- ANSWER ---")
            print(str(data.get("answer")))
            print("\n" + "-" * 80 + "\n")

if __name__ == "__main__":
    asyncio.run(run())
