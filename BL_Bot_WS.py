import os
import logging
from botstuff import env
from botstuff.env import getEnv

env.initEnv()

logging.basicConfig(
    filename="/home/cisco/Desktop/Backlog_Buddy_V2/Websocket.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from webex_bot.webex_bot import WebexBot
from bot_commands.admin_ops import admin_opsCMD, addCMD, removeCMD, addCallback, removeCallback, listCMD, listCallback, updateCMD, updateCallback

proxies = {
            'http': "http://proxy.esl.cisco.com:80",
            'https': "http://proxy.esl.cisco.com:80"
          }

def socket():

    # Create a Bot Object
    bot = WebexBot(teams_bot_token=getEnv().webexAccessToken,
               approved_domains=["cisco.com"],
               bot_name="backlog_buddy",
               include_demo_commands=False,
               proxies=proxies)

    ## Add new commands for the bot to listen out for.
    bot.add_command(addCMD())
    bot.add_command(listCMD())
    bot.add_command(updateCMD())
    bot.add_command(removeCMD())
    bot.add_command(addCallback())
    bot.add_command(listCallback())
    bot.add_command(admin_opsCMD())
    bot.add_command(updateCallback())
    bot.add_command(removeCallback())

    # Call `run` for the bot to wait for incoming messages.
    bot.run()

logging.debug("Code Started")

while True:
    try:
        logging.debug("WebSocket Established")
        socket()
    except Exception as e:
        logging.debug(f"An exception occured:{e}")
        continue


