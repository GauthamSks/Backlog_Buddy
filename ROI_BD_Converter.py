import json
from db import r_DB
import pandas as pd

db_Obj = r_DB()

# start_date = '2023-12-01'
# end_date = '2024-01-27'

start_date = '2024-01-27'
end_date = '2024-04-27'

def get_dates(start_date, end_date):
    
    # Function to get the list of dates in yyyy-mm-dd format   

    dates_df = pd.date_range(start_date,end_date,freq='d')
    return dates_df.astype(str).to_list()

Data = {}


for wg_id in db_Obj.get_workgroups():
    for date in get_dates(start_date, end_date):
        unique_case_list = db_Obj.get_ROI(wg_id, date)
        if(unique_case_list!=None):
            if(wg_id not in Data):
                Data[wg_id] = {date:unique_case_list}
            else:
                Data[wg_id].update({date:unique_case_list})

def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError    

with open("/home/cisco/Desktop/Backlog_Buddy_V2/ROI_Data/ROI_Data_BB(2024-01-28_to_2024-04-27).json", 'w') as fp:
    json.dump(Data, fp, default=set_default)

## Remove the keys after writing to the file:
# def cleanUp(start_date, end_date):
#     for wg_id in db_Obj.get_workgroups():
#         for date in get_dates(start_date, end_date):
#             db_Obj.remove_ROI_Cache(wg_id, date)
