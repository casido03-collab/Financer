from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.database import analytics as an
from app.keyboards.admin_kb import admin_main_kb, admin_back_kb

router = Router()

ADMIN_ID = 1715461306


def _guard(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ─── /admin ───────────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    await state.clear()
    if not _guard(message.from_user.id):
        return

    u   = await an.get_users_stats()
    act = await an.get_active_users()
    rev = await an.get_revenue()

    ret = await an.get_retention()
    ai  = await an.get_ai_stats()

    async def cnt(event_type):
        from app.config import DB_PATH
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT COUNT(DISTINCT user_id) FROM events WHERE event_type=?", (event_type,)
            ) as c:
                return (await c.fetchone())[0] or 0

    consults   = await cnt("ai_request")
    calcs      = await cnt("calculator_use")
    goals      = await cnt("section_open")

    text = (
        "📊 <b>Financer Admin</b>\n\n"
        f"👥 Пользователи: <b>{u['total']}</b>\n"
        f"🆕 Сегодня: <b>+{u['today']}</b>\n"
        f"🔥 Активных (DAU): <b>{act['dau']}</b>\n\n"
        f"💬 AI-запросов: <b>{ai['requests']}</b>\n\n"
        f"💰 Выручка сегодня: <b>{rev['today']} ⭐</b>\n"
        f"💰 Выручка месяц: <b>{rev['month']} ⭐</b>\n\n"
        f"📉 D1: <b>{ret.get('D1', 0)}%</b>  "
        f"D7: <b>{ret.get('D7', 0)}%</b>  "
        f"D30: <b>{ret.get('D30', 0)}%</b>"
    )
    await message.answer(text, reply_markup=admin_main_kb(), parse_mode="HTML")


# ─── Callbacks ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_main")
async def adm_main(cb: CallbackQuery):
    if not _guard(cb.from_user.id):
        await cb.answer()
        return

    u   = await an.get_users_stats()
    act = await an.get_active_users()
    rev = await an.get_revenue()
    ret = await an.get_retention()
    ai  = await an.get_ai_stats()

    text = (
        "📊 <b>Financer Admin</b>\n\n"
        f"👥 Пользователи: <b>{u['total']}</b>\n"
        f"🆕 Сегодня: <b>+{u['today']}</b>\n"
        f"🔥 Активных (DAU): <b>{act['dau']}</b>\n\n"
        f"💬 AI-запросов: <b>{ai['requests']}</b>\n\n"
        f"💰 Выручка сегодня: <b>{rev['today']} ⭐</b>\n"
        f"💰 Выручка месяц: <b>{rev['month']} ⭐</b>\n\n"
        f"📉 D1: <b>{ret.get('D1', 0)}%</b>  "
        f"D7: <b>{ret.get('D7', 0)}%</b>  "
        f"D30: <b>{ret.get('D30', 0)}%</b>"
    )
    await cb.message.edit_text(text, reply_markup=admin_main_kb(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "adm_users")
async def adm_users(cb: CallbackQuery):
    if not _guard(cb.from_user.id):
        await cb.answer(); return

    u = await an.get_users_stats()
    text = (
        "👥 <b>Пользователи</b>\n\n"
        f"Всего: <b>{u['total']}</b>\n\n"
        f"Сегодня: <b>+{u['today']}</b>\n"
        f"Вчера: <b>+{u['yesterday']}</b>\n"
        f"За 7 дней: <b>+{u['week']}</b>\n"
        f"За 30 дней: <b>+{u['month']}</b>"
    )
    await cb.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "adm_retention")
async def adm_retention(cb: CallbackQuery):
    if not _guard(cb.from_user.id):
        await cb.answer(); return

    ret = await an.get_retention()

    def flag(val, ok, warn):
        if val >= ok:   return "🟢"
        if val >= warn: return "🟡"
        return "🔴"

    text = (
        "📊 <b>Retention</b>\n\n"
        f"{flag(ret.get('D1',0),40,25)}  D1  = <b>{ret.get('D1',0)}%</b>\n"
        f"{flag(ret.get('D3',0),25,15)}  D3  = <b>{ret.get('D3',0)}%</b>\n"
        f"{flag(ret.get('D7',0),15,10)}  D7  = <b>{ret.get('D7',0)}%</b>\n"
        f"{flag(ret.get('D14',0),10,6)}  D14 = <b>{ret.get('D14',0)}%</b>\n"
        f"{flag(ret.get('D30',0),6,3)}  D30 = <b>{ret.get('D30',0)}%</b>\n\n"
        "🟢 норма  🟡 риск  🔴 проблема"
    )
    await cb.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "adm_onboarding")
async def adm_onboarding(cb: CallbackQuery):
    if not _guard(cb.from_user.id):
        await cb.answer(); return

    f = await an.get_onboarding_funnel()

    def pct(a, b):
        return f"({round(a/b*100)}%)" if b else ""

    text = (
        "🚀 <b>Воронка онбординга</b>\n\n"
        f"/start\n<b>{f['started']}</b>\n\n"
        f"Начали диагностику\n<b>{f['began_diag']}</b> {pct(f['began_diag'], f['started'])}\n\n"
        f"Завершили онбординг\n<b>{f['completed']}</b> {pct(f['completed'], f['started'])}\n\n"
        f"Открыли меню\n<b>{f['opened_menu']}</b> {pct(f['opened_menu'], f['started'])}\n\n"
        f"Первая консультация\n<b>{f['consulted']}</b> {pct(f['consulted'], f['started'])}\n\n"
        f"Купили план\n<b>{f['paid']}</b> {pct(f['paid'], f['started'])}"
    )
    await cb.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "adm_sections")
async def adm_sections(cb: CallbackQuery):
    if not _guard(cb.from_user.id):
        await cb.answer(); return

    sections = await an.get_sections_stats()
    if not sections:
        text = "📱 <b>Разделы</b>\n\nДанных пока нет."
    else:
        lines = ["📱 <b>Разделы</b>\n"]
        medals = ["🥇", "🥈", "🥉"] + ["▪️"] * 10
        for i, s in enumerate(sections):
            lines.append(f"{medals[i]} {s['section']}\n<b>{s['count']}</b>")
        text = "\n\n".join(lines)

    await cb.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "adm_sales")
async def adm_sales(cb: CallbackQuery):
    if not _guard(cb.from_user.id):
        await cb.answer(); return

    s = await an.get_sales_funnel()
    text = (
        "💰 <b>Продажи</b>\n\n"
        f"Получили бесплатный план:\n<b>{s['got_free_plan']}</b>\n\n"
        f"Увидели оффер:\n<b>{s['saw_offer']}</b>\n\n"
        f"Нажали оплатить:\n<b>{s['tapped_pay']}</b>\n\n"
        f"Оплатили:\n<b>{s['paid']}</b>\n\n"
        f"Конверсия:\n<b>{s['conversion']}%</b>"
    )
    await cb.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "adm_revenue")
async def adm_revenue(cb: CallbackQuery):
    if not _guard(cb.from_user.id):
        await cb.answer(); return

    r = await an.get_revenue()
    text = (
        "💵 <b>Доход</b>\n\n"
        f"Сегодня: <b>{r['today']} ⭐</b>\n"
        f"Вчера: <b>{r['yesterday']} ⭐</b>\n"
        f"7 дней: <b>{r['week']} ⭐</b>\n"
        f"30 дней: <b>{r['month']} ⭐</b>\n\n"
        f"Средний чек: <b>{r['avg_check']} ⭐</b>"
    )
    await cb.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "adm_ai")
async def adm_ai(cb: CallbackQuery):
    if not _guard(cb.from_user.id):
        await cb.answer(); return

    ai = await an.get_ai_stats()
    text = (
        "🤖 <b>OpenAI</b>\n\n"
        f"Запросов: <b>{ai['requests']}</b>\n"
        f"Расход: <b>${ai['total_cost']}</b>\n"
        f"Средний запрос: <b>${ai['avg_cost']}</b>\n\n"
        f"Доход: <b>{ai['total_stars']} ⭐</b>\n"
        f"Маржа: <b>{ai['margin']}%</b>"
    )
    await cb.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "adm_push")
async def adm_push(cb: CallbackQuery):
    if not _guard(cb.from_user.id):
        await cb.answer(); return

    p = await an.get_push_stats()
    text = (
        "📨 <b>Push-уведомления</b>\n\n"
        f"Отправлено: <b>{p['sent']}</b>\n"
        f"Открыли бот: <b>{p['opened']}</b>\n"
        f"CTR: <b>{p['ctr']}%</b>"
    )
    if p["top"]:
        text += "\n\n<b>Топ по CTR:</b>\n"
        medals = ["🥇", "🥈", "🥉", "▪️", "▪️"]
        for i, t in enumerate(p["top"]):
            text += f"\n{medals[i]} {t['type']} — {t['ctr']}%"

    await cb.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "adm_articles")
async def adm_articles(cb: CallbackQuery):
    if not _guard(cb.from_user.id):
        await cb.answer(); return

    arts = await an.get_articles_stats()
    if not arts:
        text = "📚 <b>Статьи</b>\n\nДанных пока нет."
    else:
        lines = ["📚 <b>ТОП статей</b>\n"]
        for i, a in enumerate(arts, 1):
            lines.append(f"{i}. {a['article']}\n<b>{a['count']}</b>")
        text = "\n\n".join(lines)

    await cb.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "adm_audience")
async def adm_audience(cb: CallbackQuery):
    if not _guard(cb.from_user.id):
        await cb.answer(); return

    a = await an.get_audience_stats()
    lines = ["👥 <b>Аудитория</b>\n"]

    if a["work_types"]:
        for wt in a["work_types"]:
            pct = round(wt["count"] / a["total"] * 100) if a["total"] else 0
            lines.append(f"{wt['type']}\n<b>{pct}%</b>")

    lines.append(f"\nНе ведут учёт расходов\n<b>{a['no_tracking']}%</b>")
    lines.append(f"Импульсивные траты (главная проблема)\n<b>{a['impulsive']}%</b>")
    lines.append(f"Не контролируют расходы\n<b>{a['overspend']}%</b>")

    await cb.message.edit_text("\n\n".join(lines), reply_markup=admin_back_kb(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "adm_health")
async def adm_health(cb: CallbackQuery):
    if not _guard(cb.from_user.id):
        await cb.answer(); return

    u   = await an.get_users_stats()
    act = await an.get_active_users()
    ret = await an.get_retention()
    s   = await an.get_sales_funnel()
    rev = await an.get_revenue()
    ai  = await an.get_ai_stats()
    secs = await an.get_sections_stats()
    top_sec = secs[0]["section"] if secs else "—"

    text = (
        "🚀 <b>Health Report</b>\n\n"
        f"Пользователи: <b>{u['total']}</b>\n"
        f"DAU: <b>{act['dau']}</b>\n"
        f"WAU: <b>{act['wau']}</b>\n"
        f"MAU: <b>{act['mau']}</b>\n\n"
        f"D1: <b>{ret.get('D1',0)}%</b>\n"
        f"D7: <b>{ret.get('D7',0)}%</b>\n"
        f"D30: <b>{ret.get('D30',0)}%</b>\n\n"
        f"Конверсия в оплату: <b>{s['conversion']}%</b>\n"
        f"Доход (месяц): <b>{rev['month']} ⭐</b>\n"
        f"Расход OpenAI: <b>${ai['total_cost']}</b>\n\n"
        f"Популярный раздел: <b>{top_sec}</b>"
    )
    await cb.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    await cb.answer()
