import os
import sys

import redis
from rq import Worker, Queue, Connection
from pysmooch.smooch import Smooch

import logging
import json
import re

import time
import random as random




s_api = Smooch(str(os.getenv("SMOOCH_KEY_ID")), str(os.getenv("SMOOCH_SECRET")))
r = redis.from_url(os.getenv("REDIS_URL", 'redis://localhost:6379'))

listen = ["default"]



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d  - %(message)s')
    with Connection(r):
        logging.debug(listen)
        worker = Worker(listen)
        worker.work()

def respond(pq):
    logging.info("respond called")
    while pq.length() > 0:
        if pq.priority() < time.time():
            task = pq.pop_task()
            logging.debug(task)
            s_api.post_message(task[0], task[1], True)
