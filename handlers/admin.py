from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from database import Database
from i18n import t
from keyboards import admin_request_keyboard, main_menu



def get_admin_router(db: Database, admin_ids: list[int]) -> Router:
    router = Router()

    def is_admin(user_id: int) -> bool:
        return user_id in admin_ids

    @router.message(F.text.in_({"Админка", "Admin panel"}))
    async def admin_panel(message: Message):
        lang = db.get_user_language(message.from_user.id)
        if not is_admin(message.from_user.id):
            await message.answer(t(lang, "not_admin"), reply_markup=main_menu(lang))
            return

        requests = db.list_requests(status="pending", limit=10)
        if not requests:
            await message.answer(t(lang, "no_requests"), reply_markup=main_menu(lang))
            return

        await message.answer(t(lang, "pending_requests"), reply_markup=main_menu(lang))
        for req in requests:
            text = (
                f"#{req['id']}\n"
                f"User: @{req['username'] or '-'} ({req['user_id']})\n"
                f"Pair: {req['source_currency']} -> {req['target_currency']}\n"
                f"Amount: {req['amount']:.8f}\n"
                f"Final rate: {req['final_rate']:.8f}\n"
                f"Receive: {req['receive_amount']:.8f}\n"
                f"Status: {req['status']}"
            )
            await message.answer(text, reply_markup=admin_request_keyboard(req["id"]))

    @router.callback_query(F.data.startswith("approve:"))
    async def approve_request(callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            await callback.answer("No access", show_alert=True)
            return

        request_id = int(callback.data.split(":", 1)[1])
        db.update_request_status(request_id, "approved")
        req = db.get_request(request_id)

        if req:
            try:
                await callback.bot.send_message(req["user_id"], f"✅ Your request #{request_id} has been approved.")
            except Exception:
                pass

        if callback.message:
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.answer(f"{t('en', 'approved')} #{request_id}")
        await callback.answer()

    @router.callback_query(F.data.startswith("reject:"))
    async def reject_request(callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            await callback.answer("No access", show_alert=True)
            return

        request_id = int(callback.data.split(":", 1)[1])
        db.update_request_status(request_id, "rejected")
        req = db.get_request(request_id)

        if req:
            try:
                await callback.bot.send_message(req["user_id"], f"❌ Your request #{request_id} has been rejected.")
            except Exception:
                pass

        if callback.message:
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.answer(f"{t('en', 'rejected')} #{request_id}")
        await callback.answer()

    return router
