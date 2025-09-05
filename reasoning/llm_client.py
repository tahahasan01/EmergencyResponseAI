# reasoning/llm_client.py
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def llm_complete(prompt: str, model: str = None, temperature: float = 0.2) -> str:
    """Legacy function for backward compatibility."""
    return get_llm_response(prompt, temperature)

def get_llm_response(prompt: str, temperature: float = 0.2) -> str:
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    
    # Set model name based on provider - using latest and strongest models
    if provider == "groq":
        model_name = "llama-3.3-70b-versatile"  # Latest Groq model
    elif provider == "gemini":
        model_name = "gemini-1.5-flash"  # Latest, fastest Gemini model
        # Alternative: "gemini-1.5-pro" (more capable but slower)
    else:
        model_name = "mock"
    
    if provider == "groq":
        try:
            from groq import Groq
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable not set")
                
            client = Groq(api_key=api_key)
            resp = client.chat.completions.create(
                model=model_name,
                messages=[{"role":"system","content":"You are a rigorous crisis planner. Always output valid JSON with commands. Respond ONLY with the JSON object, no additional text."},
                          {"role":"user","content":prompt}],
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            response = resp.choices[0].message.content
            return response
            
        except Exception as e:
            print(f"Error calling Groq: {e}")
            # Return proper JSON fallback
            return json.dumps({
                "commands": [
                    {"agent_id": "medic1", "type": "move", "to": [5, 5]},
                    {"agent_id": "truck1", "type": "move", "to": [3, 4]}
                ]
            })
    elif provider == "gemini":
        try:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set")
                
            genai.configure(api_key=api_key)
            
            # Use the latest API with proper model configuration
            generation_config = {
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
            
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
            
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Generate content with proper error handling
            response = model.generate_content(prompt)
            
            if not response.text:
                raise ValueError("Empty response from Gemini")
                
            # Try to extract JSON from response
            text_response = response.text.strip()
            
            # Handle cases where response might be wrapped in markdown or text
            if text_response.startswith('```json'):
                # Remove markdown code blocks
                text_response = text_response.replace('```json', '').replace('```', '').strip()
            elif text_response.startswith('```'):
                text_response = text_response.replace('```', '').strip()
            
            # Extract JSON if it's embedded in text
            json_start = text_response.find('{')
            json_end = text_response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = text_response[json_start:json_end]
                try:
                    # Validate it's proper JSON
                    json.loads(json_str)
                    return json_str
                except json.JSONDecodeError:
                    # If extraction fails, use the whole response
                    return text_response
            else:
                return text_response
            
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            # Return proper JSON fallback with more realistic commands
            return json.dumps({
                "commands": [
                    {"agent_id": "medic1", "type": "move", "to": [10, 10]},
                    {"agent_id": "medic2", "type": "move", "to": [12, 12]},
                    {"agent_id": "truck1", "type": "move", "to": [8, 8]},
                    {"agent_id": "drone1", "type": "move", "to": [15, 15]}
                ]
            })
    else:
        # Return more realistic mock response for better simulation
        return json.dumps({
            "commands": [
                {"agent_id": "medic1", "type": "move", "to": [7, 7]},
                {"agent_id": "medic2", "type": "move", "to": [9, 9]},
                {"agent_id": "truck1", "type": "act", "action_name": "extinguish_fire"},
                {"agent_id": "drone1", "type": "move", "to": [12, 12]}
            ]
        })