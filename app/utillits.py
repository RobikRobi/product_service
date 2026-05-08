import os
import httpx
from fastapi import HTTPException




USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://127.0.0.1:8001")
HTTP_CLIENT = httpx.AsyncClient(timeout=10.0, trust_env=False)


async def get_user_from_users_service(user_id: int) -> dict:
    try:
        response = await HTTP_CLIENT.get(f"{USERS_SERVICE_URL}/users/{user_id}")
    except httpx.HTTPError as error:
        raise HTTPException(status_code=502, detail=f"users_service unavailable: {error}") from error

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found in users_service")
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Unexpected users_service response: {response.text}")
    return response.json()
