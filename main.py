from keys import TOKEN
from time import sleep
from threading import Thread
from dateutil import tz as timezone
from datetime import datetime, timedelta
import telebot
import gdata
import random


class ChannelLinkError(Exception):
    def __init__(self):
        self.txt = "Нет ссылки на канал"


class NotAPhotoError(Exception):
    def __init__(self):
        self.txt = "Это не фотография"


bot = telebot.TeleBot(TOKEN)
bot_id = "the_combot"

Markup = telebot.types.InlineKeyboardMarkup
Button = telebot.types.InlineKeyboardButton
Poll = telebot.types.Poll

RNG = 60#*60*20
MKD = "Markdown"
time_stamp = "%H:%M %d.%m.%Y"
tm = "%M"
th = "%H"
td = "%d"

# {"groups": {}, "users": {}}

weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
content_types = ['text', 'audio', 'document', 'photo', 'sticker',
                 'video', 'video_note', 'voice', 'location', 'contact',
                 'new_chat_members', 'left_chat_member', 'new_chat_title',
                 'new_chat_photo', 'delete_chat_photo', 'group_chat_created',
                 'supergroup_chat_created', 'channel_chat_created',
                 'migrate_to_chat_id', 'migrate_from_chat_id', 'pinned_message']
group_template = {
    "vote_limit": 6,
    "users": {},
    "channel": None,
    "tasks": []
}
user_in_group_template = {
    "punish": False,
    "t_zone": 0,
    "score": 0,
    "relax_day": 6,
    "tasks": {}
}
group_types = ["group", "supergroup"]


def gen_id():
    return random.randint(0, 9999999999999)


def now_time(t_zone=0):
    return datetime.now(tz=timezone.gettz(f"UTC+{str(3 + t_zone)}"))


def decorate_channel_link(group_id: str):
    data = gdata.load()
    channel_name = data["groups"][group_id]["channel"]
    try:
        msg = bot.send_message(f"@{channel_name}", "test")
        bot.delete_message(f"@{channel_name}", msg.message_id)
    except telebot.apihelper.ApiTelegramException:
        raise ChannelLinkError
    if not channel_name:
        raise ChannelLinkError
    else:
        return f"t.me/{channel_name}"


def pre_update(group_id: str, user_id: str):
    user_id = str(user_id)
    group_id = str(group_id)
    data = gdata.load()

    global group_template

    if not (group_id in data["groups"]):
        data["groups"].update({group_id: group_template})

    if not (user_id in data["groups"][group_id]["users"].keys()):
        print(data["groups"][group_id]["users"].keys(), type(user_id),
              user_id in data["groups"][group_id]["users"].keys())
        data["groups"][group_id]["users"].update({user_id: user_in_group_template})

        if not (user_id in data["users"].keys()):
            data["users"].update({user_id: [group_id]})

        if not (group_id in data["users"][user_id]):
            data["users"][user_id].append(group_id)

    gdata.update(data)

    return 0


def show_menu(chat_id: str, user_id: str, edit=None):
    try:
        pre_update(chat_id, user_id)
        data = gdata.load()
        markup = Markup()
        btn_add_task = Button("Добавить задачу", callback_data=f"addtask{chat_id}")
        btn_show_tasks = Button("Список задач", callback_data=f"tasks{chat_id}")
        btn_change_time_zone = Button("Изменить часовой пояс", callback_data=f"changetz{chat_id}")
        btn_change_relax = Button("Изменить выходной день", callback_data=f"changerelax{chat_id}")
        btn_to_channel = Button("Ссылка на канал", url=decorate_channel_link(chat_id))
        markup.row(btn_add_task)
        markup.row(btn_show_tasks)
        markup.row(btn_change_time_zone)
        markup.row(btn_change_relax)
        markup.row(btn_to_channel)
        tz = str(data["groups"][chat_id]["users"][user_id]["t_zone"])
        score = str(data["groups"][chat_id]["users"][user_id]["score"])
        relax_day = str(data["groups"][chat_id]["users"][user_id]["relax_day"])
        have_punish_text = f"Здравствуйте!\n" \
                           f"Ваш часовой пояс - `МСК{f'+{tz}' if int(tz) >= 0 else tz}\n`" \
                           f"Ваш рейтинг: `{score}`\n" \
                           f"Ваш выходной: `{weekdays[int(relax_day)]}`\n" \
                           f"У вас *есть* действующее наказание!\n_Доступ к меню недоступен..._"
        have_no_punish_text = f"Здравствуйте!\n" \
                              f"Ваш часовой пояс - `МСК{f'+{tz}' if int(tz) >= 0 else tz}\n`" \
                              f"Ваш рейтинг: `{score}`\n" \
                              f"Ваш выходной: `{weekdays[int(relax_day)]}`\n" \
                              f"У вас нет действующих наказаний."
        if edit:
            if data["groups"][chat_id]["users"][user_id]["punish"]:
                bot.edit_message_text(have_punish_text,
                                      chat_id=user_id,
                                      message_id=edit,
                                      parse_mode=MKD)
            else:
                bot.edit_message_text(have_no_punish_text,
                                      chat_id=user_id,
                                      message_id=edit,
                                      reply_markup=markup,
                                      parse_mode=MKD)
        else:
            if data["groups"][chat_id]["users"][user_id]["punish"]:
                bot.send_message(user_id, have_punish_text,
                                 parse_mode=MKD)
            else:
                bot.send_message(user_id, have_no_punish_text, reply_markup=markup, parse_mode=MKD)
    except ChannelLinkError:
        bot.send_message(user_id, f"Ошибка! К вашей группе не привязан канал или у бота нет прав на канале...")


def watch_dog():
    while True:
        try:
            data = gdata.load()
            for chat_id in data["groups"]:
                data = gdata.load()
                channel_id = f'@{data["groups"][chat_id]["channel"]}'
                for user_id in data["groups"][chat_id]["users"]:
                    user = data["groups"][chat_id]["users"][user_id]
                    user_d = bot.get_chat_member(chat_id, user_id)
                    tz = user["t_zone"]
                    for task_id in user["tasks"]:
                        task_obj = user["tasks"][task_id]
                        time = datetime.strptime(task_obj["time"], time_stamp)
                        now = datetime.strptime(now_time(tz).strftime(time_stamp), time_stamp)
                        if now >= time:
                            data["groups"][chat_id]["users"][user_id]["tasks"].pop(task_id)
                            bot.send_message(channel_id, f"[{user_d.user.first_name}](tg://user?id={user_id}) "
                                                         f"не выполнил свою задачу в срок!", parse_mode=MKD)
                            score = data["groups"][chat_id]["users"][user_id]["score"]
                            bot.send_message(user_id, f"Ваш рейтинг теперь равен _{score} - 2_ = _{score - 2}_",
                                             parse_mode=MKD)
                            data["groups"][chat_id]["users"][user_id]["score"] -= 2
                            gdata.update(data)
                            data = gdata.load()
                for task_obj in data["groups"][chat_id]["tasks"]:
                    user_id = task_obj["user_id"]
                    channel_id = task_obj["channel_id"]
                    time = datetime.strptime(task_obj["time"], time_stamp)
                    tz = data["groups"][chat_id]["users"][user_id]["t_zone"]
                    vote_limit = data["groups"][chat_id]["vote_limit"]
                    user_d = bot.get_chat_member(chat_id, user_id)
                    now = datetime.strptime(now_time(tz).strftime(time_stamp), time_stamp)
                    if (now - time).seconds >= RNG:
                        print(channel_id)
                        poll = bot.stop_poll(chat_id=channel_id, message_id=task_obj["poll_id"])
                        if poll.options[1].voter_count > poll.options[0].voter_count:
                            bot.send_message(channel_id, f"[{user_d.user.first_name}](tg://user?id={user_id}) "
                                                         f"обманул партию и не выполнил задачу!", parse_mode=MKD)
                            score = data["groups"][chat_id]["users"][user_id]["score"]
                            bot.send_message(user_id, f"Ваш рейтинг теперь равен _{score} - 4_ = _{score - 4}_",
                                             parse_mode=MKD)
                            data["groups"][chat_id]["users"][user_id]["score"] -= 4
                            gdata.update(data)
                            data = gdata.load()
                        else:
                            score = data["groups"][chat_id]["users"][user_id]["score"]
                            bot.send_message(user_id, f"Ваш рейтинг теперь равен _{score} + 1_ = _{score + 1}_\n"
                                                      f"(за успешное выполнение задачи)", parse_mode=MKD)
                            data["groups"][chat_id]["users"][user_id]["score"] += 1
                            gdata.update(data)
                            data = gdata.load()
                        bot.delete_message(chat_id=channel_id, message_id=task_obj["poll_id"])
                        bot.delete_message(chat_id=channel_id, message_id=task_obj["photo_id"])
                        data["groups"][chat_id]["tasks"].remove(task_obj)
                        gdata.update(data)
                        data = gdata.load()
                        show_menu(chat_id, user_id)
            sleep(5)
        except RuntimeError as e:
            print(e)
            sleep(5)







def show_weekdays(chat_id, user_id, message_id):
    data = gdata.load()
    markup = Markup()
    for i in range(7):
        this_day = int(data["groups"][chat_id]["users"][user_id]["relax_day"]) == i
        markup.row(Button(
            f"{'• ' if this_day else ''}{weekdays[i]}{' •' if this_day else ''}",
            callback_data=f"change_day{str(i)}:{chat_id}"
        ))
    markup.row(Button(
        f"🔙",
        callback_data=f"go_to_menu{chat_id}"
    ))
    bot.edit_message_text("Дни недели:", reply_markup=markup, chat_id=user_id, message_id=message_id)


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
        decorate_channel_link(chat_id)
        return 0
    except telebot.apihelper.ApiTelegramException:
        bot.reply_to(message, "Такого канала не существует!")
        return 1
    except ChannelLinkError:
        bot.reply_to(message, "Пожалуйста, дайте боту права админа на канале!")


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
        bot.send_message(chat_id, "*Ошибка! Возможные причины:*\n"
                                  "• _Ссылка на канал не прикреплена_\n"
                                  "   Пример прикрепления ссылки: `/channel @test`\n"
                                  "• _У бота нет прав в прикрепленном канале_", parse_mode=MKD)


@bot.message_handler(
    func=lambda message: message.chat.type == "private" and message.text[7:].startswith("showpanel"), commands=['start']
)
def on_start(message):
    cmd = message.text[7:]
    chat_id = cmd[9:]
    user_id = str(message.from_user.id)
    show_menu(chat_id, user_id)


@bot.callback_query_handler(
    func=lambda query: query.data.startswith("changetz")
)
def on_change_tz(query):
    chat_id = query.data[8:]
    user_id = query.from_user.id
    msg = bot.send_message(user_id, "Введите новый часовой пояс в формате `МСК+x`.\n_Примеры:_\n`МСК+2`\n`МСК-1`",
                           parse_mode=MKD)
    bot.register_next_step_handler(msg, on_new_tz, _chat_id=chat_id)


@bot.callback_query_handler(
    func=lambda query: query.data.startswith("changerelax")
)
def on_change_relax(query):
    chat_id = query.data[11:]
    user_id = str(query.from_user.id)
    show_weekdays(chat_id, user_id, query.message.message_id)


@bot.callback_query_handler(
    func=lambda query: query.data.startswith("change_day")
)
def on_change_relax_day(query):
    new_day, chat_id = map(str, query.data[10:].split(":"))
    user_id = str(query.from_user.id)
    data = gdata.load()
    data["groups"][chat_id]["users"][user_id]["relax_day"] = new_day
    gdata.update(data)
    show_weekdays(chat_id, user_id, query.message.message_id)


@bot.callback_query_handler(
    func=lambda query: query.data.startswith("go_to_menu")
)
def return_to_menu(query):
    chat_id = query.data[10:]
    user_id = str(query.from_user.id)
    show_menu(chat_id, user_id, edit=query.message.message_id)


def on_new_tz(message, _chat_id):
    chat_id = _chat_id
    user_id = str(message.from_user.id)
    try:
        if message.text.startswith("МСК"):
            tz = int(message.text[3:])
            data = gdata.load()
            data["groups"][chat_id]["users"][user_id]["t_zone"] = tz
            gdata.update(data)
            bot.send_message(user_id, "Успешно!")
        else:
            raise ValueError
    except ValueError:
        bot.send_message(user_id, "Ошибка!")
    show_menu(chat_id, user_id)


@bot.callback_query_handler(
    func=lambda query: query.data.startswith("addtask")
)
def on_add_task_query(query):
    chat_id = query.data[7:]
    user_id = query.from_user.id
    pre_update(chat_id, user_id)
    msg = bot.send_message(user_id, "Введите название задачи", parse_mode=MKD)
    bot.register_next_step_handler(msg, on_task_name, _chat_id=chat_id)


def on_task_name(message, _chat_id):
    chat_id = _chat_id
    user_id = str(message.from_user.id)
    msg = bot.send_message(user_id, "Введите описание задачи", parse_mode=MKD)
    bot.register_next_step_handler(msg, on_task_description, _chat_id=chat_id, task_name=message.text)


def on_task_description(message, _chat_id, task_name):
    chat_id = _chat_id
    user_id = str(message.from_user.id)
    msg = bot.send_message(user_id, "Опишите доказательство выполнения этой задачи", parse_mode=MKD)
    bot.register_next_step_handler(msg, on_task_proof_description,
                                   _chat_id=chat_id,
                                   task_name=task_name,
                                   task_description=message.text)


def on_task_proof_description(message, _chat_id, task_name, task_description):
    chat_id = _chat_id
    user_id = str(message.from_user.id)
    msg = bot.send_message(user_id, "До какого времени вы сможете выполнить задачу?\nФормат:\n`HH:MM DD.MM.YYYY`",
                           parse_mode=MKD)
    bot.register_next_step_handler(msg, on_datetime,
                                   _chat_id=chat_id,
                                   task_name=task_name,
                                   task_description=task_description,
                                   task_proof_description=message.text)


def on_datetime(message, _chat_id, task_name, task_description, task_proof_description):
    chat_id = _chat_id
    user_id = str(message.from_user.id)
    time = datetime.strptime(message.text, time_stamp).strftime(time_stamp)
    msg = bot.send_message(user_id, "*Проверьте введенные данные.*\n"
                                    "Введите `0` если желаете отменить дейстия\n"
                                    "Введите любой другой текст для продолжения...",
                           parse_mode=MKD)
    bot.register_next_step_handler(msg, add_task,
                                   _chat_id=chat_id,
                                   task_name=task_name,
                                   task_description=task_description,
                                   task_proof_description=task_proof_description,
                                   time=time)


def add_task(message, _chat_id, task_name, task_description, task_proof_description, time):
    chat_id = _chat_id
    user_id = str(message.from_user.id)
    if message.text != "0":
        data = gdata.load()
        task_id = str(gen_id())
        print(data["groups"][chat_id]["users"][user_id]["tasks"])
        data["groups"][chat_id]["users"][user_id]["tasks"].update({
            task_id: {
                "task_name": task_name,
                "task_description": task_description,
                "task_proof_description": task_proof_description,
                "time": time
            }
        })
        gdata.update(data)
        bot.send_message(user_id, "Успешно!")
    else:
        bot.send_message(user_id, "Отменено!")
    show_menu(chat_id, user_id)


@bot.callback_query_handler(
    func=lambda query: query.data.startswith("tasks")
)
def on_show_tasks(query):
    chat_id = query.data[5:]
    user_id = str(query.from_user.id)
    data = gdata.load()
    tasks = data["groups"][chat_id]["users"][user_id]["tasks"]
    if tasks:
        bot.send_message(user_id, f"*Ваши задачи:*", parse_mode=MKD)
        for task_number in tasks:
            task_obj = tasks[task_number]
            task_text = f"*Название:*\n{task_obj['task_name']}\n\n" \
                        f"*Описание:*_\n{task_obj['task_description']}_\n\n" \
                        f"*Дедлайн:*\n`{task_obj['time']}`"
            markup = Markup()
            btn = Button("Выполнено", callback_data=f"completed{chat_id}:{str(task_number)}")
            markup.row(btn)
            bot.send_message(user_id, task_text, reply_markup=markup, parse_mode=MKD)
    else:
        markup = Markup()
        btn = Button("Добавить", callback_data=f"addtask{chat_id}")
        markup.row(btn)
        bot.send_message(user_id, f"*У вас нет задач*", reply_markup=markup, parse_mode=MKD)


@bot.callback_query_handler(
    func=lambda query: query.data.startswith("completed")
)
def on_task_complete(query):
    chat_id, task_number = map(str, query.data[9:].split(":"))
    user_id = str(query.from_user.id)
    data = gdata.load()
    tasks = data["groups"][chat_id]["users"][user_id]["tasks"]
    try:
        task_obj = tasks[task_number]
        bot.send_message(user_id, f"Формат доказательства выполнения задачи:\n_{task_obj['task_proof_description']}_",
                         parse_mode=MKD)
        msg = bot.send_message(user_id, f"Отправьте фотографию-доказательство выполнения задачи")
        bot.register_next_step_handler(msg, on_getting_proof, _chat_id=chat_id, _task=task_obj, task_number=task_number)
    except KeyError:
        bot.send_message(user_id, "Ложки не существует, нео...")


def on_getting_proof(message, _chat_id, _task, task_number):
    chat_id = _chat_id
    task_obj = _task
    user_id = str(message.from_user.id)
    data = gdata.load()
    channel_id = "@" + data["groups"][chat_id]["channel"]
    tz = str(data["groups"][chat_id]["users"][user_id]["t_zone"])

    if not message.photo:
        raise NotAPhotoError

    file_id = message.photo[0].file_id
    p_msg = bot.send_photo(channel_id, caption=f"*Название:*\n{task_obj['task_name']}\n\n"
                                               f"*Описание:*_\n{task_obj['task_description']}_\n\n"
                                               f"*Доказательство:\n*_{task_obj['task_proof_description']}_",
                           photo=file_id, parse_mode=MKD)
    poll = bot.send_poll(channel_id, question="\/\/\/", options=['👍', '👎'])
    data["groups"][chat_id]["tasks"].append({
        "poll_id": poll.message_id,
        "photo_id": p_msg.message_id,
        "time": now_time(t_zone=int(tz)).strftime(time_stamp),
        "user_id": user_id,
        "channel_id": str(p_msg.chat.id)
    })
    data["groups"][chat_id]["users"][user_id]["tasks"].pop(task_number)
    gdata.update(data)
    bot.send_message(user_id, "Успешно!")
    show_menu(chat_id, user_id)


if __name__ == "__main__":
    task = Thread(target=watch_dog)
    task.start()
    bot.polling(none_stop=True)
