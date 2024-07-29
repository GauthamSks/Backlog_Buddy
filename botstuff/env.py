import os
import dotenv
from typing import Union, Dict, Literal
from pydantic import BaseModel
import subprocess
import json
import shlex

class Env(BaseModel):
    webexAccessToken: str
    salesforceAccessToken: str

_env: Union[Env, None] = None

def initEnv():

    global _env

    if _env is not None:
        raise Exception('Env already initialised')

    dotenv.load_dotenv()

    webexAccessToken = os.getenv("WEBEX_ACCESS_TOKEN")
    salesforceAccessToken = os.getenv("SALESFORCE_ACCESS_TOKEN")

    if webexAccessToken is None:
        raise Exception("Webex access token not found")

    if salesforceAccessToken is None:
        raise Exception("Salesforce access token not found")

    _env = Env(
        webexAccessToken=webexAccessToken,
        salesforceAccessToken=salesforceAccessToken
    )


def refreshSalesforceToken():
    output = subprocess.run(
        shlex.split("sfdx force:org:display -u gasantho@cisco.fts --json"),
        capture_output=True
    )
    if output.returncode != 0:
        raise Exception("Something went wrong refreshing salesforce token")
    jsonout = json.loads(output.stdout)
    result = jsonout.get("result")
    if result is None:
        raise Exception("Parsing error")
    accessToken = result.get("accessToken")
    if accessToken is None:
        raise Exception("Parsing error: access token not found")
    _env.salesforceAccessToken = accessToken


def getEnv():
    if _env is None:
        raise Exception("Env not initialised")
    return _env