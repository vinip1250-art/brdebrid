import httpx
import urllib.parse

async def search_jackett(url, api_key, imdb_id, content_type, season=None, episode=None):
    """
    Busca por torrents no Jackett usando o ID IMDB.
    Filtra por tipo (Filme/Série) e, se série, por temporada e episódio.
    """
    
    # Garantir que a URL base termine sem barra
    clean_url = url.rstrip("/")
    endpoint = f"{clean_url}/api/v2.0/indexers/all/results"
    
    # Parâmetros de busca
    params = {
        "apikey": api_key,
        "imdbid": imdb_id, 
        "t": "search" # Tipo de consulta (geralmente não é necessário, mas garante)
    }
    
    # Categorias Jackett
    # 2000: Movies (Filmes)
    # 5000: TV (Séries)
    if content_type == "movie":
        params["Category[]"] = 2000
    elif content_type == "series":
        params["Category[]"] = 5000
        if season and episode:
            # Para séries, o Jackett aceita os parâmetros de temporada (s) e episódio (ep)
            params["season"] = season
            params["ep"] = episode
    
    # Usar httpx.AsyncClient para consultas assíncronas
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            # O Jackett pode retornar um XML ou JSON. Pedimos JSON.
            resp = await client.get(endpoint, params=params, headers={"Accept": "application/json"})
            resp.raise_for_status() # Lança exceção para status 4xx/5xx
            
            data = resp.json()
            
            results = []
            for item in data.get("Results", []):
                # Filtra apenas o que tem Magnet Link e que não são Links para página
                if item.get("MagnetUri") and item.get("Link"):
                    results.append({
                        "title": item.get("Title"),
                        "magnet": item.get("MagnetUri"),
                        # Adiciona metadados úteis
                        "quality": "UNK", # Poderia tentar extrair 720p/1080p do título
                        "seeds": item.get("Seeders", 0)
                    })
            
            # Otimização: Classificar por Seeds para priorizar resultados mais saudáveis
            results.sort(key=lambda x: x['seeds'], reverse=True)
            
            print(f"DEBUG: Jackett encontrou {len(results)} resultados.")
            return results
            
        except httpx.RequestError as e:
            print(f"ERRO JACKETT: Falha na conexão ou Timeout: {e}")
            return []
        except Exception as e:
            print(f"ERRO JACKETT: Erro ao processar resposta: {e}")
            return []
