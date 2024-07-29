import re
import requests
from db import r_DB
from datetime import date
from botstuff.env import getEnv, refreshSalesforceToken

db_Obj = r_DB()

proxy_server = {
                 'http':"http://proxy.esl.cisco.com:80",
                 'https': "http://proxy.esl.cisco.com:80"
                }

def getCases(status: str, username: str, attemptCount=0):
    """
    This function returns the list of all the cases of a particular status and particular user
    """
    query = f"SELECT C3_SR_Number__c FROM Case WHERE Status='{status}' AND Case_Owner__c = '{username}'".replace(
        ' ', '+')

    header = {'Authorization': f'Bearer {getEnv().salesforceAccessToken}'}
    base_url = 'https://csone.my.salesforce.com/services/data/v56.0/'
    query_url = f'{base_url}query?q={query}'
    response = requests.get(query_url, headers=header, proxies=proxy_server, timeout=20)
    if (response.status_code == 401 and attemptCount < 1):
        refreshSalesforceToken()
        return getCases(status, username, attemptCount+1)
    if (response.status_code != 200):
        raise Exception(
            f"request ended with an error: {response.text}, with code: ${response.status_code}")
    response_json = response.json()
    case_full = response_json.get("records")
    cases = [item.get('C3_SR_Number__c') for item in case_full]
    return cases

def get_SR_Last_Email_Update(sr_id: str, attemptCount=0):
    
    query = f"SELECT+CreatedDate,Id,NoteStatus__c,B2B_Note_Status__c,NoteType__c,Created_By_C3_User_Id__c,Note__c,IsJunk__c,Title__c+FROM+Shadow_Note__c+WHERE+Case_C3Number__c+=+'{sr_id}'+AND+NoteType__c+in+('Email In','Web Update')+AND+NoteStatus__c+=+true+ORDER+BY+CreatedDate+desc+NULLS+LAST+LIMIT+1"    
    
    header = {'Authorization': f'Bearer {getEnv().salesforceAccessToken}'}
    base_url = 'https://csone.my.salesforce.com/services/data/v56.0/'
    query_url = f'{base_url}query?q={query}'
    response = requests.get(query_url, headers=header, proxies=proxy_server, timeout=20)
    if (response.status_code == 401 and attemptCount < 1):
        refreshSalesforceToken()
        return get_SR_Last_Email_Update(sr_id, attemptCount+1)
    if (response.status_code != 200):
        raise Exception(
            f"request ended with an error: {response.text}, with code: ${response.status_code}")
    response_json = response.json()
    note_type = response_json.get("records")[0]['NoteType__c']
    case_note = response_json.get("records")[0]['Note__c']
    
    if(note_type == "Email In"):
        case_note = re.split("Subject: .*\n", re.split("From: ", case_note)[1])[1]
        case_note = re.sub(r'[\r\n]+', '\n', case_note.strip())    
    
    return case_note

    

def getCustomerUpdatedCases(username: str):
    """
    This function returns the list of all the Customer Updated cases of a particular user
    """
    return getCases('Customer Updated', username)