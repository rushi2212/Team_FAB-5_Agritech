from pydantic import BaseModel

class FarmerInput(BaseModel):
    city: str
    soil_type: str
