import httpx
import json

# ⚠️ Constante para a URL base do addon Brazuca Torrents
# Esta URL é o domínio que hospeda o addon original.
BRAZUCA_ADDON_BASE_URL = "https://94c8cb9f702d-brazuca-torrents.baby-beamup.club"

# Função Placeholder, não é mais necessária se usarmos o addon como API
async def get_title_from_imdb(imdb_id):
    # Mantemos como placeholder, mas não será usada
    return "N/A" 

async def scrape_brazuca_torrents(imdb_id: str, content_type: str, s: str, e: str):
    """
    Busca por magnets no Brazuca Torrents usando o próprio addon como API (API Chaining).
    Esta é a lógica do brazuca-rd.
    """
    
    # 1. Constrói o ID da requisição do Stremio
    if content_type == "series" and s and e:
        # Formato: tt12345:1:5 (IMDB ID:Temporada:Episódio)
        stremio_id = f"{imdb_id}:{s}:{e}"
    else:
        # Formato: tt12345
        stremio_id = imdb_id
        
    # 2. Constrói a URL de Stream do Brazuca Torrents
    # Ex: https://.../stream/movie/tt12345.json
    brazuca_stream_url = f"{BRAZUCA_ADDON_BASE_URL}/stream/{content_type}/{stremio_id}.json"
    
    print(f"DEBUG SCRAPER: Chamando Brazuca Torrents API: {brazuca_stream_url}")
    
    magnets = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(brazuca_stream_url)
            resp.raise_for_status()
            
            data = resp.json()
            
            # 3. Processa a resposta do Brazuca Torrents
            for stream in data.get("streams", []):
                # O Brazuca Torrents retorna objetos de stream que contêm a URL/magnet
                url = stream.get("url")
                title = stream.get("title", "Magnet Brazuca")
                
                if url and url.startswith("magnet:"):
                    # Aqui você pode usar REGEX ou outras técnicas para extrair qualidade e sementes
                    quality_match = re.search(r'(\d{3,4}p)', title, re.IGNORECASE)
                    quality = quality_match.group(1) if quality_match else "UNK"
                    
                    magnets.append({
                        "title": title,
                        "magnet": url,
                        "quality": quality,
                        "seeds": 1 # O Brazuca Torrents não retorna sementes, mantemos 1
                    })
            
            print(f"DEBUG SCRAPER: Brazuca Torrents API encontrou {len(magnets)} resultados.")
            return magnets
        
        except httpx.HTTPStatusError as e:
            # 404 geralmente significa que o Brazuca Torrents não encontrou o item
            print(f"ERRO SCRAPER: Brazuca Torrents retornou status {e.response.status_code}. Item não encontrado ou API Down.")
            return []
        except Exception as e:
            print(f"ERRO CRÍTICO NO SCRAPER BRAZUCA: {e}")
            return []

