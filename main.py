# ... (Trecho de imports e funções auxiliares) ...

@app.get("/{config}/stream/{type}/{id}.json")
async def get_stream(config: str, type: str, id: str):
    user_settings = decode_config(config)
    
    # ... (checagem de debrid_key) ...
    
    # 💡 CORREÇÃO CRÍTICA: Refinando a extração de Season/Episode
    imdb_id = id.split(":")[0]
    season = None
    episode = None
    
    if type == "series" and len(id.split(":")) == 3:
        try:
            _, season_str, episode_str = id.split(":")
            # Garante que sejam números inteiros, senão retorna None
            season = int(season_str) if season_str.isdigit() else None
            episode = int(episode_str) if episode_str.isdigit() else None
        except ValueError:
            pass # Ignora se o formato for inválido
            
    # Se a temporada ou episódio não for válida, forçamos a busca por temporada inteira no scraper
    
    magnets_found = []

    # 2. BUSCA: Fontes Múltiplas
    
    # 2.1 Scraper Interno (Brazuca Torrents)
    print("DEBUG: Buscando no Scraper Brazuca Torrents...")
    # Passamos apenas strings, pois Jackett/Brazuca esperam strings
    results_scraper = await scrape_brazuca_torrents(
        imdb_id, 
        type, 
        str(season) if season is not None else None, 
        str(episode) if episode is not None else None
    )
    magnets_found.extend(results_scraper)
    
    # 2.2 Jackett (Se configurado)
    if user_settings.get("jackett_url") and user_settings.get("jackett_key"):
        print("DEBUG: Buscando no Jackett do usuário...")
        results_jackett = await search_jackett(
            user_settings["jackett_url"], 
            user_settings["jackett_key"], 
            imdb_id, 
            type, 
            str(season) if season is not None else None, 
            str(episode) if episode is not None else None
        )
        magnets_found.extend(results_jackett)

    # ... (O restante da lógica de Debrid permanece igual) ...

