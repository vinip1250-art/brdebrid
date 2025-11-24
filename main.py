import base64
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Importa os utilitários
from utils.torbox import resolve_torbox
from utils.jackett import search_jackett # Novo

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir a página de configuração e estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

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
    ⚠️ SUBSTITUA PELA SUA LÓGICA DE SCRAPING DE SITES BRASILEIROS (Ex: Brazuca Torrents).
    
    Por enquanto, retorna uma lista vazia ou um magnet de teste (se quiser habilitar).
    """
    # Exemplo: Se você implementar o scraper do Brazuca Torrents, ele entraria aqui
    # results = await scrape_brazuca(imdb_id, type, s, e)
    
    # 📌 Placeholder para Magnet de Teste (Remova após implementar o scraper)
    if imdb_id == "tt0133093": 
        return [{
            "title": "Matrix 1080p Web-DL (TESTE)", 
            "magnet": "magnet:?xt=urn:btih:EXEMPLO_HASH_DO_TORRENT_DA_MATRIX&dn=The.Matrix.1999.1080p.Web-DL", 
            "quality": "1080p", 
            "seeds": 1000
        }]
    
    return []


@app.get("/", response_class=HTMLResponse)
async def config_page():
    try:
        with open("static/config.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Página de configuração não encontrada. Rode 'python -m http.server' na pasta static para testar.", 404

@app.get("/{config}/manifest.json")
async def get_manifest(config: str):
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

@app.get("/{config}/stream/{type}/{id}.json")
async def get_stream(config: str, type: str, id: str):
    user_settings = decode_config(config)
    
    # 1. Configurações e ID Parsing
    debrid_key = user_settings.get("debrid_key")
    if not debrid_key:
        return {"streams": [{"title": "⚠️ ERRO: API Key não configurada", "url": ""}]}
    
    imdb_id = id.split(":")[0]
    season, episode = (id.split(":")[1], id.split(":")[2]) if type == "series" and ":" in id else (None, None)

    magnets_found = []

    # 2. BUSCA: Fontes Múltiplas
    
    # 2.1 Jackett (Se configurado)
    if user_settings.get("jackett_url") and user_settings.get("jackett_key"):
        print("DEBUG: Buscando no Jackett do usuário...")
        results_jackett = await search_jackett(
            user_settings["jackett_url"],
            user_settings["jackett_key"],
            imdb_id,
            type,
            season,
            episode
        )
        magnets_found.extend(results_jackett)
        
    # 2.2 Scraper Interno (Substitua esta chamada pela sua lógica de busca no Brazuca)
    results_scraper = await meu_scraper(imdb_id, type, season, episode)
    magnets_found.extend(results_scraper)
    
    # 3. Processamento de Resultados
    if not magnets_found:
        print(f"DEBUG: Nenhuma fonte (Jackett/Scraper) encontrou resultados para IMDB ID {imdb_id}.")
        return {"streams": []}
        
    # Otimização: Classificar por seeds e qualidade (Melhor magnet primeiro)
    magnets_found.sort(key=lambda x: x['seeds'], reverse=True)
    
    streams = []
    
    # 4. RESOLUÇÃO: Torbox (Você pode adicionar Real-Debrid aqui com uma função similar)
    if user_settings.get("service") == "torbox":
        for magnet_obj in magnets_found:
            print(f"DEBUG: Tentando resolver magnet Torbox: {magnet_obj['title']}")
            
            link_info = await resolve_torbox(
                magnet_obj['magnet'], 
                debrid_key
            )
            
            if link_info:
                # 📌 STREAMTHRU: A integração final do Streamthru entraria aqui
                # final_url = wrap_streamthru(link_info) 
                
                streams.append({
                    "title": f"⚡ [Torbox] {magnet_obj['quality']} - {magnet_obj['title']}",
                    "url": link_info
                })
                # Não pare aqui se quiser listar várias opções, mas é mais rápido parar.
                # break 

    return {"streams": streams}

if __name__ == "__main__":
    import uvicorn
    # Não esqueça que para uso externo, você precisa de um proxy/serviço que use HTTPS.
    uvicorn.run(app, host="0.0.0.0", port=8000)
