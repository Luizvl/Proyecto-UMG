# Plataforma Nacional para la Gestión Integral de Becas

Proyecto de Análisis de Sistemas II — UMG.

## Arquitectura

El proyecto sigue una **arquitectura en capas** dentro de cada app de dominio:

```
Presentación   -> views.py, serializers.py, urls.py   (Django REST Framework)
Aplicación     -> services.py, builders.py, factories.py  (lógica de negocio)
Dominio        -> models.py, states.py, strategies.py  (entidades y reglas)
Persistencia   -> Django ORM (settings.py define el motor: SQLite o MySQL)
```

Cada app (`apps/estudiantes`, `apps/convocatorias`, `apps/solicitudes`,
`apps/evaluaciones`) representa un dominio del negocio, no una capa técnica —
esto mantiene bajo acoplamiento entre dominios y facilita que cada
integrante del equipo trabaje en una app distinta sin pisarse.

## Patrones de diseño implementados

| Categoría | Patrón | Dónde | Por qué (resumen) |
|---|---|---|---|
| Creacional | **Factory Method** | `evaluaciones/factories.py` | Centraliza qué estrategia de evaluación usar según tipo de beca |
| Creacional | **Builder** | `solicitudes/builders.py` | Arma una solicitud junto con sus documentos paso a paso |
| Estructural | **Facade** | `solicitudes/services.py` | Oculta la coordinación entre Solicitud, Documento e Historial |
| Estructural | **Adapter** | `solicitudes/adapters.py` | Prepara el sistema para integraciones futuras con otras instituciones |
| Comportamiento | **State** | `solicitudes/states.py` | Controla las transiciones válidas del ciclo de vida de una solicitud |
| Comportamiento | **Strategy** | `evaluaciones/strategies.py` | Cambia el cálculo del puntaje final según el tipo de beca |

Cada archivo tiene, en su docstring, la justificación técnica completa
(qué problema resuelve, qué alternativas se consideraron, por qué se
eligió el patrón) lista para reutilizar en el documento de
"Justificación de Patrones".

## Instalación

```bash
# 1. Clonar el repo y entrar a la carpeta
cd becas_platform

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env si se desea usar MySQL (ver instrucciones dentro del archivo)

# 5. Aplicar migraciones
python manage.py makemigrations
python manage.py migrate

# 6. Crear superusuario para entrar al panel de administración
python manage.py createsuperuser

# 7. Levantar el servidor
python manage.py runserver
```

Por defecto el proyecto usa **SQLite** (no requiere instalar nada más) para
que cualquiera del equipo lo levante en minutos. Para usar **MySQL**,
descomentar las variables `DB_*` en `.env` e instalar `mysqlclient`
(requiere `libmysqlclient-dev` / `default-libmysqlclient-dev` en Linux, o
MySQL Connector en Windows).

## Endpoints principales (API REST)

| Método | Endpoint | Descripción |
|---|---|---|
| GET/POST | `/api/estudiantes/` | Listar / registrar estudiantes |
| GET/POST | `/api/convocatorias/` | Listar / crear convocatorias |
| GET | `/api/convocatorias/?activas=true` | Solo convocatorias activas (HU-03) |
| GET/POST | `/api/solicitudes/` | Listar / crear solicitudes (usa la Facade) |
| POST | `/api/solicitudes/{id}/iniciar_evaluacion/` | Cambia estado a "En Evaluación" |
| POST | `/api/solicitudes/{id}/aprobar/` | Aprueba la solicitud |
| POST | `/api/solicitudes/{id}/rechazar/` | Rechaza la solicitud (requiere `motivo`) |
| GET/POST | `/api/comites/` | Gestión de comités evaluadores |
| GET/POST | `/api/evaluaciones/` | Registrar evaluaciones |
| GET | `/api/evaluaciones/puntaje-final/{solicitud_id}/` | Puntaje final (Factory + Strategy) |
| `/admin/` | Panel de administración de Django | Útil para que el comité gestione datos sin pantallas propias en el MVP |
| `/api-auth/` | Login/logout navegable de DRF | Para probar la API desde el navegador |

## Próximos pasos sugeridos (Sprint 1)

1. Definir permisos por rol (estudiante / comité / administrador) sobre
   los ViewSets — hoy solo exigen `IsAuthenticated` (ver HU-19).
2. Agregar tests unitarios para `states.py` (transiciones válidas e
   inválidas) y `services.py`.
3. Cargar datos de ejemplo (fixtures) para facilitar las pruebas del
   equipo y del Product Owner.
