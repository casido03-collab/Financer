from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.keyboards.reply import back_to_menu_kb
from app.keyboards.inline import articles_list_kb, back_to_articles_kb
from app.texts.articles import ARTICLES

router = Router()


@router.message(F.text == "📚 Полезные статьи")
async def articles_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📚 <b>Полезные статьи о финансах</b>\n\nВыберите статью:",
        reply_markup=articles_list_kb(page=0),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("articles_page_"))
async def articles_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[-1])
    await callback.message.edit_reply_markup(reply_markup=articles_list_kb(page=page))
    await callback.answer()


@router.callback_query(F.data.startswith("article_"))
async def show_article(callback: CallbackQuery):
    article_id = int(callback.data.split("_")[-1])
    article = ARTICLES.get(article_id)
    if not article:
        await callback.answer("Статья не найдена.")
        return

    await callback.message.answer(
        article["text"],
        reply_markup=back_to_articles_kb(),
        parse_mode="HTML",
    )
    await callback.answer()
