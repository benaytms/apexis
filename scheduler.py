import schedule
import time
import logging
from index import main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

schedule.every().day.at("06:00").do(main)


logger.info("Scheduler started - waiting for next run at 06:00 UTC (3:00 São Paulo)")

while True:
    schedule.run_pending()
    time.sleep(60)


