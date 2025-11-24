import httpx
import json

BASE_URL = "https://api.torbox.app/v1"

async def resolve_torbox(magnet, api_key):
    """Resolve um magnet link para uma URL HTTP direta usando a API do Torbox."""
    async with httpx.AsyncClient(timeout=20.0) as client: # Aumentei o timeout para 20s
        headers = {"Authorization": f"Bearer {api_key}"}

        # 1. Criar/Verificar Torrent (Isso no Torbox checa o cache automaticamente)
        try:
            print(f"DEBUS TORBOX MAGNET: Enviando payload. Magnet: {magnet[:50]}...")
            payload = {"magnet": magnet, "seed": 1, "allow_zip": False}
            
            # Torbox API usa token no corpo para /createtorrent
            payload["token"] = api_key 
            
            create_resp = await client.post(f"{BASE_URL}/api/torrents/createtorrent", json=payload, headers=headers)
            create_data = create_resp.json()
            
            if not create_data.get("success"):
                print(f"ERRO TORBOX: Falha ao criar/checar torrent: {create_data.get('message', 'Erro desconhecido')}")
                return None
                
            torrent_id = create_data["data"]["torrent_id"]
            
            # 2. Verificar Status e Arquivos
            # Usando /mylist com o ID para obter detalhes do arquivo
            info_resp = await client.get(f"{BASE_URL}/api/torrents/mylist?id={torrent_id}", headers=headers)
            info_data = info_resp.json()
            
            if not info_data.get("success") or not info_data["data"].get("files"):
                 print("ERRO TORBOX: Não foi possível obter detalhes do torrent ou nenhum arquivo listado.")
                 return None
            
            files = info_data["data"]["files"]
            
            # 💡 Correção de Seleção de Arquivo: Filtrar apenas arquivos de vídeo válidos
            video_extensions = ('.mkv', '.mp4', '.avi', '.webm')
            
            # Filtra arquivos que NÃO são samples e que têm extensão de vídeo
            video_files = [
                f for f in files 
                if f['path'].lower().endswith(video_extensions) and 'sample' not in f['path'].lower()
            ]
            
            if not video_files:
                print("ERRO TORBOX: Nenhum arquivo de vídeo principal encontrado após filtro.")
                return None
            
            # Escolhe o maior arquivo de vídeo após a filtragem (que deve ser o filme/episódio)
            best_file = max(video_files, key=lambda x: x['size'])
            
            # 3. Gerar Link de Download
            print(f"DEBUG: Arquivo escolhido: {best_file['path']}")
            
            link_resp = await client.get(
                f"{BASE_URL}/api/torrents/requestdl?token={api_key}&torrent_id={torrent_id}&file_id={best_file['id']}&zip_link=false",
                headers=headers
            )
            link_data = link_resp.json()
            
            if link_data.get("success"):
                return link_data["data"]
            
            print(f"ERRO TORBOX: Falha ao obter link de download: {link_data.get('message', 'Erro desconhecido')}")
            return None

        except Exception as e:
            print(f"ERRO CRÍTICO TORBOX: {e}")
            return None
