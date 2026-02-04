from pydantic import BaseModel

class ConfigInput(BaseModel): # check whether it is used anywhere
    service_name : str