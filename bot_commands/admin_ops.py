import logging

logging.basicConfig(
    filename="/home/calo/Desktop/Backlog_Buddy/Websocket.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from db import r_DB
from webexteamssdk import WebexTeamsAPI
from webex_bot.formatting import quote_info
from webexteamssdk.models.cards.inputs import Choices
from webexteamssdk.models.cards.actions import Submit
from webex_bot.models.command import Command, CALLBACK_KEYWORD_KEY
from webex_bot.models.response import response_from_adaptive_card
from webexteamssdk.models.cards import Text, TextBlock, FontWeight, FontSize, AdaptiveCard, Choice, Toggle

from botstuff.env import getEnv

try:
    db_Obj  = r_DB()
except Exception as e:
    logging.debug("Failed to create Redis object, please check if redis-server is running")

API = WebexTeamsAPI(getEnv().webexAccessToken)

class admin_opsCMD(Command):

    def __init__(self):
        super().__init__(
            command_keyword="admin_ops",
            help_message="Admin Options",
            delete_previous_message=True)
                
    def execute(self, message, attachment_actions, activity):

        is_mgr = None
        user_id = None
        sender_id = attachment_actions.personId

        try:
            user_id = API.people.get(sender_id).userName.split("@")[0]
            is_mgr = db_Obj.is_manager(user_id)
        except Exception as e:
            logging.debug(f"Failed to execute 'is_manager()' traceback as follows {e}")
            return 0

        if(is_mgr):

            heading = TextBlock("Select Options", weight=FontWeight.BOLDER, size=FontSize.LARGE, wrap=True)

            add_cmd = Submit(title="Add",
                            data={
                                CALLBACK_KEYWORD_KEY: "add",
                                "m_id":user_id
                            })
            
            remove_cmd = Submit(title="Remove",
                            data={
                                CALLBACK_KEYWORD_KEY: "remove",
                                "m_id":user_id
                            }) 
            
            list_cmd = Submit(title="List",
                            data={
                                CALLBACK_KEYWORD_KEY: "list",
                                "m_id":user_id
                            }) 
            
            update_cmd = Submit(title="Update",
                            data={
                                CALLBACK_KEYWORD_KEY: "update",
                                "m_id":user_id
                            }) 

            card = AdaptiveCard(body=[heading], actions=[add_cmd, remove_cmd, list_cmd, update_cmd])
            
            return response_from_adaptive_card(card)
        
        else:
            return quote_info("!!!Action not allowed, You are not an Admin")
            
class addCMD(Command):

    def __init__(self):
        super().__init__(
            card_callback_keyword="add",
            delete_previous_message=True)
        
    def execute(self, message, attachment_actions, activity):
        
        user_id = attachment_actions.inputs.get("m_id")

        heading_1 = TextBlock("Add Engineer", weight=FontWeight.BOLDER, size=FontSize.LARGE, wrap=True)
        heading_2 = TextBlock("CEC-ID",wrap=True, isSubtle=True)
        input_text = Text(id="input_CEC_ID", placeholder="Enter CEC-ID here", maxLength=50)
        heading_3 = TextBlock("Select the Space",wrap=True, isSubtle=True)

        try:
            room_ids = db_Obj.get_myRooms(user_id)
        except Exception as error:
            logging.debug(f"Failed to execute 'get_myRooms' function for user {user_id} with error {error}")
            return 0

        #Create the choice objects
        room_list = []

        for room_id in room_ids:

            room_name = None
            
            try:
                room_name = API.rooms.get(room_id).title
            except Exception as error:
                print(f"Room name lookup failed with error {error}")
            
            c_obj = Choice(title=room_name, value=room_id)
            room_list.append(c_obj)

        drop_down_menu = Choices(id='room_id', choices=room_list)

        submit_action = Submit(title="submit",
                        data={
                            CALLBACK_KEYWORD_KEY: "execute_add",
                            "m_id": user_id
                        })

        card = AdaptiveCard(body=[heading_1, heading_2, input_text, heading_3, drop_down_menu], actions=[submit_action])

        return response_from_adaptive_card(card) 
    
class addCallback(Command):

    def __init__(self):
        super().__init__(
            card_callback_keyword="execute_add",
            delete_previous_message=True) 

    def execute(self, message, attachment_actions, activity):

        manager_id = attachment_actions.inputs.get("m_id")
        eng_id = attachment_actions.inputs.get("input_CEC_ID")
        room_id = attachment_actions.inputs.get("room_id")
        src_room_id = attachment_actions.roomId

        if(eng_id == '' or room_id == ''):
            return quote_info(f"Failed!!! to execute 'Add' command as either CEC-ID or the Space was not entered")
        
        status = db_Obj.add_Engineer(eng_id, room_id)
        return quote_info(status) 
    
class removeCMD(Command):

    def __init__(self):
        super().__init__(
            card_callback_keyword="remove",
            delete_previous_message=True)
        
    def execute(self, message, attachment_actions, activity):

        user_id = attachment_actions.inputs.get("m_id")

        heading_1 = TextBlock("Remove Engineer", weight=FontWeight.BOLDER, size=FontSize.LARGE, wrap=True)
        heading_2 = TextBlock("CEC-ID",wrap=True, isSubtle=True)
        input_text = Text(id="input_CEC_ID", placeholder="Enter CEC-ID here", maxLength=50)
        heading_3 = TextBlock("Select the Space",wrap=True, isSubtle=True)

        try:
            room_ids = db_Obj.get_myRooms(user_id)
        except Exception as error:
            logging.debug(f"Failed to execute 'get_myRooms' function for user {user_id} with error {error}")
            return 0

        #Create the choice objects
        room_list = []

        for room_id in room_ids:

            room_name = None
            
            try:
                room_name = API.rooms.get(room_id).title
            except Exception as error:
                print(f"Room name lookup failed with error {error}")
            
            c_obj = Choice(title=room_name, value=room_id)
            room_list.append(c_obj)

        drop_down_menu = Choices(id='room_id', choices=room_list)

        submit_action = Submit(title="submit",
                        data={
                            CALLBACK_KEYWORD_KEY: "execute_remove",
                            "m_id": user_id
                        })

        card = AdaptiveCard(body=[heading_1, heading_2, input_text, heading_3, drop_down_menu], actions=[submit_action])

        return response_from_adaptive_card(card) 
    
class removeCallback(Command):

    def __init__(self):
        super().__init__(
            card_callback_keyword="execute_remove",
            delete_previous_message=True) 

    def execute(self, message, attachment_actions, activity):

        manager_id = attachment_actions.inputs.get("m_id")
        eng_id = attachment_actions.inputs.get("input_CEC_ID")
        room_id = attachment_actions.inputs.get("room_id")
        src_room_id = attachment_actions.roomId

        if(eng_id == '' or room_id == ''):
            return quote_info(f"Failed!!! to execute 'Remove' command as either CEC-ID or the Space was not entered")

        status = db_Obj.remove_Engineer(eng_id, room_id)
        
        return quote_info(status) 
    
class listCMD(Command):

    def __init__(self):
        super().__init__(
            card_callback_keyword="list",
            delete_previous_message=True)
        
    def execute(self, message, attachment_actions, activity):

        user_id = attachment_actions.inputs.get("m_id")

        heading_1 = TextBlock("List the Engineers", weight=FontWeight.BOLDER, size=FontSize.LARGE, wrap=True)
        heading_2 = TextBlock("Select the Space",wrap=True, isSubtle=True)

        try:
            room_ids = db_Obj.get_myRooms(user_id)
        except Exception as error:
            logging.debug(f"Failed to execute 'get_myRooms' function for user {user_id} with error {error}")
            return 0

        #Create the choice objects
        room_list = []

        for room_id in room_ids:
            
            room_name = None
            
            try:
                room_name = API.rooms.get(room_id).title
            except Exception as error:
                print(f"Room name lookup failed with error {error}")
            
            c_obj = Choice(title=room_name, value=room_id)
            room_list.append(c_obj)

        drop_down_menu = Choices(id='room_id', choices=room_list)

        submit_action = Submit(title="submit",
                        data={
                            CALLBACK_KEYWORD_KEY: "execute_list",
                            "m_id": user_id
                        })

        card = AdaptiveCard(body=[heading_1, heading_2, drop_down_menu], actions=[submit_action])

        return response_from_adaptive_card(card)
    
class listCallback(Command):

    def __init__(self):
        super().__init__(
            card_callback_keyword="execute_list",
            delete_previous_message=True)
        
    def execute(self, message, attachment_actions, activity):

        room_id = attachment_actions.inputs.get("room_id")

        if(room_id == ''):
            text = "Failed to execute 'List' command as the space was not selected"
            return quote_info(text)

        src_room_id = attachment_actions.roomId
        eng_list = db_Obj.get_engineers(room_id)
        heading = "<b>Current Engineers of the Selected Space:</b>"
        text = heading + '<br><br>- ' + '<br>- '.join(map(str, eng_list))

        return quote_info(text)

class updateCMD(Command):

    def __init__(self):
        super().__init__(
            card_callback_keyword="update",
            delete_previous_message=True)
        
    def execute(self, message, attachment_actions, activity):
        
        user_id = attachment_actions.inputs.get("m_id")

        heading_1 = TextBlock("Update Engineer Status", weight=FontWeight.BOLDER, size=FontSize.LARGE, wrap=True)
        heading_2 = TextBlock("CEC-ID", wrap=True, isSubtle=True)
        input_text = Text(id="input_cid", placeholder="Enter CEC-ID here", maxLength=50)
        heading_3 = TextBlock("Select the Space",wrap=True, isSubtle=True)
        heading_4 = TextBlock("Change OOO Status",wrap=True, isSubtle=True)
        status = Toggle(id="ooo_status", title="Is OOO", value="True")

        try:
            room_ids = db_Obj.get_myRooms(user_id)
        except Exception as error:
            logging.debug(f"Failed to execute 'get_myRooms' function for user {user_id} with error {error}")
            return 0

        #Create the choice objects
        room_list = []

        for room_id in room_ids:

            room_name = None
            
            try:
                room_name = API.rooms.get(room_id).title
            except Exception as error:
                print(f"Room name lookup failed with error {error}")
            
            c_obj = Choice(title=room_name, value=room_id)
            room_list.append(c_obj)

        drop_down_menu = Choices(id='room_id', choices=room_list)

        submit_action = Submit(title="submit",
                        data={
                            CALLBACK_KEYWORD_KEY: "execute_update",
                            "m_id": user_id
                        })
        
        card = AdaptiveCard(body=[heading_1, heading_2, input_text, heading_3, drop_down_menu, heading_4, status], actions=[submit_action])

        return response_from_adaptive_card(card)
    
class updateCallback(Command):

    def __init__(self):
        super().__init__(
            card_callback_keyword="execute_update",
            delete_previous_message=True)
        
    def execute(self, message, attachment_actions, activity):

        room_id = attachment_actions.inputs.get("room_id")
        eng_cec = attachment_actions.inputs.get("input_cid")
        is_OOOFlag = attachment_actions.inputs.get("ooo_status")

        if(eng_cec == '' or room_id == ''):
            return quote_info(f"Failed!!! to execute 'Update' command as either CEC-ID or the Space was not entered")
        elif(not db_Obj.is_Member(eng_cec, room_id)):
            return quote_info(f"Failed!!! to execute 'Update' as the entered CEC-ID:{eng_cec} is not part of the space")
        elif(is_OOOFlag == 'true'):
            db_Obj.set_mengOOO(eng_cec)
            return quote_info(f"{eng_cec} status updated")
        else:
            return quote_info("Is OOO Toggle not selected!!!!")