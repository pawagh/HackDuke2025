import streamlit as st
import streamlit as st
from streamlit_stl import stl_from_file
import api_handler
import os
from dotenv import load_dotenv

def check_api_token():
    """Verify API token is set"""
    if not os.getenv("HF_API_TOKEN"):
        st.error("⚠️ HF_API_TOKEN not found. Please check your .env file.")
        st.stop()

def main():
    # Load environment variables
    load_dotenv()
    
    # Check API token at startup
    check_api_token()
    
    # Initialize session state for error tracking
    if "api_error" not in st.session_state:
        st.session_state.api_error = None

    st.title("Fire Response Dashboard")
    
    # Test each component
    st.header("Basic Components Test")

    stl_from_file(  file_path='Cottage_FREE.stl', 
                    color='#FF9900',
                    material='material',
                    auto_rotate=False,
                    opacity=1.0,
                    height=500,
                    shininess=50,
                    cam_v_angle=60,
                    cam_h_angle=-90,
                    cam_distance=0,
                    max_view_distance=1000,
                    key='example1')
    
    # Test text input
# Initialize chat history in session state if it doesn't exist
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": "You are a helpful fire response assistant."}
        ]

    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.write(message["content"])

    # Chat input
    if prompt := st.chat_input("What would you like to know about fire response?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = api_handler.get_ai_response(st.session_state.messages)
                    if response.startswith("Error:"):
                        st.error(response)
                        st.session_state.api_error = response
                    else:
                        st.write(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    st.session_state.api_error = str(e)
    
    # Test button
    if st.button("Test Button"):
        st.success("Button works!")
    
    # Test sidebar
    with st.sidebar:
        st.header("Navigation")
        st.write("This is a sidebar test")
    
    # Test columns
    col1, col2 = st.columns(2)
    with col1:
        st.write("Column 1")
    with col2:
        st.write("Column 2")
    
    # Test metrics
    st.metric(label="Temperature", value="70 °F", delta="1.2 °F")

if __name__ == "__main__":
    main()