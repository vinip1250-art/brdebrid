import httpx

BASE_URL = "https://api.torbox.app/v1"

async def resolve_torbox(magnet, api_key):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            # 1. Criar Torrent (Verifica cache)
            payload = {"magnet": magnet, "seed": 1, "allow_zip": False}
            # Timeout baixo para a criação/cache, se demorar é melhor falhar rápido
            create_resp = await client.post(f"{BASE_URL}/api/torrents/createtorrent", json=payload, headers=headers, timeout=10)
            create_data = create_resp.json()
            
            if not create_data.get("success"):
                # LOG DE FALHA NA RESOLUÇÃO TORBOX:
                print(f"ERRO TORBOX (Criar/Cache): Falha na API. Mensagem: {create_data.get('message', 'Erro desconhecido')}. Status: {create_resp.status_code}")
                return None
                
            torrent_id = create_data["data"]["torrent_id"]
            
            # 2. Verificar Status e Arquivos
            info_resp = await client.get(f"{BASE_URL}/api/torrents/mylist?id={torrent_id}", headers=headers, timeout=5)
            info_data = info_resp.json()
            
            files = info_data["data"]["files"]
            if not files:
                print("ERRO TORBOX: Nenhum arquivo encontrado no torrent resolvido.")
                return None
                
            # Pega o maior arquivo de vídeo
            best_file = max(files, key=lambda x: x['size'])
            
            # 3. Gerar Link de Download
            link_resp = await client.get(
                f"{BASE_URL}/api/torrents/requestdl?token={api_key}&torrent_id={torrent_id}&file_id={best_file['id']}&zip_link=false", 
                headers=headers, timeout=5
            )
            link_data = link_resp.json()
            
            if link_data.get("success"):
                return link_data["data"]
            
            print(f"ERRO TORBOX (Gerar Link): {link_data.get('message', 'Falha desconhecida na geração do link.')}")
            return None

        except Exception as e:
            # Captura erro de conexão, timeout, ou JSON inválido
            print(f"ERRO TORBOX (Geral/Conexão/Timeout): {e}")
            return None
