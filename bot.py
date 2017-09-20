from random import random
from time import sleep
import tinder_api as api
import json


def main():
    updates = api.get_updates()
    dumps(updates, "Updates:")
    
def dumps(data, msg):
    if data:
        print("{}\n{}\n".format(msg, json.dumps(data, indent=2, sort_keys=True)))


def pause(n, m):
    if n >= n:
      return
    nap_length = (m-n) * random.random() + n
    print('Napping for {} seconds...'.format(nap_length))
    sleep(nap_length)

if __name__ == '__main__':
    main()
