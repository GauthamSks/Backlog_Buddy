import re
import time
import logging
import requests
from db import r_DB
from datetime import date
from botstuff import salesforce
from botstuff.env import getEnv
from typing import Union, Literal
from typing import List, Optional

db_Obj = r_DB()

proxy_server = {
                 'http':"http://proxy.esl.cisco.com:80",
                 'https': "http://proxy.esl.cisco.com:80"
                }

color_map = {1:'Default',3:'Warning',4:'Attention'}

def requestHandler(type: Literal["GET", "POST"], url: str, data: Union[dict, None] = None, maxRetries=5):
    botHeader = {'Authorization': f'Bearer {getEnv().webexAccessToken}'}
    response = requests.request(
        type, url, json=data, headers=botHeader, proxies=proxy_server, timeout=20)

    if response.status_code == 200:
        return response

    errorException = Exception(
        f"request ended with an error: ${response.text}, with code: ${response.status_code}")

    if response.status_code == 429:
        if maxRetries > 0:
            sleepTime = int(response.headers['Retry-After'])
            print("Rate limited, sleeping for", sleepTime, "seconds")
            time.sleep(sleepTime+0.5)
            return requestHandler(type, url, data, maxRetries-1)
        else:
            raise errorException

    raise errorException


# def getHumanReadableText(cases: List[str], username: str):
#     """
#     This function returns the message to be sent in a human readable format
#     """
#     link = 'https://mwz.cisco.com/'
#     text = f'Owner: {username}\n'
#     for case in cases:
#         try:
#             caseCount = db_Obj.getCaseCount(username, case)
#         except Exception as error:
#             logging.debug(f"Error occured while executing 'b_Obj.getCaseCount()': {error}")
#         caseUrl = link + case
#         if caseCount < 3:
#             text += f'SR: [{case}]({caseUrl}) Customer Updated\n'
#         elif caseCount < 4:
#             text += f'**SR: [{case}]({caseUrl}) Customer Updated**\n'
#         else:
#             text += f'**SR: [{case}]({caseUrl}) Customer Updated - Please take action!**\n'
#     text = text.strip()
#     return text

def getHumanReadableText(work_groupID: str, cases: List[str], username: str):

    card_json = get_card(username)

    for case in cases:
        try:
            caseCount = db_Obj.getCaseCount(username, case)
            text = get_TB_JSON(work_groupID, case, caseCount)
            # card["content"]["body"].append(text) 
            card_json["content"]["body"][1]["columns"][0]["items"].extend(text) 
            logging.debug(f"Card structure is: {card_json}") 
        except Exception as error:
            logging.debug(f"Error occured while executing 'b_Obj.getCaseCount()': {error}")
    
    return card_json


def notifyCustomerUpdated(work_groupID: str, roomId: str, username: str, cases: List[str]):
    """
    This function sends the cases updated message to the group
    """
    if len(cases) == 0:
        return
    text = getHumanReadableText(work_groupID, cases, username)
    toSend = {'roomId': roomId, 'text':" ", 'attachments': [text]}
    # toSend = {'roomId': roomId, 'markdown':text}
    url = 'https://webexapis.com/v1/messages'
    requestHandler("POST", url, toSend)


def isOutOfOffice(username: str, roomId: str):
    """
    This function checks whether a particular user is Out of Office or not.
    """
    current_status = None

    try:
        current_status = db_Obj.is_eng_OOO(username, roomId)
    except Exception as error:
        logging.debug(f"Error getting current status for {username} traceback as follows {e}")

    if(current_status == None):

        email = f'{username}@cisco.com'
        url = f'https://webexapis.com/v1/people?email={email}'
        response = requestHandler("GET", url)
        response_json = response.json()
        items = response_json.get('items')

        if (len(items) == 0):
            raise Exception("Username not found", username)

        status = items[0].get('status')

        if (status == 'OutOfOffice'):
            db_Obj.set_OOO_REngineers(username, "True", roomId)
            return 1
        db_Obj.set_OOO_REngineers(username, "False", roomId)
        return 0
    
    else:
        try:
            curr_eng_status = db_Obj.is_eng_OOO(username, roomId)
        except Exception as e:
            logging.error(f"Error getting current status for {username} traceback as follows {e}")
        return 1 if curr_eng_status else 0


def getMessage(messageid: str):
    url = f'https://webexapis.com/v1/messages/{messageid}'
    response = requestHandler("GET", url)
    response = response.json()
    text = response.get("text")
    return text


def sendMessage(roomid: str, message: str, messageid: Optional[str] = None):
    url = 'https://webexapis.com/v1/messages/'
    if messageid is not None:
        toSend = {'roomId': roomid, 'text': message, 'parentId': messageid}
    else:
        toSend = {'roomId': roomid, 'text': message}
    requestHandler("POST", url, data=toSend)
    return

def get_card(username):
    card = {

                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                                "type": "AdaptiveCard",
                                "body": [
                                            {
                                                "type": "TextBlock",
                                                "text": f"Owner: {username}",
                                                "color": "Default",
                                                "isSubtle": False,
                                                "wrap": True,
                                                "size": "medium",
                                                "spacing": "small",
                                            },

                                            {
                                                "type": "ColumnSet",
                                                "columns": [

                                                            {   "type": "Column",
                                                                "items": [],
                                                                "spacing":'small'
                                                            }
                                                           ],
                                                "spacing":'medium'
                                            }
                                        ],
                                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                                "version": "1.2"
                            }
            }
    return card

def trim(input_string):

    pattern_1 = re.compile(r'regards?', flags=re.IGNORECASE)
    match = pattern_1.search(input_string)

    pattern = re.compile(r'\[cid[0-9a-f\-]+\]\s*<[^>]+>')
    input_string = filter(None, map(str.strip, filter(lambda line: not re.search(pattern, line), input_string.split('\n'))))
    input_string = '\n'.join(input_string)

    if match:
        output_string = input_string[:match.end()].strip()
        if(len(output_string)>=650):
            truncated_string = output_string[:650]
            lines = truncated_string.split('\n')[:-1]
            truncated_string = '\n'.join(lines)
            return truncated_string
        return output_string
    else:
        lines = input_string.split('\n')[:5]
        truncated_string = '\n'.join(lines)
        truncated_string = truncated_string.split('.')[:5]
        truncated_string = '.'.join(truncated_string)
        return truncated_string

def get_TB_JSON(work_groupID, sr_number, count):
    
    link = 'https://mwz.cisco.com/'
    caseUrl = link + sr_number
    c_map = None
    t_msg = None
    w = None
    
    tb_JSON = {   
                "type": "TextBlock",
                "text": None,
                "color": None,
                "isSubtle": False,
                "wrap": True,
                "size": "default",
                "spacing": "small",
                # "weight": None
              }

    if(count >=4):
        logging.debug(f"Count:{count}")
        tb_JSON["color"] = color_map[4]
        tb_JSON["text"] = f'**SR:** [{sr_number}]({caseUrl}) **Customer Updated - Please take immediate action!**'
        # tb_JSON["weight"] = "bolder"
        return [tb_JSON]

    elif(count == 3):
        logging.debug(f"Count:{count}")
        tb_JSON["color"] = color_map[3]
        tb_JSON["text"] = f'**SR:** [{sr_number}]({caseUrl}) **Customer Updated**'
        # tb_JSON["weight"] = "bolder"
        return [tb_JSON]
    
    elif(count == 2):
        logging.debug(f"Count:{count}")
        tb_JSON["color"] = color_map[1]
        tb_JSON["text"] = f'**SR:** [{sr_number}]({caseUrl}) **Customer Updated**'
        # tb_JSON["weight"] = "default"
        return [tb_JSON]
    
    else:
        logging.debug(f"Count:{count}")
        tb_JSON["color"] = color_map[1]
        tb_JSON["text"] = f'SR: [{sr_number}]({caseUrl}) Customer Updated'
        # tb_JSON["weight"] = "default"

        current_date = date.today().strftime("%Y-%m-%d")
        if(db_Obj.is_Unique(work_groupID, sr_number, current_date)):
            try:   
                logging.debug(f"{sr_number} is Uniqueue")
                last_email = salesforce.get_SR_Last_Email_Update(sr_number)
                trimmed_email = trim(last_email)
                last_email_json = {   
                                    "type": "TextBlock",
                                    "text": trimmed_email,
                                    "color": 'default',
                                    "isSubtle": True,
                                    "wrap": True,
                                    "size": "small",
                                    "spacing": "small",
                                }
                return [tb_JSON, last_email_json]
            
            except Exception as error:
                logging.debug(f"Getting Last Email Failed with Error:{error}\n Input:{sr_number}")
                return [tb_JSON]
        else:
            logging.debug(f"{sr_number} is not Uniqueue, inputs {work_groupID, sr_number, current_date}")
            return [tb_JSON]