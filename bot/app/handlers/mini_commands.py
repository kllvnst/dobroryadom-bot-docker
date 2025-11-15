import httpx
from ..bot import dp, types
from ..config import settings, donation_list
from ..keyboards import reply_kb, open_link_kb

Command = types.Command
MessageCreated = types.MessageCreated
BotStarted = types.BotStarted

BACKEND = settings.bff_base_url
FRONT = settings.public_front_url
DONATE = settings.donate_links

TXT_HELLO = (
    "👋 Привет! Это «ДоброРядом» — сервис взаимопомощи, реализованный посредством мини-приложения в MAX.\n"
    "Мы помогаем тем, кто рядом: тем, кто нуждается в помощи, и тем, кто готов откликнуться.\n"
)
TXT_FEATURES = (
    "\n✨ Что умеет мини-приложение:✨\n"
    "• Создать заявку на помощь\n"
    "• Найти заявки рядом и откликнуться\n"
    "• Указать город и видеть актуальные просьбы\n"
    "• Следить за статусом и откликами\n"
    "• Всё в одном месте — быстро и удобно"
)
TXT_DONATE = (
    "💙 Хотите поддержать проверенные фонды? \nVK Добро — официальный сервис благотворительности.\n"
    "• Проверенные организации и прозрачные отчёты\n"
    "• Быстрые и безопасные платежи\n"
    "• Поддержка экосистемы VK\n"
    "Пожертвования там — это надёжно и эффективно.\n"
)
TXT_CTA = "\nВыберите проверенный фонд для благотворительности прямо здесь и сейчас с помощью VK Добро!"

MAIN_KB_F = open_link_kb([
    [("Открыть сервис «ДоброРядом»", FRONT)],
])
MAIN_KB_D = open_link_kb([
    [("Пожертвовать через проверенные фонды VK Добро", DONATE)],
])

_profile: dict[int, dict] = {}
def get_profile(uid: int) -> dict: return _profile.setdefault(uid, {"role": None, "city": settings.city_default})

MAIN_KB = reply_kb([
    ["Я Волонтёр", "Нужна Помощь"],
    ["Заявки Рядом", "Создать Заявку"],
    ["Помочь Рублём", "Открыть Приложение"],
    ["Сменить Город"]
])
MENU_TEXT = (
    "👋 Добро пожаловать в «ДоброРядом»!\n\n"
    "Выберите действие:\n"
    "• Я волонтёр / Нужна помощь\n"
    "• Заявки рядом (список)\n"
    "• Создать заявку\n"
    "• Помочь рублём (VK Добро)\n"
    "• Открыть мини-приложение\n\n"
    "Команды: /menu /help /cancel"
)
BACKEND = settings.bff_base_url

async def _safe_answer(message, text: str, kb=None):
    try:
        if kb is not None:
            return await message.answer(text, attachments=[kb])
        return await message.answer(text)
    except TypeError:
        try:
            if kb is not None:
                return await message.answer(text, reply_markup=kb)
            return await message.answer(text)
        except TypeError:
            if kb is not None:
                return await message.answer(text, keyboard=kb)
            return await message.answer(text)

async def _safe_send(bot, chat_id: int, text: str, kb=None):
    try:
        if kb is not None:
            return await bot.send_message(chat_id=chat_id, text=text, attachments=[kb])
        return await bot.send_message(chat_id=chat_id, text=text)
    except TypeError:
        try:
            if kb is not None:
                return await bot.send_message(chat_id=chat_id, text=text, reply_markup=kb)
            return await bot.send_message(chat_id=chat_id, text=text)
        except TypeError:
            if kb is not None:
                return await bot.send_message(chat_id=chat_id, text=text, keyboard=kb)
            return await bot.send_message(chat_id=chat_id, text=text)


def _get_uid(ev) -> int | None:
    paths = (
        "user_id",
        ("user", "user_id"),
        ("user", "id"),
        ("message", "user_id"),
        ("message", "from_id"),
        ("message", "sender_id"),
        ("from_user", "id"),
        ("sender", "id"),
        ("payload", "user_id"),
        "userId",
        ("user", "userId"),
        ("message", "userId"),
    )

    for path in paths:
        cur = ev
        try:
            if isinstance(path, tuple):
                for p in path:
                    cur = getattr(cur, p)
            else:
                cur = getattr(cur, path)
            if isinstance(cur, int):
                return cur
            if isinstance(cur, str):
                cur = cur.strip()
                if cur.isdigit():
                    return int(cur)
        except Exception:
            continue

    def _as_dict(obj):
        for attr in ("model_dump", "dict"):
            try:
                fn = getattr(obj, attr, None)
                if callable(fn):
                    return fn()
            except Exception:
                pass
        try:
            return obj.__dict__
        except Exception:
            return None

    def _dig(obj):
        if obj is None:
            return None
        if isinstance(obj, dict):
            for k in ("user_id", "userId", "sender_id", "from_id"):
                if k in obj:
                    v = obj[k]
                    if isinstance(v, int):
                        return v
                    if isinstance(v, str) and v.strip().isdigit():
                        return int(v.strip())
            for v in obj.values():
                r = _dig(v)
                if r is not None:
                    return r
        d = _as_dict(obj)
        if isinstance(d, dict):
            return _dig(d)
        return None

    return _dig(ev)
def _get_chat_id(ev) -> int | None:
    paths = (
        "chat_id",
        ("chat", "id"),
        ("message", "chat_id"),
        ("message", "peer_id"),
        "chatId",
        ("message", "chatId"),
    )
    for path in paths:
        cur = ev
        try:
            if isinstance(path, tuple):
                for p in path:
                    cur = getattr(cur, p)
            else:
                cur = getattr(cur, path)
            if isinstance(cur, int):
                return cur
            if isinstance(cur, str) and cur.strip().isdigit():
                return int(cur.strip())
        except Exception:
            continue
    # глубокий поиск
    try:
        d = ev.model_dump()
    except Exception:
        d = getattr(ev, "__dict__", None)
    if isinstance(d, dict):
        for k in ("chat_id", "chatId", "peer_id"):
            v = d.get(k)
            if isinstance(v, int):
                return v
            if isinstance(v, str) and v.strip().isdigit():
                return int(v.strip())
    return None

def _msg_text(ev) -> str:
    try:
        t = getattr(getattr(ev.message, "body", None), "text", None)
        if isinstance(t, str) and t.strip():
            return t.strip()
    except Exception:
        pass
    t = getattr(ev.message, "text", None)
    return t.strip() if isinstance(t, str) else ""


async def _load_profile(uid: int) -> dict:
    try:
        async with httpx.AsyncClient(timeout=8) as cl:
            r = await cl.get(f"{BACKEND}/bot/users/{uid}")
            if r.status_code == 404:
                return {"role": None, "city": None}
            r.raise_for_status()
            u = r.json()
            role = "волонтёр" if u.get("role_volunteer") else ("нуждающийся" if u.get("role_requester") else None)
            return {"role": role, "city": u.get("city_code")}
    except Exception:
        return {"role": None, "city": None}

def _profile_line(p: dict) -> str:
    role = p.get("role") or "Не выбрана"
    city = p.get("city") or "Не Задан"
    return f"\n\nТекущая Роль: {role.capitalize()}\nГород: {city}"

if not globals().get("_REGISTERED", False):

    @dp.bot_started()
    async def on_bot_started(ev: BotStarted):
        uid = _get_uid(ev)
        chat_id = _get_chat_id(ev) or getattr(ev, "chat_id", None)              
        prof = await _load_profile(uid) if uid is not None else {"role": None, "city": None}
        if chat_id is not None:
            await _safe_send(ev.bot, chat_id=chat_id, text=TXT_HELLO + TXT_FEATURES, kb=MAIN_KB_F)
            await _safe_send(ev.bot, chat_id=chat_id, text=TXT_DONATE + TXT_CTA, kb=MAIN_KB_D)

    @dp.message_created(Command('start'))
    async def on_start(ev: MessageCreated):
        uid = _get_uid(ev)
        if uid is None:
            await _safe_answer(ev.message, "Не удалось определить ваш ID. Попробуйте ещё раз.", kb=MAIN_KB)
            return
        prof = await _load_profile(uid)
        await _safe_answer(ev.message, TXT_HELLO + TXT_FEATURES, kb=MAIN_KB_F)
        await _safe_answer(ev.message, TXT_DONATE + TXT_CTA, kb=MAIN_KB_D)


    @dp.message_created(Command('menu'))
    async def on_menu(ev: MessageCreated):
        uid = _get_uid(ev)
        if uid is None:
            await _safe_answer(ev.message, "Не удалось определить ваш ID. Попробуйте ещё раз.", kb=MAIN_KB)
            return        
        prof = await _load_profile(uid)
        await _safe_answer(ev.message, TXT_HELLO + TXT_FEATURES, kb=MAIN_KB_F)
        await _safe_answer(ev.message, TXT_DONATE + TXT_CTA, kb=MAIN_KB_D)


    @dp.message_created(Command('help'))
    async def on_help(ev: MessageCreated):
        await _safe_answer(ev.message, TXT_FEATURES)
        await _safe_answer(ev.message, TXT_CTA, kb=MAIN_KB_D)

    _REGISTERED = True