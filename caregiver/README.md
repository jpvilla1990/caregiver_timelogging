# Registro de Horas — Cuidadora

App para que la cuidadora registre sus horas diarias y las sincronice automáticamente con Google Sheets.

## Stack
- Backend: FastAPI (Python)
- Frontend: HTML/CSS/JS vanilla
- Autenticación: Google OAuth2
- Almacenamiento: Google Sheets

---

## 1. Configurar Google Cloud

### Crear proyecto y credenciales OAuth

1. Ve a https://console.cloud.google.com
2. Crear proyecto nuevo (ej: "cuidadora-app")
3. APIs & Services → Enable APIs:
   - Google Sheets API
   - Google+ API (para userinfo)
4. APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID
   - Application type: Web application
   - Authorized redirect URIs: `https://tu-dominio.com/auth/callback`
5. Copiar **Client ID** y **Client Secret**

### Preparar Google Sheet

1. Crear una hoja nueva en Google Drive
2. En la primera fila agregar headers: `Fecha | Horas | Comentario | Registrado`
3. Copiar el ID de la URL: `docs.google.com/spreadsheets/d/ESTE_ES_EL_ID/edit`
4. **Importante**: La cuidadora debe tener acceso de edición a la hoja

---

## 2. Variables de entorno

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_SHEET_ID=your-sheet-id
APP_URL=https://tu-dominio.com
```

---

## 3. Docker

```bash
docker build -t cuidadora-app .
docker run -p 8000:8000 \
  -e GOOGLE_CLIENT_ID=xxx \
  -e GOOGLE_CLIENT_SECRET=xxx \
  -e GOOGLE_SHEET_ID=xxx \
  -e APP_URL=https://tu-dominio.com \
  cuidadora-app
```

---

## 4. Kubernetes Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: cuidadora-secret
  namespace: cuidadora
type: Opaque
stringData:
  GOOGLE_CLIENT_ID: "your-client-id"
  GOOGLE_CLIENT_SECRET: "your-client-secret"
  GOOGLE_SHEET_ID: "your-sheet-id"
  APP_URL: "https://tu-dominio.com"
```

## 5. Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cuidadora
  namespace: cuidadora
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cuidadora
  template:
    metadata:
      labels:
        app: cuidadora
    spec:
      containers:
        - name: cuidadora
          image: your-registry/cuidadora-app:latest
          ports:
            - containerPort: 8000
          envFrom:
            - secretRef:
                name: cuidadora-secret
---
apiVersion: v1
kind: Service
metadata:
  name: cuidadora-service
  namespace: cuidadora
spec:
  selector:
    app: cuidadora
  ports:
    - port: 8000
      targetPort: 8000
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: cuidadora
  namespace: cuidadora
spec:
  parentRefs:
    - name: traefik-gateway
      namespace: traefik
  hostnames:
    - cuidadora.tu-dominio.com
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: cuidadora-service
          port: 8000
```

---

## 6. Desarrollo local

```bash
pip install -r requirements.txt

export GOOGLE_CLIENT_ID=xxx
export GOOGLE_CLIENT_SECRET=xxx
export GOOGLE_SHEET_ID=xxx
export APP_URL=http://localhost:8000

uvicorn main:app --reload
```

Abrir http://localhost:8000
