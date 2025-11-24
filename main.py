import base64
import json
import httpx
from fastapi import FastAPI, HTTPException, Request
# ... (outros imports) ...

# 💡 Novo: Usaremos esta biblioteca para forçar um timeout em uma função
# Se não estiver instalada, use: pip install asyncio-timeout
from asyncio import timeout_at, TimeoutError
import time # Para calcular o tempo de busca

# ... (Definições app, constantes, helpers, rotas manifestos) ...

@app.get("/{config}/stream/{type}/{id}.json")
async def get_stream(config: str, type: str, id: str):
    user_settings = decode_config(config)
    
    # ... (checagem de debrid_key e parsing de ID) ...

    # Parâmetros de ID (obtidos do parsing)
    s_str = str(season) if season is not None else None
    e_str = str(episode) if episode is not None else None

    magnets_found = []

    # 2. BUSCA: Fontes Múltiplas (Com Timeout de 5 Segundos Total)
    try:
        # Define um timeout total para as chamadas lentas do scraper/jackett
        async with timeout_at(time.time() + 5): 
            
            # 2.1 Scraper Interno (Brazuca Torrents)
            results_scraper = await scrape_brazuca_torrents(imdb_id, type, s_str, e_str)
            magnets_found.extend(results_scraper)
            
            # 2.2 Jackett (Se configurado)
            if user_settings.get("jackett_url") and user_settings.get("jackett_key"):
                results_jackett = await search_jackett(
                    user_settings["jackett_url"], user_settings["jackett_key"], imdb_id, type, s_str, e_str
                )
                magnets_found.extend(results_jackett)
                
    except TimeoutError:
        print("ALERTA: Busca de fontes (Brazuca/Jackett) excedeu o limite de 5 segundos. Retornando vazio.")
        return {"streams": []}
    
    # ... (O restante da lógica de Debrid permanece igual) ...
    
    # Se chegarmos aqui, a busca foi rápida ou encontrou resultados
    if not magnets_found:
        print("DEBUG: Nenhuma fonte (Jackett/Scraper) encontrou resultados.")
        return {"streams": []}
        
    magnets_found.sort(key=lambda x: x.get('seeds', 0), reverse=True)
    
    streams = []
    service = user_settings.get("service")
    
    # 3. RESOLUÇÃO: Torbox ou Real-Debrid
    for magnet_obj in magnets_found:
        # ... (Lógica de resolução de Debrid - Esta é rápida se o arquivo estiver em cache)
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
                "title": f"⚡ [{service_name}] {magnet_obj.get('quality', 'UNK')} - {magnet_obj['title']}",
                "url": link_info
            })
            
    return {"streams": streams}

