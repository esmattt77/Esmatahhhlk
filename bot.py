# استيراد المكتبات اللازمة
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)
from flask import Flask, request, jsonify

# استيراد الكود الذي قمت بتوفيره
import smsman_api

# إعدادات تسجيل الأخطاء (Log)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# الحصول على توكن البوت من المتغيرات البيئية
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
PORT = int(os.environ.get('PORT', 5000))
# تم إضافة هذا المتغير
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))

# تهيئة تطبيق Flask
app = Flask(__name__)

# دالة مساعدة للتحقق من هوية الأدمن
def is_admin(user_id):
    return user_id == ADMIN_ID


# دالة الرد على أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton('☎️︙شراء ارقـام وهمية', callback_data='Buynum')],
        [InlineKeyboardButton('💰︙شحن رصيدك', callback_data='Payment'), InlineKeyboardButton('👤︙قسم الرشق', callback_data='sh')],
        [InlineKeyboardButton('🅿️︙كشف الحساب', callback_data='Record'), InlineKeyboardButton('🛍︙قسم العروض', callback_data='Wo')],
        [InlineKeyboardButton('☑️︙قسم العشوائي', callback_data='worldwide'), InlineKeyboardButton('👑︙قسم الملكي', callback_data='saavmotamy')],
        [InlineKeyboardButton('💰︙ربح روبل مجاني 🤑', callback_data='assignment')],
        [InlineKeyboardButton('💳︙متجر الكروت', callback_data='readycard-10'), InlineKeyboardButton('🔰︙الارقام الجاهزة', callback_data='ready')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_html(
        f"مرحباً بك يا {user.mention_html()}! تفضل لوحة التحكم الرئيسية للبوت:",
        reply_markup=reply_markup,
    )

# تم تعديل هذه الدالة
async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.message.reply_text("عذراً، هذه الميزة مخصصة للمالك فقط.")
        return
    
    balance = smsman_api.get_smsman_balance()
    if balance is not False:
        await query.message.reply_text(f"رصيد حسابك في موقع SMS-Man هو: {balance:.2f} ₽")
    else:
        await query.message.reply_text("حدث خطأ في جلب الرصيد. يرجى المحاولة مرة أخرى لاحقاً.")

# تم تعديل هذه الدالة
async def show_account_record(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.message.reply_text("عذراً، هذه الميزة مخصصة للمالك فقط.")
        return

    last_request_id = context.user_data.get('request_id')
    last_phone_number = context.user_data.get('phone_number')
    if last_request_id and last_phone_number:
        message = (
            f"**كشف الحساب (آخر طلب):**\n"
            f"**رقم الطلب:** `{last_request_id}`\n"
            f"**الرقم:** `{last_phone_number}`\n"
            f"**الحالة:** (لمعرفة الحالة، يرجى طلب الكود مرة أخرى من البوت)\n"
        )
        await query.message.reply_text(message)
    else:
        await query.message.reply_text("لا توجد سجلات لعمليات شراء سابقة في حسابك.")

async def buy_number_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton('واتساب', callback_data='service_2')],
        [InlineKeyboardButton('تلجرام', callback_data='service_3')],
        [InlineKeyboardButton('فيسبوك', callback_data='service_4')],
        [InlineKeyboardButton('انستجرام', callback_data='service_5')],
        [InlineKeyboardButton('تويتر', callback_data='service_6')],
        [InlineKeyboardButton('تيك توك', callback_data='service_7')],
        [InlineKeyboardButton('عودة', callback_data='back_to_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(
        text="اختر الخدمة التي تريدها:",
        reply_markup=reply_markup
    )
    
async def get_countries_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("جاري تحميل قائمة الدول...", show_alert=True)
    
    data = query.data.split('_')
    service_id = data[1]
    current_page = int(data[2]) if len(data) > 2 else 0
    
    context.user_data['service_id'] = service_id

    countries = smsman_api.get_smsman_countries(app_id=service_id)

    sorted_countries = sorted(countries.values(), key=lambda c: c['price'])
    
    start_index = current_page * 10
    end_index = start_index + 10
    countries_to_display = sorted_countries[start_index:end_index]
    
    keyboard = []
    
    for country in countries_to_display:
        country_name = country['name']
        price = country['price']
        count = country['count']
        
        button_text = f"🔹 {country_name} | {price:.2f} ₽ | متوفر: {count}"
        callback_data = f"request_{service_id}_{country['code']}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"countries_{service_id}_{current_page - 1}"))
    if end_index < len(sorted_countries):
        nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"countries_{service_id}_{current_page + 1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton("عودة", callback_data='back_to_services')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text="اختر الدولة التي تريدها:",
        reply_markup=reply_markup
    )

async def request_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("جاري طلب رقمك...", show_alert=True)
    
    data = query.data.split('_')
    service_id = data[1]
    country_code = data[2]
    
    result = smsman_api.request_smsman_number(service_id, country_code)

    if result and 'request_id' in result:
        request_id = result['request_id']
        phone_number = result['Phone']
        
        context.user_data['request_id'] = request_id
        context.user_data['phone_number'] = phone_number
        
        keyboard = [
            [InlineKeyboardButton('✅︙وصل الكود', callback_data='check_code')],
            [InlineKeyboardButton('❌︙إلغاء الطلب', callback_data='cancel_request')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=f"تم شراء الرقم بنجاح!\n\n**الرقم:** `{phone_number}`\n**الخدمة:** `{smsman_api.service_map.get(service_id)}`\n\nأدخل الرقم في التطبيق واضغط 'وصل الكود' عندما يصلك.",
            reply_markup=reply_markup
        )
    else:
        await query.edit_message_text("عذراً، لم يتم شراء الرقم. قد يكون الرصيد غير كافٍ أو الخدمة غير متوفرة حالياً. يرجى المحاولة مرة أخرى.")

async def check_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("جاري التحقق من الكود...", show_alert=True)
    
    request_id = context.user_data.get('request_id')

    if not request_id:
        await query.edit_message_text("عذراً، لم يتم العثور على طلب رقم نشط.")
        return

    result = smsman_api.get_smsman_code(request_id)
    
    if result and result['status'] == 'success':
        code = result['Code']
        await query.edit_message_text(f"🎉 وصل الكود بنجاح!\n\n**الكود:** `{code}`")
    elif result and result['status'] == 'pending':
        await query.edit_message_text("الكود لم يصل بعد. يرجى الانتظار والمحاولة مرة أخرى.")
    else:
        await query.edit_message_text("عذراً، حدث خطأ أثناء جلب الكود. يرجى التأكد من أنك طلبت الرقم بشكل صحيح.")

async def cancel_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("جاري إلغاء الطلب...", show_alert=True)
    
    request_id = context.user_data.get('request_id')
    
    if not request_id:
        await query.edit_message_text("لا يوجد طلب رقم نشط حالياً لإلغائه.")
        return

    result = smsman_api.cancel_smsman_request(request_id)

    if result and result['status'] == 'success':
        await query.edit_message_text("تم إلغاء الطلب بنجاح. سيتم استرجاع رصيدك.")
    else:
        await query.edit_message_text("عذراً، لم يتمكن البوت من إلغاء الطلب. يرجى التواصل مع الدعم.")

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await start(update, context)

async def back_to_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await buy_number_menu(update, context)

async def handle_static_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("هذه الميزة قيد التطوير.")
    
# الدالة الرئيسية لتشغيل البوت
def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_balance, pattern='^Payment$'))
    application.add_handler(CallbackQueryHandler(show_account_record, pattern='^Record$'))
    application.add_handler(CallbackQueryHandler(buy_number_menu, pattern='^Buynum$'))
    application.add_handler(CallbackQueryHandler(back_to_main, pattern='^back_to_main$'))
    application.add_handler(CallbackQueryHandler(back_to_services, pattern='^back_to_services$'))
    application.add_handler(CallbackQueryHandler(request_number, pattern=r'^request_\d+_\d+$'))
    application.add_handler(CallbackQueryHandler(check_code, pattern='^check_code$'))
    application.add_handler(CallbackQueryHandler(cancel_request, pattern='^cancel_request$'))

    application.add_handler(CallbackQueryHandler(get_countries_menu, pattern=r'^countries_\d+_\d+$'))
    application.add_handler(CallbackQueryHandler(get_countries_menu, pattern=r'^service_\d+$'))

    application.add_handler(CallbackQueryHandler(handle_static_buttons, pattern='^sh$'))
    application.add_handler(CallbackQueryHandler(handle_static_buttons, pattern='^Wo$'))
    application.add_handler(CallbackQueryHandler(handle_static_buttons, pattern='^worldwide$'))
    application.add_handler(CallbackQueryHandler(handle_static_buttons, pattern='^saavmotamy$'))
    application.add_handler(CallbackQueryHandler(handle_static_buttons, pattern='^assignment$'))
    application.add_handler(CallbackQueryHandler(handle_static_buttons, pattern='^readycard-10$'))
    application.add_handler(CallbackQueryHandler(handle_static_buttons, pattern='^ready$'))
    
    @app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
    async def webhook_handler():
        """Handle incoming webhook updates."""
        try:
            update = Update.de_json(request.get_json(force=True), application.bot)
            await application.process_update(update)
            return jsonify({"status": "ok"})
        except Exception as e:
            logging.error("Error processing update: %s", e)
            return jsonify({"status": "error"}), 500

    @app.route("/")
    async def index():
        return "Hello World!"
        
    application.run_webhook(listen="0.0.0.0", port=PORT, webhook_url=WEBHOOK_URL)


if __name__ == "__main__":
    main()
