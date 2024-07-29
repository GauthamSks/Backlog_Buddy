import os
import time
import logging
import schedule
from db import r_DB
from botstuff import env
from botstuff.bot import parseGroup, processRoom, updateRoomId, isCurrentTimeinRange

env.initEnv()

logging.basicConfig(
    filename="/home/cisco/Desktop/Backlog_Buddy_V2/Bots.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logging.debug(f"BOT Executed")

db_Obj = r_DB()

logging.debug(f"DB Instance Created")

def cron():

    for work_groupID in db_Obj.get_workgroups():

        try:

            s_day, e_day, s_hr, e_hr, s_min, e_min = db_Obj.get_wg_timings(work_groupID)

        except Exception as e:

            logging.error(f"Error retrieving workgroup details for {work_groupID} Trace back as follows {e}")

        if isCurrentTimeinRange(s_day, e_day, s_hr, e_hr, s_min, e_min):
            
            work_group_rooms = {}
            
            for room_ID in db_Obj.get_wg_rooms(work_groupID):
                try:
                    work_group_rooms[room_ID] = db_Obj.get_engineers(room_ID)
                except Exception as e:
                    logging.error(f"Error retrieving engineers for {room_ID} Trace back as follows {e}")
        
            work_group_OOO_rooms = parseGroup(work_group_rooms)
            updated_work_group_OOO_rooms = updateRoomId(work_group_OOO_rooms, work_group_rooms)

            print(f"This is groups OOO {work_groupID}", updated_work_group_OOO_rooms)
            newrooms = updated_work_group_OOO_rooms.keys()
            for id in newrooms:
                processRoom(work_groupID, id, updated_work_group_OOO_rooms[id])
        else:
            print(f'{work_groupID} not in shift')

schedule.every(30).minutes.do(cron)

while True:
    schedule.run_pending()
    time.sleep(1)