import asyncio
from main import dashboard_data

# Run the app to update the investment memory and dashboard json data during scheduled runs
async def main():
  data = await dashboard_data()
  print("✅ dashboard_data() was executed")

asyncio.run(main())
