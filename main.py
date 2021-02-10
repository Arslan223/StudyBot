from keys import TOKEN
from dateutil import tz as timezone
from datetime import datetime
import telebot
import gdata


class ChannelLinkError(Exception):
    def __init__(self):
        self.txt = "Нет ссылки на канал"


bot = telebot.TeleBot(TOKEN)
bot_id = "the_combot"

Markup = telebot.types.InlineKeyboardMarkup
Button = telebot.types.InlineKeyboardButton

time_stamp = "%H:%M %d.%m.%Y"
tm = "%M"
th = "%H"
td = "%d"

content_types = ['text', 'audio', 'document', 'photo', 'sticker',
                 'video', 'video_note', 'voice', 'location', 'contact',
                 'new_chat_members', 'left_chat_member', 'new_chat_title',
                 'new_chat_photo', 'delete_chat_photo', 'group_chat_created',
                 'supergroup_chat_created', 'channel_chat_created',
                 'migrate_to_chat_id', 'migrate_from_chat_id', 'pinned_message']
group_template = {
    "vote_limit": 6,
    "users": {},
    "channel": None
}
user_in_group_template = {
    "punish": False,
    "tasks": {}
}
group_types = ["group", "supergroup"]


def now_time(t_zone=0):
    return datetime.now(tz=timezone.gettz(f"UTC+{str(3 + t_zone)}"))


def decorate_channel_link(group_id: str):
    data = gdata.load()
    channel_name = data["groups"][group_id]["channel"]
    if not channel_name:
        raise ChannelLinkError
    else:
        return f"t.me/{channel_name}"


def pre_update(group_id: str, user_id: str):
    data = gdata.load()

    global group_template

    if not(group_id in data["groups"]):
        data["groups"].update({group_id: group_template})

    if not(group_id in data["groups"][group_id]["users"]):
        data["groups"][group_id]["users"].update({user_id: user_in_group_template})

        if not(user_id in data["users"]):
            data["users"].update({user_id: group_id})

    gdata.update(data)
    return 0


def watch_dog():
    pass


@bot.message_handler(
    func=lambda message: message.chat.type in group_types, content_types=content_types, commands=['channel']
)
def on_channel_command(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    pre_update(chat_id, user_id)
    channel_name = str(message.text[10:])
    try:
        bot.get_chat(f"@{channel_name}")
        data = gdata.load()
        data["groups"][chat_id]["channel"] = channel_name
        gdata.update(data)
        bot.reply_to(message, "Ссылка на канал успешно обновлена!")
        return 0
    except telebot.apihelper.ApiTelegramException:
        bot.reply_to(message, "Такого канала не существует!")
        return 1


@bot.message_handler(
    func=lambda message: message.chat.type in group_types, content_types=content_types, commands=['url']
)
def on_url(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    pre_update(chat_id, user_id)
    try:
        decorate_channel_link(chat_id)
        markup = Markup()
        btn = Button("Войти", url=f"t.me/{bot_id}?start=showpanel{chat_id}")
        markup.row(btn)
        bot.send_message(chat_id, "Вход в личный кабинет", reply_markup=markup)
    except ChannelLinkError:
        bot.send_message(chat_id, "Пожалуйста, прикрепите ссылку на канал.\n"
                                  "Пример: `/channel @test`", parse_mode="Markdown")


@bot.message_handler(
    func=lambda message: message.chat.type == "private" and message.text[7:].startswith("showpanel"), commands=['start']
)
def on_start(message):
    cmd = message.text[7:]
    chat_id = cmd[9:]
    # print(chat_id)
    user_id = str(message.from_user.id)
    try:
        pre_update(chat_id, user_id)
        data = gdata.load()
        markup = Markup()
        btn_add_task = Button("Добавить задачу", callback_data=f"addtask{chat_id}")
        btn_show_tasks = Button("Список задач", callback_data=f"tasks{chat_id}")
        btn_to_channel = Button("Ссылка на канал", url=decorate_channel_link(chat_id))
        markup.row(btn_add_task)
        markup.row(btn_show_tasks)
        markup.row(btn_to_channel)
        if data["groups"][chat_id]["users"][user_id]["punish"]:
            bot.send_message(user_id, f"Здравствуйте!\n"
                                      f"У вас *есть* действующее наказание!\n_Доступ к меню недоступен..._",
                             parse_mode="Markdown")
        else:
            bot.send_message(user_id, f"Здравствуйте!\nУ вас нет действующих наказаний.", reply_markup=markup)
    except ChannelLinkError:
        bot.send_message(user_id, f"Ошибка! В вашей группе не привязана ссылка на канал.")


@bot.callback_query_handler(
    func=lambda query: query.data.startswith("addtask")
)
def on_add_task_query(query):
    chat_id = query.data[7:]
    user_id = query.from_user.id
    msg = bot.send_message(user_id, "Введите название задачи")
    bot.register_next_step_handler_by_chat_id(chat_id=user_id, callback=f"get_task_name{chat_id}")


if __name__ == "__main__":
    bot.polling(none_stop=True)
