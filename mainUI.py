import streamlit as st
from streamlit_stl import stl_from_file
import api_handler
import os
from dotenv import load_dotenv
import time
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import geocoder
from shapely.geometry import Point
from shapely.ops import nearest_points
import openrouteservice as ors
from datetime import datetime
import requests


def check_api_token():
    """Verify API token is set"""
    if not os.getenv("HF_API_TOKEN"):
        st.error("⚠️ HF_API_TOKEN not found. Please check your .env file.")
        st.stop()

def get_route_details(client, start_coords, end_coords):
    """Get route details using OpenRouteService"""
    try:
        routes = client.directions(
            coordinates=[start_coords, end_coords],
            profile='driving-car',
            format='geojson'
        )
        
        # Extract duration (seconds) and distance (meters)
        duration = routes['features'][0]['properties']['segments'][0]['duration']
        distance = routes['features'][0]['properties']['segments'][0]['distance']
        
        # Convert to minutes and miles
        duration_minutes = duration / 60
        distance_miles = distance * 0.000621371
        
        # Get the route geometry
        route_coords = routes['features'][0]['geometry']['coordinates']
        # Flip coordinates for folium (lat, lng)
        route_coords = [[coord[1], coord[0]] for coord in route_coords]

        return duration_minutes, distance_miles, route_coords
    
    except Exception as e:
        st.warning(f"Could not get route details: {str(e)}")
        return None, None, None

def calculate_water_metrics(duration_minutes, distance_miles, tank_capacity, flow_rate, route_coords, centroid, row):
    """Calculate water supply metrics for a single water body"""
    round_trip_minutes = (duration_minutes * 2) + 15
    operating_time_per_tank = tank_capacity / flow_rate
    total_operation_time = operating_time_per_tank + round_trip_minutes
    efficiency_score = round_trip_minutes / operating_time_per_tank
    
    return {
        'duration': duration_minutes,
        'distance': distance_miles,
        'round_trip': round_trip_minutes,
        'operating_time': operating_time_per_tank,
        'efficiency_score': efficiency_score,
        'route_coords': route_coords,
        'centroid': centroid,
        'row': row
    }

def add_markers_and_routes(m, g, supply_metrics, gdf):
    """Add all markers and routes to the map"""
    # Add home marker
    folium.Marker(
        location=[g.lat, g.lng],
        popup=folium.Popup(f"Address: {g.address}<br>Coordinates: {g.lat:.6f}, {g.lng:.6f}", max_width=300),
        icon=folium.Icon(color='red', icon='home')
    ).add_to(m)
    
    if supply_metrics:
        # Calculate color scale
        max_score = max(m['efficiency_score'] for m in supply_metrics)
        min_score = min(m['efficiency_score'] for m in supply_metrics)
        score_range = max_score - min_score
        
        # Add routes and markers
        for metric in supply_metrics:
            normalized_score = (metric['efficiency_score'] - min_score) / score_range
            color = f'#{int(normalized_score * 255):02x}{int((1-normalized_score) * 255):02x}00'
            
            add_route_and_marker(m, metric, color)
    
    # Add base water bodies layer
    folium.GeoJson(
        data=gdf,
        name='All Water Bodies',
        style_function=lambda x: {
            'fillColor': '#0066cc',
            'color': '#004d99',
            'weight': 1,
            'fillOpacity': 0.6
        }
    ).add_to(m)
    
    return m

def update_chat_context(address, tank_capacity, fill_time, supply_metrics=None):
    context = (
        "You are a helpful fire response assistant with access to the following information:\n"
        f"- Current Address: {address}\n"
        f"- Fire Truck Capacity: {tank_capacity} gallons\n"
        f"- Fill Time at Water Source: {fill_time} minutes\n"
    )
    
    if supply_metrics:
        context += "\nAvailable Water Sources:\n"
        for idx, metric in enumerate(supply_metrics, 1):
            context += (
                f"{idx}. {metric['row']['NAME']} ({metric['row']['FTYPE']}):\n"
                f"   - Distance: {metric['distance']:.1f} miles\n"
                f"   - Round Trip Time: {metric['round_trip']:.0f} minutes\n"
                f"   - Max Sustainable Flow Rate: {metric['max_flow_rate']:.0f} GPM\n"
            )
    
    # Update the system message
    st.session_state.messages = [
        {"role": "system", "content": context}
    ]

def simplify_geojson(gdf, tolerance=0.001):
    """Simplify geometries and remove unnecessary columns"""
    # Keep only essential columns
    essential_columns = ['NAME', 'FTYPE', 'FCODE_DESC', 'geometry']
    gdf = gdf[essential_columns].copy()
    
    # Simplify geometries
    gdf['geometry'] = gdf['geometry'].simplify(tolerance=tolerance, preserve_topology=True)
    
    return gdf

def main():
    # Set page config to wide mode
    st.set_page_config(layout="wide")
    
    # Add custom CSS for additional width control, hide nav bar, and position toasts
    st.markdown("""
        <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 5rem;
            padding-right: 5rem;
        }
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Toast positioning and styling */
        .stToast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            background-color: white;
            border-radius: 4px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
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
            try:
                response_stream = api_handler.get_ai_response(st.session_state.messages)
                
                if isinstance(response_stream, str) and response_stream.startswith("Error:"):
                    st.toast(response_stream, icon='❌')
                    time.sleep(3)
                else:
                    # Add user message to state
                    st.session_state.messages.append({"role": "user", "content": user_input})
                    
                    # Create a message placeholder for the assistant's response
                    with chat_container:
                        with st.chat_message("assistant"):
                            message_placeholder = st.empty()
                            full_response = ""
                            
                            # Process the stream
                            for chunk in response_stream:
                                full_response += chunk
                                # Add a blinking cursor to make it look more interactive
                                message_placeholder.markdown(full_response + "▌")
                            
                            # Remove the cursor and set the final response
                            message_placeholder.markdown(full_response)
                            
                            # Add the complete response to session state
                            st.session_state.messages.append(
                                {"role": "assistant", "content": full_response}
                            )
                            
            except Exception as e:
                st.toast(f"Chat error: {str(e)}", icon='❌')
                time.sleep(3)
    
    # Right column: Image
    with col3:
        # You can use st.image to display an image
        st.image(
            "FloorPlan.png",  # Replace with your image path
            caption="Floor Plan For Requested Address"
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
    
    # Add Map Section
    st.subheader("Water Bodies")
    
    # Create three columns for inputs
    col1, col2, col3 = st.columns(3)
    with col1:
        tank_capacity = st.number_input("Fire Truck Water Capacity (gallons):", 
                                      value=3000, 
                                      min_value=100, 
                                      help="Enter the total water capacity of your fire truck")
    with col2:
        fill_time = st.number_input("Fill Time (minutes):", 
                                   value=15, 
                                   min_value=1,
                                   help="Time needed to fill the truck at the water source")
    with col3:
        st.markdown("### Maximum Flow Rate")
        st.markdown("*Calculated based on distance and fill time*")
    
    # Add address input
    address = st.text_input("Enter an address:", value="320 Old Forest Creek Dr, Chapel Hill, NC 27514")
    
    try:
        # Show loading toast
        toast_placeholder = st.toast('Loading map and calculating routes...', icon='🔄')
        time.sleep(0.1)  # Small delay to ensure toast appears
        
        # Initialize OpenRouteService client
        ors_client = ors.Client(key='5b3ce3597851110001cf624850fbe0228cc9495a9cfa80d566733a79')
        
        # Geocode the address with custom user agent
        g = geocoder.osm(address, headers={
            'User-Agent': 'FireResponseDashboard/1.0 (sashank.ganapathiraju@gmail.com)'
        })
        
        if g.ok:
            map_center = [g.lat, g.lng]
            zoom_level = 16
        else:
            st.toast('Could not find address. Showing default location.', icon='⚠️')
            map_center = [35.9132, -79.0558]
            zoom_level = 12
            time.sleep(3)  # Keep warning visible for 3 seconds
        
        m = folium.Map(location=map_center, zoom_start=zoom_level)
        
        # Add marker for the input address
        if g.ok:
            folium.Marker(
                location=[g.lat, g.lng],
                popup=folium.Popup(
                    f"Address: {address}<br>"
                    f"Coordinates: {g.lat:.6f}, {g.lng:.6f}",
                    max_width=300
                ),
                icon=folium.Icon(color='red', icon='home')
            ).add_to(m)
        
        # Read the GeoJSON file
        gdf = gpd.read_file('USA_Detailed_Water_Bodies.geojson')
        
        # Simplify the data before processing
        gdf = simplify_geojson(gdf)
        
        # Check if the data has valid geometry
        if not gdf.geometry.is_valid.all():
            st.toast('Fixing invalid geometries...', icon='🔧')
            gdf.geometry = gdf.geometry.buffer(0)
            time.sleep(3)
        
        # Check and reproject if necessary to WGS84 (EPSG:4326)
        if gdf.crs != 'EPSG:4326':
            gdf = gdf.to_crs(epsg=4326)
        
        if g.ok:
            point_gdf = gpd.GeoDataFrame(geometry=[Point(g.lng, g.lat)], crs="EPSG:4326")
            utm_zone = int((g.lng + 180) / 6) + 1
            utm_crs = f"EPSG:269{utm_zone}" if g.lat >= 0 else f"EPSG:327{utm_zone}"
            point_utm = point_gdf.to_crs(utm_crs)
            gdf_utm = gdf.to_crs(utm_crs)
            gdf_utm['distance'] = gdf_utm.geometry.distance(point_utm.geometry.iloc[0])
            nearest_bodies = gdf_utm.nsmallest(5, 'distance')
            
            supply_metrics = []
            for _, row in nearest_bodies.to_crs("EPSG:4326").iterrows():
                centroid = row.geometry.centroid
                duration_minutes, distance_miles, route_coords = get_route_details(
                    ors_client, [g.lng, g.lat], [centroid.x, centroid.y]
                )
                
                if route_coords:
                    # Calculate round trip time including fill time
                    round_trip_minutes = (duration_minutes * 2) + fill_time
                    
                    # Calculate maximum sustainable flow rate
                    max_flow_rate = tank_capacity / round_trip_minutes
                    
                    metrics = {
                        'duration': duration_minutes,
                        'distance': distance_miles,
                        'round_trip': round_trip_minutes,
                        'max_flow_rate': max_flow_rate,
                        'route_coords': route_coords,
                        'centroid': centroid,
                        'row': row
                    }
                    supply_metrics.append(metrics)
            
            if supply_metrics:
                # Find the highest sustainable flow rate
                best_flow_rate = max(m['max_flow_rate'] for m in supply_metrics)
                # Display the best flow rate in the third column
                col3.metric(
                    "Sustainable Flow Rate", 
                    f"{best_flow_rate:.0f} GPM",
                    help="Maximum sustainable flow rate based on closest water source"
                )
                
                # Update chat context with new information
                update_chat_context(address, tank_capacity, fill_time, supply_metrics)
                
                # Sort metrics by max flow rate (higher is better)
                supply_metrics.sort(key=lambda x: x['max_flow_rate'], reverse=True)
                
                # Add markers and routes
                for idx, metric in enumerate(supply_metrics):
                    normalized_score = idx / (len(supply_metrics) - 1) if len(supply_metrics) > 1 else 0
                    if normalized_score < 0.5:
                        # Green to Yellow (reversed from before - now green is best)
                        green = 255
                        red = int(normalized_score * 2 * 255)
                        color = f'#{red:02x}{green:02x}00'
                        marker_color = 'green'  # For the pin
                    else:
                        # Yellow to Red
                        red = 255
                        green = int((1 - normalized_score) * 2 * 255)
                        color = f'#{red:02x}{green:02x}00'
                        marker_color = 'red'  # For the pin
                    
                    # Add route with increased thickness
                    folium.PolyLine(
                        locations=metric['route_coords'],
                        weight=6,
                        color=color,
                        opacity=0.8
                    ).add_to(m)
                    
                    # Add marker with matching color
                    folium.Marker(
                        location=[metric['centroid'].y, metric['centroid'].x],
                        popup=folium.Popup(
                            f"Name: {metric['row']['NAME']}<br>"
                            f"Type: {metric['row']['FTYPE']}<br>"
                            f"Drive Distance: {metric['distance']:.1f} miles<br>"
                            f"Round Trip Time: {metric['round_trip']:.0f} min<br>"
                            f"Max Flow Rate: {metric['max_flow_rate']:.0f} GPM",
                            max_width=300
                        ),
                        icon=folium.Icon(color=marker_color, icon='tint', prefix='fa')
                    ).add_to(m)
        
        # Display the map
        st_folium(m, width=1400, height=600)
        
        # Clear loading toast when complete
        toast_placeholder.toast('Map loaded successfully!', icon='✅')
        time.sleep(3)
        
    except Exception as e:
        error_message = f"Error loading data: {str(e)}"
        st.toast(error_message, icon='❌')
        time.sleep(3)

if __name__ == "__main__":
    main()