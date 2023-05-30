#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position

from dotenv import load_dotenv
import os

import logging
import threading
import schedule, time

from telegram import __version__ as TG_VER

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
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, filters, MessageHandler

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Define the reminders dictionary

MORNING_PRAY = 'Боже направь мои мысли в верное русло, \nОсобенно избавь меня от жалости к себе, \nБесчестных поступков, корыстолюбия. \nПокажи мне в течение всего дня, \nКаким должен быть мой следующий шаг. \nДай мне все, что необходимо для решения проблем. \nИзбавь меня от эгоизма. \nЯ не руковожу своей жизнью. \nДа исполняю я волю Твою.'
EVENING_PRAY = 'Когда мы ложимся спать, мы конструктивно оцениваем прожитый день. Не были ли мы в течение дня наполненными resentment-ом, эгоистичными или нечестными, может, мы испытывали страх? Или должны извиниться перед кем-то? Может, мы кое-что затаили про себя, что следует немедленно обсудить с кем-либо? Проявляли ли мы любовь и доброту ко всем окружающим? Что мы могли бы сделать лучше? Может, в основном мы думаем только о себе? Или мы думали о том, что можем сделать для других, о нашем вкладе в общее течение жизни? Не нужно только поддаваться беспокойству, угрызениям совести или мрачным размышлениям, ибо в этом случае наши возможности приносить пользу другим уменьшаются. Вспомнив события прожитого дня, мы просим прощения у Бога и спрашиваем Его, как нам исправить наши ошибки.'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends explanation on how to use the bot."""
    
    reply_keyboard = [["/morning", "/evening"], ["/setmorningtime", "/seteveningtime"]]
    await update.message.reply_text("Привет, рад что ты выздоравливаешь! \nЧтобы пройти утренний ритуал используй команду /morning, для вечернего /evening. \nЕсли хочешь я буду напоминать о том что надо сделать 11 шаг. Используй /setmorningtime и /seteveningtime для установки времени напоминаний. \nУ тебя все получится! \nС Богом!", reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True))
    sched_reset(context=context)
    
MORNING1, MORNING2, MORNING3, MORNING_END = range(4)

async def morning_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Утренний ритуал начало"""
    if 'morning_is_done' in context.chat_data:
        morning_is_done = context.chat_data['morning_is_done']
    else:
        morning_is_done = False
        context.chat_data['morning_is_done'] = morning_is_done
        
    if not morning_is_done:
        reply_keyboard = [["Дальше", "/Cancel"]]
        await update.message.reply_text('Доброе утро! Пора сделать утренний ритуал! Вот, для начала, молитва: ')
        await update.message.reply_text(MORNING_PRAY, reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, input_field_placeholder="Дальше?"))
    else:
        reply_keyboard = [["Да >", "/Cancel"], []] 
        await update.message.reply_text('Ты уже сделал утренний ритуал. Хочешь повторить или хватит молитвы?')
        await update.message.reply_text(MORNING_PRAY, reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, input_field_placeholder="Повторим утренний ритуал?"))
    return MORNING1

async def morning_1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Утренний ритуал 1"""
    await update.message.delete()
    reply_keyboard = [["Дальше", "/Cancel"]]
    await update.message.reply_text('Напиши чему или кому ты сейчас благодарен (когда закончишь перечислять, напиши или нажми "Дальше"):', reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True))
    return MORNING2

async def morning_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.delete()
    reply_keyboard = [["Дальше", "/Cancel"]]
    await update.message.reply_text('Что сделает этот день прекрасным? (Нажми "Дальше" когда закончишь)', reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return MORNING3

async def morning_3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Утренний ритуал 3"""
    await update.message.delete()
    await update.message.reply_text('Позитивная установка:', reply_markup = ReplyKeyboardRemove())
    return MORNING_END

async def morning_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Утренний ритуал завершение"""
    context.chat_data['morning_is_done'] = True
    reply_keyboard = [["/morning", "/evening"], ["/setmorningtime", "/seteveningtime"]]
    await update.message.reply_text('Отличная работа! Вероятно тебе стоит еще набрать спонсору, или другому выздоравливающему, чтобы обсудить пришедшие руководства.', reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True))
    sched_reset()
    return ConversationHandler.END

EVENING1, EVENING2, EVENING3, EVENING_END = range(4)

async def evening_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вечерний ритуал начало"""
    if 'evening_is_done' in context.chat_data:
        evening_is_done = context.chat_data['evening_is_done']
    else:
        evening_is_done = False
        context.chat_data['evening_is_done'] = evening_is_done
    
    if not evening_is_done:
        reply_keyboard = [["Дальше", "/Cancel"]]
        await update.message.reply_text('День прошел, пора сделать вечерний ритуал! Вот, для начала, молитва-размышление: ')
        await update.message.reply_text(EVENING_PRAY, reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, input_field_placeholder="Дальше?"))
    else:
        reply_keyboard = [["Да", "/Cancel"]] 
        await update.message.reply_text('Ты уже сделал все на сегодня. Хочешь повторить вечерний ритуал или хватит молитвы?')
        await update.message.reply_text(EVENING_PRAY, reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, input_field_placeholder="Повторим вечерний ритуал?"))
    return EVENING1

async def evening_1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вечерний ритуал 1"""
    await update.message.delete()
    reply_keyboard = [["Дальше", "/Cancel"]]
    await update.message.reply_text('За какие события этого дня ты благодарен? (когда закончишь перечислять жми "Дальше")', reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True))
    return EVENING2

async def evening_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вечерний ритуал 2"""
    await update.message.delete()
    reply_keyboard = [["Дальше", "/Cancel"]]
    await update.message.reply_text('Что я могу завтра сделать лучше? (когда закончишь перечислять жми "Дальше")', reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True))
    return EVENING3

async def evening_3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вечерний ритуал 3"""
    await update.message.delete()
    reply_keyboard = [["Дальше", "/Cancel"]]
    await update.message.reply_text('Кому я помог сегодня? (когда закончишь перечислять жми "Дальше")', reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True))
    return EVENING_END

async def evening_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вечерний ритуал завершение"""
    if 'morning_is_done' in context.chat_data:
        morning_is_done = context.chat_data['morning_is_done']
    else:
        morning_is_done = False
        context.chat_data['morning_is_done'] = morning_is_done
        
    context.chat_data['evening_is_done'] = True
    await update.message.delete()
    reply_keyboard = [["/morning", "/evening"], ["/setmorningtime", "/seteveningtime"]]
    reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    if morning_is_done == True:
        await update.message.reply_text('Вы отлично поработали сегодня! Приятных снов!', reply_markup = reply_markup)
    else:
        await update.message.reply_text('Вы хорошо поработали сегодня! Завтра постарайтесь начать день с утреннего ритуала, день станет лучше, обещаю. Приятных снов!', reply_markup = reply_markup)
    sched_reset(context=context)
    return ConversationHandler.END

MORNING_REMINDER = range(1)
async def set_morning_time_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    await update.message.reply_text('В какое время ты обычно просыпаешься? Напиши время для утреннего напоминания в формате ЧЧ:MM')
    
    return MORNING_REMINDER
    
async def set_morning_time_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Установка утреннего напоминания начало"""
    
    morning_reminder_time = update.message.text
    if morning_reminder_time != '00:00':
        schedule.every().day.at(morning_reminder_time).do(send_morning_reminder, update, context).tag('morning_reminder')
        context.user_data['morning_reminder_job'] = run_continuously(target=send_morning_reminder, args=(update, context))
        await update.message.reply_text(f'Напоминание о утреннем ритуале установлено на {morning_reminder_time}')
    else:
        if 'morning_reminder_job' in context.user_data:
            context.user_data['morning_reminder_job'].set()
        await update.message.reply_text('Напоминание о утреннем ритуале отключено')
    
    return ConversationHandler.END
        
def send_morning_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'morning_is_done' in context.chat_data:
        if context.chat_data['morning_is_done'] == False:
            update.message.reply_text('Пора сделать утренний ритуал! Жми на команду /morning!')    

EVENING_REMINDER = range(1)

async def set_evening_time_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text('В какое время ты обычно ложишься спать? Напиши время для вечернего напоминания в формате ЧЧ:MM')
    
    return EVENING_REMINDER

async def set_evening_time_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Установка вечернего напоминания начало"""
    
    evening_reminder_time = update.message.text
    if evening_reminder_time != '00:00':
        schedule.every().day.at(evening_reminder_time).do(send_evening_reminder, update, context).tag('evening_reminder')
        context.user_data['evening_reminder_job'] = run_continuously(target=send_evening_reminder, args=(update, context))
        await update.message.reply_text(f'Напоминание о вечернем ритуале установлено на {evening_reminder_time}')
    else:
        if 'evening_reminder_job' in context.user_data:
            context.user_data['evening_reminder_job'].set()
        await update.message.reply_text('Напоминание о вечернем ритуале отключено')
        
    return ConversationHandler.END

def send_evening_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'evening_is_done' in context.chat_data:
        if context.chat_data['evening_is_done'] == False:
            update.message.reply_text('Пора сделать вечерний ритуал! Жми на команду /evening!') 
                       
async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Прервать ритуал"""
    await update.message.reply_text('Конечно, вернемся к этому когда будешь готов.')
    return ConversationHandler.END

def sched_reset(context: ContextTypes.chat_data):
    reset_achivements_jobs = schedule.get_jobs('reset_achivements')
    if reset_achivements_jobs.count == 0:
        schedule.every().day.at("00:00").do(reset_achivements, context=context).tag('reset_achivements')
        run_continuously(target=reset_achivements, args=(context))

def reset_achivements(context: ContextTypes.chat_data):
    context.chat_data['morning_is_done'] = False
    context.chat_data['evening_is_done'] = False

def run_continuously(interval=1, target = None, args = None):
        cease_continuous_run = threading.Event()

        class ScheduleThread(threading.Thread):
            @classmethod
            def run(cls):
                while not cease_continuous_run.is_set():
                    schedule.run_pending()
                    time.sleep(interval)

        continuous_thread = ScheduleThread(target=target, args=args)
        continuous_thread.start()
        return cease_continuous_run

def main() -> None:
    """Run bot."""
    
    load_dotenv()
    API_KEY = os.getenv('API_KEY_my_madhouse_bot')
    
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(API_KEY).build()
    
    # on different commands - answer in Telegram
    application.add_handler(CommandHandler(["start", "help"], start))
    
    conv_handler1 = ConversationHandler(entry_points=[CommandHandler("morning", morning_start)],
        states={MORNING1: [MessageHandler(filters.ALL & ~filters.COMMAND, morning_1)],
            MORNING2: [MessageHandler(filters.Regex('Дальше'), morning_2)],
            MORNING3: [MessageHandler(filters.Regex('Дальше'), morning_3)],
            MORNING_END: [MessageHandler(filters.ALL & ~filters.COMMAND, morning_end)],
        },
        fallbacks = [CommandHandler('cancel', cancel_conv)],
    )
    application.add_handler(conv_handler1)
    
    conv_handler2 = ConversationHandler(entry_points=[CommandHandler("evening", evening_start)],
        states={EVENING1: [MessageHandler(filters.ALL & ~filters.COMMAND, evening_1)],
            EVENING2: [MessageHandler(filters.Regex('Дальше'), evening_2)],
            EVENING3: [MessageHandler(filters.Regex('Дальше'), evening_3)],
            EVENING_END: [MessageHandler(filters.Regex('Дальше'), evening_end)],
        },
        fallbacks = [CommandHandler('cancel', cancel_conv)],
    )
    application.add_handler(conv_handler2)
    
    conv_handler3 = ConversationHandler(entry_points=[CommandHandler("setmorningtime", set_morning_time_start)],
        states={MORNING_REMINDER: [MessageHandler(filters.Regex(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'), set_morning_time_end)],
        },
        fallbacks = [CommandHandler('cancel', cancel_conv)],
    )
    application.add_handler(conv_handler3)
    
    conv_handler4 = ConversationHandler(entry_points=[CommandHandler("seteveningtime", set_evening_time_start)],
        states={EVENING_REMINDER: [MessageHandler(filters.Regex(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'), set_evening_time_end)],
        },
        fallbacks = [CommandHandler('cancel', cancel_conv)],
    )
    application.add_handler(conv_handler4)
     
    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()
