import base64
import json
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Importa os utilitários
from utils.torbox import resolve_torbox
from utils.realdebrid import resolve_realdebrid 
from utils.jackett import search_jackett 
from utils.brazuca_scraper import scrape_brazuca_torrents 

# ----------------------------------------------------
# 1. INICIALIZAÇÃO E CONFIGURAÇÃO DO FASTAPI (CORREÇÃO DO NAMERROR)
# ----------------------------------------------------

# 💡 CORREÇÃO: Inicializa a variável 'app'
app = FastAPI()

# Constante para o manifesto externo (Brazuca Torrents)
BRAZUCA_TORRENTS_MANIFEST_URL = "https://94c8cb9f702d-brazuca-torrents.baby-beamup.club/manifest.json"

# Configuração de CORS (Essencial para o Stremio)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar o diretório estático para a página de configuração
app.mount("/static", StaticFiles(directory="static"), name="static")

# Helper para decodificar a configuração (Estava faltando a definição)
def decode_config(config_str: str):
    """Decodifica a string Base64 da URL em um dicionário de configurações."""
    try:
        decoded = base64.b64decode(config_str).decode("utf-8")
        return json.loads(decoded)
    except Exception as e:
        print(f"Erro ao decodificar config: {e}")
        return {}

# --- Lógica de Busca (Scraper Placeholder) ---

# Esta função precisa ser completada por você com a lógica de Beautiful Soup
# no arquivo utils/brazuca_scraper.py
# ----------------------------------------------

# --- Rotas de Manifestos ---

@app.get("/brazuca-torrents/manifest.json")
async def get_brazuca_torrents_manifest():
    """Busca e retorna o manifesto do addon Brazuca Torrents original."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(BRAZUCA_TORRENTS_MANIFEST_URL)
            response.raise_for_status() 
            return response.json()
        except Exception as e:
            print(f"ERRO: Falha ao buscar manifesto externo: {e}")
            raise HTTPException(status_code=500, detail="Erro interno ao buscar manifesto.")

@app.get("/{config}/manifest.json")
async def get_manifest(config: str):
    """Retorna o manifesto do seu addon (o wrapper configurável)."""
    return {
        "id": "com.brazucamod.public",
        "version": "1.0.4",
        "name": "Brazuca Mod (Torbox/Jackett)",
        "description": "Addon configurável com busca em Jackett e Debrids.",
        "resources": ["stream"],
        "types": ["movie", "series"],
        "catalogs": [],
        "idPrefixes": ["tt"]
    }

@app.get("/", response_class=HTMLResponse)
async def config_page():
    """Rota para servir a página de configuração (static/config.html)."""
    try:
        with open("static/config.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Página de configuração não encontrada. Certifique-se de que static/config.html existe.", 404

# --- Rota Principal de Stream ---

@app.get("/{config}/stream/{type}/{id}.json")
async def get_stream(config: str, type: str, id: str):
    user_settings = decode_config(config)
    
    debrid_key = user_settings.get("debrid_key")
    if not debrid_key:
        return {"streams": [{"title": "⚠️ ERRO: API Key não configurada", "url": ""}]}
    
    imdb_id = id.split(":")[0]
    season, episode = (id.split(":")[1], id.split(":")[2]) if type == "series" and ":" in id else (None, None)

    magnets_found = []

    # 2. BUSCA: Fontes Múltiplas
    
    # 2.1 Scraper Interno (Brazuca Torrents)
    print("DEBUG: Buscando no Scraper Brazuca Torrents...")
    results_scraper = await scrape_brazuca_torrents(imdb_id, type, season, episode)
    magnets_found.extend(results_scraper)
    
    # 2.2 Jackett (Se configurado)
    if user_settings.get("jackett_url") and user_settings.get("jackett_key"):
        print("DEBUG: Buscando no Jackett do usuário...")
        results_jackett = await search_jackett(
            user_settings["jackett_url"], user_settings["jackett_key"], imdb_id, type, season, episode
        )
        magnets_found.extend(results_jackett)
    
    if not magnets_found:
        print("DEBUG: Nenhuma fonte (Jackett/Scraper) encontrou resultados.")
        return {"streams": []}
        
    magnets_found.sort(key=lambda x: x['seeds'], reverse=True)
    
    streams = []
    service = user_settings.get("service")
    
    # 3. RESOLUÇÃO: Torbox ou Real-Debrid
    for magnet_obj in magnets_found:
        link_info = None
        service_name = ""
        
        if service == "torbox":
            link_info = await resolve_torbox(magnet_obj['magnet'], debrid_key)
            service_name = "Torbox"
            
        elif service == "realdebrid":
            link_info = await resolve_realdebrid(magnet_obj['magnet'], debrid_key)
            service_name = "Real-Debrid"

        if link_info:
            # 💡 Ponto de Streamthru entraria aqui, se desejado
            streams.append({
                "title": f"⚡ [{service_name}] {magnet_obj['quality']} - {magnet_obj['title']}",
                "url": link_info
            })
            
    return {"streams": streams}

# --- Inicialização ---

if __name__ == "__main__":
    import uvicorn
    # A variável 'app' está agora definida e acessível aqui.
    uvicorn.run(app, host="0.0.0.0", port=8000)

