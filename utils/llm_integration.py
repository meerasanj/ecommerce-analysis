from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv

load_dotenv() # load environment variables from a .env file

# Method to get response from LLaMA 3 via Hugging Face Inference API
def get_llm_response(prompt: str, model: str = "meta-llama/Meta-Llama-3-70B-Instruct") -> str:
    HF_TOKEN = os.getenv("HF_TOKEN")
    if not HF_TOKEN:
        raise ValueError("Hugging Face token not found in environment variables")
    
    client = InferenceClient(token=HF_TOKEN)
    
    response = client.chat_completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.7
    )
    
    # Extract the content from the response
    if isinstance(response, dict) and 'choices' in response:
        return response['choices'][0]['message']['content']
    elif isinstance(response, str):
        return response
    else:
        return "Sorry, I couldn't process that request."