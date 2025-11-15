import asyncio
import logging
import os
from .bot import run_polling
from .handlers import mini_commands, max_flow  

logging.basicConfig(
    level=os.getenv("BOT_LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    force=True,
)

def main():
    logging.getLogger(__name__).info("Bot starting…")
    try:
        asyncio.run(run_polling())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Bot interrupted (SIGINT). Bye.")

if __name__ == "__main__":
    main()

