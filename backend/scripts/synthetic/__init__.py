"""Synthetic data generation for WealthGen demos.

Produces realistic, deterministic (seeded) datasets aligned to the app's Pydantic
models for the three grounding sources:

  * Fabric IQ  -> tabular holdings / weights / Brinson attribution (CSV for OneLake)
  * Foundry IQ -> fund fact-sheet SourceFacts (JSON for the PDF search index) + .md sheets
  * Work IQ    -> house view, brand-voice style guide, disclosure library (.md for M365)

Entry point:
    python -m scripts.synthetic.generate
"""
