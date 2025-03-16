# app/services/report_service.py
from app.models.lm_handler import LMStudioHandler
from pathlib import Path


async def process_report(file_path: Path):
   """Process medical report, extract content, generate explanation, and extract indicators"""
   try:
       # Initialize LMStudio handler
       lm_handler = LMStudioHandler()
      
       # Use LMStudio API to analyze image and extract content
       original_content = await lm_handler.process_medical_image(file_path)
       
       # Generate summary of the medical report
       summary = await lm_handler.summarize_medical_report(original_content)
      
       # Use LMStudio API to interpret content
       explanation = await lm_handler.interpret_medical_report(original_content)
       
       # Extract medical indicators and their values (now includes normal ranges)
       raw_indicators = await lm_handler.extract_medical_indicators(original_content)
       
       # Get indicators with normal ranges
       indicators_with_ranges = lm_handler.add_normal_ranges(raw_indicators)
      
       return summary, explanation, indicators_with_ranges
   
   except Exception as e:
       raise Exception(f"Report processing failed: {str(e)}")
