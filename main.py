#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.


import logging

from config import TOKEN
from telegram import ForceReply, Update, ChatMember, ChatMemberUpdated, Chat
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ChatMemberHandler
from telegram.constants import ParseMode
import my_settings
from gspread import Client, Spreadsheet, Worksheet, service_account
from pprint import pprint

Free_role_table = 'https://docs.google.com/spreadsheets/d/11M0r6ESBKx8hUAbzW3v-nwOHkgnl1P_BZ5xY1Kamifo'
Role_table = 'https://docs.google.com/spreadsheets/d/1qP4VMj3eulrNbliMxCH6XBB4NRc_3CtX2OeTMU_4f5w'


def client_init_json() -> Client:
    """Создание клиента для работы с Google Sheets."""
    return service_account(filename='seventh-seeker-155512-e0151e7aeedf.json')


def get_table_by_url(client: Client, table_url):
    """Получение таблицы из Google Sheets по ссылке."""
    return client.open_by_url(table_url)


my_client = client_init_json()
danil_table = get_table_by_url(my_client, Free_role_table)
role_table = get_table_by_url(my_client, Role_table)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.

def extract_status_change(chat_member_update: ChatMemberUpdated) -> tuple[bool, bool] | None:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    print(chat_member_update)
    status_change = chat_member_update.difference().get("status")
    print(chat_member_update.difference().get("status"))
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member


async def start_private_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Greets the user and records that they started a chat with the bot if it's a private chat.
    Since no `my_chat_member` update is issued when a user starts a private chat with the bot
    for the first time, we have to track it explicitly here.
    """
    user_name = update.effective_user.full_name
    chat = update.effective_chat
    if chat.type != Chat.PRIVATE or chat.id in context.bot_data.get("user_ids", set()):
        return

    logger.info("%s started a private chat with the bot", user_name)
    context.bot_data.setdefault("user_ids", set()).add(chat.id)

    await update.effective_message.reply_text(
        f"Welcome {user_name}. Use /show_chats to see what chats I'm in."
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def show_chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows which chats the bot is in"""
    user_ids = ", ".join(str(uid) for uid in context.bot_data.setdefault("user_ids", set()))
    group_ids = ", ".join(str(gid) for gid in context.bot_data.setdefault("group_ids", set()))
    channel_ids = ", ".join(str(cid) for cid in context.bot_data.setdefault("channel_ids", set()))
    text = (
        f"@{context.bot.username} is currently in a conversation with the user IDs {user_ids}."
        f" Moreover it is a member of the groups with IDs {group_ids} "
        f"and administrator in the channels with IDs {channel_ids}."
    )
    await update.effective_message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.text:
        answer = ''
        print(update.message.text.lower())
        if '!правила' in update.message.text.lower():
            answer += my_settings.RULES
        elif '!законы' in update.message.text.lower():
            answer += my_settings.BILLS
        elif '!свободныероли' in update.message.text.lower():
            rows = danil_table.worksheet('Лист1').get_all_values()
            rows = '\n'.join([i[0] for i in rows])
            answer += rows
        elif '!олигархи' in update.message.text.lower():
            answer += my_settings.OLIGARCH
        elif any(i in update.message.text.lower() for i in ['!хэлп', '!хелп', '!help']):
            answer += my_settings.HELP
        elif '!император' in update.message.text.lower():
            answer += my_settings.EMPEROR
        elif '!tasks' in update.message.text.lower():
            answer += my_settings.TASKS
        elif '!актуальныероли' in update.message.text.lower():
            rows = role_table.worksheet('Лист1').get_all_values()
            roleDict = {i[0].strip('@'): [i[1].strip('@')] + i[2:][0].split('\n') for i in rows[1:]}
            s = '\n'.join(f'{k} {v[0]}: {", ".join(v[1:])}' for k, v in roleDict.items())
            answer += s
        elif 'рабств' in update.message.text.lower():
            answer += 'Мы верные псы нашего Президента!'
        if 'рабовл' in update.message.text.lower():
            answer += 'Мы верные псы нашего Президента!'
        if 'тот чат' in update.message.text.lower():
            answer += 'Вы этой шуткой даже меня заебали'
        if 'самый крутой тип' in update.message.text.lower():
            answer += '@IlyaBovyka'
        if '!роль' in update.message.text.lower():
            rows = role_table.worksheet('Лист1').get_all_values()
            roleDict = {i[0].strip('@'): [i[1].strip('@')] + i[2:][0].split('\n') for i in rows[2:]}
            pprint(roleDict)
            roleDict['sachaperkow'] = ['sachaperkow', 'Мастер', 'Змей-искуситель', 'Вносящий хаос и раздор', 'Банкомат']
            roleDict['Wkkk1'].extend(['Гений', 'Миллиардер', 'Плейбой', 'Филантроп'])
            d = update.message.text.lower().find('!роль')
            if d != -1:
                subreq = update.message.text[d + len('!роль'):].split()[0].strip('@')
                for k, v in roleDict.items():
                    if subreq in v[0]:
                        subreq = k
                        break
                if subreq.lower() in [i.lower() for i in roleDict.keys()]:
                    roles = '\n'.join(roleDict[subreq][1:])
                    answer += f'Игрок {subreq}\nНик на Пикабу: {roleDict[subreq][0] if roleDict[subreq][0] else "Нету"}\n{roles}'
                else:
                    answer += 'Нет такого игрока'
            else:
                answer += 'Нет такого игрока'

        if any(i in update.message.text.lower() for i in ['мастер', 'гм', 'ведущ']):
            answer += 'Бог ещё с нами'
        if any(i in update.message.text.lower() for i in ['революц', 'переворот', 'свержение']):
            answer += 'Совет Пяти напоминает, что за это действие можно получить срок'
        if any(i in update.message.text.lower() for i in ['добр', 'привет']) and 'лена' in update.message.text.lower():
            user = update.effective_user
            answer += rf"И тебе привет, {user.mention_html()})"
        if my_settings.SPAM:
            answer += f'''\n ------------------------------------------------------
            Минутка рекламы\n{my_settings.SPAM}'''
        await update.message.reply_text(answer)


async def greet_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Greets new users in chats and announces when someone leaves"""
    result = extract_status_change(update.chat_member)
    print(f'result : {result}')
    if result is None:
        return

    was_member, is_member = result
    cause_name = update.chat_member.from_user.mention_html()
    member_name = update.chat_member.new_chat_member.user.mention_html()

    if not was_member and is_member:
        await update.effective_chat.send_message(
            my_settings.GREET,
            parse_mode=ParseMode.HTML,
        )
    elif was_member and not is_member:
        await update.effective_chat.send_message(
            my_settings.LEAVE,
            parse_mode=ParseMode.HTML,
        )


async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tracks the chats the bot is in."""
    result = extract_status_change(update.my_chat_member)
    if result is None:
        return
    was_member, is_member = result

    # Let's check who is responsible for the change
    cause_name = update.effective_user.full_name

    # Handle chat types differently:
    chat = update.effective_chat
    if chat.type == Chat.PRIVATE:
        if not was_member and is_member:
            # This may not be really needed in practice because most clients will automatically
            # send a /start command after the user unblocks the bot, and start_private_chat()
            # will add the user to "user_ids".
            # We're including this here for the sake of the example.
            logger.info("%s unblocked the bot", cause_name)
            context.bot_data.setdefault("user_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s blocked the bot", cause_name)
            context.bot_data.setdefault("user_ids", set()).discard(chat.id)
    elif chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if not was_member and is_member:
            logger.info("%s added the bot to the group %s", cause_name, chat.title)
            context.bot_data.setdefault("group_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s removed the bot from the group %s", cause_name, chat.title)
            context.bot_data.setdefault("group_ids", set()).discard(chat.id)
    elif not was_member and is_member:
        logger.info("%s added the bot to the channel %s", cause_name, chat.title)
        context.bot_data.setdefault("channel_ids", set()).add(chat.id)
    elif was_member and not is_member:
        logger.info("%s removed the bot from the channel %s", cause_name, chat.title)
        context.bot_data.setdefault("channel_ids", set()).discard(chat.id)


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.

    application = Application.builder().token(TOKEN).build()
    # application.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))
    # application.add_handler(CommandHandler("show_chats", show_chats))
    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram

    application.add_handler(ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
