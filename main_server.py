import os
import request
import uvicorn
from fastapi import FastAPI, Request, Response

app = FastAPI()

# Słownik tymczasowy na kody: {"123456": {"status": "pending", "psid": None}}
pending_codes = {}

VERIFY_TOKEN = "fnaf_fajny_jes_hehe" # Token do wpisania w panelu Meta Developers
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "EAAR3ed9mDEsBRp24lqYYs8p5KpZCHwfLo771XxQPBwH7czoVZCQUyJp3e9bGWDaQCVp0TZCLaBGkRAXLf3uw4BI0SQFV3SQ0GoLrFd9EUXZAH2LrUS9ht0EhPhE9JomVba9QJnUVMuErlDsIqhnrldPZAu1kuGgtvRDdkIsXRaBNs38wAI85UuPQhHbNYe1tmLe5Lbw3sfsHIZCTRKpO6JjwZDZD")

# 0. Strona główna (żeby sprawdzić czy serwer żyje)
@app.get("/")
def home():
    return {"status": "online", "message": "Serwer CallerGo dziala poprawnie!"}

# 1. Endpoints dla Aplikacji Desktopowej (CallerGo)
@app.post("/api/register-code/{code}")
def register_code(code: str):
    pending_codes[code] = {"status": "pending", "psid": None}
    return {"status": "registered", "code": code}

@app.get("/api/check-code/{code}")
def check_code(code: str):
    data = pending_codes.get(code)
    if not data:
        return {"status": "not_found"}
    return data

# 2. Webhook dla Facebooka (Weryfikacja adresu URL przy konfiguracji w Meta)
@app.get("/webhook")
def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, status_code=200)
    return Response(status_code=403)

# 3. Webhook dla Facebooka (Odbieranie wiadomości od gracza)
@app.post("/webhook")
async def receive_message(request: Request):
    body = await request.json()
    
    if body.get("object") == "page":
        for entry in body.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_psid = messaging_event.get("sender", {}).get("id")
                message_text = messaging_event.get("message", {}).get("text", "").strip()

                # Sprawdzamy czy treść wiadomości to jeden z naszych oczekujących kodów
                if message_text in pending_codes:
                    pending_codes[message_text] = {
                        "status": "verified",
                        "psid": sender_psid
                    }
                    print(f"[SUCCESS] Zweryfikowano kod {message_text} dla PSID: {sender_psid}")

        return Response(content="EVENT_RECEIVED", status_code=200)
    return Response(status_code=404)

# Nazwa użytkownika
@app.get("/api/get-username/{psid}")
def get_username(psid: str):
    """Pobiera imię użytkownika z Facebook Graph API."""
    if not PAGE_ACCESS_TOKEN or PAGE_ACCESS_TOKEN == "EAAR3ed9mDEsBRp24lqYYs8p5KpZCHwfLo771XxQPBwH7czoVZCQUyJp3e9bGWDaQCVp0TZCLaBGkRAXLf3uw4BI0SQFV3SQ0GoLrFd9EUXZAH2LrUS9ht0EhPhE9JomVba9QJnUVMuErlDsIqhnrldPZAu1kuGgtvRDdkIsXRaBNs38wAI85UuPQhHbNYe1tmLe5Lbw3sfsHIZCTRKpO6JjwZDZD":
        return {"name": None}
    
    try:
        url = f"https://graph.facebook.com/v19.0/{psid}?fields=first_name,name&access_token={PAGE_ACCESS_TOKEN}"
        res = requests.get(url, timeout=5).json()
        
        # Pobieramy najpierw pierwsze imię (first_name), a jeśli go nie ma - pełne imię (name)
        user_name = res.get("first_name") or res.get("name")
        return {"name": user_name}
    except Exception:
        return {"name": None}

if __name__ == "__main__":
    # POBIERANIE PORTU Z RENDER LUB DOMYŚLNIE 8000 LOKALNIE
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
