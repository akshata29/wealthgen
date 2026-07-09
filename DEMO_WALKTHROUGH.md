# WealthGen — Demo Walkthrough

Presenter guide (Ashish). This picks up **right after the business story** and carries
it into the product. The through-line to hold onto the whole way: **hours to seconds,
bespoke to each client, grounded in trusted data, reviewed by a human — the advisor
stays the author.** Two scenarios: the everyday case (**an annual review**) and the hard
case (**a market event**).

---

## Setting the stage (say this before you touch the app)

*Carry your peer's momentum — don't reset it. You're turning the business problem into a
working system, layer by layer.*

> "So that's the problem: a bespoke, compliant portfolio narrative takes about two hours
> today — so only the top of the book ever gets one. And a thousand advisors means a
> thousand versions of your firm's voice for compliance to police. What I'll show you is
> the same job done in seconds, for every client, in one voice, with a human still in
> control. Let me walk you through what's happening under the hood — because *how* it's
> built is what makes it a compliance product, not a chatbot."

### The data flow, in plain terms — each layer removes a piece of that two-hour job

1. **It starts with the advisor.** They sign in with your own identity (**Microsoft Entra
   ID** SSO) and open their real book. Nothing here replaces the advisor — it gives them
   their hours back. They stay the author of record.
2. **The numbers come from your systems, not a model's imagination.** Holdings, client and
   portfolio data, weights and attribution are read live from **Microsoft Fabric /
   OneLake** — the firm's system of record. No re-keying, no guessing.
3. **Independent analytics on top.** The portfolio runs through a live **Morningstar X-Ray
   over MCP** — sector, allocation, style, risk and return — with the provider's
   attribution kept on every figure. That's the analyst's first hour, done and traceable.
4. **The market context an advisor actually reads.** Live web signals and manager bulletins
   come in through **Web IQ** and a curated context library — advisor portals, market
   commentary, PM notes, webcasts, alerts, wholesaler notes — each one cited.
5. **The firm's knowledge and rules are built in.** **Foundry IQ** grounds fund/ETF facts
   and benchmarks; **Work IQ** carries your approved language, the disclosure library, and
   the next-best-action playbooks. This is the layer that makes it compliant by design.
6. **Agents draft it in your voice.** **Azure AI Foundry** agents orchestrate research →
   plan → draft against the firm's template, tuned to each client's tone and financial
   literacy.
7. **A guardrail before anything ships.** **AI Content Safety** plus a mandatory **human
   approval gate** (PM and Compliance). Every figure carries its source, nothing reaches a
   client unreviewed, and it goes out as PDF, Word, or email.

> "Two things set this in motion: **on demand** — a review that's coming up — or a **market
> event** — the day the market moves and the phones start ringing. Let me show you both,
> starting with the everyday case, and I'll call out each of those layers as we go."

---

## Scenario A — The Annual Review (~5 min)

The everyday case: an advisor prepping for a client's annual review, on demand. Client:
**Thornton Household → Thornton Lifestyle Balanced** — a novice, warm-tone client with a
life event on file (*New child / education planning*). Flow: **Clients & Portfolios →
Portfolio detail → Generate commentary**, calling out each layer from the stage-setting.

### 1. Setup (say it)
> "Let's start with the everyday case — review season. An advisor has a client meeting
> tomorrow and needs a bespoke narrative, on demand — the kind that takes two hours today."

### 2. The advisor's book — Clients & Portfolios
- Open **Clients & Portfolios**. Point to the book: **8 clients**, total AUM, and the
  **Filter by type** chips (Family Office / Institutional / Private Client).
- **Under the hood → business:** "This is the advisor's real book, read live from
  **Microsoft Fabric / OneLake** — your system of record. Every client, every mandate, no
  re-keying. That's layer one: it starts with the advisor and *your* data."

### 3. The portfolio, already analyzed — Thornton Lifestyle Balanced
- Open **Thornton Household → Thornton Lifestyle Balanced**. Walk the page: the **metrics**
  (return, active, tracking error, Sharpe), **Benchmark compare**, **Attribution by fund
  sleeve**, and the **Holdings** table — real iShares ETFs (IVV, IEFA, IEMG, IJR, IXC, LQD,
  IAU) with weights and returns.
- Point out the client's **life event** chip (*New child / education planning*) and the
  **Next best actions** panel.
- (Optional) Click **Run X-Ray** — Morningstar's independent analysis of these holdings,
  live over MCP.
- **Under the hood → business:** "Holdings and attribution are straight from Fabric;
  Morningstar's independent X-Ray sits over the top, attribution kept on every figure.
  That's the analyst's first hour — already done, already traceable. And notice the system
  already knows this client's life event; that's about to matter."

### 4. Generate the annual review — grounded, in one click
- Click **Generate commentary**. Set **Commentary type = Yearly (Annual Review)**, audience
  **Client**. Generate.
- **Under the hood → business:** "This one click orchestrates the whole pipeline —
  **Fabric** numbers, **Web IQ** market context, the **Morningstar X-Ray** over MCP (it
  shows up as *Independent research* in the 'Real-world context used' panel), **Foundry IQ /
  Work IQ** grounding and your approved language, and **Foundry agents** drafting in the
  house voice."
- The brief appears: a full-year narrative across seven sections — **every claim cites its
  source** — and the **next-best-action** surfaces *alongside* the commentary.
  ⭐ **money moment**
- Say: "Two hours becomes seconds. It's bespoke to this client — their holdings, their
  year, their life event — and every number carries its source. This is where commentary
  becomes a conversation starter, not a form letter."

### 5. Same analysis, the client's language — tone / literacy
- In **Tone & delivery**, flip **Ease (literacy)** **Expert → Novice** (and/or tick
  **Non-financial language**), then **regenerate**.
- Say: "This client isn't a CFA. Watch the same analysis become her language —
  automatically." Show the plain-English version next to the technical one.
  ⭐ **money moment**

### 6. The guardrail — review, edit, approve, deliver
- Click **Send to review & approval** (or **Review queue → open the item**).
- If compliance flags anything, click **Edit draft**, revise the wording, **Save changes**,
  then **Re-run compliance** — the banner updates live (rejected → rewritten → passed). The
  advisor stays the author.
- Approve as **PM**, then **Compliance**, then **Deliver** — **PDF**, **Word**, or **email**.
- **Under the hood → business:** "Approved language and disclosures are built in, AI Content
  Safety and a human both sign off, and every figure is traceable. Compliance stops sampling
  and starts guaranteeing — a thousand advisors, one reviewed voice."

### 7. Closer (say it)
> "That's every client's annual review — grounded, compliant, in seconds instead of hours."

---

## Scenario B — The Market Event (~4 min)

The hard case: the market moves and every client wants to know what it means for *them*.
Same engine as the annual review — the new parts are the **live trigger** and the
**holdings cross-reference**. Keep it tight; the mechanics were shown in Scenario A.

### 1. Setup (say it)
> "Now the day the market moves — the phones start ringing. Same engine, but it starts
> itself, and it already knows exactly which clients are exposed."

### 2. A live market signal, mapped to the book — Clients & Portfolios
- On **Clients & Portfolios**, click **Scan live market events**. A current market headline
  comes back from **Web IQ**, already cross-referenced to the book — **"Affects 6 of your 8
  portfolios"** with the funds involved.
- **Under the hood → business:** "That's a live web signal matched against the holdings in
  Fabric — so it's not 'the market is down,' it's 'these six clients hold what moved.'"

> If Web IQ is rate-limited the live scan returns empty — use the built-in amber **Q1-2026 ·
> VIX 31 · risk-off** scenario banner instead; the rest of the flow is identical. (Optional:
> `python -m scripts.scan_events --period Q1-2026` lists every affected portfolio with weights.)

### 3. An event brief for an affected client  ⭐ money moment
- Click **Event brief** on the event — it opens **Generate** for the most-affected client
  (one holding **IXC**), commentary type pre-set to **Event**. Generate.
- The brief opens calm and event-aware, with **"Your holdings affected: IXC 14.2%"** badges
  tying the event to that exact portfolio, and a compliant advisor **talking point**.
- Say: "Same grounded pipeline — Fabric, Web IQ, Morningstar — but now the narrative leads
  with the event, names the affected holding and its weight, and gives the advisor something
  compliant to say."

### 4. Same guardrail, same voice
- Flip tone/literacy if you like, then **Send to review & approval** → approve → **Deliver**.
  Same human-in-the-loop, same firm voice.
- Say: "A hundred clients, same morning — every one gets a bespoke, reviewed answer."

### 5. Closer (say it)
> "Triggered by markets or on demand — hours to seconds, grounded, reviewed, delivered. The
> advisor stays the author."

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

## If asked (honest one-liners)
- **Morningstar** is live over MCP (headless); **LSEG** on the architecture uses the same
  MCP pattern and is a config swap — the live market context you saw comes from **Web IQ**.
- Some **client data is synthetic** while the shared environment finishes — the architecture
  is identical either way.
- If the Morningstar X-Ray ever errors mid-demo, move on — generation still completes; it's
  best-effort grounding.
