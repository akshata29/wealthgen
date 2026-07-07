# Microsoft Fabric — reference dataset setup

The WealthGen advisory reference dataset (clients, mandates, holdings, attribution,
performance, market context) can be served from **Microsoft Fabric** over OneLake
instead of the local synthetic CSVs. Set `DATA_SOURCE_MODE=fabric` to switch.

The backend read path (`app.services.fabric_data`) is **SELECT-only** over a Fabric
**SQL analytics endpoint**, so it works against **either** a Fabric **Warehouse** *or* a
**Lakehouse** — the runtime needs no code change. The only difference is how you
*load* the 11 tables:

| | Load method | Endpoint host |
|---|---|---|
| **Lakehouse** (recommended) | PySpark notebook writing Delta tables (`load_lakehouse_tables.ipynb`) — the SQL endpoint is read-only | `<id>.datawarehouse.fabric.microsoft.com` |
| **Warehouse** | T-SQL loader (`load_fabric_tables.py`) — the SQL endpoint is read-write | `<id>.datawarehouse.fabric.microsoft.com` |

This directory holds:
- `load_lakehouse_tables.ipynb` — Fabric PySpark notebook that loads the CSVs as Delta tables (Lakehouse path).
- `schema.sql` — T-SQL DDL applied by `load_fabric_tables.py` (Warehouse path).

---

## Option A — Lakehouse (recommended)

1. **Create a Lakehouse** in a Fabric workspace (New → Lakehouse). Note its name — this is `FABRIC_DATABASE`.
2. **Import & run** `load_lakehouse_tables.ipynb` in that workspace:
   - Attach the Lakehouse to the notebook (Explorer → *Add Lakehouse*).
   - Upload the 11 CSVs from `backend/data/synthetic/fabric_iq/*.csv` into the Lakehouse **Files → `wealthgen/`** folder.
   - Run all cells → 11 managed Delta tables, exposed to the SQL endpoint as `dbo.<table>`.
3. **Capture the SQL connection string.** Lakehouse → **Settings → SQL analytics endpoint** → copy the
   server host (`<id>.datawarehouse.fabric.microsoft.com`) — this is `FABRIC_SQL_ENDPOINT`.
4. **Grant the app identity access** (see *Identity access* below).
5. **Install the ODBC driver** (see below).

## Option B — Warehouse (T-SQL loader)

1. **Create a Warehouse** in the workspace (New → Warehouse). Note the **Warehouse name** = `FABRIC_DATABASE`.
2. **Capture the SQL connection string.** Warehouse → **Settings → SQL analytics endpoint** →
   `<id>.datawarehouse.fabric.microsoft.com` = `FABRIC_SQL_ENDPOINT`.
3. **Grant the app identity access** (see below), then from `backend/`:
   ```powershell
   python -m scripts.synthetic.generate        # produce data/synthetic/** (if absent)
   python -m scripts.load_fabric_tables         # apply schema.sql + load all 11 tables
   python -m scripts.load_fabric_tables --truncate   # TRUNCATE + reload
   ```
   The loader is idempotent: it applies `schema.sql` (create-if-missing) then batch-inserts each CSV.

---

## Identity access (both options)

Authentication uses **AAD token auth** (no SQL login, no stored secret). The app picks its
credential in this order (`app.infra.clients.get_credential`):
- **service principal** if `AZURE_TENANT_ID`/`AZURE_CLIENT_ID`/`AZURE_CLIENT_SECRET` are set,
- else **AzureCliCredential** (`az login`) in local mode,
- else **DefaultAzureCredential** (managed identity) in prod.

Whichever identity is active **must be granted access in Fabric**, or the SQL endpoint returns
`login failed (18456)`:

- **Add the identity to the workspace** (Workspace → *Manage access* → add as **Member** or
  **Contributor**), **or** share the Lakehouse/Warehouse item with it (at least **Read** +
  *ReadData*).
- If using a **service principal**, the Fabric tenant setting **"Service principals can use
  Fabric APIs"** must be enabled (Fabric Admin portal → Tenant settings), and the SP added to
  the workspace as above.

## Install the ODBC driver

On the host running the backend/loader: **Microsoft ODBC Driver 18 for SQL Server**
(https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server).

## Configure `.env`

```
DATA_SOURCE_MODE=fabric
FABRIC_SQL_ENDPOINT=<id>.datawarehouse.fabric.microsoft.com
FABRIC_DATABASE=<your-lakehouse-or-warehouse-name>
FABRIC_SQL_SCHEMA=dbo
```

Verify locally from `backend/`:
```powershell
python -c "from app.services import fabric_data; print(fabric_data.query('SELECT COUNT(*) c FROM dbo.holdings'))"
```
