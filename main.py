from keys import TOKEN
from dateutil import tz as timezone
from datetime import datetime
import json
import telebot
import gdata


bot = telebot.TeleBot(TOKEN)
bot_id = "the_combot"

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
	"users": {}
}
user_in_group_template = {
	"punish": False,
	"tasks": {}
}
group_types = ["group", "supergroup"]


def now_time(t_zone=0):
	return datetime.now(tz=timezone.gettz(f"UTC+{str(3 + t_zone)}"))


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
	func=lambda message: message.chat.type in group_types, content_types=content_types, commands=['url']
)
def on_url(message):
	chat_id = str(message.chat.id)
	user_id = str(message.from_user.id)
	markup = telebot.types.InlineKeyboardMarkup()
	btn = telebot.types.InlineKeyboardButton("Войти", url=f"t.me/{bot_id}?start=showpanel{chat_id}")
	markup.row(btn)
	bot.send_message(chat_id, "Вход в личный кабинет", reply_markup=markup)


if __name__ == "__main__":
	bot.polling(none_stop=True)
