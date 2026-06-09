# integrations/__init__.py
# single import point for the ServiceNow client
# all agents import from here: `from integrations import snow`
# switch between mock and real by setting API_ENV in .env

import os
from dotenv import load_dotenv

load_dotenv()

_env = os.getenv("API_ENV", "development")

if _env == "production":
    from integrations.servicenow_client import ServiceNowClient
    snow = ServiceNowClient()
    print("[ServiceNow] Using REAL client")
else:
    from integrations.mock_servicenow_client import MockServiceNowClient
    snow = MockServiceNowClient()
    print("[ServiceNow] Using MOCK client  (set API_ENV=production to use real)")