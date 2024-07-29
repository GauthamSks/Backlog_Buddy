import redis
import logging
from typing import List

class r_DB:

    def __init__(self):
        
        try:
            self.db = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        except Exception as e:
            logging.debug(f" Failed to connect to Redis Server: {e}")


    def get_engineers(self, room_id: str):
        # Function to return list of engineers part of the room
        ## room_id: room token 
        ## Return type: List[str]
        return list(self.db.smembers(room_id))

    def get_workgroups(self):
        # Function to return list of Workgroups
        ## Return type: List[str]

        key = "wgroup_ids"
        return list(self.db.smembers(key)) 
    
    def get_wg_rooms(self, wg_ID: str):
        # Function to return list of rooms associated with the given Workgroup ID
        ## wg_ID: Workgroup ID
        ## Return type: List[str]

        return list(self.db.smembers(wg_ID)) 

    def get_wg_details(self, wg_ID: str):
        # Function to return the Workgroup details, which is a dict
        ## wg_ID: Workgroup ID
        ## Return type: Dict[str:str]
        
        key = wg_ID + "_details" 
        return self.db.hgetall(key)

    def get_wg_timings(self, wg_ID: str):
        # Function to return the Workgroup timings
        ## wg_ID: Workgroup ID
        ## Return type: int, int, int, int, int, int

        wg_details = self.get_wg_details(wg_ID)
        
        s_day = int(wg_details["start_day"])
        e_day = int(wg_details["end_day"])
        s_h,s_m = [int(val) for val in wg_details["start_time"].split(":")]
        e_h,e_m = [int(val) for val in wg_details["end_time"].split(":")]

        return s_day, e_day, s_h, e_h, s_m, e_m

    def remove_Engineer(self, cec_ID: str, room_ID: str):
        # Function to remove the engineer from the given space.
        ## cec_ID: Engineer CEC-ID
        ## room_ID: room token
        ## Return type: str  

        if(self.db.sismember(room_ID, cec_ID)):
            self.db.srem(room_ID, cec_ID)
            return f"{cec_ID} is removed succesfully from the space"
        else:
            return f'{cec_ID} is not part of the space'

    def add_Engineer(self, cec_ID: str, room_ID: str):
        # Function to add the engineer to the given space.
        ## cec_ID: Engineer CEC-ID
        ## room_ID: room token
        ## Return type: str     
    
        if(not self.db.sismember(room_ID, cec_ID)):
            self.db.sadd(room_ID, cec_ID)
            return f"{cec_ID} is added succesfully to the space"
        else:
            return f'{cec_ID} is already part of the space'

    def set_OOO_REngineers(self, cec_ID: str, is_OOO: bool, room_ID: str):
        # This function sets the current OOO status for all the engineers in the Room
        # This key expires after 3hrs
        ## cec_ID: Engineer CEC-ID
        ## is_OOO: True/False
        ## room_ID: room token
        
        key = room_ID + '_currentOOO'

        #check if the key exist
        if(self.db.exists(key)):
            #if room_ID key exist, append the cec_ID to the list 
            self.db.hset(key, cec_ID, is_OOO)
        else:
            #Create the key and then add the cec_ID and set the expiry time to 3hrs
            #Expiry time of this key would be 3hrs (3*60*60), so that it will take care of PPL on HD as well
            self.db.hset(key, cec_ID, is_OOO)
            self.db.expire(key, 3*60*60)

    def is_Member(self, cec_ID: str, room_ID: str):
        # For the given room_ID this function to checks if the give cec_ID is part of the Room 
        ## cec_ID: Engineer CEC-ID
        ## room_ID: room token
        ## Return Type: boolean

        if(self.db.sismember(room_ID, cec_ID)):
            return True
        return False

    def is_eng_OOO(self, cec_ID: str, room_ID: str):
        # For the given room_ID this function to checks if the give cec_ID is currently OOO 
        ## cec_ID: Engineer CEC-ID
        ## room_ID: room token
        ## Return Type: boolean

        key = room_ID + '_currentOOO'

        # if modified OOO status flag is set then return True 
        if(self.get_mengOOO(cec_ID)):
            return True
        elif(self.db.hget(key,cec_ID) != None):
            return eval(self.db.hget(key,cec_ID))
        else:
            return None
    
    def set_aOOO_Room(self, room_ID: str, flag: bool):
        #If all the engineers of this room are OOO set this flag.
        ## room_ID: room token
        ## flag: True/False
        
        key = room_ID + '_OOOflag'
        self.db.set(key, flag)
        self.db.expire(key, 8*60*60)

    def get_aOOO_Room(self, room_ID: str):  
        # Function to get the value of 'room_ID_OOOflag', 
        # This flag is used to send custom initial msg in case if all engineers of this room are OOO.
        ## room_ID: room token
        ## Return Type: boolean
 
        key = room_ID + '_OOOflag'
        if(self.db.get(key) != None):
            return eval(self.db.get(key))
        return None

    def getCaseCount(self, cec_id: str, sr_no: str):
        # This function returns no of times give sr has been pinged and no action has been taken.
        ## cec_ID: Engineer CEC-ID
        ## sr_no: #SR No
        ## Return Type: int

        case_Count = self.db.hget(cec_id,sr_no)
        if case_Count:
            return int(case_Count)
        else:
            return 0
    
    def removeCaseCount(self, cec_ID: str, sr_no: str):
        # Function to remove the SR, for which the backlog buddy has taken actions for.
        ## cec_ID: Engineer CEC-ID
        ## sr_no: #SR No
                
        self.db.hdel(cec_ID, sr_no)

    def getUserCases(self, cec_ID: str):
        # Function to retun the existing list of Customer Updated Cases for the given cec_ID
        ## cec_ID: Engineer CEC-ID
        ## Return Type: List[str]

        if bool(self.db.hgetall(cec_ID)):
            return list(self.db.hgetall(cec_ID).keys())
        else:
            return []

    def setUserCases(self, cec_ID: str, updated_sr_nos: List[str]):
        # Function to set the Customer Updated Cases for the given cec_ID
        ## cec_ID: Engineer CEC-ID
        ## updated_sr_nos: List of update Sr_Nos

        existing_engCases = self.getUserCases(cec_ID)

        for sr_no in existing_engCases:
            if sr_no not in updated_sr_nos:
                self.removeCaseCount(cec_ID, sr_no)

        for sr_no in updated_sr_nos:
            #check if the cec_ID key exist
            if(self.db.exists(cec_ID)):
                #check if sr_no already exists
                if(self.db.hexists(cec_ID, sr_no)):
                    # Increase the count by +1
                    curr_count = int(self.db.hget(cec_ID,sr_no))
                    self.db.hset(cec_ID,sr_no,curr_count+1)
                else:
                    self.db.hset(cec_ID,sr_no,1)
            else:
                #if cec_ID key does not exist create the key and set sr_no count as 1.
                self.db.hset(cec_ID, sr_no, 1)
                self.db.expire(cec_ID, 8*60*60)

    def get_myRooms(self, m_id: str):
        # Function to return the list of rooms assocaited with the Manager
        ## m_id: Manager CEC-ID 
        ## Return type: List[str]

        key = m_id + '_rooms'

        return list(self.db.smembers(key))
    
    def is_manager(self, cec_id: str):
        # Function to check if the given CEC-ID belongs to a Manager
        ## cec_id: Manager CEC-ID 
        ## Return type: Boolean

        key = "manager_ids"
        if(self.db.sismember(key, cec_id)):
            return True
        else:
            return False
    
    def set_mengOOO(self, cec_id: str):
        # Function to set if the Engineer OOO Modified Status Flag is set.
        ## cec_ID: Engineer CEC-ID

        key = cec_id + "_mOOOflag"
        self.db.set(key, "True")
        self.db.expire(key, 8*60*60)

    def get_mengOOO(self, cec_id: str):
        # Function to get the Engineer OOO Modified Status Flag.
        ## cec_ID: Engineer CEC-ID
        ## Return Type: Boolean

        key = cec_id + "_mOOOflag"
        if(self.db.exists(key)):
            return True
        else:
            return False
        
    def update_ROI(self, work_groupID: str, sr_List: List[str], date: str):
        
        key = f'{work_groupID}_{date}'

        if(self.db.exists(key)):
            for sr in sr_List:
                if(not self.db.sismember(key, sr)):
                    self.db.sadd(key, sr)
        else:
            for sr in sr_List:
                if(not self.db.sismember(key, sr)):
                    self.db.sadd(key, sr)

    def is_Unique(self, work_groupID: str, sr_ID: str, date: str):

        key = f'{work_groupID}_{date}'

        if(self.db.exists(key)):
            if(self.db.sismember(key,sr_ID)):
                return False
            else:
                return True
        else:
            return True

    def get_ROI(self, work_groupID, date):

        key = f'{work_groupID}_{date}'
        if(self.db.exists(key)):
            return list(self.db.smembers(key))
        return None
    
    def remove_ROI_Cache(self,  work_groupID, date):
        key = f'{work_groupID}_{date}'
        self.db.delete(key)