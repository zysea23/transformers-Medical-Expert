# app/models/rag_handler.py
import re
import json
import requests
from app.models.medrag.medrag import MedRAG


class RAGHandler:
    def __init__(self, lmstudio_api_url="http://localhost:1234/v1/chat/completions"):
        """
        Initialize the RAG handler
        
        Args:
            lmstudio_api_url: The URL for the LMStudio API
        """
        self.lmstudio_api_url = lmstudio_api_url
        self.headers = {
            "Content-Type": "application/json"
        }
        
        # Initialize MedRAG with medical textbooks corpus, disable corpus cache to save memory
        self.rag_system = MedRAG(
            llm_name="local-model",        # This is just an identifier
            rag=True,                      # Enable RAG functionality
            retriever_name="MedCPT",       # Use the medical domain-specific retriever
            corpus_name="Textbooks",       # Use the built-in medical textbooks corpus
            corpus_cache=False             # Disable corpus cache to save memory
        )
        
        # Override the generate method to use LMStudio API
        self.rag_system.generate = self._generate_with_lmstudio
    
    def _generate_with_lmstudio(self, messages, **kwargs):
        """
        Generate responses using the LMStudio API
        
        Args:
            messages: List of messages
            kwargs: Additional parameters
            
        Returns:
            str: The generated response
        """
        try:
            payload = {
                "model": "local-model",  # Model name used by LMStudio
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2000)
            }
            
            response = requests.post(
                self.lmstudio_api_url,
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                raise Exception(f"LMStudio API call failed, status code: {response.status_code}")
        
        except Exception as e:
            raise Exception(f"Failed to generate response: {str(e)}")
    
    def answer_medical_question(self, question, k=16):
        """
        Answer medical questions using RAG
        
        Args:
            question: The medical question
            k: Number of relevant texts to retrieve
            
        Returns:
            dict: Contains the answer and retrieved relevant texts
        """
        try:
            answer, snippets, scores = self.rag_system.answer(question=question, k=k)
            
            # Process answer - extract meaningful content from any JSON response
            answer_text = self._extract_answer_from_response(answer)
            
            # Format the retrieved relevant texts
            formatted_snippets = []
            for i, snippet in enumerate(snippets):
                formatted_snippets.append({
                    "title": snippet.get("title", "Unknown Title"),
                    "content": snippet.get("content", ""),
                    "relevance": scores[i] if i < len(scores) else 0
                })
            
            return {
                "answer": answer_text,
                "references": formatted_snippets
            }
        
        except Exception as e:
            raise Exception(f"Failed to answer medical question: {str(e)}")
    
    def enhance_explanation(self, medical_text, question=None, k=8):
        """
        Enhance medical text explanation using RAG
        
        Args:
            medical_text: The medical text
            question: Specific question, if None, a generic question will be generated
            k: Number of relevant texts to retrieve
            
        Returns:
            dict: Contains the enhanced explanation and retrieved relevant texts
        """
        try:
            if question is None:
                # If no specific question, create a generic query to retrieve medical information
                query = f"Please explain the key concepts and terminology mentioned in the following medical information: {medical_text}"
            else:
                # Combine medical text with specific question
                query = f"Based on the following medical information: {medical_text}\n\n{question}"
            
            # Use RAG to answer the question
            result = self.answer_medical_question(query, k=k)
            
            return {
                "enhanced_explanation": result["answer"],
                "references": result["references"]
            }
        
        except Exception as e:
            raise Exception(f"Failed to enhance explanation: {str(e)}")
    
    def _extract_answer_from_response(self, response):
        """
        Extract the actual answer from potentially JSON-formatted responses
        
        Args:
            response: The raw response from the LLM
            
        Returns:
            str: Extracted answer in natural language
        """
        # First, try to parse as JSON
        try:
            # Check if the response is a JSON string
            if response.strip().startswith('{') and response.strip().endswith('}'):
                answer_dict = json.loads(response)
                
                # If it's a JSON with step_by_step_thinking, use that
                if "step_by_step_thinking" in answer_dict:
                    return answer_dict["step_by_step_thinking"]
                
                # If there's an 'answer' field, use that
                if "answer" in answer_dict:
                    return answer_dict["answer"]
                
                # Otherwise, convert the entire JSON to a readable format
                return "Here's what I found: " + ", ".join([f"{k}: {v}" for k, v in answer_dict.items()])
        except:
            # Not valid JSON or error in parsing
            pass
        
        # Try to extract JSON from text that might contain other content
        try:
            json_match = re.search(r'({.*})', response, re.DOTALL)
            if json_match:
                answer_dict = json.loads(json_match.group(1))
                if "step_by_step_thinking" in answer_dict:
                    return answer_dict["step_by_step_thinking"]
                if "answer" in answer_dict:
                    return answer_dict["answer"]
        except:
            # Not valid JSON or error in parsing
            pass
        
        # If all else fails, return the original response
        # But try to clean it from code blocks or JSON formatting
        clean_response = re.sub(r'```json.*?```', '', response, flags=re.DOTALL)
        clean_response = re.sub(r'```.*?```', '', clean_response, flags=re.DOTALL)
        
        return clean_response.strip()