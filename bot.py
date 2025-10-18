# bot.py

import os
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from sms_activate_api import sms_api, RequestError

# إعدادات التسجيل
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# الحصول على التوكن من المتغيرات البيئية
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ADMIN_IDS = list(map(int, os.environ.get('ADMIN_IDS', '').split(','))) if os.environ.get('ADMIN_IDS') else []

# تعيين مفتاح API
sms_api.api_key = os.environ.get('SMS_ACTIVATE_API_KEY', 'your_api_key_here')

# تعيين الخدمات
SERVICES = {
    'tg': 'تيليجرام',
    'wa': 'واتساب', 
    'fb': 'فيسبوك',
    'ig': 'انستجرام',
    'tw': 'تويتر',
    'vk': 'فكونتاكتي',
    'ok': 'أودنوكلاسنيكي',
    'mm': 'مابمبا',
    'mb': 'يولا',
    'wb': 'وي شات'
}

# قاعدة بيانات بسيطة (في الإنتاج استخدم قاعدة بيانات حقيقية)
users_db = {}
orders_db = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id
    
    # تسجيل المستخدم إذا كان جديداً
    if user_id not in users_db:
        users_db[user_id] = {
            'username': user.username,
            'first_name': user.first_name,
            'join_date': datetime.now(),
            'balance': 0.0,
            'total_orders': 0
        }
    
    keyboard = [
        [InlineKeyboardButton('☎️ شراء أرقام', callback_data='buy_numbers')],
        [InlineKeyboardButton('💰 رصيدي', callback_data='my_balance'),
         InlineKeyboardButton('📊 إحصائياتي', callback_data='my_stats')],
        [InlineKeyboardButton('🛒 طلباتي', callback_data='my_orders')],
    ]
    
    # إضافة لوحة المشرفين إذا كان المستخدم مشرفاً
    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton('👑 لوحة المشرفين', callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_html(
        f"مرحباً {user.mention_html()}! 👋\n\n"
        "أهلاً بك في بوت شراء الأرقام الافتراضية.\n"
        "اختر الخدمة التي تريدها من القائمة:",
        reply_markup=reply_markup
    )

async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    try:
        balance_info = sms_api.get_balance_and_cashback()
        user_balance = users_db.get(user_id, {}).get('balance', 0)
        
        message = (
            f"💳 **رصيدك الحالي:**\n\n"
            f"• رصيد SMS Activate: ${balance_info['balance']:.2f}\n"
            f"• رصيد الكاش باك: ${balance_info['cashback']:.2f}\n"
            f"• رصيدك في البوت: ${user_balance:.2f}"
        )
        
        keyboard = [
            [InlineKeyboardButton('🔙 العودة', callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except RequestError as e:
        await query.edit_message_text(f"❌ حدث خطأ: {str(e)}")

async def buy_numbers_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for service_code, service_name in SERVICES.items():
        keyboard.append([InlineKeyboardButton(f'📱 {service_name}', callback_data=f'service_{service_code}')])
    
    keyboard.append([InlineKeyboardButton('🔙 العودة', callback_data='main_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🛍️ **اختر الخدمة:**\n\n"
        "اختر الخدمة التي تريد شراء رقم لها:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_countries(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    service_code = query.data.split('_')[1]
    context.user_data['selected_service'] = service_code
    
    try:
        countries = sms_api.get_countries()
        prices = sms_api.get_prices(service=service_code)
        
        keyboard = []
        for country_code, country_info in countries.items():
            country_id = int(country_code)
            service_key = f"{service_code}_{country_id}"
            
            if service_key in prices:
                price = prices[service_key]['cost']
                count = prices[service_key]['count']
                
                if count > 0:
                    button_text = f"🇺🇳 {country_info['name']} - ${price} ({count})"
                    keyboard.append([
                        InlineKeyboardButton(
                            button_text, 
                            callback_data=f'country_{country_id}'
                        )
                    ])
        
        keyboard.append([InlineKeyboardButton('🔙 العودة', callback_data='buy_numbers')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🌍 **اختر الدولة للخدمة: {SERVICES[service_code]}**\n\n"
            "اختر الدولة التي تريد الرقم منها:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except RequestError as e:
        await query.edit_message_text(f"❌ حدث خطأ: {str(e)}")

async def request_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    country_id = int(query.data.split('_')[1])
    service_code = context.user_data.get('selected_service')
    
    try:
        number_info = sms_api.get_number(service_code, country_id)
        
        order_id = number_info['id']
        orders_db[order_id] = {
            'user_id': query.from_user.id,
            'service': service_code,
            'country': country_id,
            'number': number_info['number'],
            'status': 'active',
            'order_time': datetime.now()
        }
        
        user_id = query.from_user.id
        if user_id in users_db:
            users_db[user_id]['total_orders'] += 1
        
        keyboard = [
            [InlineKeyboardButton('📩 الحصول على الكود', callback_data=f'get_code_{order_id}')],
            [InlineKeyboardButton('❌ إلغاء الطلب', callback_data=f'cancel_{order_id}')],
            [InlineKeyboardButton('🔙 العودة', callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ **تم شراء الرقم بنجاح!**\n\n"
            f"📱 **الرقم:** `{number_info['number']}`\n"
            f"🛍️ **الخدمة:** {SERVICES[service_code]}\n"
            f"🆔 **رقم الطلب:** `{order_id}`\n\n"
            f"استخدم الرقم في التطبيق المطلوب، ثم اضغط على 'الحصول على الكود'",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except RequestError as e:
        await query.edit_message_text(f"❌ حدث خطأ في طلب الرقم: {str(e)}")

async def get_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    order_id = query.data.split('_')[2]
    
    try:
        status_info = sms_api.get_status(order_id)
        
        if status_info['code']:
            orders_db[order_id]['status'] = 'completed'
            orders_db[order_id]['code'] = status_info['code']
            
            await query.edit_message_text(
                f"🎉 **تم استلام الكود بنجاح!**\n\n"
                f"🔢 **الكود:** `{status_info['code']}`\n"
                f"🆔 **رقم الطلب:** `{order_id}`\n\n"
                f"يمكنك الآن استخدام الكود لإكمال العملية.",
                parse_mode='Markdown'
            )
        else:
            keyboard = [
                [InlineKeyboardButton('🔄 تحديث', callback_data=f'get_code_{order_id}')],
                [InlineKeyboardButton('❌ إلغاء الطلب', callback_data=f'cancel_{order_id}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"⏳ **في انتظار الكود...**\n\n"
                f"لم يصل الكود بعد. يرجى الانتظار قليلاً ثم الضغط على تحديث.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
    except RequestError as e:
        await query.edit_message_text(f"❌ حدث خطأ: {str(e)}")

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    order_id = query.data.split('_')[1]
    
    try:
        sms_api.set_status(order_id, 8)
        
        if order_id in orders_db:
            orders_db[order_id]['status'] = 'cancelled'
        
        await query.edit_message_text(
            f"✅ **تم إلغاء الطلب بنجاح**\n\n"
            f"🆔 رقم الطلب: `{order_id}`\n"
            f"تم إلغاء الطلب واسترجاع الرصيد.",
            parse_mode='Markdown'
        )
        
    except RequestError as e:
        await query.edit_message_text(f"❌ حدث خطأ في الإلغاء: {str(e)}")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ ليس لديك صلاحية الوصول لهذه اللوحة.")
        return
    
    try:
        balance_info = sms_api.get_balance_and_cashback()
        numbers_status = sms_api.get_numbers_status()
        
        total_users = len(users_db)
        total_orders = sum(user['total_orders'] for user in users_db.values())
        active_orders = sum(1 for order in orders_db.values() if order['status'] == 'active')
        
        keyboard = [
            [InlineKeyboardButton('📊 إحصائيات مفصلة', callback_data='admin_stats')],
            [InlineKeyboardButton('👥 إدارة المستخدمين', callback_data='admin_users')],
            [InlineKeyboardButton('🔄 تحديث البيانات', callback_data='admin_panel')],
            [InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            f"👑 **لوحة المشرفين**\n\n"
            f"💳 **الرصيد:**\n"
            f"• الرصيد الرئيسي: ${balance_info['balance']:.2f}\n"
            f"• الكاش باك: ${balance_info['cashback']:.2f}\n\n"
            f"📊 **إحصائيات البوت:**\n"
            f"• إجمالي المستخدمين: {total_users}\n"
            f"• إجمالي الطلبات: {total_orders}\n"
            f"• الطلبات النشطة: {active_orders}\n\n"
            f"📱 **الأرقام المتاحة:**\n"
        )
        
        for service, count in list(numbers_status.items())[:5]:
            if count > 0:
                message += f"• {SERVICES.get(service, service)}: {count}\n"
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except RequestError as e:
        await query.edit_message_text(f"❌ حدث خطأ: {str(e)}")

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    
    keyboard = [
        [InlineKeyboardButton('☎️ شراء أرقام', callback_data='buy_numbers')],
        [InlineKeyboardButton('💰 رصيدي', callback_data='my_balance'),
         InlineKeyboardButton('📊 إحصائياتي', callback_data='my_stats')],
        [InlineKeyboardButton('🛒 طلباتي', callback_data='my_orders')],
    ]
    
    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton('👑 لوحة المشرفين', callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"مرحباً {user.first_name}! 👋\n\n"
        "أهلاً بك في بوت شراء الأرقام الافتراضية.\n"
        "اختر الخدمة التي تريدها من القائمة:",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة الرسائل النصية"""
    await update.message.reply_text(
        "يرجى استخدام الأزرار في القائمة للتفاعل مع البوت.\n"
        "اكتب /start لعرض القائمة الرئيسية."
    )

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("يجب تعيين متغير البيئة TELEGRAM_BOT_TOKEN")
    
    # إنشاء التطبيق مع الإصدار المتوافق
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # معالجات الاستدعاء
    application.add_handler(CallbackQueryHandler(show_balance, pattern='^my_balance$'))
    application.add_handler(CallbackQueryHandler(buy_numbers_menu, pattern='^buy_numbers$'))
    application.add_handler(CallbackQueryHandler(show_countries, pattern='^service_'))
    application.add_handler(CallbackQueryHandler(request_number, pattern='^country_'))
    application.add_handler(CallbackQueryHandler(get_code, pattern='^get_code_'))
    application.add_handler(CallbackQueryHandler(cancel_order, pattern='^cancel_'))
    application.add_handler(CallbackQueryHandler(admin_panel, pattern='^admin_panel$'))
    application.add_handler(CallbackQueryHandler(main_menu, pattern='^main_menu$'))
    
    # معالجات للوظائف المستقبلية
    application.add_handler(CallbackQueryHandler(lambda update, ctx: update.callback_query.answer("قيد التطوير..."), 
                                              pattern='^my_stats$'))
    application.add_handler(CallbackQueryHandler(lambda update, ctx: update.callback_query.answer("قيد التطوير..."), 
                                              pattern='^my_orders$'))
    application.add_handler(CallbackQueryHandler(lambda update, ctx: update.callback_query.answer("قيد التطوير..."), 
                                              pattern='^admin_stats$'))
    application.add_handler(CallbackQueryHandler(lambda update, ctx: update.callback_query.answer("قيد التطوير..."), 
                                              pattern='^admin_users$'))
    
    print("🤖 البوت يعمل...")
    
    # بدء البوت
    application.run_polling()

if __name__ == "__main__":
    main()
