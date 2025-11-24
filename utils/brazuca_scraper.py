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
                 return []
            resp.raise_for_status() 

            data = resp.json()
            
            # 💡 Correção: Garantir que a chave 'streams' seja tratada corretamente
            for stream in data.get("streams", []):
                
                # O magnet DEVE estar na chave 'url' para que o debrid funcione.
                # Se o Brazuca Torrents usa outra chave (como 'magnet'), precisamos mapear.
                
                # Priorizamos 'url', mas se 'url' não for um magnet, procuramos em 'magnet'
                url = stream.get("url", stream.get("magnet")) 
                title = stream.get("title", stream.get("name", "Magnet Brazuca"))
                
                if url and url.startswith("magnet:"):
                    quality_match = re.search(r'(\d{3,4}p|4K)', title, re.IGNORECASE)
                    quality = quality_match.group(1) if quality_match else "UNK"
                    
                    magnets.append({
                        "title": title,
                        "magnet": url, # Usamos 'url' que contem o magnet link
                        "quality": quality,
                        "seeds": 1 
                    })
            
            return magnets
        
        except httpx.RequestError as e:
            print(f"ERRO CRÍTICO NO SCRAPER BRAZUCA (Rede/Timeout): {e}")
            return []
        except Exception as e:
            print(f"ERRO CRÍTICO NO SCRAPER BRAZUCA (Geral - Falha ao processar JSON): {e}")
            return []

