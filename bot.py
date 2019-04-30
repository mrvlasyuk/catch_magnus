import time
import requests
import traceback
import threading

import telegram
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, ConversationHandler

import db
import util 
import config

PLAYER_NAME = 'Magnus Carlsen'
PLAYER_NICK = 'DrNykterstein'

URL_PAGE = f'https://lichess.org/@/{PLAYER_NICK}'
URL_API = f'https://lichess.org/api/users/status?ids={PLAYER_NICK}'

HELLO_TEXT = f'Hi!\n\nThis simple bot will notify you when {PLAYER_NAME} (aka [{PLAYER_NICK}]({URL_PAGE})) plays on lichess.org'
PLAYING_TEXT = f'{PLAYER_NAME} is playing right now! {URL_PAGE}'

TIME_DELAY_SEC = 10 * 60


class MagnusState:
    def __init__(self):
        self.last_time_played = 0
        self.last_time_online = 0
        self.is_online = False
        self.is_playing = False
        self.need_send_update = False

    def update_status(self):
        try:
            res = requests.get(URL_API)
            data = res.json()[0]
            is_online = data.get('online', False)
            is_playing = data.get('playing', False)
        except:
            traceback.print_exc()
            print('Failed to get status')
            print(res.text)
            is_online = False
            is_playing = False

        _time = time.time()
        if is_playing:
            if not self.is_playing and _time - self.last_time_played > TIME_DELAY_SEC:
                print(f'{PLAYER_NAME} is playing!')
                self.need_send_update = True
            self.last_time_played = _time

        if is_online:
            self.last_time_online = _time

        self.is_playing = is_playing
        self.is_online = is_online

    def __repr__(self):
        return f'{PLAYER_NICK} status: *online*= {self.is_online}, *playing*= {self.is_playing}'
    

class TelegramBot:
    def __init__(self, state, user_db, api_key):
        self.state = state
        self.user_db = user_db

        updater = Updater(token=api_key)
        dispatcher = updater.dispatcher


        start_handler = CommandHandler('start', self.send_greetings)
        conv_handler = ConversationHandler(
            entry_points=[start_handler],
            fallbacks=[start_handler],
            states={}
        )
        dispatcher.add_handler(conv_handler)
        dispatcher.add_error_handler(self.error_handler)

        self.bot = updater.bot
        self.updater = updater

    def error_handler(self, bot, update, error):
        print('Update "%s" caused error "%s"', update, error)

    def send_greetings(self, bot, update):
        my_upd = util.log_update('start', update)
        self.user_db.try_create(my_upd.user_id, my_upd.nick, my_upd.fullname)
        text = HELLO_TEXT + f'\n\n{self.state}'
        update.message.reply_text(text, 
            parse_mode=ParseMode.MARKDOWN, 
            disable_web_page_preview=True)

    def send_msg_to_all(self):
        for user in self.user_db.get_all():
            try:
                self.bot.send_message(
                    chat_id=user.user_id,
                    text=PLAYING_TEXT,
                    disable_web_page_preview=True)
            except:
                traceback.print_exc()
                print(f'Error sending to {user}. Skipping')

    def run_forever(self):
        self.updater.start_polling()
        self.updater.idle()



SLEEP_TIME_SEC = 5
PRINT_TIME_SEC = 60 * 60

def run_status_checker_forever(state, telegram_bot):
    def forever():
        last_time_print = 0
        while True:
            time.sleep(SLEEP_TIME_SEC)
            state.update_status()

            if state.need_send_update:
                telegram_bot.send_msg_to_all()
                state.need_send_update = False

            if time.time() - last_time_print > PRINT_TIME_SEC:
                last_time_print = time.time()
                print(f'Checker is alive: {state}')

    t = threading.Thread(target=forever, args=())
    t.start()


if __name__ == '__main__':
    base = db.DB('data/main.sqlite')
    user_db = db.UserDB(base)

    state = MagnusState()
    _bot = TelegramBot(state, user_db, config.API_KEY) 
    run_status_checker_forever(state, _bot)
    _bot.run_forever()
