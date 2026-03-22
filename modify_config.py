#!/usr/bin/env python3
"""
Modify Configuration Script - Refactored Version

This script modifies or creates MCP configuration on a remote server using
the centralized ssh_utils module and the global tools configuration.

Usage:
    python modify_config.py
    SSH_HOST=your_server SSH_PASSWORD=your_pass python modify_config.py
"""

import os
import sys
import json
from ssh_utils import SSHConfig, update_mcp_servers_config, get_mcp_servers_config


def load_global_mcp_config() -> dict:
    """Load MCP configuration from global tools directory"""
    config_path = "global_tools/mcps/configuration/claude_desktop_config.json"
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  Global config not found at {config_path}")
        print("   Using default configuration...")
        
        # Default configuration
        return {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
                },
                "git": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-git"]
                },
                "sqlite": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-sqlite"]
                }
            }
        }
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing global config: {e}")
        raise


def get_user_confirmation(current_config: dict, new_config: dict) -> bool:
    """Get user confirmation before making changes"""
    current_servers = list(current_config.get('mcpServers', {}).keys()) if current_config else []
    new_servers = list(new_config.get('mcpServers', {}).keys())
    
    print("\n📋 Configuration Changes:")
    print(f"  Current servers ({len(current_servers)}): {', '.join(current_servers) if current_servers else 'None'}")
    print(f"  New servers ({len(new_servers)}): {', '.join(new_servers)}")
    
    added = set(new_servers) - set(current_servers)
    removed = set(current_servers) - set(new_servers)
    
    if added:
        print(f"  ➕ Will add: {', '.join(added)}")
    if removed:
        print(f"  ➖ Will remove: {', '.join(removed)}")
    
    print("\n⚠️  This will modify the remote MCP configuration.")
    response = input("   Continue? (y/N): ").strip().lower()
    
    return response == 'y' or response == 'yes'


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
    
    print(f"⚙️  Modifying MCP configuration on {config.host}...")
    
    try:
        config.validate()
        
        # Load global configuration
        print("📁 Loading global MCP configuration...")
        new_config = load_global_mcp_config()
        
        # Get current configuration
        current_config = get_mcp_servers_config(config)
        
        # Show changes and get confirmation
        if not get_user_confirmation(current_config, new_config):
            print("❌ Operation cancelled by user")
            return 0
        
        # Update configuration
        print("\n🔄 Updating remote configuration...")
        success = update_mcp_servers_config(config, new_config)
        
        if success:
            print("✅ Configuration updated successfully!")
            
            # Verify the update
            print("\n🔍 Verifying update...")
            updated_config = get_mcp_servers_config(config)
            
            if updated_config:
                servers = list(updated_config.get('mcpServers', {}).keys())
                print(f"   ✅ Verified: {len(servers)} servers configured")
                print(f"   📋 Servers: {', '.join(servers)}")
                
                print("\n💡 Next steps:")
                print("   1. Install required MCP servers globally:")
                print("      npm install -g @modelcontextprotocol/server-filesystem @modelcontextprotocol/server-git @modelcontextprotocol/server-sqlite")
                print("   2. Set environment variables for servers that need them")
                print("   3. Restart Claude Desktop/Hermes")
            else:
                print("   ⚠️  Warning: Could not verify update")
        else:
            print("❌ Failed to update configuration")
            return 1
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())