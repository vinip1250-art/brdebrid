from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import base64
import json
import traceback # Importado para capturar e logar erros fatais

from utils.torbox import resolve_torbox
# A busca do Jackett continua importada, mas a chamada foi removida para o teste isolado
# from utils.jackett import search_jackett 

app = FastAPI()

# Configuração de CORS (Essencial para o Stremio)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper para decodificar a configuração
def decode_config(config_str: str):
    try:
        decoded = base64.b64decode(config_str).decode("utf-8")
        return json.loads(decoded)
    except:
        return {}

@app.get("/", response_class=HTMLResponse)
async def config_page():
    # Servir a página de configuração (static/config.html)
    with open("static/config.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/{config}/manifest.json")
async def get_manifest(config: str):
    return {
        "id": "com.brazucamod.public",
        "version": "1.0.1",
        "name": "Brazuca Mod (Public)",
        "description": "Addon configurável com suporte a Torbox, Jackett e Scrapers BR",
        "resources": ["stream"],
        "types": ["movie", "series"],
        "catalogs": [],
        "idPrefixes": ["tt"]
    }

@app.get("/{config}/stream/{type}/{id}.json")
async def get_stream(config: str, type: str, id: str):
    
    # --- NOVO BLOCO TRY/EXCEPT GLOBAL PARA PEGAR FALHAS SILENCIOSAS ---
    try:
        user_settings = decode_config(config)
        
        if not user_settings.get("debrid_key"):
            return {"streams": [{"title": "⚠️ ERRO: API Key Debrid não configurada", "url": ""}]}

        # --- TESTE ISOLADO DO TORBOX (IGNORA JACKETT) ---
        # Magnet de Teste (Popular para garantir que esteja em cache no Torbox)
        TEST_MAGNET = "magnet:?xt=urn:btih:3137B75F3908851724D3D560A3F1F1E8E62294E8&dn=Filme+Teste+Cach%C3%A9" 
        
        magnets_found = [{
            "title": "Filme Teste (Magnet Fixo)",
            "magnet": TEST_MAGNET,
            "quality": "1080p",
            "seeds": 999
        }]
        
        if not magnets_found:
            return {"streams": []}

        streams = []
        
        # 4. RESOLUÇÃO: Torbox
        if user_settings.get("service") == "torbox":
            for magnet_obj in magnets_found:
                link_info = await resolve_torbox(
                    magnet_obj['magnet'], 
                    user_settings["debrid_key"]
                )
                
                if link_info:
                    print(f"DEBUG SUCESSO TORBOX: Link obtido para {magnet_obj['title']}")
                    streams.append({
                        "title": f"⚡ [Torbox] {magnet_obj['quality']} - {magnet_obj['title']}",
                        "url": link_info
                    })
                else:
                    print(f"DEBUG FALHA TORBOX: Torbox não conseguiu resolver {magnet_obj['title']}")
                    
        return {"streams": streams}
    
    except Exception as e:
        # Imprime o traceback completo para debug
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("ERRO FATAL NÃO TRATADO NA ROTA DE STREAM (VERIFIQUE TRACEBACK):")
        print(traceback.format_exc())
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        
        # Retorna o erro para o Stremio, forçando a visibilidade
        return {"streams": [{"title": f"🔴 ERRO INTERNO: {e.__class__.__name__}", "url": ""}]}


if __name__ == "__main__":
    import uvicorn
    # Não use esta porta 8000 se você estiver usando o Nginx como proxy, mas é padrão para testes
    uvicorn.run(app, host="0.0.0.0", port=8000)
