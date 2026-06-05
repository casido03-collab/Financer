from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext

from app.database import db
from app.keyboards.reply import back_to_menu_kb, personal_cabinet_kb
from app.keyboards.inline import subscription_kb
from app.database.analytics import record_payment, track_event

router = Router()

PLAN_14_PRICE_STARS = 200
PLAN_14_DAYS = 14


@router.message(F.text == "💎 Подписка")
async def subscription_info(message: Message, state: FSMContext):
    await state.clear()
    is_active = await db.is_subscription_active(message.from_user.id)

    if is_active:
        user = await db.get_user(message.from_user.id)
        from datetime import datetime
        sub_until = user.get("subscription_until", "")
        try:
            until_dt = datetime.fromisoformat(sub_until)
            date_str = until_dt.strftime("%d.%m.%Y")
        except Exception:
            date_str = "—"

        await message.answer(
            f"💎 <b>Ваша подписка активна</b>\n\n"
            f"Тариф: Премиум\n"
            f"Доступ до: {date_str}\n\n"
            f"Включено:\n"
            f"✅ Расширенный план на 14 дней\n"
            f"✅ Неограниченные консультации\n"
            f"✅ Персональный ИИ-анализ\n\n"
            f"Хотите продлить подписку?",
            reply_markup=subscription_kb(),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            "💎 <b>Премиум-подписка</b>\n\n"
            "📋 <b>Что включено:</b>\n"
            "✅ Персональный финансовый план на 14 дней\n"
            "✅ Детальное распределение бюджета по категориям\n"
            "✅ Дневной лимит расходов\n"
            "✅ Прогноз остатка и рекомендации\n"
            "✅ Мягкий план накоплений\n\n"
            "💰 Стоимость: 200 ⭐ (Telegram Stars)\n\n"
            "Оплата безопасная — через официальную платежную систему Telegram.",
            reply_markup=subscription_kb(),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "buy_14_days")
async def buy_14_days(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    if user:
        await track_event(user["id"], "payment_initiated")
    await callback.message.answer_invoice(
        title="Финансовый план на 14 дней",
        description=(
            "Персональный расширенный финансовый план: "
            "распределение бюджета, дневные лимиты, прогноз и рекомендации по экономии."
        ),
        payload="plan_14_days",
        currency="XTR",
        prices=[LabeledPrice(label="Финансовый план на 14 дней", amount=PLAN_14_PRICE_STARS)],
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    stars = message.successful_payment.total_amount

    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Ошибка при обработке платежа. Обратитесь в поддержку.")
        return

    await db.save_payment(
        user_id=user["id"],
        amount_stars=stars,
        product_name=payload,
        status="completed",
    )

    if payload == "plan_14_days":
        await db.activate_subscription(message.from_user.id, PLAN_14_DAYS)
        await record_payment(user["id"])
        await message.answer(
            f"✅ <b>Оплата получена!</b>\n\n"
            f"Вам открыт расширенный финансовый план на {PLAN_14_DAYS} дней.\n\n"
            f"Перейдите в раздел 💬 Консультация для получения плана.",
            reply_markup=back_to_menu_kb(),
            parse_mode="HTML",
        )
