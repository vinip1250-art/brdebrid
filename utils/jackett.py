import httpx

async def search_jackett(url, api_key, imdb_id, type, season=None, episode=None):
    clean_url = url.rstrip("/")
    endpoint = f"{clean_url}/api/v2.0/indexers/all/results"
    
    # Parâmetros de busca
    params = {
        "apikey": api_key,
        "imdbid": imdb_id,
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
            # Timeout aumentado para dar tempo do Jackett consultar os indexadores
            resp = await client.get(endpoint, params=params, timeout=60) 
            resp.raise_for_status() 
            data = resp.json()
            
            # LOG DE RESULTADOS:
            print(f"DEBUG JACKETT: Encontrados {len(data.get('Results', []))} resultados no Jackett.")
            
            results = []
            for item in data.get("Results", []):
                if item.get("MagnetUri"):
                    results.append({
                        "title": item.get("Title"),
                        "magnet": item.get("MagnetUri"),
                        "quality": "UNK", 
                        "seeds": item.get("Seeders", 0)
                    })
            results.sort(key=lambda x: x['seeds'], reverse=True)
            return results
            
        except httpx.HTTPStatusError as e:
            print(f"ERRO JACKETT (HTTP): Status {e.response.status_code}. Verifique a API Key ou se o Jackett está OK.")
            return []
        except Exception as e:
            print(f"ERRO JACKETT (Conexão/Timeout/JSON): {e}")
            return []
