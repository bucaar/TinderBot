import time
import json
import random
import tinder_api as api
import messages
import datetime
import re

MY_PERSON_ID = "59c203813d56b3bc35c1ba85"
last_activity_date = ""

MIN_NUM = 1
MAX_NUM = 25
NUM_GUESSES = 5

class State:
    New = "New"
    Playing = "Playing"
    Win = "Win"
    Lose = "Lose"
    Done = "Done"

Users = {}
"""
{
  <match_id>: {
    "game_state": "xxx",
    "guess_history": [],
    "is_super_like": false,
    "last_activity_date": "0000-00-00T00:00:00.000Z",
    "messages": [
      {
        "from": "xxx",
        "match_id": "xxxxx",
        "message": "Hello",
        "message_id": "xxx",
        "to": "xxx"
      }
    ],
    "person_id": "xxx",
    "person_name": "xxx",
    "secret_number": 0
  }
}
"""

def main():
    load_state()
    while True:
        update()
        save_state()
        print("Running in 3 seconds.")
        pause(3, 3)

def update():
    global Users, last_activity_date

    updates = api.get_updates(last_activity_date)

    print(dumps(updates, "Updates"))

    if "last_activity_date" in updates:
        last_activity_date = updates["last_activity_date"]

    if "blocks" in updates:
        for block in updates["blocks"]:
            if block in Users:
                print("Delete {}".format(Users[block]["person_name"]))
                log("Unmatched with {}".format(Users[block]["person_name"]))
                del(Users[block])

    if "matches" in updates:
        for match in updates["matches"]:
            match_id = match["_id"]

            if match_id in Users:
                #We only need to update this user
                user = Users[match_id]
            else:
                #it is a new user, so set up all of the default stuff first
                user = Users[match_id] = {}
                user["match_id"] = match_id
                user["is_super_like"] = match["is_super_like"]
                user["messages"] = []

                person = match["person"]
                user["person_id"] = person["_id"]
                user["person_name"] = person["name"]
                user["guess_history"] = []
                user["secret_number"] = 0
                user["game_state"] = State.New

                send_greeting(user)

            #in either new or an update, we still update these things
            user["last_activity_date"] = match["last_activity_date"]
            messages = match["messages"]
            for message in messages:
                msg = {}
                msg["message_id"] = message["_id"]
                msg["match_id"] = message["match_id"]
                msg["from"] = message["from"]
                msg["to"] = message["to"]
                msg["message"] = message["message"]
                user["messages"].append(msg)

                #interpret the message as a number guessing game
                process_message(msg)

def process_message(msg):
    # {"from": "xxx", "match_id": "xxxxx", "message": "Hello", "message_id": "xxx", "to": "xxx" }
    if msg["from"] == MY_PERSON_ID:
        return

    user = Users[msg["match_id"]]
    state = user["game_state"]
    text = msg["message"].lower()

    log("{} {}: {}".format("From", user["person_name"], text))

    if state == State.New:
        if any([x for x in messages.affirmative if x in text]):
            send_message(user, messages.how_to_play)
            user["game_state"] = State.Playing
            user["guess_history"] = []
            user["secret_number"] = random.randint(MIN_NUM, MAX_NUM)
        else:
            send_message(user, messages.begs)

    elif state == State.Playing:
        guesses = []
        temp = text
        search = re.search('(\d+)', temp)
        while search:
            guesses.append(int(search.group(1)))
            temp = temp[search.end():]
            search = re.search('(-?\d+)', temp)
        if len(guesses) == 0:
            send_message(user, messages.make_guess)
        elif len(guesses) > 1:
            send_message(user, messages.too_many)
        if len(guesses) == 1:
            user["guess_history"].append(guesses[0])
            process_last_guess(user)

    elif state == State.Win:
        pass
    elif state == State.Lose:
        pass
    elif state == State.Done:
        pass
    else:
        user["game_state"] = State.Done

def process_last_guess(user):
    history = user["guess_history"]
    guess_count = len(history)
    guesses_remain = NUM_GUESSES - guess_count
    last_guess = history[-1]
    secret = user["secret_number"]
    result = "higher" if last_guess < secret else "lower"
    lower_bound = MIN_NUM
    upper_bound = MAX_NUM

    for guess in history[:-1]:
        if guess < upper_bound and guess > secret:
            upper_bound = guess-1
        if guess > lower_bound and guess < secret:
            lower_bound = guess+1

    if last_guess == secret:
        #win
        send_message(user, messages.win)
        user["game_state"] = State.Win
        return

    if last_guess < lower_bound or last_guess > upper_bound:
        #bad guess
        send_message(user, messages.dumb_guess, lower_bound=str(lower_bound), upper_bound=str(upper_bound))
    else:
        #results of last guess
        send_message(user, messages.guess_result, result=result)

        if guesses_remain == 0:
            #just made last guess
            pass
        if guesses_remain == 1:
            #last guess
            send_message(user, messages.last_guess)
        elif guesses_remain == NUM_GUESSES // 2:
            #taunt
            send_message(user, messages.taunts)

    if guesses_remain == 0:
            send_message(user, messages.lose)
            user["game_state"] = State.Lose

def send_message(user, msg, lower_bound="", upper_bound="", result=""):
    if type(msg) == list:
        msg = random.choice(msg)
    msg = populate_string_variables(user, msg, lower_bound=lower_bound, upper_bound=upper_bound, result=result)
    print("To: {}; {}".format(user["person_name"], msg))

    log("{} {}: {}".format("To", user["person_name"], msg))
    result = api.send_msg(user["match_id"], msg)
    print(dumps(result, "Result"))
    pause(1, 3)

def send_greeting(user):
    greeting = random.choice(messages.greetings)
    if user["is_super_like"]:
        greeting = "Just how you super liked me... I super want to play a game! Do you want to play?"
    send_message(user, greeting)

def populate_string_variables(user, text, lower_bound="", upper_bound="", result=""):
    text = text.replace("{name}", user["person_name"])
    text = text.replace("{min_num}", str(MIN_NUM))
    text = text.replace("{max_num}", str(MAX_NUM))
    text = text.replace("{num_guesses}", str(NUM_GUESSES))
    text = text.replace("{secret_number}", str(user["secret_number"]))
    text = text.replace("{guess_count}", str(len(user["guess_history"])))
    text = text.replace("{guesses_remain}", str(NUM_GUESSES-len(user["guess_history"])))
    text = text.replace("{last_guess}", str(user["guess_history"][-1] if len(user["guess_history"]) > 0 else ""))
    text = text.replace("{lower_bound}", str(lower_bound))
    text = text.replace("{upper_bound}", str(upper_bound))
    text = text.replace("{result}", result)

    return text

def dumps(data, msg=None):
    output = ""
    if msg:
        output = "{}\n".format(str(msg))
    output += "{}".format(json.dumps(data, indent=2, sort_keys=True)) if data else "{}"
    return output

def log(msg):
    print(msg, file=open("log.txt", "a"))

def save_state():
    print(dumps(Users), file=open("users.json", "w"))
    print(last_activity_date, file=open("latest_activity_date.txt", "w"), end="")

def load_state():
    global Users, last_activity_date

    with open("users.json") as file:
        Users = json.loads('\n'.join(file.readlines()))
    with open("latest_activity_date.txt") as file:
        last_activity_date = ''.join(file.readlines())

def pause(n, m):
    if n > m:
      return
    nap_length = (m-n) * random.random() + n
    print('Napping for {} seconds...'.format(nap_length))
    time.sleep(nap_length)

if __name__ == '__main__':
    main()
