"""Application settings (pydantic-settings), loaded from environment / .env.

Missing required Azure configuration fails loudly at startup — never substitute
placeholder or fake values (see azure-services standard: real services only).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- App ---
    app_env: str = "local"
    # NoDecode: values come as CSV in .env; let _split_csv parse them (not JSON).
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]
    jurisdictions: Annotated[list[str], NoDecode] = ["UK", "US"]
    default_audience: str = "client"
    # Grounding source for analysis/market facts:
    #   local      -> synthetic dataset (data/synthetic) + Foundry LLM narration (no KB needed)
    #   foundry_iq -> retrieve from the provisioned Foundry IQ knowledge base (requires KB + RemoteTool connection)
    grounding_mode: str = "local"

    # --- Azure AI Foundry ---
    foundry_endpoint: str
    agent_model: str = "gpt-4.1"

    # --- Foundry IQ knowledge base (MCP hub) ---
    search_endpoint: str
    kb_name: str = "wealthgen-kb"
    kb_connection_name: str
    kb_mcp_api_version: str = "2026-05-01-preview"

    # --- Azure AI Search (PDF source index) ---
    search_admin_key: str | None = None
    pdf_index_name: str = "wealthgen-pdf-facts"

    # --- Content Understanding (primary) ---
    cu_endpoint: str
    cu_analyzer_id: str = "wealthgen-factsheet-analyzer"

    # --- Document Intelligence (fallback) ---
    di_endpoint: str | None = None

    # --- Fabric IQ ---
    fabric_workspace_id: str | None = None
    fabric_data_agent_id: str | None = None
    fabric_ontology_id: str | None = None

    # --- Cosmos DB ---
    cosmos_endpoint: str
    cosmos_database: str = "wealthgen"
    cosmos_container: str = "commentary"

    # --- LSEG market data ---
    lseg_mcp_url: str | None = None
    lseg_connection_name: str | None = None

    # --- Research MCP tools (Foundry project connections) ---
    # Create the connection in the Foundry portal (Tools -> add -> authenticate),
    # then set the connection name here. See research_agent for usage.
    morningstar_mcp_url: str = "https://mcp.morningstar.com/mcp"
    morningstar_connection_name: str | None = None

    # --- Content Safety ---
    content_safety_endpoint: str

    # --- Blob storage ---
    blob_account_url: str | None = None
    blob_container: str = "factsheets"

    # --- Identity (service principal; used in preference to CLI when present) ---
    azure_tenant_id: str | None = None
    azure_client_id: str | None = None
    azure_client_secret: str | None = None

    @property
    def has_service_principal(self) -> bool:
        return bool(self.azure_tenant_id and self.azure_client_id and self.azure_client_secret)

    @field_validator("cors_origins", "jurisdictions", mode="before")
    @classmethod
    def _split_csv(cls, v: object) -> object:
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @property
    def is_local(self) -> bool:
        return self.app_env.lower() == "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
