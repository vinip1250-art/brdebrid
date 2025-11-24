import base64
import json
import httpx # 💡 Certifique-se de que httpx está instalado!
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Importa os utilitários
from utils.torbox import resolve_torbox
from utils.jackett import search_jackett 
from utils.realdebrid import resolve_realdebrid 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constante para o manifesto externo
BRAZUCA_TORRENTS_MANIFEST_URL = "https://94c8cb9f702d-brazuca-torrents.baby-beamup.club/manifest.json"

# Montar o diretório estático para a página de configuração
app.mount("/static", StaticFiles(directory="static"), name="static")

# Helper para decodificar a configuração
def decode_config(config_str: str):
    """Decodifica a string Base64 da URL em um dicionário de configurações."""
    try:
        decoded = base64.b64decode(config_str).decode("utf-8")
        return json.loads(decoded)
    except Exception as e:
        print(f"Erro ao decodificar config: {e}")
        return {}

# --- Lógica de Busca ---
async def meu_scraper(imdb_id: str, type: str, s: str, e: str):
    """
    Substitua o conteúdo desta função para buscar resultados no Brazuca Torrents.
    """
    # ... (Seu código de scraper entra aqui) ...
    
    # 📌 Placeholder para Magnet de Teste (Remova após implementar o scraper)
    if imdb_id == "tt0133093": 
        return [{
            "title": "Matrix 1080p Web-DL (TESTE SCRAPER BR)", 
            "magnet": "magnet:?xt=urn:btih:EXEMPLO_HASH_DO_TORRENT_DA_MATRIX&dn=The.Matrix.1999.1080p.Web-DL", 
            "quality": "1080p", 
            "seeds": 1000
        }]
    
    return [] 

# --- Rotas de Manifestos ---

@app.get("/brazuca-torrents/manifest.json")
async def get_brazuca_torrents_manifest():
    """
    Busca e retorna o manifesto do addon Brazuca Torrents original.
    """
    async with httpx.AsyncClient() as client:
        try:
            # Faz a requisição para o manifesto externo
            response = await client.get(BRAZUCA_TORRENTS_MANIFEST_URL)
            response.raise_for_status() 
            
            # Retorna o JSON exato recebido
            return response.json()
        except httpx.HTTPStatusError as e:
            # Trata erro se o manifesto original estiver offline
            print(f"ERRO: Manifesto Brazuca Torrents externo falhou ao carregar: {e}")
            raise HTTPException(status_code=503, detail="Manifesto Brazuca Torrents está indisponível.")
        except Exception as e:
            print(f"ERRO: Falha ao buscar manifesto externo: {e}")
            raise HTTPException(status_code=500, detail="Erro interno ao buscar manifesto.")

@app.get("/{config}/manifest.json")
async def get_manifest(config: str):
    """Retorna o manifesto do seu addon (o wrapper configurável)."""
    return {
        "id": "com.brazucamod.public",
        "version": "1.0.3",
        "name": "Brazuca Mod (Torbox/Jackett)",
        "description": "Addon configurável com busca em Jackett e Debrids.",
        "resources": ["stream"],
        "types": ["movie", "series"],
        "catalogs": [],
        "idPrefixes": ["tt"]
    }

# --- Rotas Principais (Home e Stream) ---

@app.get("/", response_class=HTMLResponse)
async def config_page():
    """Rota para servir a página de configuração (static/config.html)."""
    try:
        with open("static/config.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Página de configuração não encontrada. Certifique-se de que static/config.html existe.", 404

@app.get("/{config}/stream/{type}/{id}.json")
async def get_stream(config: str, type: str, id: str):
    # ... (O código de busca Jackett, Scraper e resolução Torbox/RD continua aqui, como no último envio) ...
    user_settings = decode_config(config)
    
    debrid_key = user_settings.get("debrid_key")
    if not debrid_key:
        return {"streams": [{"title": "⚠️ ERRO: API Key não configurada", "url": ""}]}
    
    imdb_id = id.split(":")[0]
    season, episode = (id.split(":")[1], id.split(":")[2]) if type == "series" and ":" in id else (None, None)

    # ... (código de busca Jackett/Scraper e resolução debrids) ...
    
    # 📌 Nota: O código de stream é extenso, mas sua lógica permanece a mesma do envio anterior, 
    # apenas certifique-se de que a nova função de manifesto foi adicionada e os imports estão corretos.
    
    # ... (final do get_stream) ...
    
    magnets_found = []
    
    # 2.1 Jackett
    if user_settings.get("jackett_url") and user_settings.get("jackett_key"):
        results_jackett = await search_jackett(
            user_settings["jackett_url"], user_settings["jackett_key"], imdb_id, type, season, episode
        )
        magnets_found.extend(results_jackett)
        
    # 2.2 Scraper Interno (Brazuca Torrents)
    results_scraper = await meu_scraper(imdb_id, type, season, episode)
    magnets_found.extend(results_scraper)
    
    if not magnets_found:
        return {"streams": []}
        
    magnets_found.sort(key=lambda x: x['seeds'], reverse=True)
    
    streams = []
    service = user_settings.get("service")
    
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
            streams.append({
                "title": f"⚡ [{service_name}] {magnet_obj['quality']} - {magnet_obj['title']}",
                "url": link_info
            })
            
    return {"streams": streams}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
