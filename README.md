# 🔐 Secure Lock Backend

Backend robusto de una aplicación móvil para **bloqueo remoto de dispositivos** en tiempo real. 

El sistema sigue un modelo **Freemium**, permitiendo a los usuarios creadores administrar dispositivos, agruparlos en salas mediante códigos QR y ejecutar bloqueos programados o instantáneos con notificaciones de alta prioridad.

### 📋 Características Principales

- ✅ **Autenticación JWT** con roles diferenciados (Creator / Target)
- ✅ **Bloqueo remoto en tiempo real** mediante WebSockets
- ✅ **Notificaciones Push** con Firebase FCM
- ✅ **Desbloqueos programados** con Celery
- ✅ **Modelo Freemium** con planes Premium
- ✅ **Organización de dispositivos** por salas
- ✅ **Códigos QR** para invitaciones a salas
- ✅ **Auditoría completa** de eventos de bloqueo
- ✅ **Alto rendimiento** con Redis y Channels

---

## 🏗️ Arquitectura del Sistema

El flujo de datos está diseñado para ser **rápido** y **tolerante a fallos**, utilizando **Django Channels** para conexiones persistentes y **Firebase Cloud Messaging (FCM)** como respaldo de alta prioridad.

```mermaid
graph TB
    subgraph Clientes["📲 Clientes"]
        C["📱 App Creador<br/>(Admin)"]
        T["📱 App Target<br/>(Dispositivo)"]
    end
    
    subgraph Backend["🌐 Backend"]
        API["🌐 Django REST API<br/>(REST Endpoints)"]
        WS["⚡ Django Channels<br/>(WebSocket ASGI)"]
        AUTH["🔐 JWT Auth<br/>(simplejwt)"]
    end

    subgraph Workers["⏱️ Tareas Asincrónicas"]
        Celery["⏰ Celery Worker<br/>(Redis Broker)"]
    end

    subgraph Data["💾 Datos & Cache"]
        DB["🐬 MySQL<br/>(Modelos ORM)"]
        Redis["🔴 Redis<br/>(Cache & Pub/Sub)"]
    end

    subgraph External["🔌 Servicios Externos"]
        FCM["🔥 Firebase FCM<br/>(Push Notifications)"]
    end

    %% Relaciones del Creador
    C -->|HTTP REST<br/>JWT Token| AUTH
    AUTH -->|Valida| API
    
    %% Lógica de la API
    API -->|Lee/Escribe<br/>ORM| DB
    API -->|Publica Eventos| Redis
    API -->|Agenda<br/>Auto-desbloqueo| Celery
    API -->|Envía Push| FCM
    
    %% Tareas Asíncronas
    Celery -->|Consume<br/>Eventos| Redis
    Celery -->|Actualiza| DB
    Celery -->|Envía Push| FCM
    
    %% Relaciones del Target
    T -->|WebSocket<br/>Conexión| WS
    WS -->|Suscripción<br/>a Eventos| Redis
    FCM -->|Push<br/>Notification| T
```

---

## 📁 Estructura del Proyecto

```
AppMovil-Backend/
├── 📄 Docker & Configuración
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── manage.py
│
├── 🔑 Core Config
│   └── secure_lock/
│       ├── settings.py          # Configuración Django
│       ├── asgi.py              # ASGI para WebSockets
│       ├── wsgi.py              # WSGI para Gunicorn
│       ├── urls.py              # Router principal
│       ├── celery.py            # Config de Celery
│       └── routing.py           # WebSocket routing
│
├── 👥 Módulo: Usuarios
│   ├── users/
│   │   ├── models.py            # Modelo User (Creator/Target)
│   │   ├── serializers.py       # Serialización
│   │   ├── views.py             # Endpoints REST
│   │   ├── urls.py              # Rutas
│   │   ├── managers.py          # Custom QuerySet
│   │   ├── admin.py             # Panel admin
│   │   ├── apps.py
│   │   ├── __init__.py
│   │   └── migrations/
│   │       ├── 0001_initial.py
│   │       └── 0002_initial.py
│
├── 📱 Módulo: Dispositivos
│   ├── dispositivos/
│   │   ├── models.py            # Device, DeviceLockEvent
│   │   ├── serializers.py       # Serialización
│   │   ├── views.py             # CRUD endpoints
│   │   ├── urls.py              # Rutas
│   │   ├── services.py          # Lógica de negocio
│   │   ├── tasks.py             # Tareas Celery
│   │   ├── consumers.py         # WebSocket consumers
│   │   ├── routing.py           # Rutas WebSocket
│   │   ├── permissions.py       # Permisos custom
│   │   ├── admin.py             # Panel admin
│   │   ├── apps.py
│   │   ├── __init__.py
│   │   └── migrations/
│   │       ├── 0001_initial.py
│   │       └── 0002_initial.py
│
├── 🏠 Módulo: Salas
│   ├── salas/
│   │   ├── models.py            # Modelo Room
│   │   ├── serializers.py       # Serialización
│   │   ├── views.py             # Endpoints REST
│   │   ├── urls.py              # Rutas
│   │   ├── services.py          # Lógica de negocio
│   │   ├── admin.py             # Panel admin
│   │   ├── apps.py
│   │   ├── __init__.py
│   │   └── migrations/
│   │       ├── 0001_initial.py
│   │       └── 0002_initial.py
│
└── 💳 Módulo: Suscripciones
    └── suscripciones/
        ├── models.py            # Modelo Subscription
        ├── serializers.py       # Serialización
        ├── views.py             # Endpoints REST
        ├── urls.py              # Rutas
        ├── services.py          # Lógica de negocio
        ├── admin.py             # Panel admin
        ├── apps.py
        ├── __init__.py
        └── migrations/
            ├── 0001_initial.py
            └── 0002_initial.py
```

---

## 🗄️ Diagrama de Modelos de Datos

```mermaid
erDiagram
    USER ||--o{ DEVICE : owns
    USER ||--o{ ROOM : administers
    USER ||--o{ SUBSCRIPTION : has
    DEVICE ||--o{ DEVICELOCKEVENT : logs
    DEVICE }o--|| USER : locked_by
    DEVICE }o--o{ ROOM : belongs_to
    
    USER {
        int id PK
        string email UK
        string full_name
        string role "CREATOR | TARGET"
        boolean is_active
        datetime date_joined
    }
    
    DEVICE {
        int id PK
        int owner_id FK
        string id_unico UK
        string display_name
        string fcm_token
        boolean is_locked
        int battery_level
        datetime locked_at
        datetime locked_until
        string platform
        datetime last_seen
        datetime created_at
    }
    
    DEVICELOCKEVENT {
        int id PK
        int device_id FK
        int requested_by_id FK
        string action "LOCK | UNLOCK | AUTO_UNLOCK"
        string reason
        int duration_minutes
        datetime expires_at
        datetime created_at
    }
    
    ROOM {
        int id PK
        int admin_id FK
        string name
        string invite_code UK
        datetime created_at
    }
    
    SUBSCRIPTION {
        int id PK
        int user_id FK
        string plan_type "FREE | PREMIUM"
        decimal price_usd
        string status "ACTIVE | CANCELED | EXPIRED"
        datetime starts_at
        datetime expires_at
    }
```

---

## 🔄 Flujos Principales

### Flujo de Bloqueo Remoto

```mermaid
sequenceDiagram
    actor Creator as 📱 Creador
    participant API
    participant DB as MySQL
    participant Redis
    participant WS as WebSocket
    participant Device as 📱 Dispositivo
    participant FCM as Firebase FCM
    participant Celery

    Creator->>API: POST /devices/{id}/lock
    API->>DB: Crear DeviceLockEvent
    API->>DB: Actualizar Device.is_locked
    API->>Redis: Publicar evento lock
    API-->>Creator: ✅ 200 OK
    
    par Real-time a Dispositivo
        WS->>Redis: Escuchar eventos
        Redis-->>WS: Evento lock
        WS->>Device: WebSocket: {action: "lock"}
        Device-->>Device: 🔒 Bloquear dispositivo
    and Notificación Push
        FCM->>Device: Push notification
        Device-->>Device: 🔔 Mostrar notificación
    end
    
    Note over Celery: Si duration_minutes
    Celery->>DB: Esperar duración
    Celery->>DB: Auto-unlock
    Celery->>Redis: Publicar evento unlock
    Redis-->>WS: Evento unlock
    WS->>Device: WebSocket: {action: "unlock"}
    Device-->>Device: 🔓 Desbloquear
```

### Flujo de Autenticación

```mermaid
sequenceDiagram
    actor User as 👤 Usuario
    participant App
    participant API as Django API
    participant DB
    participant JWT as JWT Token

    User->>App: Email + Password
    App->>API: POST /auth/login
    API->>DB: Verificar User
    alt Usuario válido
        API->>JWT: Generar access + refresh tokens
        JWT-->>API: Tokens firmados
        API-->>App: {access_token, refresh_token}
        App->>App: 💾 Guardar tokens localmente
    else Usuario inválido
        API-->>App: ❌ 401 Unauthorized
    end
    
    Note over App: Próximas requests
    App->>API: GET /devices/<br/>Header: Authorization: Bearer {access_token}
    API->>API: Validar token JWT
    alt Token válido
        API->>DB: Ejecutar request
        API-->>App: ✅ Datos
    else Token expirado
        App->>API: POST /auth/refresh
        API->>JWT: Regenerar access_token
        API-->>App: Nuevo access_token
    end
```

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| **Framework** | Django | 4.2+ |
| **API REST** | Django REST Framework | 3.15.0+ |
| **Autenticación** | djangorestframework-simplejwt | 5.3.1+ |
| **WebSockets** | Django Channels | 4.1.0+ |
| **WebSocket Redis** | channels-redis | 4.2.0+ |
| **Base de Datos** | MySQL | - |
| **Driver MySQL** | PyMySQL | 1.1.1+ |
| **Cache & Pub/Sub** | Redis | 5.0.7+ |
| **Task Queue** | Celery | 5.4.0+ |
| **Web Server** | Gunicorn + Uvicorn | 22.0.0+ |
| **CORS** | django-cors-headers | 4.4.0+ |
| **Push Notifications** | Firebase Admin SDK | 6.5.0+ |
| **QR Codes** | qrcode | 7.4.2+ |
| **Containerización** | Docker & Docker Compose | Latest |

---

## ⚙️ Instalación y Configuración

### Prerequisitos

- Python 3.10+
- Docker & Docker Compose
- MySQL 5.7+
- Redis 6.0+
- Firebase Cloud Messaging (FCM) credenciales

### 1️⃣ Clonar Repositorio

```bash
git clone <tu-repo>
cd AppMovil-Backend
```

### 2️⃣ Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# Core Django
SECRET_KEY=your-secret-key-change-in-production
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Base de Datos
DATABASE_URL=mysql://user:password@localhost:3306/secure_lock
MYSQL_HOST=db
MYSQL_PORT=3306
MYSQL_USER=secure_lock
MYSQL_PASSWORD=secure_lock_pass
MYSQL_DATABASE=secure_lock

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=redis
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Firebase FCM
FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json
FIREBASE_PROJECT_ID=your-firebase-project-id

# JWT
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
JWT_REFRESH_EXPIRATION_DAYS=7

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://your-app.com

# Suscripciones
PREMIUM_PRICE_USD=13.00
```

### 3️⃣ Instalación Local

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor de desarrollo
python manage.py runserver
```

### 4️⃣ Instalación con Docker

```bash
# Construir imágenes
docker-compose build

# Ejecutar contenedores
docker-compose up -d

# Ver logs
docker-compose logs -f web

# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Aplicar migraciones
docker-compose exec web python manage.py migrate
```

---

## 🚀 Ejecutar en Desarrollo

### Backend Django

```bash
# Desarrollo local
python manage.py runserver 0.0.0.0:8000

# Con Uvicorn (ASGI)
uvicorn secure_lock.asgi:application --host 0.0.0.0 --port 8000 --reload
```

### Celery Worker

```bash
# Terminal 1: Celery Worker
celery -A secure_lock worker -l info

# Terminal 2: Celery Beat (Tareas programadas)
celery -A secure_lock beat -l info
```

### Redis y MySQL

```bash
# Con Docker Compose
docker-compose up redis db

# O localmente
redis-server
mysql -u secure_lock -p
```

---

## 📌 Endpoints Principales

### Autenticación

| Método | Endpoint | Descripción |
|--------|----------|------------|
| `POST` | `/api/auth/register/` | Registrar nuevo usuario |
| `POST` | `/api/auth/login/` | Login y obtener tokens JWT |
| `POST` | `/api/auth/refresh/` | Renovar access token |
| `POST` | `/api/auth/logout/` | Cerrar sesión |

### Dispositivos

| Método | Endpoint | Descripción |
|--------|----------|------------|
| `GET` | `/api/devices/` | Listar dispositivos del usuario |
| `POST` | `/api/devices/` | Registrar nuevo dispositivo |
| `GET` | `/api/devices/{id}/` | Detalles de un dispositivo |
| `PUT` | `/api/devices/{id}/` | Actualizar dispositivo |
| `DELETE` | `/api/devices/{id}/` | Eliminar dispositivo |
| `POST` | `/api/devices/{id}/lock/` | 🔒 Bloquear dispositivo |
| `POST` | `/api/devices/{id}/unlock/` | 🔓 Desbloquear dispositivo |
| `POST` | `/api/devices/{id}/lock-timed/` | ⏰ Bloqueo programado |
| `GET` | `/api/devices/{id}/lock-events/` | Historial de bloqueos |

### Salas

| Método | Endpoint | Descripción |
|--------|----------|------------|
| `GET` | `/api/rooms/` | Listar salas del usuario |
| `POST` | `/api/rooms/` | Crear nueva sala |
| `GET` | `/api/rooms/{id}/` | Detalles de una sala |
| `PUT` | `/api/rooms/{id}/` | Actualizar sala |
| `DELETE` | `/api/rooms/{id}/` | Eliminar sala |
| `POST` | `/api/rooms/{id}/add-device/` | Agregar dispositivo a sala |
| `DELETE` | `/api/rooms/{id}/remove-device/` | Remover dispositivo de sala |
| `GET` | `/api/rooms/invite/{code}/` | Unirse a sala por código |

### Suscripciones

| Método | Endpoint | Descripción |
|--------|----------|------------|
| `GET` | `/api/subscriptions/` | Ver suscripción actual |
| `POST` | `/api/subscriptions/upgrade/` | Actualizar a Premium |
| `POST` | `/api/subscriptions/cancel/` | Cancelar suscripción |
| `GET` | `/api/subscriptions/plans/` | Listar planes disponibles |

---

## 💾 Base de Datos

### Configuración MySQL

```bash
# Crear base de datos
CREATE DATABASE secure_lock CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Crear usuario
CREATE USER 'secure_lock'@'localhost' IDENTIFIED BY 'secure_lock_pass';

# Otorgar permisos
GRANT ALL PRIVILEGES ON secure_lock.* TO 'secure_lock'@'localhost';
FLUSH PRIVILEGES;
```

### Migraciones

```bash
# Crear nueva migración
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Ver estado de migraciones
python manage.py showmigrations

# Revertir última migración
python manage.py migrate app_name 0001
```

---

## 🔌 WebSocket / Real-time

### Conexión WebSocket

```javascript
// Cliente (JavaScript)
const socket = new WebSocket('ws://localhost:8000/ws/devices/123/?token=JWT_TOKEN');

socket.onopen = (event) => {
    console.log('✅ Conectado');
};

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('📨 Mensaje:', data);
    // {type: 'lock', action: 'LOCK', device_id: 123}
};

socket.onerror = (event) => {
    console.error('❌ Error:', event);
};

socket.onclose = (event) => {
    console.log('❌ Desconectado');
};
```

### Eventos WebSocket

```javascript
// Evento de bloqueo
{
    "type": "lock_event",
    "action": "LOCK",
    "device_id": 123,
    "timestamp": "2024-04-12T10:30:00Z",
    "duration_minutes": 30
}

// Evento de desbloqueo
{
    "type": "lock_event",
    "action": "UNLOCK",
    "device_id": 123,
    "timestamp": "2024-04-12T11:00:00Z"
}

// Actualización de batería
{
    "type": "device_update",
    "device_id": 123,
    "battery_level": 75,
    "last_seen": "2024-04-12T10:35:00Z"
}
```

---

## 🧪 Testing

```bash
# Ejecutar tests
python manage.py test

# Tests con cobertura
coverage run --source='.' manage.py test
coverage report

# Tests específicos
python manage.py test usuarios.tests
```

---

## 📊 Admin Panel

Acceder a panel administrativo:

```
URL: http://localhost:8000/admin/
Usuario: (el que creaste con createsuperuser)
Contraseña: (la que configuraste)
```

### Modelos disponibles en Admin

- ✅ Usuarios (Users)
- ✅ Dispositivos (Devices)
- ✅ Eventos de Bloqueo (DeviceLockEvent)
- ✅ Salas (Rooms)
- ✅ Suscripciones (Subscriptions)

---

## 🔐 Seguridad

### Implementado

- ✅ **JWT Token-based** autenticación
- ✅ **CORS** configurado
- ✅ **Permisos** por rol (Creator/Target)
- ✅ **HTTPS** en producción
- ✅ **SECRET_KEY** secreto
- ✅ **Rate limiting** (recomendado)
- ✅ **CSRF** protección
- ✅ **SQL Injection** protección (ORM Django)

### Recomendaciones para Producción

```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {...}
```

---

## 📈 Monitoreo y Logs

### Logs de Celery

```bash
# Ver tareas en tiempo real
celery -A secure_lock events

# Inspeccionar workers
celery -A secure_lock inspect active
```

### Logs de Django

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

---

## 🐛 Troubleshooting

### Problema: No conecta a MySQL

```bash
# Verificar conexión
python manage.py dbshell

# Revisar settings DATABASE_URL
# Verificar MySQL está corriendo
```

### Problema: WebSocket no funciona

```bash
# Verificar Redis está corriendo
redis-cli ping  # Debe devolver PONG

# Verificar Channels está instalado
pip install channels channels-redis
```

### Problema: Celery tasks no ejecutan

```bash
# Verificar Celery worker está corriendo
celery -A secure_lock worker -l info

# Verificar Redis broker
redis-cli KEYS '*'

# Ver tasks en queue
celery -A secure_lock inspect active
```

---

## 📚 Recursos Útiles

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django Channels](https://channels.readthedocs.io/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Firebase Cloud Messaging](https://firebase.google.com/docs/cloud-messaging)
- [JWT Best Practices](https://tools.ietf.org/html/rfc7519)

---

## 📝 Licencia

Este proyecto está bajo licencia [MIT](LICENSE).

---

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📞 Contacto

Para preguntas o sugerencias, abre un issue en el repositorio.

---

**Última actualización:** Abril 2026