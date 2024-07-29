import json
import redis

"""
Sample mapping_dict Data Format:

work_group:{room_id:[cec_ids]}

"""

redis_obj = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

work_group_ids = redis_obj.smembers("wgroup_ids")

mapping_dict = {}

for work_group in work_group_ids:
    room_ids = list(redis_obj.smembers(work_group))
    for room_id in room_ids:
        engineer_cec_list = list(redis_obj.smembers(room_id))
        if(mapping_dict.get(work_group)):
            mapping_dict[work_group].update({room_id:engineer_cec_list})
        else:
            mapping_dict[work_group] = {room_id:engineer_cec_list}

file_path = "./Work_group_Room_ID_Engineer_mapping_23_04_24.json"

with open(file_path, 'w') as file_ptr:
    json.dump(mapping_dict, file_ptr)
