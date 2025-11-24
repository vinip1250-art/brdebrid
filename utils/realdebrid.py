import httpx
import json

RD_API_URL = "https://api.real-debrid.com/rest/1.0"

async def resolve_realdebrid(magnet, api_key):
    """Resolve um magnet link para uma URL HTTP direta usando o Real-Debrid."""
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # 1. Adicionar o Magnet
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 1.1 Adiciona o magnet ao RD
            add_resp = await client.post(
                f"{RD_API_URL}/torrents/addMagnet",
                headers=headers,
                data={"magnet": magnet}
            )
            add_resp.raise_for_status()
            add_data = add_resp.json()
            torrent_id = add_data.get("id")
            
            if not torrent_id:
                print("ERRO RD: Falha ao adicionar magnet.")
                return None

            # 1.2 Selecionar os arquivos (simulamos que o torrent tem apenas um arquivo principal)
            # Na maioria dos casos de cache, o RD já tem a info dos arquivos
            
            # É necessário chamar /torrents/selectFiles/ID com o ID dos arquivos.
            # O ID "all" (ou '1' se for apenas um arquivo) geralmente funciona para torrents cached.
            
            select_resp = await client.post(
                f"{RD_API_URL}/torrents/selectFiles/{torrent_id}",
                headers=headers,
                data={"files": "all"} # Tenta selecionar todos os arquivos para aceleração
            )
            select_resp.raise_for_status()

            # 1.3 Obter o Link de Streaming
            # Isso é feito pelo endpoint /unrestrict/link, que converte o link do torrent em stream.
            
            # O RD agora precisa do link de download. Vamos pegar a info do torrent
            info_resp = await client.get(
                f"{RD_API_URL}/torrents/info/{torrent_id}",
                headers=headers
            )
            info_data = info_resp.json()
            
            # Pega o link de download (geralmente o maior arquivo)
            download_link = info_data.get("links", [])
            if not download_link:
                print("ERRO RD: Torrent não está pronto ou não tem links.")
                return None
            
            # Desrestringe o link (Converte para URL direta)
            unrestrict_resp = await client.post(
                f"{RD_API_URL}/unrestrict/link",
                headers=headers,
                data={"link": download_link[0]} # Pega o primeiro link (melhorar se houver vários)
            )
            unrestrict_data = unrestrict_resp.json()
            
            return unrestrict_data.get("download") # Retorna a URL final
            
        except httpx.RequestError as e:
            print(f"ERRO CRÍTICO RD: {e}")
            return None
        except Exception as e:
            print(f"ERRO RD Desconhecido: {e}")
            return None

