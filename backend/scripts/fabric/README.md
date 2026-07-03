# Microsoft Fabric Warehouse — reference dataset setup

The WealthGen advisory reference dataset (clients, mandates, holdings, attribution,
performance, market context) can be served from a Microsoft **Fabric Warehouse** over
OneLake instead of the local synthetic CSVs. Set `DATA_SOURCE_MODE=fabric` to switch.

This directory holds the one-time schema DDL (`schema.sql`) applied by the loader
(`backend/scripts/load_fabric_tables.py`).

## One-time Fabric setup

1. **Create a Fabric Workspace** (or reuse an existing one) in the Fabric portal
   (https://app.fabric.microsoft.com), in the **same Entra tenant** as the app identity.
2. **Create a Warehouse** in that workspace (New → Warehouse). Note the **Warehouse name** —
   this is `FABRIC_DATABASE`.
3. **Capture the SQL connection string.** In the Warehouse, open **Settings → SQL analytics
   endpoint** (or the ⚙️ / "Copy SQL connection string"). The server host looks like
   `<id>.datawarehouse.fabric.microsoft.com` — this is `FABRIC_SQL_ENDPOINT`.
4. **Grant the app / user identity access** to the Warehouse (Share → at least read/write, or
   add the identity as a Workspace member with a contributor role) so it can create tables and
   run `INSERT`/`SELECT`.
5. **Install the driver** on the host running the backend and loader:
   **Microsoft ODBC Driver 18 for SQL Server**
   (https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server).

## Configure `.env`

```
DATA_SOURCE_MODE=fabric
FABRIC_SQL_ENDPOINT=<id>.datawarehouse.fabric.microsoft.com
FABRIC_DATABASE=<your-warehouse-name>
FABRIC_SQL_SCHEMA=dbo
```

Authentication uses AAD token auth via `DefaultAzureCredential` / `AzureCliCredential`
(no SQL login, no stored secret). Run `az login` locally, or use a managed identity /
service principal in deployed environments.

## Load the data

From `backend/`:

```powershell
python -m scripts.synthetic.generate        # produce data/synthetic/** (if not present)
python -m scripts.load_fabric_tables         # apply schema.sql + load all 11 tables
python -m scripts.load_fabric_tables --truncate   # TRUNCATE + reload
```

The loader is idempotent: it applies `schema.sql` (create-if-missing) then batch-inserts
each CSV into the matching Warehouse table via the SQL analytics endpoint.
