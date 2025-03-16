# app/main.py
from fastapi import FastAPI, File, UploadFile, Request, Body
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from pathlib import Path
import uuid
import aiofiles
from typing import Dict, Any
import csv
import io
from fastapi.responses import StreamingResponse




# Import services
from app.services.report_service import process_report
from app.models.lm_handler import LMStudioHandler
from app.services.rag_service import rag_service




# Create FastAPI application
app = FastAPI(title="Medical Report Interpreter")


# Add CORS middleware
app.add_middleware(
   CORSMiddleware,
   allow_origins=["*"],
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"],
)

# Setup static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")




# Ensure upload directory exists
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)




@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
   """Render home page"""
   return templates.TemplateResponse("index.html", {"request": request})




async def save_upload_file(file: UploadFile, directory: Path, filename: str) -> Path:
   """Save uploaded file and return file path"""
   file_path = directory / filename


   async with aiofiles.open(file_path, 'wb') as out_file:
       content = await file.read()
       await out_file.write(content)


   return file_path




@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
   """Process uploaded medical report image"""
   # calculate processing time
   import time
   start_time = time.time()
   
   try:
       # Generate unique filename
       file_extension = os.path.splitext(file.filename)[1]
       unique_filename = f"{uuid.uuid4()}{file_extension}"


       # Save uploaded file
       file_path = await save_upload_file(file, UPLOAD_DIR, unique_filename)

      
       # Process report
       original_content, explanation, indicators = await process_report(file_path)


      
       # calculate processing time
       end_time = time.time()
       processing_time = end_time - start_time
       print(f"Processing time: {processing_time} seconds")
       return {
           "success": True,
           "original_content": original_content,
           "explanation": explanation,
           "indicators": indicators,
           "filename": unique_filename
       }
   except Exception as e:
       import traceback
       error_details = traceback.format_exc()
       print(f"Error details: {error_details}")
       return JSONResponse(
           status_code=500,
           content={"success": False, "message": f"Processing failed: {str(e)}"}
       )




@app.post("/translate")
async def translate_text(payload: Dict[str, Any] = Body(...)):
   """Translate text to the specified language"""
   try:
       # Get text and target language from request
       text = payload.get("text")
       target_language = payload.get("language", "Chinese")
  
       if not text:
           return JSONResponse(
               status_code=400,
               content={"success": False, "message": "No text provided for translation"}
           )
  
       # Initialize LMStudio handler
       lm_handler = LMStudioHandler()
  
       # Translate the text
       translated_text = await lm_handler.translate_text(text, target_language)
  
       return {
           "success": True,
           "translated_text": translated_text,
           "language": target_language
       }
   except Exception as e:
       return JSONResponse(
           status_code=500,
           content={"success": False, "message": f"Translation failed: {str(e)}"}
       )




@app.post("/ask")
async def answer_question(payload: Dict[str, Any] = Body(...)):
   """Answer medical questions based on report content"""
   try:
       # Get report content and question from request
       report_content = payload.get("report_content")
       question = payload.get("question")
  
       if not report_content or not question:
           return JSONResponse(
               status_code=400,
               content={"success": False, "message": "Both report content and question are required"}
           )
  
       # Initialize LMStudio handler
       lm_handler = LMStudioHandler()
  
       # Answer the question based on report content
       answer = await lm_handler.answer_medical_question(report_content, question)
  
       return {
           "success": True,
           "question": question,
           "answer": answer
       }
   except Exception as e:
       return JSONResponse(
           status_code=500,
           content={"success": False, "message": f"Question answering failed: {str(e)}"}
       )




# Add RAG enhancement endpoint
@app.post("/rag-enhance")
async def enhance_with_rag(payload: Dict[str, Any] = Body(...)):
   """Enhance medical report explanation using RAG"""
   try:
       # Get medical report content and optional question from request
       report_content = payload.get("report_content")
       question = payload.get("question")
    
       if not report_content:
           return JSONResponse(
               status_code=400,
               content={"success": False, "message": "Medical report content is required"}
           )
    
       # Process report with RAG service
       result = await rag_service.process_with_rag(report_content, question)
    
       return result
   except Exception as e:
       return JSONResponse(
           status_code=500,
           content={"success": False, "message": f"RAG enhancement failed: {str(e)}"}
       )


# Add endpoint for exporting medical indicators to CSV
@app.post("/export-indicators")
async def export_indicators(payload: Dict[str, Any] = Body(...)):
   """Export medical indicators to CSV file"""
   try:
       # Get indicators from request
       indicators = payload.get("indicators")
      
       if not indicators:
           return JSONResponse(
               status_code=400,
               content={"success": False, "message": "No indicators provided for export"}
           )
      
       # Create CSV in memory
       output = io.StringIO()
       writer = csv.writer(output)
      
       # Write header
       writer.writerow(["Indicator", "Value"])
      
       # Write indicators
       for indicator, value in indicators.items():
           writer.writerow([indicator, value])
      
       # Create response with CSV file
       output.seek(0)
       return StreamingResponse(
           iter([output.getvalue()]),
           media_type="text/csv",
           headers={"Content-Disposition": "attachment; filename=medical_indicators.csv"}
       )
      
   except Exception as e:
       return JSONResponse(
           status_code=500,
           content={"success": False, "message": f"CSV export failed: {str(e)}"}
       )




if __name__ == "__main__":
   uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)