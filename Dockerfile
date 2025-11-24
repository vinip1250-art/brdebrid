FROM python:3.10-slim

WORKDIR /app

# Copia e instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código
COPY . .

# Expõe a porta interna
EXPOSE 8000

# Roda o servidor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
