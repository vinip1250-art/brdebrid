# Usa uma imagem Python leve e oficial
FROM python:3.10-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de dependências primeiro (para otimizar o cache do Docker)
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o restante do código para dentro do container
COPY . .

# Expõe a porta que o FastAPI usa
EXPOSE 8000

# Comando para rodar o servidor
# main:app refere-se ao arquivo main.py e a variável app = FastAPI()
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
