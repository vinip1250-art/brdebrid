import httpx

BASE_URL = "https://api.torbox.app/v1"

async def resolve_torbox(magnet, api_key):
    async with httpx.AsyncClient() as client:
        # Padrão mais comum: Chave como Bearer Token
        headers = {"Authorization": f"Bearer {api_key}"}
        
        try:
            # 1. Criar Torrent (Verifica cache)
            payload = {"magnet": magnet, "seed": 1, "allow_zip": False}
            
            # Debug: Mostrar a URL e o HEADER sendo enviados
            print(f"DEBUG TORBOX: Enviando POST para {BASE_URL}/api/torrents/createtorrent com Headers: {headers}")

            create_resp = await client.post(f"{BASE_URL}/api/torrents/createtorrent", json=payload, headers=headers, timeout=10)
            
            # --- TRATAMENTO DO ERRO 400 (Chave Incorreta ou Payload Inválido) ---
            if create_resp.status_code == 400:
                # Tenta ler o corpo do erro para obter detalhes
                try:
                    error_data = create_resp.json()
                    error_detail = error_data.get('message', error_data)
                except:
                    error_detail = create_resp.text[:150]
                
                print(f"ERRO TORBOX (DEBUG DETALHADO): Status 400. Detalhe da Resposta do Torbox: {error_detail}")
                return None
            
            # Se a resposta não for 2xx (e não for 400, que já tratamos), levantamos a exceção
            create_resp.raise_for_status()
            
            # --- Continuação da Lógica (Se a requisição inicial foi 2xx) ---
            
            create_data = create_resp.json()
            
            if not create_data.get("success"):
                # Captura falha no campo 'success' do JSON (se houver)
                print(f"ERRO TORBOX (Criar/Cache): Falha no campo success. Mensagem: {create_data.get('message', 'Erro desconhecido no JSON')}")
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
            
            link_resp.raise_for_status() # Garante que erros 4xx/5xx sejam registrados na geração do link
            link_data = link_resp.json()
            
            if link_data.get("success"):
                return link_data["data"]
            
            print(f"ERRO TORBOX (Gerar Link): {link_data.get('message', 'Falha desconhecida na geração do link.')}")
            return None

        except httpx.HTTPStatusError as e:
            # Captura 401, 403, 404, 500 etc. que não foram 400
            print(f"ERRO TORBOX (HTTPStatus): Status {e.response.status_code}. Resposta: {e.response.text[:100]}")
            return None
        
        except Exception as e:
            # Captura erro de conexão, timeout, ou JSON inválido
            print(f"ERRO TORBOX (Geral/Conexão/Timeout): {e}")
            return None
