import base64
import json
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Importa os utilitários
from utils.torbox import resolve_torbox
from utils.realdebrid import resolve_realdebrid 
from utils.jackett import search_jackett 
from utils.brazuca_scraper import scrape_brazuca_torrents # 💡 NOVO: Scraper Brazuca

# ... (Constantes, app, middlewares, helpers) ...

# --- Rotas Principais (Config/Stream) ---

# ... (Rotas get_brazuca_torrents_manifest e get_manifest) ...

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
    
    # 2.1 Scraper Interno (Brazuca Torrents) - IMPLEMENTAÇÃO DO BRAZUCA-RD
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
            streams.append({
                "title": f"⚡ [{service_name}] {magnet_obj['quality']} - {magnet_obj['title']}",
                "url": link_info
            })
            
            # Se quiser apenas o primeiro link encontrado, descomente:
            # break 
            
    return {"streams": streams}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
