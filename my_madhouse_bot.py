#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to send timed Telegram messages.

This Bot uses the Application class to handle the bot and the JobQueue to send
timed messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Alarm Bot example, sends a message after a set time.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.

Note:
To use the JobQueue, you must install PTB via
`pip install python-telegram-bot[job-queue]`
"""

import logging
import threading
import time

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
reminders = {}
morning_is_done = False
evening_is_done = False
morning_reminder_time = '00:00'
evening_reminder_time = '00:00'

MORNING_PRAY = 'Боже направь мои мысли в верное русло, \nОсобенно избавь меня от жалости к себе, \nБесчестных поступков, корыстолюбия. \nПокажи мне в течение всего дня, \nКаким должен быть мой следующий шаг. \nДай мне все, что необходимо для решения проблем. \nИзбавь меня от эгоизма. \nЯ не руковожу своей жизнью. \nДа исполняю я волю Твою.'
EVENING_PRAY = 'Когда мы ложимся спать, мы конструктивно оцениваем прожитый день. Не были ли мы в течение дня наполненными resentment-ом, эгоистичными или нечестными, может, мы испытывали страх? Или должны извиниться перед кем-то? Может, мы кое-что затаили про себя, что следует немедленно обсудить с кем-либо? Проявляли ли мы любовь и доброту ко всем окружающим? Что мы могли бы сделать лучше? Может, в основном мы думаем только о себе? Или мы думали о том, что можем сделать для других, о нашем вкладе в общее течение жизни? Не нужно только поддаваться беспокойству, угрызениям совести или мрачным размышлениям, ибо в этом случае наши возможности приносить пользу другим уменьшаются. Вспомнив события прожитого дня, мы просим прощения у Бога и спрашиваем Его, как нам исправить наши ошибки.'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends explanation on how to use the bot."""
    await update.message.reply_text("Привет, рад что ты выздоравливаешь! \nЧтобы пройти утренний ритуал используй команду /morning, для вечернего /evening. \nЕсли хочешь я буду напоминать о том что надо сделать 11 шаг. Используй /setmorningtime и /seteveningtime для установки времени напоминаний. \nУ тебя все получится! \nС Богом!")

MORNING1, MORNING2, MORNING3, MORNING_END = range(4)

async def morning_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Утренний ритуал начало"""
    global morning_is_done
    context.user_data['str_remain'] = 3
    if not morning_is_done:
        reply_keyboard = [["Дальше", "/Cancel"]]
        await update.message.reply_text('Доброе утро! Пора сделать утренний ритуал! Вот, для начала, молитва: ')
        await update.message.reply_text(MORNING_PRAY, reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Дальше?"))
    else:
        reply_keyboard = [["Да", "/Cancel"], []] 
        await update.message.reply_text('Ты уже сделал утренний ритуал. Хочешь повторить или хватит молитвы?')
        await update.message.reply_text(MORNING_PRAY, reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Повторим утренний ритуал?"))
    return MORNING1

async def morning_1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Утренний ритуал 1"""
    str_remain = context.user_data['str_remain']
    if str_remain == 3: 
        str_remain = 2
        await update.message.reply_text('Напиши 3 благодарности:', reply_markup=ReplyKeyboardRemove())
        context.user_data['str_remain'] = str_remain
        return MORNING1
    else:
        if str_remain == 2:
            str_remain = 1
            bot_message = await update.message.reply_text('Еще 2...')
            context.user_data['bot_message'] = bot_message
            context.user_data['str_remain'] = str_remain
            return MORNING1
        else:
            if str_remain == 1:
                str_remain = 0
                bot_message = context.user_data['bot_message']
                await bot_message.delete()
                bot_message = await context.user_data['bot_message'].reply_text('Еще всего одну...')
                context.user_data['bot_message'] = bot_message
                context.user_data['str_remain'] = str_remain
                return MORNING1
            else:
                bot_message = context.user_data['bot_message']
                await bot_message.delete()
                return MORNING2

async def morning_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Утренний ритуал 2"""
    reply_keyboard = [["Да", "/Cancel"], []]
    await update.message.reply_text('Что сделает этот день прекрасным?')
    return MORNING3

async def morning_3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Утренний ритуал 3"""
    await update.message.reply_text('Позитивная установка:')
    return MORNING_END

async def morning_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Утренний ритуал завершение"""
    global morning_is_done
    morning_is_done = True
    await update.message.reply_text('Отличная работа! Вероятно тебе стоит еще набрать спонсору, или другому выздоравливающему, чтобы обсудить пришедшие руководства.')
    return ConversationHandler.END

EVENING1, EVENING2, EVENING3, EVENING_END = range(4)

async def evening_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вечерний ритуал начало"""
    global evening_is_done
    if not evening_is_done:
        reply_keyboard = [["Дальше", "/Cancel"]]
        await update.message.reply_text('День прошел, пора сделать вечерний ритуал! Вот, для начала, молитва-размышление: ')
        await update.message.reply_text(EVENING_PRAY, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True, input_field_placeholder="Дальше?"))
    else:
        reply_keyboard = [["Да", "/Cancel"]] 
        await update.message.reply_text('Ты уже сделал все на сегодня. Хочешь повторить вечерний ритуал или хватит молитвы?')
        await update.message.reply_text(EVENING_PRAY, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True, input_field_placeholder="Повторим вечерний ритуал?"))
    return EVENING1

async def evening_1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вечерний ритуал 1"""
    await update.message.reply_text('За какие 3 события этого дня ты благодарен?', reply_markup=ReplyKeyboardRemove())
    return EVENING2

async def evening_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вечерний ритуал 2"""
    await update.message.reply_text('Что я могу завтра сделать лучше?')
    return EVENING3

async def evening_3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вечерний ритуал 3"""
    await update.message.reply_text('Кому я помог сегодня?')
    return EVENING_END

async def evening_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вечерний ритуал завершение"""
    global morning_is_done, evening_is_done
    evening_is_done = True
    if morning_is_done == True:
        await update.message.reply_text('Вы отлично поработали сегодня! Приятных снов!')
    else:
        await update.message.reply_text('Вы хорошо поработали сегодня! Завтра постарайтесь начать день с утреннего ритуала, день станет лучше, обещаю. Приятных снов!')
    return ConversationHandler.END

MORNING_REMINDER = range(1)
async def set_morning_time_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    await update.message.reply_text('В какое время ты обычно просыпаешься? Напиши время для утреннего напоминания в формате ЧЧ:MM')
    
    return MORNING_REMINDER
    
async def set_morning_time_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Установка утреннего напоминания начало"""
    global morning_reminder_time
    morning_reminder_time = update.message.text
    await update.message.reply_text(f'Напоминание о утреннем ритуале установлено на {morning_reminder_time}')
    threading.Thread(target=send_morning_reminder, args=(update,context)).start()
    return ConversationHandler.END

async def send_morning_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global morning_is_done
    global morning_reminder_time
    
    # Continuously send reminders every day at the specified time
    while True:
        # Get the current time
        current_time = time.strftime('%H:%M')

        # If the current time matches the reminder time, send a reminder to the user
        if current_time == morning_reminder_time:
            if morning_is_done == False: 
                await update.message.reply_text('Пора сделать утренний ритуал! Жми на команду /morning!') 
            
        if morning_reminder_time == '00:00':
            break

        # Wait for 1 day before checking the time again
        time.sleep(86400)

EVENING_REMINDER = range(1)
async def set_evening_time_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    await update.message.reply_text('В какое время ты обычно ложишься спать? Напиши время для вечернего напоминания в формате ЧЧ:MM')
    
    return EVENING_REMINDER

async def set_evening_time_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Установка утреннего напоминания начало"""
    global evening_reminder_time
    evening_reminder_time = update.message.text
    await update.message.reply_text(f'Напоминание о вечернем ритуале установлено на {evening_reminder_time}')
    threading.Thread(target=send_evening_reminder, args=(update,context)).start()
    return ConversationHandler.END

# Define the send_reminders function
async def send_evening_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global evening_is_done
    global evening_reminder_time
    
    # Continuously send reminders every day at the specified time
    while True:
        # Get the current time
        current_time = time.strftime('%H:%M')

        # If the current time matches the reminder time, send a reminder to the user
        if current_time == evening_reminder_time:
            if evening_is_done == False:
                await update.message.reply_text('Пора сделать вечерний ритуал! Жми на команду /evening!') 
        if evening_reminder_time == '00:00':
            break
        
        # Wait for 1 day before checking the time again
        time.sleep(86400)
                       
async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Прервать ритуал"""
    await update.message.reply_text('Конечно, вернемся к этому когда будешь готов.')
    return ConversationHandler.END

def set_reminders():
    global morning_is_done, evening_is_done
    while True:
        current_time = time.strftime('%H:%M')

        if current_time == '00:00':
            morning_is_done = False
            evening_is_done = False

        # Wait for one day
        time.sleep(86400)

def main() -> None:
    """Run bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("6140800415:AAF97xZHjlc7905a8dk67RIjTypTmPIILFo").build()
    #testbot
    #application = Application.builder().token("1479968532:AAEcVpbAajkHq8KIXGuTBHHsWJuwiRn1BSE").build()
    
    # on different commands - answer in Telegram
    application.add_handler(CommandHandler(["start", "help"], start))
    
    conv_handler = ConversationHandler(entry_points=[CommandHandler("evening", evening_start)],
        states={EVENING1: [MessageHandler(filters.ALL & ~filters.COMMAND, evening_1)],
            EVENING2: [MessageHandler(filters.ALL & ~filters.COMMAND, evening_2)],
            EVENING3: [MessageHandler(filters.ALL & ~filters.COMMAND, evening_3)],
            EVENING_END: [MessageHandler(filters.ALL & ~filters.COMMAND, evening_end)],
        },
        fallbacks = [CommandHandler('cancel', cancel_conv)],
    )
    application.add_handler(conv_handler)
    
    conv_handler = ConversationHandler(entry_points=[CommandHandler("morning", morning_start)],
        states={MORNING1: [MessageHandler(filters.ALL & ~filters.COMMAND, morning_1)],
            MORNING2: [MessageHandler(filters.ALL & ~filters.COMMAND, morning_2)],
            MORNING3: [MessageHandler(filters.ALL & ~filters.COMMAND, morning_3)],
            MORNING_END: [MessageHandler(filters.ALL & ~filters.COMMAND, morning_end)],
        },
        fallbacks = [CommandHandler('cancel', cancel_conv)],
    )
    application.add_handler(conv_handler)
    
    conv_handler = ConversationHandler(entry_points=[CommandHandler("setmorningtime", set_morning_time_start)],
        states={MORNING_REMINDER: [MessageHandler(filters.Regex(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'), set_morning_time_end)],
        },
        fallbacks = [CommandHandler('cancel', cancel_conv)],
    )
    application.add_handler(conv_handler)
    
    conv_handler = ConversationHandler(entry_points=[CommandHandler("seteveningtime", set_evening_time_start)],
        states={MORNING_REMINDER: [MessageHandler(filters.Regex(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'), set_evening_time_end)],
        },
        fallbacks = [CommandHandler('cancel', cancel_conv)],
    )
    application.add_handler(conv_handler)
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling()

    # Start the thread to set the reminders
    threading.Thread(target=set_reminders).start()

if __name__ == "__main__":
    main()
