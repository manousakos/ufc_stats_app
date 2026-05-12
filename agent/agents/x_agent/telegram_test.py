import os
from dotenv import load_dotenv
import logging
from telegram import Update, Message
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

import x_agent

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    responseMD:str = ''
    try:
        responseMD = await x_agent.x_agent()
        if responseMD == None:
            raise Exception("Something went wrong with the agent...")
    except Exception as e:
        
        if not update.message.direct_messages_topic:       # if this was posted in a thread or topic , post it there too
            await context.bot.send_message(
                chat_id = update.effective_chat.id,
                text = "Sorry , something went wrong with the agent...",
                parse_mode= 'Markdown'
            )
        else :
            await context.bot.send_message(
                chat_id = update.effective_chat.id,
                text = "Sorry , something went wrong with the agent...",
                message_thread_id = update.message.reply_to_message.message_thread_id,
                parse_mode= 'Markdown'
            )
    
    if not update.message.direct_messages_topic:       # if this was posted in a thread or topic , post it there too
        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = responseMD,
            parse_mode= 'Markdown'
        )
    else :
        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = responseMD,
            parse_mode= 'Markdown',
            message_thread_id = update.message.reply_to_message.message_thread_id,
        )
    return




if __name__ == '__main__':
    application = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN") or "").build()
    
    report_handler = CommandHandler('report', report)
    application.add_handler(report_handler)
    
    application.run_polling()
