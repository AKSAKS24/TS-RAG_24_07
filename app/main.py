import os
from fastapi import FastAPI, Form
from starlette.responses import FileResponse
from dotenv import load_dotenv
from app.generator import create_spec_document

load_dotenv()
app = FastAPI(title="SAP ABAP Spec Generator")


@app.post("/generate_spec/")
async def generate_spec(
    requirement: str = Form(...),
    template: str = Form(...)
):
    # requirement and template are already strings
    output_path = create_spec_document(requirement, template)
    return FileResponse(
        output_path,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        filename='tech_spec_down.docx'
    )