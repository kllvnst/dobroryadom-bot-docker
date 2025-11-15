import httpx
from ..keyboards import reply_kb, open_link_kb
from ..bot import dp, types   
from ..config import donation_list, settings
from ..http import request_json


MessageCreated = types.MessageCreated
BACKEND = settings.bff_base_url
FRONT = settings.public_front_url
DONATE = settings.donate_links

MAIN_KB = open_link_kb([
    [("Открыть мини-приложение «ДоброРядом»", FRONT)],
    [("Пожертвовать через проверенные фонды VK Добро", DONATE)],
])

TXT_REDIRECT = (
    "Все основные действия теперь доступны в мини-приложении: создать заявку, найти помощь и т.д."
)

_state: dict[int, dict] = {}
_profile_cache: dict[int, dict] = {}

def get_state(uid: int): return _state.get(uid)
def set_state(uid: int, v: dict): _state[uid] = v
def clear_state(uid: int): _state.pop(uid, None)

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

def _msg_text(ev) -> str:
    # 1) основной путь maxapi
    try:
        t = getattr(getattr(ev.message, "body", None), "text", None)
        if isinstance(t, str) and t.strip():
            return t.strip()
    except Exception:
        pass
    t = getattr(ev.message, "text", None)
    if isinstance(t, str) and t.strip():
        return t.strip()
    p = getattr(ev.message, "payload", None)
    if isinstance(p, dict):
        for k in ("text", "label", "title", "command", "cmd"):
            v = p.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    return ""

def _uid(ev) -> int | None:
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
            if isinstance(cur, str) and cur.strip().isdigit():
                return int(cur.strip())
        except Exception:
            continue

    # глубокий поиск
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
def _payload(ev) -> dict | None:
    for path in (("message", "payload"), "payload"):
        cur = ev
        try:
            if isinstance(path, tuple):
                for p in path:
                    cur = getattr(cur, p)
            else:
                cur = getattr(cur, path)
            if isinstance(cur, dict):
                return cur
        except Exception:
            continue

    def _as_dict(obj):
        for attr in ("model_dump", "dict"):
            fn = getattr(obj, attr, None)
            if callable(fn):
                try:
                    return fn()
                except Exception:
                    pass
        return getattr(obj, "__dict__", None)

    def _dig(obj):
        if obj is None:
            return None
        if isinstance(obj, dict):
            if "payload" in obj and isinstance(obj["payload"], dict):
                return obj["payload"]
            for v in obj.values():
                r = _dig(v)
                if r is not None:
                    return r
            return None
        d = _as_dict(obj)
        if isinstance(d, dict):
            return _dig(d)
        return None

    return _dig(ev)


HELP_CREATE = (
    "📝 Создание заявки. Шаги:\n"
    "1) Заголовок\n"
    "2) Описание\n"
    "3) Широта (lat)\n"
    "4) Долгота (lon)\n\n"
    "В любой момент: /cancel"
)

async def _ensure_profile(uid: int, role: str | None = None, city: str | None = None) -> dict:
    payload = {"max_user_id": str(uid)}
    if role is not None:
        payload["role"] = role
    if city is not None:
        payload["city_code"] = city
    try:
        async with httpx.AsyncClient(timeout=8) as cl:
            r = await cl.put(f"{BACKEND}/bot/users", json=payload)
            r.raise_for_status()
            u = r.json()
            role_text = "волонтёр" if u.get("role_volunteer") else ("нуждающийся" if u.get("role_requester") else None)
            return {"id": u.get("id"), "role": role_text, "city": u.get("city_code")}
    except Exception:
        return {"id": None, "role": role, "city": city}

async def _get_profile(uid: int) -> dict:
    try:
        async with httpx.AsyncClient(timeout=8) as cl:
            r = await cl.get(f"{BACKEND}/bot/users/{uid}")
            if r.status_code == 404:
                return {"id": None, "role": None, "city": None}
            r.raise_for_status()
            u = r.json()
            role_text = "волонтёр" if u.get("role_volunteer") else ("нуждающийся" if u.get("role_requester") else None)
            return {"id": u.get("id"), "role": role_text, "city": u.get("city_code")}
    except Exception:
        return {"id": None, "role": None, "city": None}

async def list_open_requests(ev: MessageCreated, city: str | None, limit: int = 5):
    params = {"status": "open", "limit": limit}
    if city:
        params["city_code"] = city
    
    data, code = await request_json("GET", "/requests", params=params, timeout=10)

    try:
        if code == 404:
            await _safe_answer(
                ev.message,
                "Пока нет открытых заявок рядом. Нажмите «Создать Заявку», чтобы оставить просьбу, "
                "или «Я Волонтёр», чтобы помогать.",
                kb=MAIN_KB
            )
            return

        if not (code and 200 <= code < 300) or not isinstance(data, list):
            await _safe_answer(
                ev.message,
                "Сервис заявок временно недоступен. Попробуйте позже.",
                kb=MAIN_KB
            )
            return

        if not data:
            await _safe_answer(
                ev.message,
                "Пока нет открытых заявок рядом. Загляните чуть позже или создайте свою заявку.",
                kb=MAIN_KB
            )
            return

        lines = [f"#{it['id']} • {it.get('category','?')} • {it['title']}" for it in data]
        await _safe_answer(ev.message, "🗂 Заявки рядом:\n" + "\n".join(lines), kb=MAIN_KB)

    except httpx.HTTPError:
        await _safe_answer(
            ev.message,
            "Сервис заявок временно недоступен. Попробуйте позже.",
            kb=MAIN_KB
        )


if not globals().get("_REGISTERED", False):

    @dp.message_created()
    async def on_message(ev: MessageCreated):
        uid = _uid(ev)
        if uid is None:
            await _safe_answer(ev.message, "Не удалось определить ваш ID. Попробуйте ещё раз.", kb=MAIN_KB)
            return
        text = _msg_text(ev)
        if not text:
            pl = _payload(ev) or {}
            if isinstance(pl, dict):
                text = (
                    pl.get("text")
                    or pl.get("cmd")
                    or pl.get("command")
                    or pl.get("label")
                    or ""
                )

        low = (text or "").strip().lower()

        if not settings.classic_flow_enabled:
            if low in ("открыть приложение", "открыть мини-приложение", "мини-приложение"):
                await _safe_answer(ev.message, f"🔗 Открыть мини-приложение: ", kb=MAIN_KB)
                return
            if low in ("пожертвовать через проверенные фонды vk добро", "помочь рублем", "донат", "/donate"):
                links = donation_list()
                await _safe_answer(ev.message, "💙 Поддержать через VK Добро:\n", kb=MAIN_KB)
                return
            await _safe_answer(ev.message, TXT_REDIRECT, kb=MAIN_KB)
            return

        if low in ("/cancel", "отмена", "стоп"):
            if get_state(uid):
                clear_state(uid)
                await _safe_answer(ev.message, "Окей, прервали текущий шаг. Можете нажать кнопки меню ниже.", kb=MAIN_KB)

            else:
                await _safe_answer(ev.message, "Нечего отменять. Кнопки меню ниже.", kb=MAIN_KB)
            return

        if low in ("я волонтёр", "я волонтер", "волонтёр", "волонтер"):
            prof = await _ensure_profile(uid, role="volunteer")
            await _safe_answer(ev.message, "Роль сохранена: Волонтёр. Можете открыть «Заявки Рядом» или «Создать Заявку».", kb=MAIN_KB)
            return
        if low in ("нужна помощь", "я нуждаюсь", "заявитель"):
            prof = await _ensure_profile(uid, role="requester")
            await _safe_answer(ev.message, "Роль сохранена: Нуждающийся. Нажмите «Создать Заявку», чтобы опубликовать просьбу.", kb=MAIN_KB)
            return

        if low in ("сменить город", "/city"):
            set_state(uid, {"flow": "set_city"})
            await _safe_answer(ev.message, "Введите название города (например: Москва):", kb=MAIN_KB)
            return
        st = get_state(uid)
        if st and st.get("flow") == "set_city":
            city = text.strip()
            prof = await _ensure_profile(uid, city=city)
            clear_state(uid)
            await _safe_answer(ev.message, f"Город сохранён: {city}. Теперь «Заявки Рядом» будут учитываться по городу.", kb=MAIN_KB)
            return

        if low in ("заявки рядом", "список", "заявки"):
            prof = await _get_profile(uid)
            try:
                await list_open_requests(ev, city=prof.get("city"), limit=5)
            except httpx.HTTPError as e:
                await _safe_answer(ev.message, f"Не удалось получить список заявок: {e}", kb=MAIN_KB)
            return

        if low in ("создать заявку", "создать", "оставить заявку"):
            if get_state(uid):
                await _safe_answer(ev.message, "У вас уже идёт процесс. Наберите /cancel для отмены.", kb=MAIN_KB)
                return
            set_state(uid, {"flow": "create", "stage": "title", "data": {}})
            await _safe_answer(ev.message, HELP_CREATE + "\n\nЗаголовок Заявки (кратко):", kb=MAIN_KB)
            return

        st = get_state(uid)
        if st and st.get("flow") == "create":
            stage = st["stage"]
            data = st["data"]

            if stage == "title":
                text_clean = (text or "").strip()
                if len(text_clean) < 3:
                    await _safe_answer(ev.message, "Заголовок слишком короткий. Минимум 3 символа. Введите заголовок ещё раз:", kb=MAIN_KB)
                    return
                data["title"] = text_clean
                st["stage"] = "desc"
                await _safe_answer(ev.message, "Короткое Описание:", kb=MAIN_KB)
                return

            if stage == "desc":
                data["description"] = text
                st["stage"] = "lat"
                await _safe_answer(ev.message, "Введите Широту (lat), пример 55.75:", kb=MAIN_KB)
                return

            if stage == "lat":
                try:
                    data["lat"] = float(text.replace(",", "."))
                except:
                    await _safe_answer(ev.message, "Не похоже на число. Пример: 55.75", kb=MAIN_KB)
                    return
                st["stage"] = "lon"
                await _safe_answer(ev.message, "Введите Долготу (lon), пример 37.61:", kb=MAIN_KB)
                return

            if stage == "lon":
                try:
                    data["lon"] = float(text.replace(",", "."))
                except:
                    await _safe_answer(ev.message, "Не похоже на число. Пример: 37.61", kb=MAIN_KB)
                    return
                prof = await _get_profile(uid)
                if not prof.get("id"):
                    prof = await _ensure_profile(uid)  
                user_id = prof.get("id")
                if not user_id:
                    await _safe_answer(ev.message, "Не удалось определить профиль пользователя. Наберите /start и попробуйте снова.", kb=MAIN_KB)
                    clear_state(uid)
                    return

                payload = {
                    "max_user_id": str(uid),
                    "category": "social",
                    "title": data["title"],
                    "description": data["description"],
                    "lat": data["lat"],
                    "lon": data["lon"],
                    "city_code": prof.get("city") or None,   
                }

                url = settings.bff_base_url.rstrip("/") + "/requests"

                try:
                    async with httpx.AsyncClient(timeout=10) as cl:
                        r = await cl.post(url, json=payload)

                    code = r.status_code
                    ctype = r.headers.get("content-type", "")
                    resp = r.json() if "application/json" in ctype else {"raw": r.text}

                    if 200 <= code < 300 and isinstance(resp, dict):
                        await _safe_answer(
                            ev.message,
                            f"✅ Заявка создана: #{resp.get('id')} — {resp.get('title')}",
                            kb=MAIN_KB
                        )

                    elif code == 422 and isinstance(resp, dict):
                        detail = resp.get("detail") or []
                        msg = None
                        for err in detail:
                            loc = err.get("loc") or []
                            if len(loc) >= 2 and loc[-1] == "title":
                                msg = "Заголовок слишком короткий. Минимум 3 символа."
                                break
                        await _safe_answer(ev.message, msg or "Данные некорректны. Проверьте форму и попробуйте ещё раз.", kb=MAIN_KB)

                    elif code == 400:
                        await _safe_answer(ev.message, "Не удалось создать заявку: проверьте профиль/город.", kb=MAIN_KB)

                    elif code == 404:
                        await _safe_answer(ev.message, "Сервис создания заявок сейчас недоступен. Попробуйте позже.", kb=MAIN_KB)

                    else:
                        await _safe_answer(ev.message, f"Не удалось создать заявку (код {code}). Попробуйте позже.", kb=MAIN_KB)

                except httpx.HTTPError:
                    await _safe_answer(ev.message, "Сеть/сервер недоступны. Попробуйте позже.", kb=MAIN_KB)
                finally:
                    clear_state(uid)
                return

        if low in ("помочь рублём", "помочь рублем", "донат", "/donate"):
            links = donation_list()
            if not links:
                await _safe_answer(ev.message, "Ссылки для пожертвований пока не настроены.", kb=MAIN_KB)
            else:
                await _safe_answer(ev.message, "💙 Поддержать официально:", kb=MAIN_KB)
            return

        if low in ("открыть приложение", "открыть мини-приложение", "мини-приложение"):
            await _safe_answer(ev.message, "Открыть Мини-Приложение: ", kb=MAIN_KB)
            return

        if low in ("/start", "/help", "/menu", "меню"):
            return

        await _safe_answer(ev.message, "Не понял. Нажмите кнопку ниже или используйте /menu. /cancel — отмена шага.", kb=MAIN_KB)

    _REGISTERED = True
