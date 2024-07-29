import logging
from db import r_DB
from datetime import date, datetime
from typing import Dict, List, Literal

from botstuff import salesforce, webex

db_Obj = r_DB()


def parseGroup(groups: Dict[str, List[str]]):
    rooms = groups.keys()
    groupsOOO: Dict[str, List[str]] = {}
    for id in rooms:
        users = groups[id]
        groupsOOO[id] = []
        for username in users:
            try:
                if webex.isOutOfOffice(username, id) == 1:
                    groupsOOO[id].append(username)
            except Exception as e:
                logging.error(
                    f"Error occurred while checking out of office for {username}"
                )
                logging.exception(e)
                continue
    return groupsOOO

def processUser(work_groupID: str, username: str, roomId: str):
    logging.debug(f"Pinging cases for {username}")

    current_date = date.today().strftime("%Y-%m-%d")

    cases = salesforce.getCustomerUpdatedCases(username)

    case_count = len(cases)
    logging.debug(f"Found {case_count} Customer Updated Cases for {username}")

    try:
        db_Obj.setUserCases(username, cases)
    except Exception as e:
        logging.error(
            f"Error marking cases for user {username} traceback as follows {e}"
        )

    webex.notifyCustomerUpdated(work_groupID, roomId, username, cases)
    logging.debug(f"Notified {case_count} customer updated cases of {username} to their room")

    try:
        db_Obj.update_ROI(work_groupID, cases, current_date)
    except Exception as e:
        logging.error(f"Error calling the update_ROI function: {e}")


def processRoom(work_groupID: str, id: str, users: List[str]):
    for username in users:
        try:
            processUser(work_groupID, username, id)
        except Exception as error:
            logging.exception(f"Error while executing the 'processUser()':{error}")
            continue


def updateRoomId(groupsOOO: Dict[str, List[str]], groups: Dict[str, List[str]]):
    outOfOfficeRooms = []
    weightedActiveRooms: Dict[str, int] = {}

    for roomId in groupsOOO:
        if len(groupsOOO[roomId]) == len(groups[roomId]):
            outOfOfficeRooms.append(roomId)
        else:
            weightedActiveRooms[roomId] = len(groupsOOO[roomId])

    priorityRooms = sorted(weightedActiveRooms.items(), key=lambda x: x[1])
    priorityRoomIds = [i[0] for i in priorityRooms]

    assert len(outOfOfficeRooms) <= len(priorityRoomIds)

    for index in range(len(outOfOfficeRooms)):
        sourceRoomId = outOfOfficeRooms[index]
        destRoomId = priorityRoomIds[index]
        groupsOOO[destRoomId] += groupsOOO[sourceRoomId]
        groupsOOO[sourceRoomId] = []
        try:
            all_OOOflag = db_Obj.get_aOOO_Room(destRoomId)
        except Exception as error:
            logging.exception(f"Error occured while executing 'db_Obj.get_aOOO_Room()':{error}")
        
        if all_OOOflag == True:
                continue
        else:
            webex.sendMessage(
                sourceRoomId,
                "As all engineers in this group are currently OOO, we will be sending their case updates to another space.",
            )
            webex.sendMessage(
                destRoomId,
                "As all engineers in another space are currently OOO, we will be sending their case updates here",
            )
            db_Obj.set_aOOO_Room(destRoomId, "True")
    return groupsOOO

def isCurrentTimeinRange(
    startDay: Literal[0, 1, 2, 3, 4, 5, 6],
    endDay: Literal[0, 1, 2, 3, 4, 5, 6],
    startHour: int,
    endHour: int,
    startMin: int,
    endMin: int,
):
    tolerable_diff = 5

    now = datetime.today()
    dayOfWeek = now.weekday()

    if dayOfWeek < startDay or dayOfWeek > endDay:
        return False
    if now.hour < startHour or now.hour > endHour:
        return False
    if now.hour == startHour and now.minute < startMin - tolerable_diff:
        return False
    if now.hour == endHour and now.minute > endMin + tolerable_diff:
        return False

    return True