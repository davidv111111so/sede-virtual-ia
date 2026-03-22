"""
SSH Utilities Module

This module provides secure SSH connection utilities for remote server operations.
It centralizes SSH connection logic and provides secure credential management.
"""

import paramiko
import json
import os
import sys
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from contextlib import contextmanager


@dataclass
class SSHConfig:
    """SSH connection configuration"""
    host: str
    port: int = 22
    username: str = "root"
    password: Optional[str] = None
    key_filename: Optional[str] = None
    timeout: int = 10
    
    @classmethod
    def from_env(cls) -> 'SSHConfig':
        """Create configuration from environment variables"""
        return cls(
            host=os.getenv('SSH_HOST', ''),
            port=int(os.getenv('SSH_PORT', '22')),
            username=os.getenv('SSH_USERNAME', 'root'),
            password=os.getenv('SSH_PASSWORD'),
            key_filename=os.getenv('SSH_KEY_PATH'),
            timeout=int(os.getenv('SSH_TIMEOUT', '10'))
        )
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.host:
            raise ValueError("SSH host is required")
        if not self.username:
            raise ValueError("SSH username is required")
        if not self.password and not self.key_filename:
            raise ValueError("Either password or key filename is required")
        return True


class SSHConnectionError(Exception):
    """SSH connection related errors"""
    pass


class SSHCommandError(Exception):
    """SSH command execution errors"""
    def __init__(self, message: str, exit_code: int, stderr: str):
        super().__init__(message)
        self.exit_code = exit_code
        self.stderr = stderr


@contextmanager
def ssh_connection(config: SSHConfig):
    """
    Context manager for SSH connections.
    
    Usage:
        with ssh_connection(config) as client:
            result = execute_command(client, "ls -la")
    """
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        connect_kwargs = {
            'hostname': config.host,
            'port': config.port,
            'username': config.username,
            'timeout': config.timeout
        }
        
        if config.password:
            connect_kwargs['password'] = config.password
        if config.key_filename:
            connect_kwargs['key_filename'] = config.key_filename
        
        client.connect(**connect_kwargs)
        yield client
        
    except paramiko.AuthenticationException as e:
        raise SSHConnectionError(f"Authentication failed: {e}")
    except paramiko.SSHException as e:
        raise SSHConnectionError(f"SSH connection failed: {e}")
    except Exception as e:
        raise SSHConnectionError(f"Unexpected error: {e}")
    finally:
        if client:
            client.close()


def execute_command(client: paramiko.SSHClient, command: str) -> Tuple[int, str, str]:
    """
    Execute a command on the remote server.
    
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    try:
        stdin, stdout, stderr = client.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()
        stdout_text = stdout.read().decode('utf-8', errors='ignore')
        stderr_text = stderr.read().decode('utf-8', errors='ignore')
        
        return exit_code, stdout_text, stderr_text
        
    except Exception as e:
        raise SSHCommandError(f"Command execution failed: {e}", -1, str(e))


def safe_json_parse(json_str: str) -> Dict[str, Any]:
    """Safely parse JSON string"""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")


def secure_execute_remote_json_command(client: paramiko.SSHClient, command: str) -> Dict[str, Any]:
    """Execute command and parse JSON response safely"""
    exit_code, stdout, stderr = execute_command(client, command)
    
    if exit_code != 0:
        raise SSHCommandError(f"Command failed with exit code {exit_code}", exit_code, stderr)
    
    if not stdout.strip():
        raise ValueError("Command returned empty output")
    
    return safe_json_parse(stdout)


def get_remote_file_content(client: paramiko.SSHClient, filepath: str) -> str:
    """Get content of a remote file"""
    command = f"cat {filepath} 2>/dev/null || echo 'FILE_NOT_FOUND'"
    exit_code, stdout, stderr = execute_command(client, command)
    
    if exit_code != 0 or stdout.strip() == 'FILE_NOT_FOUND':
        raise FileNotFoundError(f"Remote file not found: {filepath}")
    
    return stdout


def write_remote_file(client: paramiko.SSHClient, filepath: str, content: str) -> bool:
    """Write content to a remote file"""
    # Escape content for shell
    escaped_content = content.replace("'", "'\"'\"'")
    command = f"echo '{escaped_content}' > {filepath}"
    
    exit_code, stdout, stderr = execute_command(client, command)
    
    if exit_code != 0:
        raise SSHCommandError(f"Failed to write file: {stderr}", exit_code, stderr)
    
    # Verify file was written
    verify_command = f"test -f {filepath} && echo 'OK' || echo 'FAIL'"
    exit_code, stdout, stderr = execute_command(client, verify_command)
    
    return stdout.strip() == 'OK'


# Example usage functions for common tasks
def check_hermes_directory(config: SSHConfig) -> Dict[str, Any]:
    """Check if .hermes directory exists and list contents"""
    with ssh_connection(config) as client:
        command = "ls -la ~/.hermes 2>/dev/null || echo 'DIRECTORY_NOT_FOUND'"
        exit_code, stdout, stderr = execute_command(client, command)
        
        result = {
            'exists': stdout.strip() != 'DIRECTORY_NOT_FOUND',
            'listing': stdout if stdout.strip() != 'DIRECTORY_NOT_FOUND' else '',
            'error': stderr if exit_code != 0 else ''
        }
        
        return result


def get_mcp_servers_config(config: SSHConfig) -> Optional[Dict[str, Any]]:
    """Get MCP servers configuration from remote server"""
    with ssh_connection(config) as client:
        try:
            content = get_remote_file_content(client, "~/.hermes/mcp_servers.json")
            return safe_json_parse(content)
        except FileNotFoundError:
            return None
        except ValueError as e:
            print(f"Warning: Invalid JSON in mcp_servers.json: {e}")
            return None


def update_mcp_servers_config(config: SSHConfig, new_config: Dict[str, Any]) -> bool:
    """Update MCP servers configuration on remote server"""
    with ssh_connection(config) as client:
        # First, ensure .hermes directory exists
        execute_command(client, "mkdir -p ~/.hermes")
        
        # Get existing config if it exists
        try:
            existing_content = get_remote_file_content(client, "~/.hermes/mcp_servers.json")
            existing_config = safe_json_parse(existing_content)
            
            # Merge new servers into existing config
            if 'mcpServers' not in existing_config:
                existing_config['mcpServers'] = {}
            
            if 'mcpServers' in new_config:
                existing_config['mcpServers'].update(new_config['mcpServers'])
            
            final_config = existing_config
        except (FileNotFoundError, ValueError):
            # File doesn't exist or is invalid, use new config
            final_config = new_config
        
        # Write updated config
        config_json = json.dumps(final_config, indent=2)
        return write_remote_file(client, "~/.hermes/mcp_servers.json", config_json)


if __name__ == "__main__":
    # Example usage
    config = SSHConfig.from_env()
    
    try:
        config.validate()
        print(f"Connecting to {config.host} as {config.username}...")
        
        # Check Hermes directory
        result = check_hermes_directory(config)
        if result['exists']:
            print("Hermes directory exists:")
            print(result['listing'])
        else:
            print("Hermes directory not found")
        
        # Get MCP config
        mcp_config = get_mcp_servers_config(config)
        if mcp_config:
            print(f"MCP servers configured: {list(mcp_config.get('mcpServers', {}).keys())}")
        else:
            print("No MCP servers configuration found")
            
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except SSHConnectionError as e:
        print(f"Connection error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)