import os
import json
import time
import docker
from datetime import datetime

class JavaContainerManager:
    def __init__(self, container_name="java-app-persistent"):
        self.docker_client = docker.from_env()
        self.container_name = container_name
        self.state_file = os.path.join(os.getcwd(), "java_app", "process_state.json")
    
    def load_process_state(self):
        """Load persisted state from disk if exists"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def save_process_state(self, pid, log_file, start_time, is_running, container_name=None):
        """Save process state to disk"""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump({
                'pid': pid,
                'log_file': log_file,
                'start_time': start_time,
                'is_running': is_running,
                'container_name': container_name or self.container_name
            }, f)
    
    def clear_process_state(self):
        """Clear process state"""
        if os.path.exists(self.state_file):
            os.remove(self.state_file)
    
    def is_java_process_running(self, container_name=None):
        """Check if Java process is running inside the container"""
        name = container_name or self.container_name
        try:
            container = self.docker_client.containers.get(name)
            exit_code, output = container.exec_run("pgrep -f 'java.*App'")
            return exit_code == 0
        except docker.errors.NotFound:
            return False
        except Exception:
            return False
    
    def get_container_status(self, container_name=None):
        """Returns 'running', 'stopped', or None if container doesn't exist"""
        name = container_name or self.container_name
        try:
            container = self.docker_client.containers.get(name)
            return container.status
        except docker.errors.NotFound:
            return None
        except Exception:
            return None
    
    def is_container_running(self, container_name=None):
        """Check if container is running"""
        return self.get_container_status(container_name) == 'running'
    
    def build_image(self, java_app_dir, tag="java-dummy-app"):
        """Build Docker image"""
        try:
            image, build_logs = self.docker_client.images.build(
                path=java_app_dir,
                tag=tag,
                rm=True
            )
            return True, "Image built successfully"
        except docker.errors.BuildError as e:
            return False, f"Build Error: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"
    
    def get_or_create_container(self, log_message, iterations, host_log_file):
        """Get existing container or create new one"""
        try:
            container = self.docker_client.containers.get(self.container_name)
            if container.status == 'running':
                return container, "reused"
            elif container.status == 'exited':
                container.start()
                return container, "started"
        except docker.errors.NotFound:
            # Container doesn't exist, create it
            container = self.docker_client.containers.run(
                "java-dummy-app",
                name=self.container_name,
                detach=True,
                environment={
                    "LOG_MESSAGE": log_message,
                    "ITERATIONS": str(iterations)
                },
                volumes={
                    host_log_file: {'bind': '/app/app.log', 'mode': 'rw'}
                }
            )
            return container, "created"
    
    def execute_java_app(self, container, log_message, iterations):
        """Execute Java app inside the container"""
        try:
            exec_result = container.exec_run(
                "java -cp /app App",
                detach=True,
                environment={
                    "LOG_MESSAGE": log_message,
                    "ITERATIONS": str(iterations)
                }
            )
            return True, "Java app started"
        except Exception as e:
            return False, f"Failed to execute: {e}"
    
    def stop_java_app(self, container_name=None):
        """Stop Java application running in container"""
        name = container_name or self.container_name
        try:
            container = self.docker_client.containers.get(name)
            container.exec_run("pkill -9 java", detach=True)
            return True, "Application stopped"
        except Exception as e:
            return False, f"Failed to stop: {e}"
    
    def remove_container(self, container_name=None):
        """Remove container"""
        name = container_name or self.container_name
        try:
            container = self.docker_client.containers.get(name)
            container.remove(force=True)
            return True, "Container removed"
        except Exception as e:
            return False, f"Failed to remove: {e}"
    
    def prepare_log_file(self, host_log_file):
        """Prepare log file for mounting"""
        # Clear previous log
        if os.path.exists(host_log_file):
            os.remove(host_log_file)
        # Create empty file
        open(host_log_file, 'a').close()
    
    def read_logs(self, log_file):
        """Read log file contents"""
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    return f.read()
            except:
                return ""
        return ""