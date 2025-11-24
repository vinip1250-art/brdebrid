import base64
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from utils.torbox import resolve_torbox

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar o diretório estático para a página de configuração
app.mount("/static", StaticFiles(directory="static"), name="static")

# Helper para decodificar a configuração
def decode_config(config_str: str):
    """Decodifica a string Base64 da URL em um dicionário de configurações."""
    try:
        # A codificação Base64 usa URL-safe
        decoded = base64.b64decode(config_str).decode("utf-8")
        return json.loads(decoded)
    except Exception as e:
        print(f"Erro ao decodificar config: {e}")
        return {}

# --- Rotas do Addon ---

@app.get("/", response_class=HTMLResponse)
async def config_page():
    """Rota para servir a página de configuração (static/config.html)."""
    try:
        with open("static/config.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Página de configuração não encontrada. Certifique-se de que static/config.html existe.", 404

@app.get("/{config}/manifest.json")
async def get_manifest(config: str):
    """Retorna o manifesto do addon."""
    return {
        "id": "com.brazucamod.public",
        "version": "1.0.2",
        "name": "Brazuca Mod (Torbox Teste)",
        "description": "Addon configurável com suporte a Torbox.",
        "resources": ["stream"],
        "types": ["movie", "series"],
        "catalogs": [],
        "idPrefixes": ["tt"]
    }

# 💡 ATENÇÃO: ESTA FUNÇÃO PRECISA SER SUBSTITUÍDA PELA SUA LÓGICA REAL DE BUSCA NO BRAZUCA TORRENTS!
async def buscar_magnet_no_indexador(imdb_id):
    """
    Função Placeholder: Substitua isso pelo seu Scraper ou Jackett.
    
    Abaixo, um magnet real e conhecido por estar em cache em serviços de debrid (para testes).
    SE VOCÊ NÃO TROCAR ISSO, TODOS OS FILMES BUSCARÃO ESTE MESMO MAGNET.
    """
    if imdb_id == "tt0133093": # The Matrix (apenas para exemplo)
        return [{
            "title": "Matrix 1080p Web-DL", 
            "magnet": "magnet:?xt=urn:btih:EXEMPLO_HASH_DO_TORRENT_DA_MATRIX&dn=The.Matrix.1999.1080p.Web-DL", 
            "quality": "1080p", 
            "seeds": 1000
        }]
    
    # IMPORTANTE: Se não for o filme de teste, retorna lista vazia!
    return [] 

@app.get("/{config}/stream/{type}/{id}.json")
async def get_stream(config: str, type: str, id: str):
    # 1. Decodificar as configurações do usuário
    user_settings = decode_config(config)
    
    debrid_key = user_settings.get("debrid_key")
    if not debrid_key:
        return {"streams": [{"title": "⚠️ ERRO: API Key não configurada", "url": ""}]}

    imdb_id = id.split(":")[0]

    # 2. BUSCA: Obter Magnets (usando o placeholder, que você deve substituir)
    magnets_found = await buscar_magnet_no_indexador(imdb_id) 

    if not magnets_found:
        print(f"DEBUG: Nenhum magnet encontrado para IMDB ID {imdb_id}. Retornando sem streams.")
        return {"streams": []}

    streams = []
    
    # 3. RESOLUÇÃO: Torbox
    for magnet_obj in magnets_found:
        print(f"DEBUG: Tentando resolver magnet: {magnet_obj['title']}")
        
        link_info = await resolve_torbox(
            magnet_obj['magnet'], 
            debrid_key
        )
        
        if link_info:
            streams.append({
                "title": f"⚡ [Torbox] {magnet_obj['quality']} - {magnet_obj['title']}",
                "url": link_info
            })
            
            # Se achou um link, para a busca para evitar requisições extras
            break 

    return {"streams": streams}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
