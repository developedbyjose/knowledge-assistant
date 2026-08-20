# Running and Accessing the Database

Knowledge Assistant uses PostgreSQL 16 with the pgvector extension. Docker
Compose runs it as the `db` service in the `knowledge-assistant-db` container.
Its data is stored in the named `postgres_data` volume, so normal container
restarts do not erase the database.

Run all Docker Compose commands below from the repository root.

## Essential Commands

Start only the database in the background:

```bash
docker compose up -d db
```

Check whether it is running and healthy:

```bash
docker compose ps db
```

Open an interactive PostgreSQL shell inside the database container:

```bash
docker compose exec db psql -U knowledge_user -d knowledge_assistant
```

Stop the database without deleting its stored data:

```bash
docker compose stop db
```

Start the stopped database again:

```bash
docker compose start db
```

## Initialize the Schema

Starting only `db` creates the PostgreSQL database but does not run the
application's Alembic migrations. Apply all migrations with a temporary API
container:

```bash
docker compose run --rm api alembic upgrade head
```

Alternatively, starting the API applies migrations automatically before the
FastAPI server starts:

```bash
docker compose up -d api
```

The first migration enables pgvector and creates the initial tables. Later
migrations add conversations, messages, citations, and feedback.

To display the current migration revision while the API container is running:

```bash
docker compose exec api alembic current
```

## Access With `psql`

The recommended access method requires no PostgreSQL client on the host:

```bash
docker compose exec db psql -U knowledge_user -d knowledge_assistant
```

Useful commands inside `psql`:

```text
\conninfo              Show the active connection
\dt                    List tables
\d knowledge_bases     Describe a table
\dx                    List installed extensions
SELECT version();       Show the PostgreSQL version
SELECT * FROM alembic_version;  Show the applied migration revision
\q                     Exit psql
```

To run one query without opening an interactive shell:

```bash
docker compose exec db psql -U knowledge_user -d knowledge_assistant -c "SELECT version();"
```

## Access From the Host

The Compose configuration publishes PostgreSQL on `localhost:5432`. If `psql`
is installed on the host, connect with:

```bash
psql -h localhost -p 5432 -U knowledge_user -d knowledge_assistant
```

When prompted, the local-development password from `docker-compose.yml` is:

```text
knowledge_password
```

Use these settings for a desktop database client such as DBeaver, DataGrip, or
pgAdmin:

| Setting | Local value |
| --- | --- |
| Host | `localhost` |
| Port | `5432` |
| Database | `knowledge_assistant` |
| User | `knowledge_user` |
| Password | `knowledge_password` |
| SSL | Disabled for local development |

These credentials are safe example defaults for local development only. Use
secrets and stronger credentials in deployed environments.

## Application Connection URLs

Code running directly on the host connects through the published port:

```text
postgresql+psycopg://knowledge_user:knowledge_password@localhost:5432/knowledge_assistant
```

Code running in the Compose network uses the service name `db` as its host:

```text
postgresql+psycopg://knowledge_user:knowledge_password@db:5432/knowledge_assistant
```

The first URL is the default in `.env.example`. The second is supplied to the
`api` service by `docker-compose.yml`.

## Logs and Troubleshooting

Follow database logs:

```bash
docker compose logs -f db
```

Ask PostgreSQL whether it is ready to accept connections:

```bash
docker compose exec db pg_isready -U knowledge_user -d knowledge_assistant
```

If port `5432` is already in use, stop the other local PostgreSQL instance or
change the host side of the port mapping in `docker-compose.yml`. Keep the
container port as `5432`, and update host-side connection URLs to match.

If tables are missing, apply the migrations from the repository root:

```bash
docker compose run --rm api alembic upgrade head
```

## Remove Containers or Data

Remove the Compose containers and network while preserving the database volume:

```bash
docker compose down
```

To permanently delete the local database data as well, add `--volumes`:

```bash
docker compose down --volumes
```

The second command deletes the `postgres_data` volume and cannot be undone.
Use it only when a completely clean local database is intended.
