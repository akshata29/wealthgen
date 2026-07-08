# WealthGen — Demo Walkthrough (Scenarios A & B)

Click-by-click guide for the July 9 readout demo (Ashish, ~10 min). Each step maps a
script beat to the **actual screen/action** in the app, what to **say**, and any
**honest caveat**. Also available in-app under **Architecture → Demo Flow**.

---

## Pre-flight checklist (do this before you present)

- [ ] **Backend running** — `./run_backend.bat` (http://localhost:8000)
- [ ] **Frontend running** — `./run_frontend.bat` → open the printed URL
- [ ] **Testing the DEPLOYED app?** It's one App Service container serving UI + API at `https://wgenhack-app.azurewebsites.net`. Config comes from App Service settings (pushed from `.env` at deploy). Sign in with Entra; hard-refresh after a fresh deploy.
- [ ] **Modes** — backend `.env`: `DATA_SOURCE_MODE=fabric` (real iShares ETFs), `GROUNDING_MODE=foundry_iq`
- [ ] **Hard-refresh** the browser (Ctrl+Shift+R) so it isn't showing stale data
- [ ] **Morningstar is already logged in** (headless) — the OAuth refresh token is stored, so the app auto-mints access tokens at runtime. No manual step. Only re-run `python -m scripts.mcp_login morningstar` if the token was revoked (a `getaddrinfo` error is just transient network — retry).
- [ ] **Pre-export a PDF** for one commentary and keep it in a browser tab (never demo the export retry)
- [ ] **Have the recorded backup** open in a tab in case live fails

### What's live vs. substituted (say this if asked)
- **Live**: Fabric holdings/attribution (real iShares ETFs), commentary generation, tone/literacy toggle, review→approve→export (PDF/Word/email), next-best-action, event-driven context.
- **Live provider (MCP)**: **Morningstar X-Ray** runs headlessly and is **auto-included as grounding when you generate commentary** (shows as an "Independent research (MCP)" context source). The manual **Run X-Ray** button on the portfolio page still works for the on-screen panel.
- **Not wired in this env**: **LSEG** (placeholder creds). Market context comes from **Web IQ** (live web search; trial key is rate-limited so it may fall back) blended with the **curated market-context library** and **Fabric** index/FX numbers. Don't claim LSEG is live unless you re-enable it.

---

## Deck alignment (for the presenter)

**Flow slide — "Ingest → Analyze → Contextualize → Draft → Guardrail":**

| Deck step | In the app |
|---|---|
| Ingest — holdings & client context | Clients & Portfolios + Holdings table (Fabric / OneLake) |
| Analyze — Morningstar X-Ray | Attribution / risk / weights (Fabric) + Morningstar X-Ray over MCP |
| Contextualize — market events · manager bulletins | Live **Web IQ** events + curated context library (advisor portals, market commentary, PM notes, webcasts, alerts, wholesaler) |
| Draft — template · tone · literacy | Generate → Tone & delivery + commentary type |
| Guardrail — review & approve | Review & Approve — compliance gate, edit + re-run compliance, PM/Compliance sign-off |

**Architecture slide — say it straight if asked:**

- **Morningstar (MCP)** is live and headless — the backend mints access tokens from a stored OAuth refresh token (the slide's "OAuth token mint").
- **LSEG** on the slide uses the *same* MCP + OAuth pattern — a config swap, not wired in this build. The live **market events & context** you'll demo come from **Web IQ** (Microsoft AI web search), filling the same "external providers" role.
- **Foundry Models**: the slide says GPT-4o; the running deployment uses **GPT-5** (GPT-4o was retired in this tenant). Same architecture, newer model.
- **Fabric Data Agent + API Management** are the productionization path on the slide; the working build reads **Fabric over its SQL analytics endpoint** and mints MCP tokens **headlessly in the backend** — same shape, fewer moving parts.
- Everything else matches the build: Entra ID SSO, Foundry IQ grounding, Work IQ approved-language / next-best-action, AI Content Safety, human approval, PDF/Word/Email delivery, and the private-link / VNet production path.

---

## Scenario A — The Market-Event Morning (~6 min)

> Period to use: **Q1-2026** (the VIX-spike / risk-off quarter). Client to use:
> **Delacroix Global Growth** or **Northbridge Global Balanced** (both hold the energy fund **IXC** and gold **IAU**, so the event lands on real holdings).

### 1. Setup (say it, no click)
> "It's that Monday morning. Watch what happens for one of your advisor's clients."

### 2. A market event, mapped to your clients
- On **Clients & Portfolios**, click **Scan live market events**. A current market headline appears, already cross-referenced to your book — **"Affects 6 of your 8 portfolios"** with the funds involved.
- Click **Event brief** on it to open Generate for the most-affected client — or open **Delacroix Family Office → Delacroix Global Growth** at **Q1-2026** directly.
- Say: "A live market signal, mapped to the exact clients who hold what moved — not the market in general."

> If Web IQ is rate-limited the live scan returns empty — use the built-in amber **Q1-2026 · VIX 31 · risk-off** scenario banner instead; the rest of the flow is identical. (Optional autonomous angle: `python -m scripts.scan_events --period Q1-2026` lists every affected portfolio with weights.)

### 3. The portfolio, analyzed
- The portfolio page shows the **metrics** (return, active, tracking error, Sharpe), **Benchmark compare**, **Index/ETF compare**, **Attribution by fund sleeve**, and the **Holdings** table (IVV, IEFA, IEMG, IJR, **IXC**, LQD, **IAU** …) with weights and returns — all from Fabric.
- (Optional) Click **Run X-Ray** to show Morningstar's independent analysis of these holdings, live over MCP.
- Say: "Sector, allocation, weights, risk and return — with Morningstar's independent X-Ray over the top, every figure traces to its source."

### 4. Generate the brief — grounded, in one click
- Click **Generate commentary** (the type is already **Event** if you came from the live-event **Event brief**).
- One call orchestrates it all: **Fabric** holdings/attribution, **Web IQ** market context, and **Morningstar's X-Ray over MCP** — which appears in the **"Real-world context used"** panel as an *Independent research* source, alongside advisor portals, market commentary, PM notes, webcasts, alerts, and wholesaler notes.
- Every claim cites its source, and **"Your holdings affected: IXC 14.2%"** badges tie the event to this exact portfolio.
- Say: "Foundry, Fabric, and the Morningstar provider — one click — and every number carries its source, tied to the holdings the event touches."

### 5. Tone / literacy toggle — flip it live  ⭐ money moment
- In **Tone & delivery**, flip **Ease (literacy)** from **Expert → Novice** (and/or tick **Non-financial language**), then **regenerate**.
- Say: "This client is a retired teacher, not a CFA. Watch the same analysis become her language." Show the plain-English version next to the technical one.

### 6. Reviewer approval → delivery  (Guardrail — the advisor stays the author)
- Click **Send to review & approval** (or **Review queue → open the item**).
- On **Review & Approve**: if compliance flagged something, click **Edit draft**, revise the flagged wording, **Save changes**, then **Re-run compliance** — the banner updates live (rejected → rewritten → passed). This is the human-in-the-loop: the advisor stays the author of record.
- Approve as **PM**, then **Compliance** (both gates), then **Deliver**.
- Open **Export**: **PDF**, **Word (.docx)**, or **Email** (downloads a ready-to-send `.eml`).
- Say: "Reviewed — and editable — by a human before it leaves the building." (Use the pre-exported PDF tab if export is slow.)

### 7. Closer (say it)
> "A hundred clients. Same morning. Every one gets this."

---

## Scenario B — The Quarterly Review (~4 min)

> Period to use: **Q2-2026** (calmer quarter). Client to use: **Thornton Household →
> Thornton Lifestyle Balanced** (life event: *New child / education planning* — matches
> "her daughter starts university"). Alternatives: **Northbridge** (*Approaching
> retirement 5y*), **Rivera** (*Liquidity event — business sale*).

### 1. Setup (say it)
> "Now the calmer, more common case — review season."

### 2. Open the client, prep for tomorrow's review
- Open **Thornton Household → Thornton Lifestyle Balanced**, period **Q2-2026**. Note the **life event** chip ("New child / education planning") and the **Next best actions** panel on the portfolio page.
- Say: "No market emergency — an advisor prepping for tomorrow's review, on demand."

### 3. Life event → next-best-action, in the brief  ⭐ money moment
- Click **Generate commentary**, **Commentary type = Quarterly**. The recommendation surfaces *alongside* the commentary — grounded in the client's life, not just the market.
- Say: "Her daughter starts university next year. This is where commentary becomes a conversation starter."

### 4. Same firm voice, different client
- Briefly open a second client (e.g. **Northbridge**) and generate — same house voice, different portfolio and tone.
- Say: "A thousand advisors. One voice."

### 5. Closer (say it)
> "Hours to seconds — grounded, reviewed, delivered."

---

## Quick reference — where each feature lives

| Script beat | In the app |
|---|---|
| Market event banner | Clients & Portfolios (top) + portfolio page EventBanner |
| Live market events (Web IQ) | Clients & Portfolios → **Scan live market events** → "Affects N of M portfolios" + Event brief |
| Event → affected holdings | `scripts/scan_events.py` / `GET /api/events/scan`; "holdings affected" badges |
| Sector / allocation / weights / risk / attribution | Portfolio page: StatGrid, Benchmark compare, Attribution by fund sleeve, Holdings |
| Morningstar X-Ray (live, MCP) | Auto-included in generated commentary as "Independent research" + Portfolio page “Run X-Ray” (headless — no login needed) |
| Market context / "the why" | Commentary "Market Context" section + "Real-world context used" panel (Web IQ + curated) |
| Tone / literacy / plain-English | Generate → Tone & delivery |
| Commentary type | Generate → Commentary type (Ad-hoc / Quarterly / Yearly / Event) |
| Edit + re-run compliance | Review & Approve → **Edit draft** → **Save changes** → **Re-run compliance** |
| Review → approve gate | Review queue → Review & Approve (PM + Compliance) |
| Export PDF / Word / Email | Commentary view → Export |
| Next-best-action | Portfolio page → Next best actions (driven by client life event) |

## Two things not to say
- Don't call **LSEG** live — it's not wired in this environment.
- If the Morningstar X-Ray ever errors mid-demo (transient network), just move on — generation still completes; the X-Ray is best-effort grounding.
