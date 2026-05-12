import json
from dotenv import load_dotenv
import requests
import datetime
import os
from pydantic import BaseModel, Field
from pydantic_ai import Agent , ModelSettings, settings

from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.mistral import MistralProvider
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.models.ollama import OllamaModel

from report import *
from qdrant_client import qdrant_client


load_dotenv()





x_accounts = [
    "danawhite",
    "ChampRDS",
    "arielhelwani",
    "realkevink",
]

def getPostsById(id: str , cursor: str | None = None) -> tuple:
    """
    This is an RAPID api available at : https://rapidapi.com/alexanderxbx/api/twitter-api45/
    that allows to get all the recent posts from a given X id.
    This call returns the 19 most recent posts of a X user with ID: <id>, along with prev
    and next page pointers.

    Args:
        - id : str, the X id of profile
        - cursor : str , the "next_page" of the posts ( used by the RAPID API)
    Returns:
        - tuple :
            - dict : a dictionary that contains the output of the API Call
            - string : a cursor (next_page pointer) to the next page of 19 posts of the user

    The api follows the below structure:
        curl --request GET \
            --url 'https://twitter-api45.p.rapidapi.com/timeline.php?screenname=DovySimuMMA' \
            --header 'Content-Type: application/json' \
            --header 'x-rapidapi-host: twitter-api45.p.rapidapi.com' \
            --header 'x-rapidapi-key: 3279362f39msh18933dc9449f741p14d976jsn5f331005d583'
    """

    url = 'https://twitter-api45.p.rapidapi.com/timeline.php'
    headers = {
	    'Content-Type': 'application/json',
	    'x-rapidapi-host': 'twitter-api45.p.rapidapi.com',
	    'x-rapidapi-key':  os.getenv("RAPID_API_KEY")
    }
    params={
        'screenname': id,
    }

    if cursor != None:
        params['cursor'] = cursor

    response = requests.get(url, headers=headers, params= params)

    if response.ok:
        response = response.json()
        next_cursor = response["next_cursor"]
        return response, next_cursor

    else:
        print(f"Error: {response.status_code}")
        return None,None

def getTodaysPostsById(id) -> list:
    """
    Get all the X posts of a user with ID : <id> from withing a day from the time of the call.
    Args:
        - id : string, the X ID of the user
    Returns:
        - list(strings): a list of the texts of all the posts of a user from withing 24 hours
            from the time of the request
    """
    def transformDate(dt: str)-> datetime.datetime:
        """
        Transorms a "created_at" string to a datetime.datetime object
        Args:
            - dt : a string of a date
        Returns:
            - datetime.datetime
        """
        try:
            date_object = datetime.datetime.strptime(dt, '%a %b %d %H:%M:%S %z %Y')
        except Exception as e:
            print(e)
            print(f"Date : {dt}")
        return date_object

    dateNow= datetime.datetime.now(datetime.timezone.utc)
    postDate : datetime.datetime | None= None
    texts = []
    responseDict , cursor = getPostsById(id)
    print(f"Starting for id: {id}...")
    for post in responseDict['timeline']:
        texts.append(post["text"])
        if transformDate(post["created_at"]) == None:
            continue
        postDate= transformDate(post["created_at"])

    if(postDate):
        while (dateNow - postDate).days < 1 and cursor:
            print("Getting more posts...")
            responseDict, cursor = getPostsById(id, cursor)
            for post in responseDict['timeline']:
                postDate = transformDate(post["created_at"])
                if (dateNow - postDate).days < 1:
                    texts.append(post["text"])
                else:
                    break

    return texts

def createPostList(account_ids: list):
    texts : list= []
    counter = 0

    for account_id in account_ids:
        while counter< 3:
            try:
                response_texts = getTodaysPostsById(account_id)
                texts.append(response_texts)
                break
            except Exception as e:
                print(f"For id : {account_id} ,times : {counter+1}\nException {e} ")
                counter += 1
                continue
        counter = 0

    return texts


def createAgent()-> Agent:
    '''
    Simple Pydantic agent that returns a text output
    '''
    try:

        sysPrompt: str=""
        with open("./reportAgentSPrompt.txt", "r") as fl:
            sysPrompt= fl.read()

        ollamaModel = OllamaModel(
            model_name=os.getenv("OLLAMA_MODEL") or "ministral-3:8b",
            provider=OllamaProvider(base_url=os.getenv("OLLAMA_URL") or "http://localhost:11434/v1")
        )
        agent = Agent(
            model= ollamaModel,
            instructions= sysPrompt,
            model_settings= ModelSettings(temperature=0.2)
        )

        return agent

    except Exception as e:
        print(e)
        raise Exception(e)


# texts =getTodaysPostsById(id= "ChampRDS")
#
# textsDict = {
#     "texts" : texts
# }
# with open("texts.json","w") as fl:
#     fl.write(json.dumps(textsDict))

# print(texts)
def example_use():
    textsDict: dict | None = None
    with open("texts.json", "r") as fl:
        textsDict = json.loads(fl.read())

    rep_sys_prompt : str= ""
    extr_sys_prompt : str= ""
    with open("./reportAgentSPrompt.txt", "r") as fl:
        rep_sys_prompt= fl.read()

    with open("./fighterExtractorSprompt.txt", "r") as fl:
        extr_sys_prompt= fl.read()

    model_small = MistralModel(
        model_name =  os.getenv("MISTRAL_SMALL") or "mistral-small-latest",
        provider = MistralProvider(api_key=os.getenv("MISTRAL_API_KEY"))
    )

    model_mini = MistralModel(
        model_name =  os.getenv("MINITRAL") or "mistral-small-latest",
        provider = MistralProvider(api_key=os.getenv("MISTRAL_API_KEY"))
    )

    # summaryAgent = Agent(
    #     model = model_small,
    #     instructions=sys_prompt
    # )
    #
    # response = summaryAgent.run_sync(json.dumps(textsDict))
    # with open("mistral_small_output.md", "w") as fl:
    #     fl.write(response.output)

    class Fighter(BaseModel):
        fighterName: str = Field(description= "Then name of the fighter as depicted in the report")
        reports : list[str] = Field(description="A list of the information reported. Each bullet point must be a separate string in the list")

    class Fighters(BaseModel):
        fighters : list[Fighter] = Field(description="The total list of the depicted fighters in the  ")

    class Event(BaseModel):
        eventName: str = Field(description= "Then name of the Event as depicted in the report")
        reports : list[str] = Field(description="A list of the information reported. Each bullet point must be a separate string in the list")

    class Events(BaseModel):
        fighters : list[Fighter] = Field(description="The total list of the depicted fighters in the  ")


    summaryAgent = Agent(
        model = model_mini,
        instructions=rep_sys_prompt
    )

    fighterExtractorAgent = Agent(
        model= model_mini,
        instructions= extr_sys_prompt,
        output_type= Fighters
    )

    response = summaryAgent.run_sync(json.dumps(textsDict))

    with open("ministral_output.md", "w") as fl:
        fl.write(response.output)

    extr= fighterExtractorAgent.run_sync(response.output)

    with open("strOutput.json", "w") as fl:
        fl.write(json.dumps(extr.output.model_dump()))

async def generateReport():
    accounts: dict= {}
    with open("./accountsX.json" , "r") as fl:
        try:
            accounts = json.loads(fl.read())
        except Exception as e:
            print(f"Exception {e}")
    texts = createPostList(accounts["account_ids"])

    agent= createAgent()

    input = {
        "texts" : texts
    }
    
    with open("texts.json", "w") as fl:
        fl.write(json.dumps(input))

    finalReport = Report()
    outputStr = f"Report {finalReport.created_at}\n"

    report= await agent.run(
        user_prompt= "Below follow the posts: " + json.dumps(input) ,
        instructions="""
You are a Professional Mixed Martial Arts (MMA) Reporter that analyzes multiple X.com posts from selected MMA media accounts, and then generate a daily report on the non-gossip news of the MMA world.
Take note that most of the posts come from accounts that are not professional MMA journalists, rather than media that deliver fast news

You must get all the Fighter Names and Event names mentioned in texts of the posts given by the USER.
        """,
        output_type= ReportComponents
    )

    fighterPrompt=f"Get All the information available for the fighter asked for by the user and generate the reports according to the contents of the texts of the post provided by the user"
    for fighter in report.fighters:
        fighterReports = await agent.run(
            user_prompt= f"Fill the in information for the Fighter : {fighter.name} from the given posts. Below follow the posts: " + json.dumps(input),
            output_type= FighterReports,
            instructions=fighterPrompt
        )
        finalReport.fighters[fighter.name] = fighterReports.output.reports
        if len(fighterReports.output.reports)>0:
            for report in fighterReports.output.reports:
                

    eventPrompt=f"Get All the information available for the event asked for by the user and generate the reports according to the contents of the texts of the post provided by the user"
    for event in report.events:
        eventReports = await agent.run(
            user_prompt= f"Fill the in information for the event : {event.name} from the given posts. Below follow the posts: " + json.dumps(input),
            output_type= EventReports,
            instructions=eventPrompt
        )
        finalReport.events[event.name] = eventReports.output.reports

    finalReport.created_at = datetime.datetime.now().strftime("%A %d %B %Y")

    
    print("Entering the agent...")

async def x_agent()-> str:
    accounts: dict= {}
    with open("./accountsX.json" , "r") as fl:
        try:
            accounts = json.loads(fl.read())
        except Exception as e:
            print(f"Exception {e}")

    texts = createPostList(accounts["account_ids"])

    agent= createAgent()

    input = {
        "texts" : texts
    }

    print("Enterning the agent...")
    response = await agent.run( user_prompt= "Below follow the posts: " + json.dumps(input) )

    return response.output
