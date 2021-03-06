import logging
import re

import smooch

import conv_mechanics.tip as tip
from adventure import advent
from conn import r
from conv_mechanics.scheduler import respond


def yes_no_question(user_response, user_id):
    response_type = r.get("yesno:" + user_id)
    logging.debug("Response type={}".format(response_type))
    if response_type == b'restart':
        smooch.send_postbacks(user_id, "Do you want to restart?",
                              [("Yes", "restart_yes"),
                               ("No", "restart_no")])
        return True
    elif response_type == b'new_game':
        smooch.send_postbacks(user_id, "Do you want to play again?",
                              [("Yes", "start_new_yes"),
                               ("No", "start_new_no")])
        return True
    elif response_type == b'game':
        smooch.send_postbacks(user_id, "Please answer the question.",
                              [("Yes", "yes"),
                               ("No", "no")])
        return True
    else:
        logging.error("Extraneous response type={}".format(response_type))
        return False


def process_tip(user_response, user_id):
    logging.info("TIP TEXT={}".format(user_response))
    tip_amount = tip.tip_amount(user_response)

    # Smooch deals in terms of cents, so dollar amounts have to be converted
    tip_amount_adj = 100 * tip_amount
    smooch.request_payment(user_id, "Thank you for supporting Adventure",
                           [("Confirm Tip for {:.2f}".format(tip_amount), tip_amount_adj)])
    logging.info("{1} tip from {0}".format(user_id, tip_amount))
    r.lpush("tip:" + user_id, tip_amount)
    return True


def restart(user_response, user_id):
    r.set("yesno:" + user_id, "restart")
    smooch.send_postbacks(user_id, "Do you want to restart?\n I cannot undo this.",
                          [("Yes", "restart_yes"),
                           ("No", "restart_no")])
    return True


def new_user(user_response, user_id):
    logging.info("CREATING NEW USER={}".format(user_id))
    advent.new_game(user_id).strip()
    split_response = ["Welcome to Adventure!!",
                      "Adventure is a text based game, and a port of the classic terminal game Advent."]
    question = "Would you like instructions?"
    logging.debug("split_response={} question={}".format(split_response, question))
    respond(user_id, "\n".join(split_response))
    smooch.send_postbacks(user_id, question,
                          [("Yes", "yes"),
                           ("No", "no")])
    r.set("yesno:" + user_id, "game")
    return True


def normal_response(user_response, user_id):
    response = advent.respond(user_id, user_response).strip()
    logging.info("user={0} game reply={1}".format(user_id, response.replace("\n", " ")))
    if advent.yes_no_question(user_id):
        split_response = response.split("\n")
        question = split_response[-1]
        del split_response[-1]
        respond(user_id, "\n".join(split_response))
        smooch.send_postbacks(user_id, question,
                              [("Yes", "yes"),
                               ("No", "no")])
        r.set("yesno:" + user_id, "game")
        return True

    elif re.search("You scored \d+ out of a possible \d+ using \d+ turns.", response):
        respond(user_id, response)
        advent.new_game(user_id)
        r.set("yesno:" + user_id, "new_game")
        smooch.send_postbacks(user_id, "Do you want to play again?",
                              [("Yes", "start_new_yes"),
                               ("No", "start_new_no")])
        return True
    else:
        respond(user_id, response)
        return True


def help_message(user_response, user_id):
    """1378"""
    response = advent.respond(user_id, "help").split("\n")
    message = response[0:2]
    smooch.send_message(user_id, "\n".join(message), True)
    smooch.send_links(user_id, response[2], [("More Help", "https://devinmcgloin.com/advent/help/"),
                                             ("Hints", "https://devinmcgloin.com/advent/hints/")])
    return True


def info_message(user_response, user_id):
    """1531"""
    response = advent.respond(user_id, "info").split("\n")
    message = response[0:3]
    smooch.send_message(user_id, "\n".join(message), True)
    smooch.send_links(user_id, response[3], [("More Info", "https://devinmcgloin.com/advent/info/")])
    return True


def process_response(user_response, user_id):
    user_exists = advent.user_exists(user_id)

    if user_response.startswith("/"):
        user_response = user_response.replace("/", "")

    if r.get("yesno:" + user_id):
        return yes_no_question(user_response, user_id)
    elif tip.is_tip(user_response.lower()):
        return process_tip(user_response, user_id)
    elif user_exists and (user_response.lower() == "restart" or user_response.lower() == "reset"):
        return restart(user_response, user_id)
    elif user_exists and (user_response.lower() == "help" or user_response.lower() == "?"):
        return help_message(user_response, user_id)
    elif user_exists and user_response.lower() == "info":
        return info_message(user_response, user_id)
    elif user_exists:
        return normal_response(user_response, user_id)
    else:
        return new_user(user_response, user_id)
