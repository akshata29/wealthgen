-- ==========================================================================
-- WealthGen reference dataset — Microsoft Fabric Warehouse schema (T-SQL DDL)
--
-- Idempotent create for the 11 advisory tables that back the /clients,
-- /mandates, /performance, and /events endpoints. Applied by
-- backend/scripts/load_fabric_tables.py before loading rows.
--
-- Fabric Warehouse T-SQL notes:
--   * No `CREATE TABLE IF NOT EXISTS` — use `IF OBJECT_ID(...) IS NULL`.
--   * Limited constraint/identity support — no PK/FK/identity declared here.
--   * Column names match the CSV headers exactly so the reference_data mappers
--     stay unchanged.
-- Schema is substituted as {schema} by the loader (default: dbo).
-- ==========================================================================

-- --- advisors -------------------------------------------------------------
IF OBJECT_ID('{schema}.advisors', 'U') IS NULL
CREATE TABLE {schema}.advisors (
    advisor_id    VARCHAR(32)  NOT NULL,
    name          VARCHAR(128) NOT NULL,
    team          VARCHAR(128) NULL,
    jurisdiction  VARCHAR(8)   NULL
);

-- --- clients (full model field set — see app.models.portfolio.Client) ------
IF OBJECT_ID('{schema}.clients', 'U') IS NULL
CREATE TABLE {schema}.clients (
    client_id           VARCHAR(32)  NOT NULL,
    display_name        VARCHAR(128) NOT NULL,
    advisor_id          VARCHAR(32)  NULL,
    jurisdiction        VARCHAR(8)   NULL,
    risk_profile        VARCHAR(16)  NULL,
    financial_literacy  VARCHAR(16)  NULL,
    tone_preference     VARCHAR(16)  NULL,
    segment             VARCHAR(64)  NULL,
    life_event          VARCHAR(128) NULL,
    esg_preference      BIT          NULL
);

-- --- mandates -------------------------------------------------------------
IF OBJECT_ID('{schema}.mandates', 'U') IS NULL
CREATE TABLE {schema}.mandates (
    mandate_id      VARCHAR(64)   NOT NULL,
    display_name    VARCHAR(128)  NOT NULL,
    client_id       VARCHAR(32)   NULL,
    strategy        VARCHAR(256)  NULL,
    benchmark_id    VARCHAR(32)   NULL,
    base_currency   VARCHAR(8)    NULL,
    inception       VARCHAR(16)   NULL,
    aum_musd        DECIMAL(18,4) NULL,
    target_holdings VARCHAR(1024) NULL
);

-- --- benchmarks -----------------------------------------------------------
IF OBJECT_ID('{schema}.benchmarks', 'U') IS NULL
CREATE TABLE {schema}.benchmarks (
    benchmark_id  VARCHAR(32)   NOT NULL,
    name          VARCHAR(256)  NOT NULL,
    sector        VARCHAR(64)   NULL,
    weight        FLOAT         NULL
);

-- --- holdings -------------------------------------------------------------
IF OBJECT_ID('{schema}.holdings', 'U') IS NULL
CREATE TABLE {schema}.holdings (
    mandate_id        VARCHAR(64)   NOT NULL,
    period            VARCHAR(16)   NOT NULL,
    ticker            VARCHAR(32)   NULL,
    instrument        VARCHAR(128)  NULL,
    isin              VARCHAR(16)   NULL,
    asset_class       VARCHAR(32)   NULL,
    sector            VARCHAR(64)   NULL,
    region            VARCHAR(32)   NULL,
    weight            FLOAT         NULL,
    market_value_usd  DECIMAL(18,4) NULL,
    period_return_pct FLOAT         NULL
);

-- --- portfolio_performance ------------------------------------------------
IF OBJECT_ID('{schema}.portfolio_performance', 'U') IS NULL
CREATE TABLE {schema}.portfolio_performance (
    mandate_id           VARCHAR(64) NOT NULL,
    period               VARCHAR(16) NOT NULL,
    total_return_net_pct FLOAT       NULL,
    benchmark_return_pct FLOAT       NULL,
    active_return_bps    FLOAT       NULL,
    tracking_error_pct   FLOAT       NULL,
    information_ratio    FLOAT       NULL,
    ex_ante_vol_pct      FLOAT       NULL,
    sharpe               FLOAT       NULL,
    max_drawdown_pct     FLOAT       NULL
);

-- --- attribution ----------------------------------------------------------
IF OBJECT_ID('{schema}.attribution', 'U') IS NULL
CREATE TABLE {schema}.attribution (
    mandate_id       VARCHAR(64) NOT NULL,
    period           VARCHAR(16) NOT NULL,
    segment          VARCHAR(64) NOT NULL,
    portfolio_weight FLOAT       NULL,
    benchmark_weight FLOAT       NULL,
    portfolio_return FLOAT       NULL,
    benchmark_return FLOAT       NULL,
    allocation_bps   FLOAT       NULL,
    selection_bps    FLOAT       NULL,
    interaction_bps  FLOAT       NULL,
    source_id        VARCHAR(64) NULL
);

-- --- positioning_changes --------------------------------------------------
IF OBJECT_ID('{schema}.positioning_changes', 'U') IS NULL
CREATE TABLE {schema}.positioning_changes (
    mandate_id   VARCHAR(64)   NOT NULL,
    period       VARCHAR(16)   NOT NULL,
    description  VARCHAR(512)  NULL,
    direction    VARCHAR(32)   NULL,
    magnitude    VARCHAR(32)   NULL,
    rationale    VARCHAR(512)  NULL,
    source_id    VARCHAR(64)   NULL
);

-- --- market_index_returns -------------------------------------------------
IF OBJECT_ID('{schema}.market_index_returns', 'U') IS NULL
CREATE TABLE {schema}.market_index_returns (
    period            VARCHAR(16)  NOT NULL,
    index_name        VARCHAR(128) NOT NULL,
    period_return_pct FLOAT        NULL,
    source_id         VARCHAR(64)  NULL
);

-- --- fx_moves -------------------------------------------------------------
IF OBJECT_ID('{schema}.fx_moves', 'U') IS NULL
CREATE TABLE {schema}.fx_moves (
    period      VARCHAR(16) NOT NULL,
    pair        VARCHAR(16) NOT NULL,
    change_pct  FLOAT       NULL,
    source_id   VARCHAR(64) NULL
);

-- --- vix_events -----------------------------------------------------------
IF OBJECT_ID('{schema}.vix_events', 'U') IS NULL
CREATE TABLE {schema}.vix_events (
    period        VARCHAR(16)  NOT NULL,
    vix_close     FLOAT        NULL,
    event_trigger BIT          NULL,
    regime        VARCHAR(32)  NULL,
    headline      VARCHAR(512) NULL
);
