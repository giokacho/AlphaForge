# Debug Dashboard Showing Unknown
When dashboard shows unknown/null for any data section:

1. Check Railway logs for the backend service
2. Verify bot_outputs table has recent rows: SELECT bot_name, run_date FROM bot_outputs ORDER BY created_at DESC LIMIT 10
3. Check if bots are POSTing successfully — look for POST errors in bot run logs
4. Verify INTERNAL_SECRET matches between bot .env and Railway env vars
5. Check data.py get_latest_output() is being called with the correct bot_name string
6. If all rows exist but dashboard still shows unknown — check payload schema matches what frontend expects
