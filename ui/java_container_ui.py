import streamlit as st
import os
import time
from datetime import datetime
from lib.JavaContainerManager import JavaContainerManager

def render_java_container_section():
    """Render the Java Container section UI"""
    st.title("☕ Java Container Executor")
    st.markdown("Execute a Java application inside a Docker container and stream the logs.")
    
    # Initialize Java Container Manager
    if 'java_manager' not in st.session_state:
        st.session_state.java_manager = JavaContainerManager()
    
    manager = st.session_state.java_manager
    
    # Initialize session state from persisted file
    _initialize_session_state(manager)
    
    # Check if there's an active process from previous run
    if st.session_state.is_running and st.session_state.container_name:
        _render_running_state(manager)
    else:
        st.session_state.is_running = False
        manager.clear_process_state()

    # Inputs
    log_message, iterations = _render_input_fields()

    # Build & Run button
    _render_build_run_button(manager, log_message, iterations)



def _initialize_session_state(manager):
    """Initialize session state from persisted file"""
    if 'process_pid' not in st.session_state:
        state = manager.load_process_state()
        if state:
            st.session_state.process_pid = state.get('pid')
            st.session_state.is_running = state.get('is_running', False)
            st.session_state.log_file = state.get('log_file')
            st.session_state.start_time = state.get('start_time')
            st.session_state.container_name = state.get('container_name', manager.container_name)
        else:
            st.session_state.process_pid = None
            st.session_state.is_running = False
            st.session_state.log_file = None
            st.session_state.start_time = None
            st.session_state.container_name = manager.container_name


def _render_running_state(manager):
    """Render UI when a process is running"""
    # First check if container is running
    if not manager.is_container_running(st.session_state.container_name):
        st.warning(f"⚠️ Container {st.session_state.container_name} is not running")
        st.session_state.is_running = False
        manager.clear_process_state()
        
        # Show final logs if available
        _show_final_logs(manager)
    
    # Check if Java process is still running inside container
    elif not manager.is_java_process_running(st.session_state.container_name):
        st.success(f"✅ Java application completed! (Container: {st.session_state.container_name})")
        st.session_state.is_running = False
        manager.clear_process_state()
        
        # Show final logs
        _show_final_logs(manager)
    
    # Container is running and Java process is active
    else:
        st.info(f"🟢 Java application running in {st.session_state.container_name} (started at {st.session_state.start_time})")
        
        # Show stop button
        _render_stop_button(manager)
        
        # Stream logs from the active process
        _stream_live_logs(manager)


def _show_final_logs(manager):
    """Display final logs"""
    if st.session_state.log_file:
        content = manager.read_logs(st.session_state.log_file)
        if content:
            st.subheader("Application Logs (Final)")
            st.code(content, language="plaintext")


def _render_stop_button(manager):
    """Render stop application button"""
    if st.button("🛑 Stop Application"):
        success, message = manager.stop_java_app(st.session_state.container_name)
        if success:
            st.session_state.is_running = False
            manager.clear_process_state()
            st.success(message)
            time.sleep(1)
            st.rerun()
        else:
            st.error(message)


def _stream_live_logs(manager):
    """Stream and display live logs"""
    if st.session_state.log_file:
        content = manager.read_logs(st.session_state.log_file)
        if content:
            st.subheader("Application Logs (Live)")
            log_container = st.empty()
            log_container.code(content, language="plaintext")
        
        # Auto-refresh to show live logs
        time.sleep(1)
        st.rerun()


def _render_input_fields():
    """Render input fields for log message and iterations"""
    col1, col2 = st.columns(2)
    with col1:
        log_message = st.text_input("Log Message", value="Hello from Docker!")
    with col2:
        iterations = st.number_input("Iterations", min_value=1, max_value=400, value=20)
    
    return log_message, iterations


def _render_build_run_button(manager, log_message, iterations):
    """Render build & run button and handle execution"""
    button_disabled = st.session_state.is_running
    if st.button("Build & Run Java App", disabled=button_disabled):
        status_text = st.empty()
        
        # Build
        status_text.info("🔨 Building Docker image...")
        
        # Define paths
        java_app_dir = os.path.join(os.getcwd(), "java_app")
        host_log_file = os.path.join(java_app_dir, "app_host.log")
        
        # Prepare log file
        manager.prepare_log_file(host_log_file)

        # Build image
        success, message = manager.build_image(java_app_dir)
        if not success:
            status_text.error(f"❌ {message}")
            st.session_state.is_running = False
            manager.clear_process_state()
        else:
            status_text.success(f"✅ {message}")
            time.sleep(1)
            
            # Get or create container and execute
            _execute_java_app(manager, status_text, log_message, iterations, host_log_file)


def _execute_java_app(manager, status_text, log_message, iterations, host_log_file):
    """Execute Java application in container"""
    try:
        container, action = manager.get_or_create_container(log_message, iterations, host_log_file)
        
        if action == "reused":
            status_text.info(f"♻️ Reusing running container: {manager.container_name}")
        elif action == "started":
            status_text.info(f"▶️ Starting stopped container: {manager.container_name}")
        elif action == "created":
            status_text.info(f"🚀 Creating new container: {manager.container_name}")
        
        time.sleep(1)
        
        # Execute Java app
        status_text.info("☕ Starting Java application...")
        success, message = manager.execute_java_app(container, log_message, iterations)
        
        if success:
            # Save state
            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.process_pid = None
            st.session_state.is_running = True
            st.session_state.log_file = host_log_file
            st.session_state.start_time = start_time
            st.session_state.container_name = manager.container_name
            
            manager.save_process_state(None, host_log_file, start_time, True, manager.container_name)
            
            status_text.success(f"✅ Java application started in container: {manager.container_name}")
            time.sleep(1)
            st.rerun()
        else:
            status_text.error(f"❌ {message}")
            st.session_state.is_running = False
            manager.clear_process_state()
            
    except Exception as e:
        status_text.error(f"❌ Unexpected error: {str(e)}")
        st.session_state.is_running = False
        manager.clear_process_state()


def _render_remove_container_button(manager):
    """Render remove container button if container exists and not running"""
    if not st.session_state.is_running and manager.get_container_status() is not None:
        if st.button("🗑️ Remove Container"):
            success, message = manager.remove_container()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)