from pydantic import BaseModel

class PDFDocumentCreate(BaseModel):
    filename: str
    text_content: str

class PDFDocumentResponse(BaseModel):
    id: int
    filename: str
    text_content: str

    class Config:
        orm_mode = True
