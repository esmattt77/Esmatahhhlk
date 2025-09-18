# استيراد المكتبات اللازمة
import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)

# استيراد الكود الذي قمت بتوفيره
import smsman_api

# إعدادات تسجيل الأخطاء (Log)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# الحصول على توكن البوت من المتغيرات البيئية
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# تعريف دالة الرد على أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ترسل لوحة التحكم الرئيسية."""
    user = update.effective_user

    keyboard = [
        [InlineKeyboardButton('☎️︙شراء ارقـام وهمية', callback_data='Buynum')],
        [
            InlineKeyboardButton('💰︙شحن رصيدك', callback_data='Payment'),
            InlineKeyboardButton('👤︙قسم الرشق', callback_data='sh')
        ],
        [
            InlineKeyboardButton('🅿️︙كشف الحساب', callback_data='Record'),
            InlineKeyboardButton('🛍︙قسم العروض', callback_data='Wo')
        ],
        [
            InlineKeyboardButton('☑️︙قسم العشوائي', callback_data='worldwide'),
            InlineKeyboardButton('👑︙قسم الملكي', callback_data='saavmotamy')
        ],
        [InlineKeyboardButton('💰︙ربح روبل مجاني 🤑', callback_data='assignment')],
        [
            InlineKeyboardButton('💳︙متجر الكروت', callback_data='readycard-10'),
            InlineKeyboardButton('🔰︙الارقام الجاهزة', callback_data='ready')
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_html(
        f"مرحباً بك يا {user.mention_html()}! تفضل لوحة التحكم الرئيسية للبوت:",
        reply_markup=reply_markup,
    )

# دالة لعرض رصيد المستخدم
async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    balance = smsman_api.get_smsman_balance()
    
    if balance is not False:
        await query.message.reply_text(f"رصيد حسابك في موقع SMS-Man هو: {balance:.2f} $")
    else:
        await query.message.reply_text("حدث خطأ في جلب الرصيد. يرجى المحاولة مرة أخرى لاحقاً.")

# الدالة الجديدة: لعرض كشف الحساب
async def show_account_record(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # استخدام البيانات المخزنة في سياق المستخدم
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


# الدالة الجديدة: لعرض قائمة الخدمات
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
    
# الدالة الجديدة: لعرض قائمة الدول
async def get_countries_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("جاري تحميل قائمة الدول...", show_alert=True)
    
    service_id = query.data.split('_')[1]
    
    # حفظ هوية الخدمة في سياق المستخدم
    context.user_data['service_id'] = service_id

    countries = smsman_api.get_smsman_countries(app_id=service_id)

    keyboard = []
    sorted_countries = sorted(countries.values(), key=lambda c: c['price'])
    
    for country in sorted_countries:
        country_name = country['name']
        price = country['price']
        count = country['count']
        
        button_text = f"{country_name} | {price:.2f}$ | متوفر: {count}"
        callback_data = f"request_{service_id}_{country['code']}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
    keyboard.append([InlineKeyboardButton("عودة", callback_data='back_to_services')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text="اختر الدولة التي تريدها:",
        reply_markup=reply_markup
    )

# دالة لطلب الرقم الفعلي من SMS-Man
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


# دالة جديدة: لجلب الكود بعد ضغط زر 'وصل الكود'
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


# دالة جديدة: لإلغاء طلب الرقم
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


# دالة العودة للقائمة الرئيسية
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await start(update, context)

# دالة العودة لقائمة الخدمات
async def back_to_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await buy_number_menu(update, context)


# الدالة الرئيسية لتشغيل البوت
def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # إضافة الأوامر (Handlers)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_balance, pattern='^Payment$')) # تم تغيير هذا
    application.add_handler(CallbackQueryHandler(show_account_record, pattern='^Record$')) # تم إضافة هذا
    application.add_handler(CallbackQueryHandler(back_to_main, pattern='^back_to_main$'))
    application.add_handler(CallbackQueryHandler(buy_number_menu, pattern='^Buynum$'))
    application.add_handler(CallbackQueryHandler(back_to_services, pattern='^back_to_services$'))
    application.add_handler(CallbackQueryHandler(get_countries_menu, pattern='^service_\d+$'))
    application.add_handler(CallbackQueryHandler(request_number, pattern='^request_\d+_\d+$'))
    
    # معالجات الأزرار الجديدة: 'وصل الكود' و 'إلغاء الطلب'
    application.add_handler(CallbackQueryHandler(check_code, pattern='^check_code$'))
    application.add_handler(CallbackQueryHandler(cancel_request, pattern='^cancel_request$'))

    # معالجات الأزرار المتبقية (لا تقوم بشيء حالياً)
    application.add_handler(CallbackQueryHandler(lambda update, context: update.callback_query.answer(), pattern='^sh$'))
    application.add_handler(CallbackQueryHandler(lambda update, context: update.callback_query.answer(), pattern='^Wo$'))
    application.add_handler(CallbackQueryHandler(lambda update, context: update.callback_query.answer(), pattern='^worldwide$'))
    application.add_handler(CallbackQueryHandler(lambda update, context: update.callback_query.answer(), pattern='^saavmotamy$'))
    application.add_handler(CallbackQueryHandler(lambda update, context: update.callback_query.answer(), pattern='^assignment$'))
    application.add_handler(CallbackQueryHandler(lambda update, context: update.callback_query.answer(), pattern='^readycard-10$'))
    application.add_handler(CallbackQueryHandler(lambda update, context: update.callback_query.answer(), pattern='^ready$'))


    print("البوت يعمل...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
