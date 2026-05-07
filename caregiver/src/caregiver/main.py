import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from caregiver.config import Settings

settings = Settings()

app = FastAPI()

GOOGLE_JSON = settings.GOOGLE_JSON

print(GOOGLE_JSON)
print(GOOGLE_JSON.keys())
GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET.get_secret_value()
GOOGLE_SHEET_ID = settings.GOOGLE_SHEET_ID
SHEET_NAME = "records"
APP_URL = settings.APP_URL

REDIRECT_URI = f"{APP_URL}/auth/callback"
SCOPES = "openid email profile"
ALLOWED_EMAILS = settings.ALLOWED_EMAILS


# ── Models ────────────────────────────────────────────────────────────────────

class EntryRequest(BaseModel):
    fecha: str
    horas: float
    comentario: Optional[str] = ""


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.get("/auth/login")
def login():
    params = (
        f"client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={SCOPES}"
        f"&access_type=offline"
        f"&prompt=select_account"
    )
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@app.get("/auth/callback")
async def callback(code: str):
    async with httpx.AsyncClient() as client:
        r = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        })
    if r.status_code != 200:
        raise HTTPException(400, "Error obteniendo token de Google")
    tokens = r.json()
    access_token = tokens["access_token"]

    # Get user info
    async with httpx.AsyncClient() as client:
        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(
                401,
                "No se pudo obtener información del usuario"
            )

        email = userinfo_response.json().get("email")

        # Restrict access
        if email.lower() not in ALLOWED_EMAILS:
            raise HTTPException(
                status_code=403,
                detail=f"Usuario no autorizado: {email}"
            )

    return RedirectResponse(f"/?access_token={access_token}")


@app.get("/auth/userinfo")
async def userinfo(access_token: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
    if r.status_code != 200:
        raise HTTPException(401, "Token inválido")
    return r.json()

def get_google_token() -> str:
    """
    Method to get google token
    """
    creds = service_account.Credentials.from_service_account_info(
        GOOGLE_JSON,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
        ]
    )
    creds.refresh(Request())

    return creds.token


# ── Sheets ────────────────────────────────────────────────────────────────────
@app.post("/api/register")
async def registro(entry: EntryRequest):
    from datetime import datetime
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")

    values = [[entry.fecha, entry.horas, entry.comentario, ahora]]

    if entry.fecha == "":
        raise HTTPException(status_code=400, detail="La fecha es requerida")
    if entry.horas <= 0 or entry.horas > 24:
        raise HTTPException(status_code=400, detail="Las horas deben ser mayores a 0 o menor a 24")

    check_url = (
            f"https://sheets.googleapis.com/v4/spreadsheets/{GOOGLE_SHEET_ID}"
            f"/values/{SHEET_NAME}!A:A"
        )

    async with httpx.AsyncClient() as client:
        check_response = await client.get(
            check_url,
            headers={
                "Authorization": f"Bearer {get_google_token()}",
            },
        )

        if check_response.status_code != 200:
            raise HTTPException(
                check_response.status_code,
                "Error checking existing entries"
            )

        data = check_response.json()

        existing_dates = []

        for row in data.get("values", []):
            if row:
                existing_dates.append(row[0])

        # Prevent duplicate date
        if entry.fecha in existing_dates:
            raise HTTPException(
                status_code=400,
                detail=f"Entrada ya existe para la fecha {entry.fecha}"
            )

    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{GOOGLE_SHEET_ID}"
        f"/values/{SHEET_NAME}!A1:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS"
    )
    async with httpx.AsyncClient() as client:
        r = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {get_google_token()}",
                "Content-Type": "application/json",
            },
            json={"values": values},
        )
    if r.status_code not in (200, 201):
        detail = r.json().get("error", {}).get("message", "Error desconocido")
        raise HTTPException(r.status_code, detail)
    return {"ok": True, "registrado": ahora}


@app.get("/api/registers")
async def get_registros():
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{GOOGLE_SHEET_ID}"
        f"/values/{SHEET_NAME}!A:D"
    )
    async with httpx.AsyncClient() as client:
        r = await client.get(
            url,
            headers={"Authorization": f"Bearer {get_google_token()}"}
        )
    if r.status_code != 200:
        raise HTTPException(r.status_code, "Error leyendo la hoja")
    rows = r.json().get("values", [])
    entries = []
    for row in reversed(rows[-20:]):
        if len(row) >= 2:
            entries.append({
                "fecha": row[0] if len(row) > 0 else "",
                "horas": row[1] if len(row) > 1 else "",
                "comentario": row[2] if len(row) > 2 else "",
                "ahora": row[3] if len(row) > 3 else "",
            })
    return entries


# ── Static frontend ───────────────────────────────────────────────────────────

app.mount("/", StaticFiles(directory="static", html=True), name="static")
