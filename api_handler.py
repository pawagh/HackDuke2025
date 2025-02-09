import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Load environment variables at the start
load_dotenv()

def format_prompt(messages):
    """Format messages into a prompt that instruction-following models can understand"""
    formatted_prompt = ""
    
    # Add system message if it exists
    system_msg = next((msg["content"] for msg in messages if msg["role"] == "system"), None)
    if system_msg:
        formatted_prompt += f"<|system|>{system_msg}\n"
    
    # Add the conversation history
    for message in messages:
        if message["role"] != "system":
            role = "assistant" if message["role"] == "assistant" else "user"
            formatted_prompt += f"<|{role}|>{message['content']}\n"
    
    # Add final assistant prompt
    formatted_prompt += "<|assistant|>"
    
    return formatted_prompt

def get_ai_response(messages, temperature=0.7, max_tokens=512):
    # Get API token
    api_token = os.getenv("HF_API_TOKEN")
    if not api_token:
        return "Error: HF_API_TOKEN not found in environment variables"
    
    # Initialize client
    client = InferenceClient(
        token=api_token,
        timeout=30
    )
    
    try:
        # Format the conversation
        prompt = format_prompt(messages)
        
        # Make the API call with streaming
        response_stream = client.text_generation(
            model="mistralai/Mistral-7B-Instruct-v0.2",
            prompt=prompt,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_p=0.95,
            repetition_penalty=1.1,
            do_sample=True,
            seed=42,
            stream=True  # Enable streaming
        )
        
        # Process the stream
        for chunk in response_stream:
            yield chunk  # Yield each chunk of the response
        
    except Exception as e:
        return f"Error: {str(e)}" 