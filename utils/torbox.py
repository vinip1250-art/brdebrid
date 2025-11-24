import httpx

BASE_URL = "https://api.torbox.app/v1"

async def resolve_torbox(magnet, api_key):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {api_key}"}

        # 1. Criar Torrent (Isso no Torbox checa o cache automaticamente)
        try:
            payload = {"magnet": magnet, "seed": 1, "allow_zip": False}
            create_resp = await client.post(f"{BASE_URL}/api/torrents/createtorrent", json=payload, headers=headers)
            create_data = create_resp.json()
            
            if not create_data.get("success"):
                return None
                
            torrent_id = create_data["data"]["torrent_id"]
            
            # 2. Verificar Status (Se é cached, download_state deve ser ok)
            info_resp = await client.get(f"{BASE_URL}/api/torrents/mylist?id={torrent_id}", headers=headers)
            info_data = info_resp.json()
            
            files = info_data["data"]["files"]
            if not files:
                return None
                
            # Lógica simples: Pega o maior arquivo de vídeo
            # (Pode melhorar isso filtrando por .mkv, .mp4 e sample)
            best_file = max(files, key=lambda x: x['size'])
            
            # 3. Gerar Link
            link_resp = await client.get(
                f"{BASE_URL}/api/torrents/requestdl?token={api_key}&torrent_id={torrent_id}&file_id={best_file['id']}&zip_link=false", 
                headers=headers
            )
            link_data = link_resp.json()
            
            if link_data.get("success"):
                return link_data["data"]
            return None

        except Exception as e:
            print(f"Erro Torbox: {e}")
            return None
