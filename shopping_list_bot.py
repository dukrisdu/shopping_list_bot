"""
Date: 08/04/2021
@author: Kristina

This is a simple bot for Telegram, to create a shopping list, 
that can be easily modified and accessed.
Functionality:
    1. Add an item
    2. Remove an item
    3. Show the list (possibility to show it in a few languages? (English, Spanish, Lithuanian...))
    4. Delete the whole list
    5. Unknown commands would send a list of  possible commands
    6. Help
    7. Start
"""

import json 
import requests
import time
import urllib

from dblist import DBHelper

db = DBHelper()

TOKEN = "<<ADD YOUR TOKEN HERE>>"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)


def get_url(url):
    """
    Getting the content from the url
    INPUT:  String of an url of the bot
    OUTPUT: String of the content in the URL
    """
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    """
    Gets the string response (that is JSON) and parses it
    INPUT:  String of a response 
    OUTPUT: String that has been parsed 
    """
    content = get_url(url)
    js = json.loads(content)
    return js


def get_updates(offset=None):
    """
    Goes to the API updates page and gets the updates
    Updates - messages that were send to the bot
    INPUT:  String of an url updates
    OUTPUT: String that is parsed of the updates
    """
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js

def get_last_update_id(updates):
    """
    Gets the last update and in this allows the tracking 
    of the updates, that have been already handled
    INPUT:  Updates of the bot
    OUTPUT: The update with the highest ID 
    """
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)

def get_last_chat_id_and_text(updates):
    """
    Gets the last chat ID and a message that was send
    INPUT:  All updates
    OUTPUT: Last updates text and chat ID
    """
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)


def send_message(text, chat_id, reply_markup=None):
    """
    Sends a message to a user
    INPUT:  Text, chat ID
    OUTPUT: None
    """
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)

def build_keyboard(items):
    """
    Builds a keyboard for a user of the items
    INPUT:  A list of items
    OUTPUT: JSON string (the Python dictionary converted to a JSON string)
    """
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)

def delete_all_items(items, chat):
    """
    Deletes all the items of a user and sends a message once it's done
    INPUT:  The list of items, chat
    OUTPUT: None
    """
    for item in items:
        db.delete_item(item, chat)
    send_message("Your list was deleted successfully!", chat)

def handle_updates(updates):
    """
    Handle an update
    Responsible for the functionality of this bot.
    Checks each of the updates and gives an appropriate
    for each of the update received.
    INPUT:  A list of updates
    OUTPUT: None
    """
    for update in updates["result"]:
        text = update["message"]["text"]
        chat = update["message"]["chat"]["id"]
        items = db.get_items(chat)
        if text == "/done":
            keyboard = build_keyboard(items)
            send_message("Select an item to delete", chat, keyboard)
        elif text == "/start" or text == "/help":
            send_message("Hello! \nI'm your shopping helper. \nPossible commands are:\n1. /start - To start the bot and have a list of the commands\n2. To ADD an item to a list, simply write it down for me\n3. To list all of the items you have, type in /list\n4. To DELETE an item from a list type it down for me OR write /done and I will list you the items that you can be done with\n5. To delete the whole list, type /allDone\n6. If you are ever confused, just type /help", chat)
        elif text == "/allDone" or text == "/alldone":
            delete_all_items(items, chat)
        elif text == "/list":
            items = db.get_items(chat)
            message = "\n".join(items)
            send_message(message, chat)
        elif text.startswith("/"):
            send_message("Hello!  \nI'm your shopping helper. \nPossible commands are:\n1. /start - To start the bot and have a list of the commands\n2. To ADD an item to a list, simply write it down for me\n3. To list all of the items you have, type in /list\n4. To DELETE an item from a list type it down for me OR write /done and I will list you the items that you can be done with\n5. To delete the whole list, type /allDone\n6. If you are ever confused, just type /help", chat)
            continue
        elif text in items:
            db.delete_item(text, chat)
            items = db.get_items(chat)
            send_message("You've deleted " + text + " from the list", chat)
        else:
            db.add_item(text, chat)
            items = db.get_items(chat)
            message = "\n".join(items)
            send_message(message, chat)

def main():
    db.setup()
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        time.sleep(0.5)


if __name__ == '__main__':
    main()