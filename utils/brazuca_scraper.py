import httpx
import json
import re

# Constante para a URL base do addon Brazuca Torrents
BRAZUCA_ADDON_BASE_URL = "https://94c8cb9f702d-brazuca-torrents.baby-beamup.club"

async def scrape_brazuca_torrents(imdb_id: str, content_type: str, s: str, e: str):
    """
    Busca por magnets no Brazuca Torrents usando o próprio addon como API (API Chaining).
    """
    
    if content_type == "series" and s and e:
        stremio_id = f"{imdb_id}:{s}:{e}"
    else:
        stremio_id = imdb_id
        
    brazuca_stream_url = f"{BRAZUCA_ADDON_BASE_URL}/stream/{content_type}/{stremio_id}.json"
    
    magnets = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(brazuca_stream_url)
            
            if resp.status_code == 404:
                 print("ERRO SCRAPER: Brazuca Torrents retornou 404. Item não encontrado.")
                 return []
            
            # Garante que qualquer erro HTTP seja levantado (5xx)
            resp.raise_for_status() 

            # 💡 PASSO CRÍTICO DE DEBUG: Imprimir o JSON recebido
            # Isso vai mostrar se o httpx está pegando o JSON que você vê no navegador
            print(f"DEBUG SCRAPER: JSON Recebido do Brazuca: {resp.text[:200]}...")
            
            data = resp.json()
            
            # Verifica se a chave 'streams' existe e é uma lista
            if not isinstance(data.get("streams"), list):
                print("ERRO SCRAPER: Resposta do Brazuca não tem a chave 'streams' ou não é uma lista.")
                return []
            
            # Itera sobre os streams
            for stream in data.get("streams"):
                url = stream.get("url")
                title = stream.get("title", "Magnet Brazuca")
                
                if url and url.startswith("magnet:"):
                    quality_match = re.search(r'(\d{3,4}p|4K)', title, re.IGNORECASE)
                    quality = quality_match.group(1) if quality_match else "UNK"
                    
                    magnets.append({
                        "title": title,
                        "magnet": url,
                        "quality": quality,
                        "seeds": 1 
                    })
            
            print(f"DEBUG SCRAPER: Brazuca Torrents API encontrou {len(magnets)} resultados.")
            return magnets
        
        except httpx.RequestError as e:
            print(f"ERRO CRÍTICO NO SCRAPER BRAZUCA (Rede/Timeout): {e}")
            return []
        except Exception as e:
            # Isso capturaria erros de JSON (mal formatado) ou KeyError
            print(f"ERRO CRÍTICO NO SCRAPER BRAZUCA (Geral - Falha ao processar JSON): {e}")
            return []

