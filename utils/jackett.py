import httpx

async def search_jackett(url, api_key, imdb_id, type, season=None, episode=None):
    clean_url = url.rstrip("/")
    endpoint = f"{clean_url}/api/v2.0/indexers/all/results"
    
    # Parâmetros de busca
    params = {
        "apikey": api_key,
        "imdbid": imdb_id, # Jackett aceita busca por ID IMDB, o que é ótimo!
    }
    
    if type == "series" and season and episode:
        params["season"] = season
        params["ep"] = episode
    
    # Categoria 2000 (Movies), 5000 (TV)
    if type == "movie":
        params["Category[]"] = 2000
    else:
        params["Category[]"] = 5000

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(endpoint, params=params, timeout=10)
            data = resp.json()
            
            results = []
            for item in data.get("Results", []):
                # Filtrar apenas o que tem Magnet Link
                if item.get("MagnetUri"):
                    results.append({
                        "title": item.get("Title"),
                        "magnet": item.get("MagnetUri"),
                        "quality": "UNK", # Tentar extrair qualidade do titulo se quiser
                        "seeds": item.get("Seeders")
                    })
            
            # Ordenar por Seeds para garantir saúde
            results.sort(key=lambda x: x['seeds'], reverse=True)
            return results
            
        except Exception as e:
            print(f"Erro no Jackett: {e}")
            return []
