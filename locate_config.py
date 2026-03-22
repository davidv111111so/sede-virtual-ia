#!/usr/bin/env python3
"""
Locate Configuration Script - Refactored Version

This script locates MCP configuration files on a remote server using the
centralized ssh_utils module.

Usage:
    python locate_config.py
"""

import os
import sys
from ssh_utils import SSHConfig, get_mcp_servers_config, execute_command, ssh_connection


def search_mcp_configs(config: SSHConfig):
    """Search for MCP configuration files in common locations"""
    with ssh_connection(config) as client:
        print("🔍 Searching for MCP configuration files...")
        
        # Common locations to search
        search_paths = [
            "~/.hermes",
            "~/.config/hermes",
            "~/.config/claude",
            "/etc/hermes",
            "/usr/local/etc/hermes"
        ]
        
        for path in search_paths:
            command = f"find {path} -name '*.json' -o -name '*.yaml' -o -name '*.yml' 2>/dev/null | head -5"
            exit_code, stdout, stderr = execute_command(client, command)
            
            if stdout.strip():
                print(f"\n📁 Found in {path}:")
                print(stdout)
        
        # Also search for any mcp_servers.json
        command = "find /home /etc /usr -name 'mcp_servers.json' 2>/dev/null | head -10"
        exit_code, stdout, stderr = execute_command(client, command)
        
        if stdout.strip():
            print("\n🔧 Found mcp_servers.json files:")
            print(stdout)


def check_config_yaml(config: SSHConfig):
    """Check config.yaml for MCP references"""
    with ssh_connection(config) as client:
        print("\n📋 Checking config.yaml for MCP settings...")
        
        command = "grep -i mcp ~/.hermes/config.yaml 2>/dev/null || echo 'config.yaml not found or no MCP references'"
        exit_code, stdout, stderr = execute_command(client, command)
        
        print(stdout)


def main():
    """Main function"""
    # Configuration from environment variables
    config = SSHConfig(
        host=os.getenv('SSH_HOST', '65.108.151.207'),
        port=int(os.getenv('SSH_PORT', '22')),
        username=os.getenv('SSH_USERNAME', 'root'),
        password=os.getenv('SSH_PASSWORD'),
        key_filename=os.getenv('SSH_KEY_PATH')
    )
    
    print(f"🔎 Locating MCP configuration on {config.host}...")
    
    try:
        config.validate()
        
        # Get MCP servers configuration
        mcp_config = get_mcp_servers_config(config)
        
        if mcp_config:
            servers = list(mcp_config.get('mcpServers', {}).keys())
            print(f"✅ Found mcp_servers.json with {len(servers)} servers:")
            for server_name, server_config in mcp_config.get('mcpServers', {}).items():
                command = server_config.get('command', 'unknown')
                args = ' '.join(server_config.get('args', []))
                print(f"  - {server_name}: {command} {args}")
        else:
            print("❌ mcp_servers.json not found in ~/.hermes")
            
            # Search for configuration files
            search_mcp_configs(config)
        
        # Check config.yaml
        check_config_yaml(config)
        
        print("\n📊 Summary:")
        if mcp_config:
            print("  ✅ MCP configuration is present")
            print("  ✅ Ready for MCP server operations")
        else:
            print("  ⚠️  MCP configuration not found")
            print("  💡 Run modify_config.py to create configuration")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
