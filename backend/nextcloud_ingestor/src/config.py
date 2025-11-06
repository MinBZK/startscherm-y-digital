import dataclasses
import os


@dataclasses.dataclass(frozen=True)
class Config:
    nextcloud_url: str
    nextcloud_admin_username: str
    nextcloud_admin_password: str
    dossier_parent_path: str = "dossiers"
    es_url: str = "http://localhost:9200"
    es_index_documents: str = "document-index"
    es_index_dossiers: str = "dossier-index"
    # PostgreSQL configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "nextcloud_ingestor"
    postgres_user: str = "ingestor"
    postgres_password: str = "ingestor_password"
    # Tika server configuration
    tika_server_url: str = "http://localhost:9998"
    dry_run: bool = False

    @staticmethod
    def from_env(envfile: str = None) -> "Config":

        if envfile is not None:
            from dotenv import load_dotenv
            load_dotenv(envfile)

        def env(name: str, default: str | None = None, required: bool = False) -> str:
            val = os.getenv(name, default)
            if required and not val:
                raise RuntimeError(f"Missing required environment variable: {name}")
            return val or ""

        return Config(
            nextcloud_url=env("NEXTCLOUD_URL", required=True),
            nextcloud_admin_username=env("NEXTCLOUD_ADMIN_USERNAME", required=True),
            nextcloud_admin_password=env("NEXTCLOUD_ADMIN_PASSWORD", required=True),
            dossier_parent_path=env("NEXTCLOUD_DOSSIER_PARENT_PATH", "dossiers"),
            es_url=env("ELASTICSEARCH_URL", "http://localhost:9200"),
            es_index_documents=env("ELASTICSEARCH_INDEX_DOCUMENTS", "documents"),
            es_index_dossiers=env("ELASTICSEARCH_INDEX_DOSSIERS", "dossiers"),
            postgres_host=env("POSTGRES_HOST", "localhost"),
            postgres_port=int(env("POSTGRES_PORT", "5432")),
            postgres_db=env("POSTGRES_DB", "nextcloud_ingestor"),
            postgres_user=env("POSTGRES_USER", "ingestor"),
            postgres_password=env("POSTGRES_PASSWORD", "ingestor_password"),
            tika_server_url=env("TIKA_SERVER_URL", "http://localhost:9998"),
            dry_run=env("DRY_RUN", "false").lower() == "true"
        )
