import base64
import json
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
# ... (outros imports) ...

# 💡 CORREÇÃO CRÍTICA: Mudar o import da biblioteca de timeout
from async_timeout import timeout as async_timeout, TimeoutError # Usamos async_timeout agora
import time 

# ... (Definições app, constantes, helpers, rotas manifestos) ...

@app.get("/{config}/stream/{type}/{id}.json")
async def get_stream(config: str, type: str, id: str):
    user_settings = decode_config(config)
    
    # ... (parsing de ID e variáveis) ...
    
    magnets_found = []

    # 2. BUSCA: Fontes Múltiplas (Com Timeout de 5 Segundos Total)
    try:
        # 💡 USANDO A NOVA BIBLIOTECA: Força o timeout em 5 segundos
        async with async_timeout(5): 
            
            # 2.1 Scraper Interno (Brazuca Torrents)
            results_scraper = await scrape_brazuca_torrents(imdb_id, type, s_str, e_str)
            magnets_found.extend(results_scraper)
            
            # 2.2 Jackett (Se configurado)
            if user_settings.get("jackett_url") and user_settings.get("jackett_key"):
                results_jackett = await search_jackett(
                    user_settings["jackett_url"], user_settings["jackett_key"], imdb_id, type, s_str, e_str
                )
                magnets_found.extend(results_jackett)
                
    except TimeoutError:
        print("ALERTA: Busca de fontes (Brazuca/Jackett) excedeu o limite de 5 segundos. Retornando vazio.")
        return {"streams": []}
    
    # ... (Restante da lógica de debrid) ...

(O restante do código main.py é o mesmo que enviei na última correção, apenas a seção de importação e o get_stream foram ajustados para o novo nome da biblioteca).
Passo 2: Instalar a Biblioteca Correta
Você deve ativar o seu venv e instalar a biblioteca com o nome correto:
# Se o venv não estiver ativo
source venv/bin/activate

# 1. Instale o nome correto
pip install async-timeout

# 2. Remova o nome incorreto (opcional, mas limpa o ambiente)
pip uninstall asyncio-timeout

Após instalar o async-timeout e garantir que o main.py foi atualizado com o código acima, o servidor deve iniciar corretamente e o problema de "não carregar" no Stremio (devido ao timeout) será corrigido, permitindo-nos depurar a falha final na busca.
O Problema de Busca (Recapitulando)
Se o servidor finalmente iniciar, mas você continuar vendo 0 resultados, isso confirma que a chave de API do Brazuca Torrents está funcionando (o site retorna 200 OK), mas a estrutura de busca está falhando.
A falha é quase certamente na linha:
# utils/brazuca_scraper.py
for stream in data.get("streams", []):
    # ... a chave 'url' ou 'magnet' não está no stream object que o Brazuca retorna.

