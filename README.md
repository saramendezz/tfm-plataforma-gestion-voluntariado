# Plataforma web para la gestión y coordinación del voluntariado en situaciones de emergencia

Trabajo Fin de Máster · Desarrollo práctico

**Autora:** Sara Méndez Bravo
**Director:** Antonio Cañellas Coll

## Descripción

Plataforma web que conecta organizaciones y personas voluntarias durante una situación de emergencia. Las organizaciones publican necesidades de voluntariado con sus requisitos, y el sistema muestra a cada voluntario las necesidades compatibles con su perfil, según sus **habilidades**, su **disponibilidad** y su **localización**, ordenadas por una puntuación explicable. La decisión de participar corresponde al voluntario: la organización solo conoce cuántos voluntarios compatibles hay y ve la identidad y el contacto únicamente de quienes han aceptado.

El sistema contempla tres perfiles de usuario: voluntarios, organizaciones y administradores.

## Estado del proyecto

Funcionalidad completa (desarrollo en fase de cierre y pruebas).

| Sprint | Objetivo | Estado |
|---|---|---|
| 1 | Base del sistema, autenticación con roles y perfiles | Completado |
| 2 | Gestión de necesidades y disponibilidad | Completado |
| 3 | Compatibilidad y participación del voluntario | Completado |
| 4 | Pruebas y cierre | En curso |

## Tecnologías

| Capa | Tecnología |
|---|---|
| Backend | Python, Django, Django REST Framework |
| Autenticación | JWT (`djangorestframework-simplejwt`) |
| Frontend | React con Vite, Axios, React Router |
| Base de datos | SQLite en desarrollo (previsto migrar a PostgreSQL) |
| Pruebas | pytest-django (backend) |
| Control de versiones | Git |
| Cálculo de distancias | Fórmula de Haversine sobre códigos postales de GeoNames |

## Estructura del repositorio

```
tfm-voluntariado/
├── backend/     # API: Django + DRF (accounts, profiles, needs, matching, participations)
├── frontend/    # Interfaz: React + Vite
├── tools/       # Utilidades (prueba de carga)
├── .gitignore
└── README.md
```

## Requisitos previos

- Python 3
- Node.js (versión LTS) y npm
- Git

## Puesta en marcha

### 1. Backend

Desde la carpeta `backend` (PowerShell en Windows):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

En Linux o macOS, el entorno virtual se activa con `source .venv/bin/activate`.

Crea el archivo `backend/.env` con este contenido (no se sube al repositorio):

```
SECRET_KEY=pega-aqui-una-clave-aleatoria
DEBUG=True
```

Para generar la clave:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Aplica las migraciones, crea un superusuario y arranca el servidor:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_skills
python manage.py runserver
```

El backend queda disponible en `http://127.0.0.1:8000/`. Para comprobar que funciona, abre `http://127.0.0.1:8000/api/health/`, que debe devolver `{"status": "ok"}`. El panel de administración está en `/admin/`.

### 2. Frontend

En otra terminal, desde la carpeta `frontend`:

```powershell
npm install
npm run dev
```

El frontend queda disponible en `http://localhost:5173/`. Si ves **Backend: ok**, la comunicación entre React y Django funciona. Necesitas tener el backend arrancado.

### 3. Datos de demostración (opcional)

Para calcular distancias se necesitan los códigos postales de GeoNames. Descarga `ES.zip` desde https://download.geonames.org/export/zip/, descomprime `ES.txt` en `backend/data/` (esa carpeta no se sube al repositorio) y ejecuta, desde `backend`:

```powershell
python manage.py load_postal_codes
python manage.py seed_demo --reset
```

El segundo comando crea 2 organizaciones, 6 necesidades y 30 voluntarios ficticios (`demo_org1`, `demo_org2`, `demo_vol01`…, contraseña `Demo-2026-pass`). Son datos de prueba.

## Pruebas

```powershell
cd backend
pytest                      # 77 pruebas automatizadas
python manage.py analyze_weights --csv resultados_sensibilidad.csv   # sensibilidad de pesos
cd ..
python tools/loadtest.py --base http://127.0.0.1:8000 --users 20 --requests 50   # carga básica
```

## Privacidad y protección de datos

La plataforma se diseña con criterios de minimización de datos:

- Solo se recogen los datos necesarios para el proceso de asignación.
- Las habilidades se gestionan como un **catálogo controlado**, sin campos de texto libre.
- No se recogen atributos que puedan revelar o permitir inferir información sensible, como la ideología política o las creencias religiosas.
- El acceso a los datos se controla según el rol del usuario.
- La identidad y el contacto de un voluntario solo se revelan a la organización cuando él acepta participar; antes solo se muestra un número.

## Alcance

Queda fuera del alcance del proyecto la gestión de recursos materiales, la geolocalización de voluntarios en tiempo real, la comunicación directa con organismos oficiales y el desarrollo de una aplicación móvil.

## Contexto académico

Este repositorio forma parte de un Trabajo Fin de Máster del Máster Universitario en Ingeniería de Software y Sistemas Informáticos de la Universidad Internacional de La Rioja (UNIR), curso 2026-2027.