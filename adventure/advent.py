"""
Handles interfacing with the Adventure module.
"""

import logging
import os
import random
import re

from conn import r
from .data import parse
from .game import Game

capitalize = ["don", "woods", "i", "willie", "crowther.", "devin", "mcgloin", "i'll", "i've", "i'd"]
upper = ["sw", "w", "n", "e", "s", "ne", "nw", "ne", "se"]


def user_exists(user_id):
    return r.exists("save:" + user_id)


def new_game(user_id, seed=None):
    """Create new game"""
    logging.debug("creating new came for {}".format(user_id))
    game = Game(seed)
    load_advent_dat(game)
    game.start()
    response = format_response(game.output)
    r.set("save:" + user_id, game.t_suspend())
    return response


def respond(user_id, user_response):
    """Gets the game response for a specific user_id and user_response"""
    game = Game.resume(r.get("save:" + user_id))
    user_tupl_resp = tuple(user_response.lower().split(" "))
    response = format_response(game.do_command(user_tupl_resp))
    r.set("save:" + user_id, game.t_suspend())
    return response


def yes_no_question(user_id):
    game = Game.resume(r.get("save:" + user_id))
    return game.yes_no_question()


def load_advent_dat(data):
    """Called for each came object"""
    datapath = os.path.join(os.path.dirname(__file__), 'advent.dat')
    with open(datapath, 'r') as datafile:
        parse(data, datafile)


def format_response(response):
    clean_response = response.replace("\n", " ").lower().strip()
    clean_response = " ".join([cap(s) for s in clean_response.split(" ")])
    rsp = " ".join(accum_words(clean_response))
    return rsp


def cap(s):
    if s == "mcgloin":
        return "McGloin"
    if s in capitalize:
        return s.capitalize()
    if s in upper:
        return s.upper()
    return s


def first_upper(s):
    """Capitalizes the first letter, leaves everything else alone"""
    return re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), s, 1)


def accum_words(response):
    """Takes words split by space and capitalizes first character and special cases"""
    cleaned_sentences = []
    regex = re.compile("(\!+|\?+|\.+)")
    split = re.split(regex, response)
    if len(split) > 1:
        puncts = split[1::2]
        sentences = split[::2]
        for s, p in zip(sentences, puncts):
            sent = s.strip()
            pun = p.strip()
            if len(pun) + len(sent) < 30 and cleaned_sentences and random.random() < .8:
                cleaned_sentences[-1] += " " + first_upper(sent) + pun
                continue
            cleaned_sentences.append(first_upper(sent) + pun)
        return cleaned_sentences
    else:
        return [first_upper(s) for s in split]


        # else:
        #     regex = re.compile("(\!+|\?+|\.+|\")")
        #     split = re.split(regex, response)
        #     s = ""
        #     for section in split:
        #
        #         if re.search("[a-zA-Z ]+", section):
        #             s += accum_words(section)[0]
        #         else:
        #             s += section
        #
        #     return [s]
