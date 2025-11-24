import base64
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from utils.jackett import search_jackett
from utils.torbox import resolve_torbox

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir a página de configuração na raiz
@app.get("/", response_class=HTMLResponse)
async def config_page():
    with open("static/config.html", "r", encoding="utf-8") as f:
        return f.read()

# Helper para decodificar a configuração
def decode_config(config_str: str):
    try:
        decoded = base64.b64decode(config_str).decode("utf-8")
        return json.loads(decoded)
    except:
        return {}

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
    # 1. Decodificar as configurações do usuário
    user_settings = decode_config(config)
    
    if not user_settings.get("debrid_key"):
        return {"streams": [{"title": "⚠️ ERRO: API Key não configurada", "url": ""}]}

    imdb_id = id.split(":")[0]
    season = None
    episode = None
    if ":" in id:
        # Lógica para tratar séries (tt123:1:1)
        parts = id.split(":")
        if len(parts) == 3:
            season = parts[1]
            episode = parts[2]

    magnets_found = []

    # 2. BUSCA: Jackett (Se configurado)
    if user_settings.get("jackett_url") and user_settings.get("jackett_key"):
        print("Buscando no Jackett do usuário...")
        results_jackett = await search_jackett(
            user_settings["jackett_url"],
            user_settings["jackett_key"],
            imdb_id,
            type,
            season,
            episode
        )
        magnets_found.extend(results_jackett)

    # 3. BUSCA: Scraper Interno (Estilo Brazuca - Opcional)
    # Aqui você adicionaria sua lógica de scrapers fixos se quiser manter
    # magnets_found.extend(await meus_scrapers_brasileiros(imdb_id))

    if not magnets_found:
        return {"streams": []}

    streams = []
    
    # 4. RESOLUÇÃO: Torbox / Debrid
    # Processamos os magnets para verificar cache e gerar link
    
    if user_settings.get("service") == "torbox":
        for magnet_obj in magnets_found:
            # Tenta resolver. Se estiver em cache, retorna link rápido.
            link_info = await resolve_torbox(
                magnet_obj['magnet'], 
                user_settings["debrid_key"]
            )
            
            if link_info:
                streams.append({
                    "title": f"⚡ [Torbox] {magnet_obj['quality']} - {magnet_obj['title']}",
                    "url": link_info
                })
                
                # Otimização: Se achar um cached 1080p ou 4k, pode parar o loop para ser mais rápido
                # ou continuar para listar todas opções.

    return {"streams": streams}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
