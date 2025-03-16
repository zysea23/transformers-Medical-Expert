#app/models/lm_handler.py
import requests
import json
import base64
import os
from pathlib import Path
import cv2
import numpy as np
import easyocr  
import re

from PIL import Image

if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

class LMStudioHandler:
   def __init__(self, api_url="http://localhost:1234/v1/chat/completions"):
       self.api_url = api_url
       self.headers = {
           "Content-Type": "application/json"
       }
       
       # Path to the medical metrics reference file
       self.metrics_file = os.path.join(os.path.dirname(__file__), 'medical_metrics.json')
  
   async def process_medical_image(self, image_path: Path):
        """Extract content from medical report image using EasyOCR"""
        try:

            reader = easyocr.Reader(['en'])
            
            image = cv2.imread(str(image_path))
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            results = reader.readtext(gray, detail=0, paragraph=True)
            
            text = "\n".join(results)
            
            print(f"OCR extracted {len(text)} characters from the image")
            return text
            
        except Exception as e:
            raise Exception(f"Image processing failed: {str(e)}")

   async def summarize_medical_report(self, report_content):
        """Summarize key findings, test results, and clinical observations concisely."""
        try:
            prompt = f"""
            Extract key medical findings from the report clearly and concisely.

            **Format:**
            - **Key Findings:** Main medical observations.
            - **Test Results:** Only critical values (highlight abnormal ones with `*`).
            - **Clinical Observations:** Significant notes only.

            **Report:**
            {report_content}
            """

            payload = {
                "model": "local-model",
                "messages": [
                    {"role": "system", "content": "Extract key medical findings clearly and concisely."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 400,
            }

            response = requests.post(self.api_url, headers=self.headers, data=json.dumps(payload))

            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                raise Exception(f"API call failed, status code: {response.status_code}, response: {response.text}")

        except requests.RequestException as e:
            raise Exception(f"LMStudio API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Report summarization failed: {str(e)}")


   async def interpret_medical_report(self, report_content):
        """Provide a simple explanation of the medical report for patients."""
        try:
            prompt = f"""
            Explain this medical report in simple terms.

            **Guidelines:**
            - Focus on key concerns.
            - Explain only abnormal findings.
            - Provide brief insights and lifestyle suggestions.
            - Use a clear, reassuring tone.

            **Report:**
            {report_content}
            """

            payload = {
                "model": "local-model",
                "messages": [
                    {"role": "system", "content": "Explain medical reports simply and reassuringly."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 1200,
            }

            response = requests.post(self.api_url, headers=self.headers, data=json.dumps(payload))

            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                raise Exception(f"API call failed, status code: {response.status_code}")

        except requests.RequestException as e:
            raise Exception(f"LMStudio API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Report interpretation failed: {str(e)}")
          
   async def extract_medical_indicators(self, report_content):
       """Extract medical indicators and their numeric values from report content"""
       try:
           prompt = f"""
           Analyze the following medical report content and extract all medical indicators and their numeric values.
           Return ONLY a JSON object with indicator names as keys and numeric values as values.
           
           Important rules:
           1. Extract ONLY the numeric part of values (remove units and any other text)
           2. If a value has a range, take the middle value
           3. If a value is presented as "less than X" or "greater than X", just use X
           4. Return values as numbers (not strings) when possible
           5. Use standardized indicator names where possible
           6. Include ALL medical indicators found in the report
           
           Example return format:
           {{
               "Glucose": 95,
               "Hemoglobin": 14.2,
               "Cholesterol": 180
           }}
           
           Medical report content:
           {report_content}
           """
           
           payload = {
               "model": "local-model", # Model name used by LMStudio
               "messages": [
                   {"role": "system", "content": "You are a medical data extraction assistant. Extract structured data from medical reports accurately."},
                   {"role": "user", "content": prompt}
               ],
               "temperature": 0,
               "max_tokens": 2000
           }
           
           response = requests.post(self.api_url, headers=self.headers, data=json.dumps(payload))
           
           if response.status_code == 200:
               result = response.json()
               response_text = result['choices'][0]['message']['content']
               
               # Extract JSON from response (it might be embedded in other text)
               import re
               json_match = re.search(r'({.*})', response_text, re.DOTALL)
               if json_match:
                   indicators_json = json.loads(json_match.group(1))
               else:
                   # Try direct JSON parsing if no match found
                   indicators_json = json.loads(response_text)
                   
            #    # Add normal ranges to indicators
            #    indicators_with_ranges = self.add_normal_ranges(indicators_json)
               
               return indicators_json
           else:
               raise Exception(f"API call failed, status code: {response.status_code}")
           
       except requests.RequestException as e:
           raise Exception(f"LMStudio API request failed: {str(e)}")
       except json.JSONDecodeError as e:
           raise Exception(f"Failed to parse indicators JSON: {str(e)}")
       except Exception as e:
           raise Exception(f"Indicators extraction failed: {str(e)}")
  
   def add_normal_ranges(self, indicators_json):
       """
       Check if extracted indicators are in medical_metrics.json and add normal ranges
       
       Args:
           indicators_json: Dictionary of extracted indicators and their values
           
       Returns:
           dict: Dictionary with indicators and their values plus normal ranges
       """
       try:
           # Load medical metrics reference data
           with open(self.metrics_file, 'r') as f:
               reference_metrics = json.load(f)
           
           # Initialize result dictionary
           result = {}
           
           # For each extracted indicator, check if it's in the reference data
           for indicator_name, actual_value in indicators_json.items():
               # Check if indicator exists in reference data (case insensitive)
               for ref_name, ref_range in reference_metrics.items():
                   if indicator_name.lower() == ref_name.lower():
                       # Add indicator with actual value and normal range
                       result[ref_name] = [actual_value, ref_range[0], ref_range[1]]
                       print(f"Added normal range for {ref_name}: {ref_range}")
                       break
           return result
           
       except Exception as e:
           print(f"Error adding normal ranges: {str(e)}")
           # Return original indicators if anything goes wrong
           return indicators_json
  
   async def translate_text(self, text, target_language="Chinese"):
       """Translate text to the specified target language using LMStudio API"""
       try:
           prompt = f"""
           Translate the following text into {target_language}.
           Maintain the meaning, tone, and style of the original text.
           If there are any medical terms, ensure they are translated accurately.
          
           Text to translate:
           {text}
           """
          
           payload = {
               "model": "local-model", # Model name used by LMStudio
               "messages": [
                   {"role": "system", "content": f"You are a professional translator specializing in medical terminology. Translate the given text to {target_language} accurately."},
                   {"role": "user", "content": prompt}
               ],
               "temperature": 0.1,
               "max_tokens": 2000
           }
          
           response = requests.post(self.api_url, headers=self.headers, data=json.dumps(payload))
          
           if response.status_code == 200:
               result = response.json()
               return result['choices'][0]['message']['content']
           else:
               raise Exception(f"Translation API call failed, status code: {response.status_code}")
      
       except requests.RequestException as e:
           raise Exception(f"LMStudio API request failed: {str(e)}")
       except Exception as e:
           raise Exception(f"Translation failed: {str(e)}")
          
   async def answer_medical_question(self, report_content, question):
       """Answer medical questions based on report content using LMStudio API"""
       try:
           # Create a prompt that emphasizes responding in the same language as the question
           prompt = f"""
           You are a professional doctor answering questions about a medical report. The user has provided their medical report and has a question about it.
          
           Medical report content:
           {report_content}
          
           User's question:
           {question}
          
           IMPORTANT: You must respond in the same language that the user asked the question in.
           For example, if they asked in English, respond in English. If they asked in Chinese, respond in Chinese.
          
           Please provide a clear, accurate, and helpful response based on the medical report.
           Focus on answering the specific question while providing relevant context from the report.
           Use simple language that a non-medical professional would understand.
           If the question cannot be answered based on the report, explain what information is missing.
           """
          
           payload = {
               "model": "local-model", # Model name used by LMStudio
               "messages": [
                   {"role": "system", "content": "You are a professional doctor specializing in explaining medical reports and answering health-related questions in a way that's easy to understand. Always respond in the same language as the user's question."},
                   {"role": "user", "content": prompt}
               ],
               "temperature": 0.3,
               "max_tokens": 2000
           }
          
           response = requests.post(self.api_url, headers=self.headers, data=json.dumps(payload))
          
           if response.status_code == 200:
               result = response.json()
               return result['choices'][0]['message']['content']
           else:
               raise Exception(f"Q&A API call failed, status code: {response.status_code}")
      
       except requests.RequestException as e:
           raise Exception(f"LMStudio API request failed: {str(e)}")
       except Exception as e:
           raise Exception(f"Question answering failed: {str(e)}")