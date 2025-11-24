import httpx
import urllib.parse

async def search_jackett(url, api_key, imdb_id, content_type, season=None, episode=None):
    """
    Busca por torrents no Jackett usando o ID IMDB.
    Ajusta os parâmetros para garantir que a busca por séries seja precisa.
    """
    
    clean_url = url.rstrip("/")
    endpoint = f"{clean_url}/api/v2.0/indexers/all/results"
    
    # Parâmetros de busca (imdbid é o mais confiável)
    params = {
        "apikey": api_key,
        "imdbid": imdb_id, 
        "t": "search" 
    }
    
    # 1. Categorias Jackett e Parâmetros de Série
    if content_type == "movie":
        params["Category[]"] = 2000 # Filmes
    elif content_type == "series":
        params["Category[]"] = 5000 # Séries/TV
        
        # 💡 CORREÇÃO CRÍTICA: O Jackett espera parâmetros s e ep para busca específica.
        if season and episode:
            # Garante que temporada e episódio sejam strings e tratados (embora Jackett seja flexível)
            params["season"] = str(season)
            params["ep"] = str(episode)
            
            # ⚠️ Debugging Tip: Se estiver falhando, tente usar 'q' (query) em vez de 'imdbid'
            # params["q"] = f"S{str(season).zfill(2)}E{str(episode).zfill(2)}"
            
    
    async with httpx.AsyncClient(timeout=150.0) as client:
        try:
            resp = await client.get(endpoint, params=params, headers={"Accept": "application/json"})
            resp.raise_for_status() 
            
            data = resp.json()
            
            results = []
            for item in data.get("Results", []):
                if item.get("MagnetUri") and item.get("Link"):
                    results.append({
                        "title": item.get("Title"),
                        "magnet": item.get("MagnetUri"),
                        "quality": "UNK", 
                        "seeds": item.get("Seeders", 0)
                    })
            
            results.sort(key=lambda x: x['seeds'], reverse=True)
            
            print(f"DEBUG: Jackett encontrou {len(results)} resultados.")
            return results
            
        except httpx.RequestError as e:
            print(f"ERRO JACKETT: Falha na conexão ou Timeout: {e}")
            return []
        except Exception as e:
            print(f"ERRO JACKETT: Erro ao processar resposta: {e}")
            return []

