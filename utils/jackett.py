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
        resp.raise_for_status() # Garante que erros 4xx/5xx sejam registrados
        data = resp.json()
        
        # LOG DE RESULTADOS:
        print(f"DEBUG JACKETT: Encontrados {len(data.get('Results', []))} resultados no Jackett.") 
        
        # ... o restante da lógica ...
    except httpx.HTTPStatusError as e:
        print(f"ERRO JACKETT (HTTP): Status {e.response.status_code}. Verifique a API Key ou se o Jackett está OK.")
        return []
    except Exception as e:
        print(f"ERRO JACKETT (Conexão/JSON): {e}")
        return []
