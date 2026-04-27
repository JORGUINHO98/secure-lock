<p align="center">
  <img src="secure_lock_logo_1777329199122.png" width="200" alt="Secure Lock Logo">
</p>

# 🔐 Secure Lock Backend

> [!IMPORTANT]
> **Secure Lock** is a robust backend solution for real-time remote device locking, designed with a focus on security, performance, and scalability.

El sistema sigue un modelo **Freemium**, permitiendo a los usuarios creadores administrar dispositivos, agruparlos en salas mediante códigos QR y ejecutar bloqueos programados o instantáneos. 

> [!TIP]
> Esta fase del proyecto está optimizada para demostraciones con **Expo Go**, utilizando **WebSockets** como motor principal de tiempo real. El código cuenta con **"Degradación Elegante"** (Graceful Degradation).

---

## 📋 Características Principales

- 🔐 **Autenticación JWT**: Roles diferenciados (Creator / Target).
- ⚡ **Tiempo Real**: Bloqueo remoto instantáneo mediante WebSockets.
- 💳 **Modelo Freemium**: Gestión de planes y suscripciones Premium.
- 🏠 **Organización Inteligente**: Gestión de dispositivos por salas y códigos QR.
- 📑 **Auditoría**: Registro completo de eventos de bloqueo y actividad.
- 🚀 **Alto Rendimiento**: Integración con Redis y Django Channels.

---

## 🏗️ Arquitectura del Sistema

La arquitectura está diseñada para ser **altamente reactiva** y **tolerante a fallos**, minimizando la latencia en las operaciones de bloqueo.

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

    subgraph Data["💾 Datos & Cache"]
        DB["🗄️ PostgreSQL<br/>(Modelos ORM)"]
        Redis["🔴 Redis<br/>(Cache & Pub/Sub)"]
    end

    %% Relaciones del Creador
    C -->|HTTP REST<br/>JWT Token| AUTH
    AUTH -->|Valida| API
    
    %% Lógica de la API
    API -->|Lee/Escribe<br/>ORM| DB
    API -->|Publica Eventos| Redis

    %% Relaciones del Target
    T -->|WebSocket<br/>Conexión| WS
    WS -->|Suscripción<br/>a Eventos| Redis
```

---

## 📁 Estructura del Proyecto

Organización modular siguiendo las mejores prácticas de Django:

```text
AppMovil-Backend/
├── 🔑 core/                 # Configuración principal (Settings, ASGI/WSGI, Routing)
├── 👥 users/                # Gestión de usuarios, roles y autenticación JWT
├── 📱 dispositivos/         # Modelos de dispositivos, eventos y lógica WebSocket
├── 🏠 salas/                # Organización de dispositivos en espacios compartidos
└── 💳 suscripciones/       # Lógica de planes freemium y pagos
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
        string email "UK"
        string full_name
        string role "CREATOR | TARGET"
        boolean is_active
        datetime date_joined
    }
    
    DEVICE {
        int id PK
        int owner_id FK
        string id_unico "UK"
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
        string action "LOCK | UNLOCK"
        string reason
        int duration_minutes
        datetime expires_at
        datetime created_at
    }
    
    ROOM {
        int id PK
        int admin_id FK
        string name
        string invite_code "UK"
        datetime created_at
    }
    
    SUBSCRIPTION {
        int id PK
        int user_id FK
        string plan_type "FREE | PREMIUM"
        decimal price_usd
        string status "ACTIVE | CANCELED"
        datetime starts_at
        datetime expires_at
    }
```

---

## 🔄 Flujos de Trabajo

### 1. Bloqueo Remoto (Real-time)
```mermaid
sequenceDiagram
    actor Creator as 📱 Creador
    participant API
    participant DB as PostgreSQL
    participant Redis
    participant WS as WebSocket
    participant Device as 📱 Dispositivo

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
    end
```

### 2. Autenticación y Refresh
```mermaid
sequenceDiagram
    actor User as 👤 Usuario
    participant App
    participant API as Django API
    participant JWT as JWT Service

    User->>App: Login Credentials
    App->>API: POST /auth/login
    API->>JWT: Generar Tokens
    JWT-->>App: {access, refresh}
    
    Note over App: Solicitudes posteriores
    App->>API: GET /data (Header: Bearer)
    alt Token Expirado
        App->>API: POST /auth/refresh
        API-->>App: Nuevo Access Token
    end
```

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología | Propósito |
| :--- | :--- | :--- |
| **Backend** | Django 4.2+ | Framework robusto y escalable |
| **Real-time** | Django Channels | Gestión de WebSockets asíncronos |
| **API** | DRF | REST Framework para endpoints móviles |
| **Database** | PostgreSQL 16 | Almacenamiento relacional persistente |
| **Cache/Pub-Sub** | Redis | Motor para Channels y caché rápida |
| **Auth** | SimpleJWT | Estándar de seguridad para APIs |

---

## ⚙️ Instalación y Configuración

### 🐳 Con Docker (Recomendado)

```bash
# 1. Construir y levantar servicios
docker-compose up -d --build

# 2. Aplicar migraciones
docker-compose exec backend python manage.py migrate

# 3. Crear administrador
docker-compose exec backend python manage.py createsuperuser
```

### 🐍 Instalación Manual

1. **Entorno**: `python -m venv venv` y actívalo.
2. **Dependencias**: `pip install -r requirements.txt`.
3. **Migraciones**: `python manage.py migrate`.
4. **Ejecutar**: `python manage.py runserver`.

---

## 🔐 Seguridad Avanzada

> [!NOTE]
> Se han implementado medidas de seguridad críticas en la última actualización (Abril 2026).

- **WebSocket Auth**: Middleware personalizado que valida JWT en conexiones persistentes.
- **Ownership Validation**: Los dispositivos solo aceptan conexiones del propietario verificado.
- **Auditoría Persistente**: Uso de `SET_NULL` para mantener logs incluso tras eliminar usuarios.
- **HSTS & SSL**: Configuración lista para entornos de producción seguros.

---

## 📌 Endpoints Clave

| Recurso | Método | Endpoint |
| :--- | :--- | :--- |
| **Auth** | `POST` | `/api/auth/login/` |
| **Devices** | `POST` | `/api/devices/{id}/lock/` |
| **Rooms** | `GET` | `/api/rooms/invite/{code}/` |
| **Plans** | `GET` | `/api/subscriptions/plans/` |

---

<p align="center">
  Desarrollado con ❤️ por el equipo de Secure Lock. 2026.
</p>
