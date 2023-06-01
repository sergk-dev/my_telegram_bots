#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position

from dotenv import load_dotenv
import os

import logging
from datetime import time
import arrow
from telegram import __version__ as TG_VER
from pathlib import Path

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ReplyKeyboardMarkup, Update, Bot, BotCommand, BotCommandScopeChat, Document
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, filters, MessageHandler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

MORNING_PRAY = 'Боже направь мои мысли в верное русло, \nОсобенно избавь меня от жалости к себе, \nБесчестных поступков, корыстолюбия. \nПокажи мне в течение всего дня, \nКаким должен быть мой следующий шаг. \nДай мне все, что необходимо для решения проблем. \nИзбавь меня от эгоизма. \nЯ не руковожу своей жизнью. \nДа исполняю я волю Твою.'
EVENING_PRAY = 'Когда мы ложимся спать, мы конструктивно оцениваем прожитый день. Не были ли мы в течение дня наполненными resentment-ом, эгоистичными или нечестными, может, мы испытывали страх? Или должны извиниться перед кем-то? Может, мы кое-что затаили про себя, что следует немедленно обсудить с кем-либо? Проявляли ли мы любовь и доброту ко всем окружающим? Что мы могли бы сделать лучше? Может, в основном мы думаем только о себе? Или мы думали о том, что можем сделать для других, о нашем вкладе в общее течение жизни? Не нужно только поддаваться беспокойству, угрызениям совести или мрачным размышлениям, ибо в этом случае наши возможности приносить пользу другим уменьшаются. Вспомнив события прожитого дня, мы просим прощения у Бога и спрашиваем Его, как нам исправить наши ошибки.'

MAIN_REPKEY = [["🌞Утренний ритуал", "🌛Вечерний ритуал"], ["⏰ Напоминать мне утром", "⏰ Напоминать мне вечером"], ["📜 Как слушать Бога", "📜 Молитвы и медитации"]]
CONVERSATION_REPKEY = [["✅ Дальше", "❌ Отмена"]]
FILE_PATH = ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends explanation on how to use the bot."""
    await set_mybot_command(update, context, True)
    await update.message.reply_text("Привет, рад что ты выздоравливаешь! \nЧтобы пройти утренний ритуал используй команду /morning, для вечернего /evening. \nЕсли хочешь я буду напоминать о том что надо сделать 11 шаг. Используй /setmorningtime и /seteveningtime для установки времени напоминаний. \nУ тебя все получится! \nС Богом!", reply_markup=ReplyKeyboardMarkup(MAIN_REPKEY, resize_keyboard=True, one_time_keyboard=True))
    sched_reset(context=context)
    
MORNING1, MORNING2, MORNING3, MORNING_END = range(4)

async def morning_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Утренний ритуал начало"""
    await set_mybot_command(update, context, False)
    morning_is_done = context.chat_data.get('morning_is_done', False)
        
    if not morning_is_done:
        await update.message.reply_text('Доброе утро! Пора сделать утренний ритуал! Вот, для начала, молитва: ')
        await update.message.reply_text(MORNING_PRAY, reply_markup=ReplyKeyboardMarkup(CONVERSATION_REPKEY, resize_keyboard=True, input_field_placeholder="Дальше?"))
    else: 
        await update.message.reply_text('Ты уже сделал утренний ритуал. Хочешь повторить или хватит молитвы?')
        await update.message.reply_text(MORNING_PRAY, reply_markup=ReplyKeyboardMarkup([["Да", "Отмена"]], resize_keyboard=True, input_field_placeholder="Повторим утренний ритуал?"))
    
    return MORNING1

async def morning_1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Утренний ритуал 1"""
    await update.message.delete()
    await update.message.reply_text('Напиши чему или кому ты сейчас благодарен (когда закончишь перечислять, напиши или нажми "Дальше"):', reply_markup=ReplyKeyboardMarkup(CONVERSATION_REPKEY, resize_keyboard=True))
    return MORNING2

async def morning_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Утренний ритуал 2"""
    await update.message.delete()
    await update.message.reply_text('Что сделает этот день прекрасным? (Нажми "Дальше" когда закончишь)', reply_markup=ReplyKeyboardMarkup(CONVERSATION_REPKEY, resize_keyboard=True))
    return MORNING3

async def morning_3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Утренний ритуал 3"""
    await update.message.delete()
    await update.message.reply_text('Позитивная установка:', reply_markup=ReplyKeyboardMarkup(CONVERSATION_REPKEY, resize_keyboard=True, input_field_placeholder="Напиши себе позитивную установку на день."))
    return MORNING_END

async def morning_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Утренний ритуал завершение"""
    await set_mybot_command(update, context, True)
    context.chat_data['morning_is_done'] = True
    await update.message.reply_text('Отличная работа! Вероятно тебе стоит еще набрать спонсору, или другому выздоравливающему, чтобы обсудить пришедшие руководства.', reply_markup=ReplyKeyboardMarkup(MAIN_REPKEY, resize_keyboard=True))
    sched_reset(context)
    return ConversationHandler.END

EVENING1, EVENING2, EVENING3, EVENING_END = range(4)

async def evening_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вечерний ритуал начало"""
    await set_mybot_command(update, context, False)
    evening_is_done = context.chat_data.get('evening_is_done', False)
    
    if not evening_is_done:
        await update.message.reply_text('День прошел, пора сделать вечерний ритуал! Вот, для начала, молитва-размышление: ')
        await update.message.reply_text(EVENING_PRAY, reply_markup=ReplyKeyboardMarkup(CONVERSATION_REPKEY, resize_keyboard=True, input_field_placeholder="Дальше?"))
    else: 
        await update.message.reply_text('Ты уже сделал все на сегодня. Хочешь повторить вечерний ритуал или хватит молитвы?')
        await update.message.reply_text(EVENING_PRAY, reply_markup=ReplyKeyboardMarkup([["Да", "Отмена"]], resize_keyboard=True, input_field_placeholder="Повторим вечерний ритуал?"))
    
    return EVENING1

async def evening_1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вечерний ритуал 1"""
    await update.message.delete()
    await update.message.reply_text('За какие события этого дня ты благодарен? (когда закончишь перечислять жми "Дальше")', reply_markup=ReplyKeyboardMarkup(CONVERSATION_REPKEY, resize_keyboard=True))
    return EVENING2

async def evening_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вечерний ритуал 2"""
    await update.message.delete()
    await update.message.reply_text('Что я могу завтра сделать лучше? (когда закончишь перечислять жми "Дальше")', reply_markup=ReplyKeyboardMarkup(CONVERSATION_REPKEY, resize_keyboard=True))
    return EVENING3

async def evening_3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вечерний ритуал 3"""
    await update.message.delete()
    await update.message.reply_text('Кому я помог сегодня? (когда закончишь перечислять жми "Дальше")', reply_markup=ReplyKeyboardMarkup(CONVERSATION_REPKEY, resize_keyboard=True))
    return EVENING_END

async def evening_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вечерний ритуал завершение"""
    await set_mybot_command(update, context, True)
    morning_is_done = context.chat_data.get('morning_is_done', False)
    context.chat_data['evening_is_done'] = True
    await update.message.delete()
    reply_markup = ReplyKeyboardMarkup(MAIN_REPKEY, resize_keyboard=True, one_time_keyboard=True)
    message = 'Вы отлично поработали сегодня! Приятных снов!' if morning_is_done else 'Вы хорошо поработали сегодня! Завтра постарайтесь начать день с утреннего ритуала, день станет лучше, обещаю. Приятных снов!'
    await update.message.reply_text(message, reply_markup=reply_markup)
    sched_reset(context)
    return ConversationHandler.END

MORNING_REMINDER = range(1)

async def set_morning_time_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_mybot_command(update, context, False)
    reply_keyboard = [["06:00", "06:30", "07:00", "07:30"], ["08:00", "08:30", "09:00", "09:30"], ["10:00", "10:30", "11:00", "11:30"], ["12:00", "12:30", "13:00", "13:30"]]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text('В какое время ты обычно просыпаешься? Напиши время для утреннего напоминания в формате ЧЧ:MM', reply_markup=reply_markup)
    return MORNING_REMINDER
    
async def set_morning_time_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Установка утреннего напоминания начало"""
    await set_mybot_command(update, context, True)
    time_str = update.message.text
    hour, minute = map(int, time_str.split(':'))
    morning_reminder_time = convert_time_to_UTC(time(hour, minute));
    mychat_id = update.effective_message.chat_id
    context.job_queue.run_daily(send_morning_reminder, time=morning_reminder_time, chat_id=mychat_id)
    await update.message.reply_text(f'Напоминание об утреннем ритуале установлено на {time_str}', reply_markup = ReplyKeyboardMarkup(MAIN_REPKEY, resize_keyboard=True, one_time_keyboard=True))
    return ConversationHandler.END
        
async def send_morning_reminder(context: ContextTypes.DEFAULT_TYPE):
    if context.chat_data.get('morning_is_done', False) == False:
        await context.bot.send_message(context.job.chat_id, 'Пора сделать утренний ритуал! Жми на команду /morning!')  

EVENING_REMINDER = range(1)

async def set_evening_time_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_mybot_command(update, context, False)
    reply_keyboard = [["20:00", "20:15", "20:30", "20:45"], ["21:00", "21:15", "21:30", "21:45"], ["22:00", "22:15", "22:30", "22:45"], ["23:00", "23:15", "23:30", "23:45"]]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text('В какое время ты обычно ложишься спать? Напиши время для вечернего напоминания в формате ЧЧ:MM', reply_markup=reply_markup)
    return EVENING_REMINDER

async def set_evening_time_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Установка вечернего напоминания начало"""
    await set_mybot_command(update, context, True)
    time_str = update.message.text
    hour, minute = map(int, time_str.split(':'))
    evening_reminder_time = convert_time_to_UTC(time(hour, minute))
    mychat_id = update.effective_message.chat_id
    context.job_queue.run_daily(send_evening_reminder, time=evening_reminder_time, chat_id=mychat_id)
    await update.message.reply_text(f'Напоминание о вечернем ритуале установлено на {time_str}', reply_markup = ReplyKeyboardMarkup(MAIN_REPKEY, resize_keyboard=True, one_time_keyboard=True))
    return ConversationHandler.END

async def send_evening_reminder(context: ContextTypes.DEFAULT_TYPE):
    if context.chat_data.get('evening_is_done', False) == False:
        await context.bot.send_message(context.job.chat_id, 'Пора сделать вечерний ритуал! Жми на команду /evening!')
                       
async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Прервать ритуал"""
    await set_mybot_command(update, context, True)
    reply_markup = ReplyKeyboardMarkup(MAIN_REPKEY, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text('Конечно, вернемся к этому когда будешь готов.', reply_markup=reply_markup)
    return ConversationHandler.END

async def reset_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Прервать ритуал"""
    await set_mybot_command(update, context, True)
    reply_markup = ReplyKeyboardMarkup(MAIN_REPKEY, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text('Прости, я сбился, давай начнем с начала.', reply_markup=reply_markup)
    return ConversationHandler.END

def sched_reset(context: ContextTypes.DEFAULT_TYPE):
    context.job_queue.run_daily(reset_achivements, time=time.fromisoformat('03:00'))

def reset_achivements(context: ContextTypes.chat_data):
    context.chat_data['morning_is_done'] = False
    context.chat_data['evening_is_done'] = False

def convert_time_to_UTC(my_time: time) -> time:
    local_datetime = arrow.now()
    my_datetime = local_datetime.replace(hour=my_time.hour, minute=my_time.minute, second=0, microsecond=0)
    utc_datetime = my_datetime.to('UTC')
    return utc_datetime.time()

async def set_mybot_command(update: Update, context: ContextTypes.DEFAULT_TYPE, full: bool) -> None:
    if full:
        command_list = [BotCommand("morning","Утренний ритуал")
                        , BotCommand("evening", "Вечерний ритуал")
                        , BotCommand("setmorningtime", "Настроить напоминания об утреннем ритуале")
                        , BotCommand("seteveningtime", "Настроить напоминания о вечернем ритуале")
                        , BotCommand("help", "Помощь")]
    else:
        command_list = [BotCommand("next","Дальше")
                        , BotCommand("cancel", "Отмена")]
    scope = BotCommandScopeChat(chat_id = update.effective_message.chat_id)
    await context.bot.set_my_commands(command_list, scope)

async def send_file_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    files_path = context.bot_data['files_path']
    doc_name = update.message.text
    if doc_name == "Как слушать Бога":
        doc_path = f'{files_path}Как слушать Бога.pdf'
    elif doc_name == "Молитвы и медитации":
        doc_path = f'{files_path}Молитвы и медитации.pdf'
    else:
        return
    with open(doc_path, 'rb') as fh:
        content = fh.read()
        await update.message.reply_document(document=content, filename=f'{doc_name}.pdf')

def main() -> None:
    """Run bot."""
    load_dotenv()
    API_KEY = os.getenv('API_KEY_my_madhouse_bot')
    
    #API_KEY = '1479968532:AAEcVpbAajkHq8KIXGuTBHHsWJuwiRn1BSE'
    application = Application.builder().token(API_KEY).build()
    application.add_handler(CommandHandler(["start", "help"], start))
    application.add_handler(MessageHandler(filters.Regex('Как слушать Бога'), send_file_pdf))
    application.add_handler(MessageHandler(filters.Regex('Молитвы и медитации'), send_file_pdf))
    
    application.bot_data['files_path'] = os.getenv('FILES_PATH')
    
    conv_handler1 = ConversationHandler(entry_points=[CommandHandler("morning", morning_start), MessageHandler(filters.Regex('Утренний ритуал'), morning_start)],
        states={MORNING1: [MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.Regex('Отмена'), morning_1), CommandHandler(["next"], morning_1)],
            MORNING2: [MessageHandler(filters.Regex('Дальше'), morning_2), CommandHandler(["next"], morning_2)],
            MORNING3: [MessageHandler(filters.Regex('Дальше'), morning_3), CommandHandler(["next"], morning_3)],
            MORNING_END: [MessageHandler(filters.ALL & ~filters.COMMAND, morning_end), CommandHandler(["next"], morning_end)],
        },
        fallbacks = [CommandHandler('cancel', cancel_conv), MessageHandler(filters.Regex('Отмена'), cancel_conv), MessageHandler(filters.COMMAND & ~filters.Regex('cancel'), reset_conv)],
    )
    application.add_handler(conv_handler1)
    
    conv_handler2 = ConversationHandler(entry_points=[CommandHandler("evening", evening_start), MessageHandler(filters.Regex('Вечерний ритуал'), evening_start)],
        states={EVENING1: [MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.Regex('Отмена'), evening_1), CommandHandler(["next"], evening_1)],
            EVENING2: [MessageHandler(filters.Regex('Дальше'), evening_2), CommandHandler(["next"], evening_2)],
            EVENING3: [MessageHandler(filters.Regex('Дальше'), evening_3), CommandHandler(["next"], evening_3)],
            EVENING_END: [MessageHandler(filters.Regex('Дальше'), evening_end), CommandHandler(["next"], evening_end)],
        },
        fallbacks = [CommandHandler('cancel', cancel_conv), MessageHandler(filters.Regex('Отмена'), cancel_conv), MessageHandler(filters.COMMAND & ~filters.Regex('cancel'), reset_conv)],
    )
    application.add_handler(conv_handler2)
    
    conv_handler3 = ConversationHandler(entry_points=[CommandHandler("setmorningtime", set_morning_time_start), MessageHandler(filters.Regex('Напоминать мне утром'), set_morning_time_start)],
        states={MORNING_REMINDER: [MessageHandler(filters.Regex(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'), set_morning_time_end)],
        },
        fallbacks = [CommandHandler('cancel', cancel_conv), MessageHandler(filters.Regex('Отмена'), cancel_conv), MessageHandler(filters.COMMAND & ~filters.Regex('cancel'), reset_conv)],
    )
    application.add_handler(conv_handler3)
    
    conv_handler4 = ConversationHandler(entry_points=[CommandHandler("seteveningtime", set_evening_time_start), MessageHandler(filters.Regex('Напоминать мне вечером'), set_evening_time_start)],
        states={EVENING_REMINDER: [MessageHandler(filters.Regex(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'), set_evening_time_end)],
        },
        fallbacks = [CommandHandler('cancel', cancel_conv), MessageHandler(filters.Regex('Отмена'), cancel_conv), MessageHandler(filters.COMMAND & ~filters.Regex('cancel'), reset_conv)],
    )
    application.add_handler(conv_handler4)
     
    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()
