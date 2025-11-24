import httpx

async def search_jackett(url, api_key, imdb_id, type, season=None, episode=None):
    clean_url = url.rstrip("/")
    endpoint = f"{clean_url}/api/v2.0/indexers/all/results"
    
    # Parâmetros de busca (idem)
    # ...
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(endpoint, params=params, timeout=60)
            resp.raise_for_status() # Garante que erros 4xx/5xx sejam registrados
            data = resp.json()
            
            # LOG DE RESULTADOS:
            print(f"DEBUG JACKETT: Encontrados {len(data.get('Results', []))} resultados no Jackett.")
            
            # Lógica de processamento dos resultados
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
            print(f"ERRO JACKETT (HTTP): Status {e.response.status_code}. Resposta: {e.response.text[:100]}")
            return []
        except Exception as e:
            print(f"ERRO JACKETT (Conexão/Timeout/JSON): {e}")
            return []
