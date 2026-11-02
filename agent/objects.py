from pydantic import BaseModel,Field

class Answer(BaseModel):
    answer:str = Field(description="answer needed for the user question")
    conversation:bool = Field(description="Indicator to know if the conversation" \
                              "should continue or no. If the agent made decision about the refund then it should be false"\
                                "If conversation still need more chat then it's True" ,default=True)



class PurchaseItem(BaseModel):
    name:str = Field(description="name of the item purchased")
    