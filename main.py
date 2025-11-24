from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import base64
import json

from utils.torbox import resolve_torbox
# from utils.jackett import search_jackett # Desativado para teste

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper para decodificar a configuração
def decode_config(config_str: str):
    try:
        decoded = base64.b64decode(config_str).decode("utf-8")
        return json.loads(decoded)
    except:
        return {}

@app.get("/", response_class=HTMLResponse)
async def config_page():
    # Assumindo que você está servindo static/config.html com o Nginx ou rota Flask/FastAPI
    with open("static/config.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/{config}/manifest.json")
async def get_manifest(config: str):
    return {
        "id": "com.brazucamod.public",
        "version": "1.0.1",
        "name": "Brazuca Mod (Public)",
        "description": "Addon configurável com suporte a Torbox, Jackett e Scrapers BR",
        "resources": ["stream"],
        "types": ["movie", "series"],
        "catalogs": [],
        "idPrefixes": ["tt"]
    }

@app.get("/{config}/stream/{type}/{id}.json")
async def get_stream(config: str, type: str, id: str):
    user_settings = decode_config(config)
    
    if not user_settings.get("debrid_key"):
        return {"streams": [{"title": "⚠️ ERRO: API Key Debrid não configurada", "url": ""}]}

    # --- TESTE ISOLADO DO TORBOX (IGNORA JACKETT) ---
    # Use um magnet de teste (popular para garantir que esteja em cache no Torbox)
    TEST_MAGNET = "magnet:?xt=urn:btih:3137B75F3908851724D3D560A3F1F1E8E62294E8&dn=Filme+Teste+Cach%C3%A9" 
    
    magnets_found = [{
        "title": "Filme Teste (Magnet Fixo)",
        "magnet": TEST_MAGNET,
        "quality": "1080p",
        "seeds": 999
    }]
    # --- FIM DO TESTE ISOLADO ---

    if not magnets_found:
        return {"streams": []}

    streams = []
    
    # 4. RESOLUÇÃO: Torbox
    if user_settings.get("service") == "torbox":
        for magnet_obj in magnets_found:
            link_info = await resolve_torbox(
                magnet_obj['magnet'], 
                user_settings["debrid_key"]
            )
            
            if link_info:
                print(f"DEBUG SUCESSO TORBOX: Link obtido para {magnet_obj['title']}")
                streams.append({
                    "title": f"⚡ [Torbox] {magnet_obj['quality']} - {magnet_obj['title']}",
                    "url": link_info
                })
            else:
                print(f"DEBUG FALHA TORBOX: Torbox não conseguiu resolver {magnet_obj['title']}")
                
    return {"streams": streams}

# Se você ainda tiver o '__name__ == "__main__":' no final, mantenha.
