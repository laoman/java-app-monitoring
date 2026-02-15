import streamlit as st
from ui.java_container_ui import render_java_container_section

# Set page configuration
st.set_page_config(
    page_title="Streamlit UI Showcase",
    page_icon="🎈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar for navigation
st.sidebar.title("Navigation")
section = st.sidebar.radio(
    "Go to",
    ["Java Container", "Oracle Monitoring"]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "This app demonstrates various UI elements available in Streamlit "
    "to help you learn how to code interactive web apps."
)

# Route to appropriate section
if section == "Java Container":
    render_java_container_section()

elif section == "Oracle Monitoring":
    st.title("Oracle Monitoring")
    st.info("Oracle monitoring section - to be implemented")