import time
import json
import random
import tinder_api as api
import datetime
import re

my_person_id = "59c0946bd134935f459928e6"
last_activity_date = ""
greetings = [
              "Hello {n}! Would you like to play one of my favorite games?",
              "Hey {n}, I know a pretty fun game! Would you want to play?"
            ]
explains = [
             "It is simple, I will think of a number between 1 and 25 and you have 5 guesses!"
           ]


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
    update()
    save_state()
    
def update():
    global Users, last_activity_date
    
    updates = api.get_updates(last_activity_date)
            
    print(dumps(updates, "Updates"))
    
    if "last_activity_date" in updates:
        last_activity_date = updates["last_activity_date"]
        
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
    if msg["from"] == my_person_id:
        return
    user = Users[msg["match_id"]]
    state = user["game_state"]
    text = msg["message"].lower()
    
    if state == State.New:
        if any([x for x in ["yes", "yeah", "sure", "okay", "yup", "ya", "love"] if x in text]):
            send_message(user, random.choice(explains))
            user["game_state"] = State.Playing
            user["guess_history"] = []
            user["secret_number"] = random.randint(1, 25)
    elif state == State.Playing:
        guesses = []
        temp = text
        search = re.search('(\d+)', temp)
        while search:
            guesses.append(int(search.group(1)))
            temp = temp[search.end():]
            search = re.search('(\d+)', temp)
        if len(guesses) == 0:
            send_message(user, "Go ahead and make a guess! between 1 and 25")
        if len(guesses) == 1:
            user["guess_history"].append(guesses[0])
            if guesses[0] == user["secret_number"]:
                send_message(user, "You got the secret number of {}!".format(user["secret_number"]))
                user["game_state"] = State.Win
            else:
                if len(user["guess_history"]) == 4:
                    send_message(user, "Sorry! you didnt get it. The number was {}!".format(user["secret_number"]))
                    user["game_state"] = State.Lose
                else:
                    send_message(user, "You need to guess {} next time".format("higher" if user["secret_number"] < guesses[0] else "lower"))
    elif state == State.Win:
        pass
    elif state == State.Lose:
        pass
    elif state == State.Done:
        pass
    else:
        user["game_state"] = State.Done

def send_message(user, msg):
    result = api.send_msg(user["match_id"], greeting)
    print(dumps(result, "Result"))

def send_greeting(user):
    name = user["person_name"]
    greeting = random.choice(greetings).format(n=name)
    if user["is_super_like"]:
        greeting = "Just how you super liked me, I super want to play a game! Do you want to play?"
    result = api.send_msg(user["match_id"], greeting)
    print(dumps(result, "Result"))

def dumps(data, msg=None):
    output = ""
    if msg:
        output = "{}\n".format(str(msg))
    output += "{}".format(json.dumps(data, indent=2, sort_keys=True)) if data else "{}"
    return output
        
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
    if n >= m:
      return
    nap_length = (m-n) * random.random() + n
    print('Napping for {} seconds...'.format(nap_length))
    time.sleep(nap_length)

if __name__ == '__main__':
    main()
