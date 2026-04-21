# Add New Asset to Pipeline
When asked to add a new tradeable asset to AlphaForge:

1. Add ticker to technicals-bot/data_fetcher.py asset list
2. Add COT contract code to cot-bot/config.py
3. Update dashboard frontend — add new asset card in Signals page
4. Update combined_context.json schema documentation
5. Verify risk engine handles new asset's unit type (contracts vs shares)
6. Update health_check.py to verify new asset outputs exist
7. Never add an asset without a corresponding COT code — flag if unavailable
