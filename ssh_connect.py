#!/usr/bin/env python3
"""
SSH Connection Script - Refactored Version

This script uses the centralized ssh_utils module for secure SSH operations.
It checks the remote server's .hermes directory and MCP configuration.

Usage:
    python ssh_connect.py
    SSH_HOST=65.108.151.207 SSH_PASSWORD=your_password python ssh_connect.py
"""

import os
import sys
from ssh_utils import SSHConfig, check_hermes_directory, get_mcp_servers_config


def main():
    """Main function"""
    # Configuration - prefer environment variables for security
    config = SSHConfig(
        host=os.getenv('SSH_HOST', '65.108.151.207'),
        port=int(os.getenv('SSH_PORT', '22')),
        username=os.getenv('SSH_USERNAME', 'root'),
        password=os.getenv('SSH_PASSWORD'),  # Get from environment variable
        key_filename=os.getenv('SSH_KEY_PATH')
    )
    
    print(f"Checking Hermes configuration on {config.host}...")
    
    try:
        # Validate configuration
        config.validate()
        
        # Check Hermes directory
        result = check_hermes_directory(config)
        
        if result['exists']:
            print("✅ Hermes directory exists:")
            print(result['listing'])
            
            # Get MCP servers configuration
            mcp_config = get_mcp_servers_config(config)
            
            if mcp_config:
                servers = list(mcp_config.get('mcpServers', {}).keys())
                print(f"✅ MCP servers configured ({len(servers)}):")
                for server in servers:
                    print(f"  - {server}")
            else:
                print("⚠️  No MCP servers configuration found")
                print("   Run modify_config.py to create configuration")
        else:
            print("❌ Hermes directory not found")
            print("   The remote server may not have Hermes/Claude Desktop installed")
            
            if result['error']:
                print(f"   Error: {result['error']}")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nEnvironment variables needed:")
        print("  SSH_HOST - Remote server hostname or IP")
        print("  SSH_USERNAME - SSH username (default: root)")
        print("  SSH_PASSWORD or SSH_KEY_PATH - Authentication method")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())