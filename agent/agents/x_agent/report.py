from pydantic import BaseModel, Field
import datetime

from pydantic_core import ValidationError

class FighterName(BaseModel):
    name: str = Field(description="The full name of the Fighter as displayed in the texts, avoid duplicates.")

class EventName(BaseModel):
    name: str = Field(description="The full name of the Event as displayed in the texts, avoid duplicates.")

class FighterReports(BaseModel):
    reports: list[str] =Field(description="A list of reports for the asked Fighter")

class EventReports(BaseModel):
    reports: list[str]= Field(description="A list of reports for the event")

class ReportComponents(BaseModel):
    fighters: list[FighterName] = Field(description="The names of all the fightes listed")
    events: list[EventName]= Field(description="The names of all the events listed")



class Report:
    created_at: datetime.datetime
    fighters:  dict = {}
    events: dict = {}
