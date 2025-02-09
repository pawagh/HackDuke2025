import streamlit as st
import streamlit as st
from streamlit_stl import stl_from_file
import api_handler
import os
from dotenv import load_dotenv
import time
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

def check_api_token():
    """Verify API token is set"""
    if not os.getenv("HF_API_TOKEN"):
        st.error("⚠️ HF_API_TOKEN not found. Please check your .env file.")
        st.stop()

def main():
    # Set page config to wide mode
    st.set_page_config(layout="wide")
    
    # Add custom CSS for additional width control
    st.markdown("""
        <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 15rem;
            padding-right: 15rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Load environment variables and check API token
    load_dotenv()
    check_api_token()
    
    # Initialize session states
    if "api_error" not in st.session_state:
        st.session_state.api_error = None
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": "You are a helpful fire response assistant."}
        ]

    st.title("Fire Response Dashboard")
    
    # Create three columns
    col1, col2, col3 = st.columns(3)
    
    # Left column: STL Model
    with col1:
        stl_from_file(
            file_path='Cottage_FREE.stl', 
            color='#FF9900',
            material='material',
            auto_rotate=False,
            opacity=1.0,
            height=500,
            shininess=50,
            cam_v_angle=60,
            cam_h_angle=-90,
            cam_distance=30,
            max_view_distance=1000,
            key='example1'
        )
    
    # Middle column: Chat Interface with scrolling
    with col2:
        # Create the input at the top
        user_input = st.chat_input("What would you like to know about fire response?")

        # Create a container with fixed height for scrolling
        chat_container = st.container(height=500)
        
        # Display messages in reverse order (newest first)
        with chat_container:
            for message in reversed(st.session_state.messages[1:]):  # Skip system message
                with st.chat_message(message["role"]):
                    st.write(message["content"])

        # Handle new input
        if user_input:
            # Add user message to state
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Get AI response
            try:
                response = api_handler.get_ai_response(st.session_state.messages)
                if response.startswith("Error:"):
                    st.error(response)
                    st.session_state.api_error = response
                else:
                    st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.session_state.api_error = str(e)
            
            # Force a rerun to update the chat
            st.rerun()
    
    # Right column: Image
    with col3:
        # You can use st.image to display an image
        st.image(
            "FloorPlan.png",  # Replace with your image path
            caption="Floor Plan For Requested Address",
            use_container_width=True
        )

    # Accelerometer Graph Section (below all columns)
    st.subheader("Accelerometer Data")
    
    # Generate static time series data
    time_range = np.linspace(0, 10, 1000)  # 10 seconds of data with 1000 points
    
    # Create interesting patterns for each axis
    x_data = 0.5 * np.sin(2 * np.pi * 0.5 * time_range) + 0.2 * np.sin(2 * np.pi * 2 * time_range)
    y_data = 0.3 * np.cos(2 * np.pi * 0.7 * time_range) + 0.1 * np.cos(2 * np.pi * 3 * time_range)
    z_data = 0.4 * np.sin(2 * np.pi * 0.3 * time_range) * np.exp(-0.1 * time_range)
    
    # Create the graph
    fig = go.Figure()
    
    # Add traces for each axis
    fig.add_trace(go.Scatter(
        x=time_range, 
        y=x_data,
        name='X-axis',
        line=dict(color='red', width=2)
    ))
    fig.add_trace(go.Scatter(
        x=time_range, 
        y=y_data,
        name='Y-axis',
        line=dict(color='green', width=2)
    ))
    fig.add_trace(go.Scatter(
        x=time_range, 
        y=z_data,
        name='Z-axis',
        line=dict(color='blue', width=2)
    ))

    # Update layout with more detailed styling
    fig.update_layout(
        title={
            'text': 'Accelerometer Data Analysis',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title='Time (seconds)',
        yaxis_title='Acceleration (g)',
        height=400,
        margin=dict(l=60, r=30, t=50, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        plot_bgcolor='white',
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor='lightgray'
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor='lightgray'
        )
    )

    # Display the graph
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()