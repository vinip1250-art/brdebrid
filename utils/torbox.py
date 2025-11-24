import httpx

BASE_URL = "https://api.torbox.app/v1"

# A função de extração de hash foi removida. O magnet é usado como string completa.
async def resolve_torbox(magnet, api_key):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            # 1. Criar Torrent (Verifica cache). Payload com a URL Magnet completa.
            payload = {"magnet": magnet, "seed": 1, "allow_zip": False}
            
            # --- CORREÇÃO CRÍTICA: USAR 'data=' AO INVÉS DE 'json=' ---
            # O Torbox rejeita o formato JSON e exige form-data.
            print(f"DEBUG TORBOX MAGNET: Enviando payload como form-data. Magnet: {magnet[:50]}...") 
            
            create_resp = await client.post(
                f"{BASE_URL}/api/torrents/createtorrent", 
                data=payload, # <--- AQUI ESTÁ A CORREÇÃO
                headers=headers, 
                timeout=10
            )
            
            # --- TRATAMENTO DO ERRO 400 ---
            if create_resp.status_code == 400:
                try:
                    error_data = create_resp.json()
                    error_detail = error_data.get('detail', error_data.get('message', 'Erro desconhecido.'))
                except:
                    error_detail = create_resp.text[:150]
                
                print(f"ERRO TORBOX (DEBUG DETALHADO): Status 400. Detalhe da Resposta do Torbox: {error_detail}")
                return None
            
            create_resp.raise_for_status() 
            
            # --- Continuação da Lógica ---
            
            create_data = create_resp.json()
            
            if not create_data.get("success"):
                print(f"ERRO TORBOX (Criar/Cache): Falha no campo success. Mensagem: {create_data.get('message', 'Erro desconhecido no JSON')}")
                return None
                
            torrent_id = create_data["data"]["torrent_id"]
            
            # 2. Verificar Status e Arquivos (idem)
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
            
            link_resp.raise_for_status() 
            link_data = link_resp.json()
            
            if link_data.get("success"):
                return link_data["data"]
            
            print(f"ERRO TORBOX (Gerar Link): {link_data.get('message', 'Falha desconhecida na geração do link.')}")
            return None

        except httpx.HTTPStatusError as e:
            print(f"ERRO TORBOX (HTTPStatus): Status {e.response.status_code}. Falha na API. Resposta: {e.response.text[:100]}")
            return None
        
        except Exception as e:
            print(f"ERRO TORBOX (Geral/Conexão/Timeout): {e}")
            return None
