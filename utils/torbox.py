import httpx
# Importa bibliotecas para parsear strings de URL (necessário para extrair o hash)
from urllib.parse import parse_qs, urlparse 

BASE_URL = "https://api.torbox.app/v1"

# --- FUNÇÃO HELPER PARA EXTRAIR O HASH BTIH ---
def extract_btih_hash(magnet_uri):
    """Extrai o hash BTIH de um magnet link."""
    if magnet_uri and magnet_uri.startswith('magnet:'):
        query = urlparse(magnet_uri).query
        params = parse_qs(query)
        if 'xt' in params:
            # Busca o valor 'urn:btih:HASH'
            for xt_value in params['xt']:
                if xt_value.startswith('urn:btih:'):
                    # Retorna apenas o hash (o que a API do Torbox espera)
                    return xt_value.split(':')[-1]
    # Se falhar ou não for um magnet, retorna a string original
    return magnet_uri 


async def resolve_torbox(magnet, api_key):
    async with httpx.AsyncClient() as client:
        # Padrão de autenticação: Bearer Token
        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            # EXTRAÇÃO DO HASH CRÍTICA
            torrent_hash = extract_btih_hash(magnet)
            
            # 1. Criar Torrent (Verifica cache). O payload agora usa o hash BTIH.
            payload = {"magnet": torrent_hash, "seed": 1, "allow_zip": False}
            
            print(f"DEBUG TORBOX HASH: Hash extraído e enviado: {torrent_hash}")

            create_resp = await client.post(f"{BASE_URL}/api/torrents/createtorrent", json=payload, headers=headers, timeout=10)
            
            # --- TRATAMENTO DO ERRO 400 (O Torbox deve aceitar o hash agora) ---
            if create_resp.status_code == 400:
                try:
                    error_data = create_resp.json()
                    error_detail = error_data.get('detail', error_data.get('message', 'Erro desconhecido.'))
                except:
                    error_detail = create_resp.text[:150]
                
                print(f"ERRO TORBOX (DEBUG DETALHADO): Status 400. Detalhe da Resposta do Torbox: {error_detail}")
                return None
            
            create_resp.raise_for_status() # Lança erro para 4xx/5xx que não sejam 400
            
            # --- Continuação da Lógica (Se a requisição inicial foi 2xx) ---
            
            create_data = create_resp.json()
            
            if not create_data.get("success"):
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
            
            link_resp.raise_for_status() 
            link_data = link_resp.json()
            
            if link_data.get("success"):
                return link_data["data"]
            
            print(f"ERRO TORBOX (Gerar Link): {link_data.get('message', 'Falha desconhecida na geração do link.')}")
            return None

        except httpx.HTTPStatusError as e:
            # Captura 401, 403, 404, 500 etc. que não foram 400
            print(f"ERRO TORBOX (HTTPStatus): Status {e.response.status_code}. Falha na API. Resposta: {e.response.text[:100]}")
            return None
        
        except Exception as e:
            # Captura erro de conexão, timeout, ou JSON inválido
            print(f"ERRO TORBOX (Geral/Conexão/Timeout): {e}")
            return None
