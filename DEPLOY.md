# Guia de Deploy — MedID Data API

Este documento detalha o processo completo de deploy da aplicação em diferentes ambientes.

---

## 📋 Pré-requisitos

- Conta Railway (recomendado) ou Docker/Kubernetes
- Banco PostgreSQL 14+
- Redis 7+ (opcional, para rate limiting)
- Domínio configurado (produção)

---

## 🚀 Deploy Railway (Recomendado)

### 1. Preparação

```bash
# Fork ou clone o repositório
git clone https://github.com/mediddata/mediddata-api.git
cd mediddata-api

# Fazer push para seu repositório GitHub
git remote add origin https://github.com/SEU-USUARIO/mediddata-api.git
git push -u origin main
```

### 2. Criar Projeto Railway

1. Acesse [railway.app](https://railway.app)
2. Login com GitHub
3. **New Project** → **Deploy from GitHub repo**
4. Selecione `mediddata-api`
5. Railway detecta automaticamente o `Dockerfile`

### 3. Adicionar PostgreSQL

1. No dashboard do projeto, clique em **+ New**
2. Selecione **Database** → **PostgreSQL**
3. Railway cria automaticamente a variável `DATABASE_URL`

### 4. Adicionar Redis (Opcional)

1. No dashboard, clique em **+ New**
2. Selecione **Database** → **Redis**
3. Railway cria automaticamente a variável `REDIS_URL`

### 5. Configurar Variáveis de Ambiente

No painel do serviço da API, vá em **Variables** e adicione:

```env
# Obrigatório
SECRET_KEY=<gerar-com-openssl-rand-hex-32>
ENVIRONMENT=production

# CORS (substituir pelo domínio real)
ALLOWED_ORIGINS=https://seuapp.com,https://app.seuapp.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=5000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

**Gerar SECRET_KEY segura:**

```bash
openssl rand -hex 32
```

### 6. Deploy

Railway faz deploy automático a cada push na branch `main`.

Monitor o deploy em **Deployments**.

### 7. Configurar Domínio

1. No painel do serviço, vá em **Settings**
2. **Networking** → **Custom Domain**
3. Adicione `api.mediddata.com`
4. Configure CNAME no seu DNS:
   ```
   CNAME api mediddata.up.railway.app
   ```

### 8. Executar Migrações

Railway executa automaticamente via `entrypoint.sh` (se configurado).

Caso precise executar manualmente:

1. No painel do serviço, clique em **⋯** → **Shell**
2. Execute:
   ```bash
   alembic upgrade head
   ```

### 9. Importar Dados

**Opção 1: Via Railway Shell**

```bash
# Acessar shell do container
railway shell

# Executar scripts de importação
python -m app.scripts.importar_anvisa
python -m app.scripts.importar_cmed
python -m app.scripts.importar_cid10
python -m app.scripts.importar_sigtap
```

**Opção 2: Via Job Único**

Criar um serviço auxiliar no Railway para rodar uma vez:

```bash
# Criar arquivo import-data.sh
#!/bin/bash
python -m app.scripts.importar_anvisa
python -m app.scripts.importar_cmed
python -m app.scripts.importar_cid10
python -m app.scripts.importar_sigtap
echo "Importação concluída"
```

### 10. Verificar Deploy

```bash
# Health check
curl https://api.mediddata.com/saude

# Swagger
https://api.mediddata.com/docs
```

---

## 🐳 Deploy Docker

### Dockerfile Otimizado

Já incluído no projeto (`Dockerfile`):

- Multi-stage build (reduz tamanho da imagem)
- Usuário não-root (segurança)
- Health check automático
- Variável $PORT configurável

### Build e Push

```bash
# Build
docker build -t mediddata/api:1.0.0 .

# Tag latest
docker tag mediddata/api:1.0.0 mediddata/api:latest

# Push para registry
docker push mediddata/api:1.0.0
docker push mediddata/api:latest
```

### Run Local

```bash
docker run -d \
  --name mediddata-api \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e SECRET_KEY="..." \
  -e ENVIRONMENT="production" \
  mediddata/api:1.0.0
```

### Docker Compose Completo

```yaml
version: '3.8'

services:
  api:
    image: mediddata/api:1.0.0
    container_name: mediddata-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/mediddata
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
      - ALLOWED_ORIGINS=https://mediddata.com
      - RATE_LIMIT_ENABLED=true
      - LOG_FORMAT=json
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/saude"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s

  db:
    image: postgres:16-alpine
    container_name: mediddata-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=mediddata
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: mediddata-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

volumes:
  postgres_data:
  redis_data:
```

**Usar:**

```bash
# Criar .env
echo "SECRET_KEY=$(openssl rand -hex 32)" > .env
echo "DB_PASSWORD=senha-segura" >> .env

# Iniciar
docker-compose up -d

# Logs
docker-compose logs -f api

# Parar
docker-compose down
```

---

## ☸️ Deploy Kubernetes

### Manifests

**Deployment:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mediddata-api
  labels:
    app: mediddata-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mediddata-api
  template:
    metadata:
      labels:
        app: mediddata-api
    spec:
      containers:
      - name: api
        image: mediddata/api:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: mediddata-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: mediddata-secrets
              key: secret-key
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_FORMAT
          value: "json"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /saude
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /saude
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

**Service:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mediddata-api-service
spec:
  selector:
    app: mediddata-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

**Secrets:**

```bash
kubectl create secret generic mediddata-secrets \
  --from-literal=database-url="postgresql://..." \
  --from-literal=secret-key="$(openssl rand -hex 32)"
```

---

## 🔧 Configurações de Produção

### Nginx Reverse Proxy

```nginx
upstream mediddata_api {
    server localhost:8000;
    # Para múltiplas instâncias:
    # server localhost:8001;
    # server localhost:8002;
}

server {
    listen 80;
    server_name api.mediddata.com;

    # Redirecionar para HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.mediddata.com;

    ssl_certificate /etc/letsencrypt/live/api.mediddata.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.mediddata.com/privkey.pem;

    # SSL config
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Headers de segurança
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;

    # Proxy
    location / {
        proxy_pass http://mediddata_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Rate limiting global
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;
}
```

### Systemd Service (Linux)

```ini
[Unit]
Description=MedID Data API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=mediddata
Group=mediddata
WorkingDirectory=/opt/mediddata-api
Environment="PATH=/opt/mediddata-api/venv/bin"
EnvironmentFile=/opt/mediddata-api/.env
ExecStart=/opt/mediddata-api/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Ativar:**

```bash
sudo systemctl enable mediddata-api
sudo systemctl start mediddata-api
sudo systemctl status mediddata-api
```

---

## 📊 Monitoramento

### Logs Estruturados

Com `LOG_FORMAT=json`, todos os logs são emitidos em JSON:

```json
{
  "asctime": "2026-06-04T10:00:00Z",
  "levelname": "INFO",
  "name": "app.main",
  "message": "request_completed",
  "method": "GET",
  "path": "/medicamentos/buscar",
  "status_code": 200,
  "duration_ms": 45.23,
  "client_ip": "203.0.113.42"
}
```

**Integração com DataDog:**

```bash
# Instalar agente DataDog
DD_API_KEY=<sua-key> DD_SITE="datadoghq.com" bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script.sh)"

# Configurar tail de logs
echo "logs:
  - type: file
    path: /var/log/mediddata/*.log
    service: mediddata-api
    source: python
    sourcecategory: sourcecode" >> /etc/datadog-agent/conf.d/python.d/conf.yaml

sudo systemctl restart datadog-agent
```

### Health Check Avançado

Adicionar ao código:

```python
@app.get("/saude/completo")
async def health_completo(db: Session = Depends(get_db)):
    checks = {
        "database": False,
        "redis": False,
    }

    # Testar DB
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except:
        pass

    # Testar Redis (se configurado)
    # ...

    status_code = 200 if all(checks.values()) else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if all(checks.values()) else "degraded",
            "checks": checks
        }
    )
```

---

## 🔒 Segurança em Produção

### Checklist

- [ ] `SECRET_KEY` gerada com `openssl rand -hex 32`
- [ ] `ENVIRONMENT=production`
- [ ] `ALLOWED_ORIGINS` restrito a domínios específicos
- [ ] HTTPS configurado (Let's Encrypt ou CloudFlare)
- [ ] Senha do banco forte e armazenada em secrets
- [ ] Firewall configurado (apenas portas 80/443 expostas)
- [ ] Rate limiting ativo (`RATE_LIMIT_ENABLED=true`)
- [ ] Logs estruturados (`LOG_FORMAT=json`)
- [ ] Backup automático do banco (Railway: automático)
- [ ] Senha padrão alterada (`admin@mediddata.com`)
- [ ] Chaves API antigas revogadas
- [ ] Monitoramento de uptime ativo
- [ ] Alertas configurados para erros 5xx

---

## 📈 Escalabilidade

### Horizontal Scaling (Railway)

Railway escala automaticamente baseado em uso de CPU/memória.

**Manual:**
1. Settings → Scaling
2. Ajustar replicas (1-10)

### Workers Uvicorn

Ajustar número de workers:

```env
# development: 1
# produção: (2 x CPU cores) + 1
WORKERS=4
```

### Cache Redis

Implementar cache de queries frequentes:

```python
import redis
cache = redis.from_url(settings.redis_url)

@app.get("/medicamentos/buscar")
async def buscar(q: str):
    cache_key = f"busca:{q}"
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)

    resultado = _executar_busca(q)
    cache.setex(cache_key, 3600, json.dumps(resultado))
    return resultado
```

---

## 🆘 Troubleshooting

### Erro: "Database connection failed"

```bash
# Verificar variável DATABASE_URL
echo $DATABASE_URL

# Testar conexão direta
psql $DATABASE_URL -c "SELECT 1"
```

### Erro: "Rate limit exceeded" em desenvolvimento

```bash
# Desativar rate limiting
export RATE_LIMIT_ENABLED=false
```

### Logs não aparecem

```bash
# Forçar formato texto
export LOG_FORMAT=text

# Aumentar nível de log
export LOG_LEVEL=DEBUG
```

### Container reiniciando constantemente

```bash
# Ver logs do container
docker logs mediddata-api --tail 100

# Verificar health check
curl http://localhost:8000/saude
```

---

**Suporte:** deploy@mediddata.com
