from pydantic import BaseModel

class ConfigInput(BaseModel):
    service_name : str