import importlib
from typing import Any
from .config import settings
import logging


log = logging.getLogger("bot")

_pkg = None
for name in ("maxapi_python", "maxapi"):
    try:
        _pkg = importlib.import_module(name)
        break
    except Exception:
        continue
if _pkg is None:
    raise ImportError("Не найден установленный SDK: maxapi-python/maxapi")

_types = None
for tmod in (f"{_pkg.__name__}.types", "maxapi_python.types", "maxapi.types"):
    try:
        _types = importlib.import_module(tmod)
        break
    except Exception:
        pass
if _types is None:
    raise ImportError("В SDK не найден модуль types (Command, MessageCreated, BotStarted).")

types = _types  

Bot: Any = None
Dispatcher: Any = None
candidates = [
    ("Bot", "Dispatcher"),
    ("Client", "Dispatcher"),
    ("MaxBot", "Dispatcher"),
]
for bot_name, dp_name in candidates:
    try:
        Bot = getattr(_pkg, bot_name)
        Dispatcher = getattr(_pkg, dp_name)
        break
    except Exception:
        continue

if not Bot or not Dispatcher:
    raise ImportError("В SDK не найдены совместимые классы Bot/Dispatcher.")

log.info("Importing SDK and initializing Bot/Dispatcher…")

bot = Bot(token=settings.max_token)
dp = Dispatcher()

async def _start_polling():
    try:
        for attr in ("run_polling", "start_polling", "polling"):
            if hasattr(dp, attr):
                fn = getattr(dp, attr)
                try:
                    return await fn(bot=bot)
                except TypeError:
                    try:
                        return await fn(bot)
                    except TypeError:
                        return await fn()
        for attr in ("run_polling", "start_polling", "polling"):
            if hasattr(bot, attr):
                fn = getattr(bot, attr)
                try:
                    return await fn(dp=dp)
                except TypeError:
                    try:
                        return await fn(dp)
                    except TypeError:
                        return await fn()
        raise RuntimeError("Не найден метод запуска polling в SDK.")
    finally:
        for obj in (globals().get("dp"), globals().get("bot")):
            for meth in ("shutdown", "close", "aclose"):
                if obj and hasattr(obj, meth):
                    try:
                        res = getattr(obj, meth)
                        if callable(res):
                            await res() if "await" in str(type(res)) or getattr(res, "__code__", None) else res()
                    except Exception as e:
                        logging.getLogger("bot").warning("On shutdown: %s.%s failed: %s", obj, meth, e)

def run_polling():
    import asyncio
    asyncio.run(_start_polling())
