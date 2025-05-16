from pydantic import BaseModel


class BaseInputModel(BaseModel, arbitrary_types_allowed=True):
    pass
