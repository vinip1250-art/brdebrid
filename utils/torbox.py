async def resolve_torbox(magnet, api_key):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {api_key}"}

        # 1. Criar Torrent (Isso no Torbox checa o cache automaticamente)
        try: # <--- Início do try
            payload = {"magnet": magnet, "seed": 1, "allow_zip": False}
            create_resp = await client.post(f"{BASE_URL}/api/torrents/createtorrent", json=payload, headers=headers)
        create_data = create_resp.json() # <--- ERRO: Fora do bloco try! Se a requisição falhar (create_resp), esta linha trava.

        # ... todo o restante do código (torrent_id, info_resp, link_resp)
        # ... está dentro da chave 'try', mas fora do escopo após a falha da primeira linha.
        
        except Exception as e:
            print(f"Erro Torbox: {e}")
            return None # <--- Este bloco except só pega erros na criação do payload.
