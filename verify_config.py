#!/usr/bin/env python3
"""
Verify Configuration Script - Refactored Version

This script verifies MCP configuration on a remote server using the
centralized ssh_utils module.

Usage:
    python verify_config.py
"""

import os
import sys
import json
from ssh_utils import SSHConfig, get_mcp_servers_config, execute_command, ssh_connection


def check_mcp_server_installation(config: SSHConfig, mcp_config: dict) -> dict:
    """Check if MCP servers are installed on the remote system"""
    results = {}
    
    with ssh_connection(config) as client:
        for server_name, server_config in mcp_config.get('mcpServers', {}).items():
            command = server_config.get('command', '')
            args = server_config.get('args', [])
            
            # Check if the command is available
            if command == 'npx' and args:
                # For npx packages, check if they can be run
                package_name = args[-1] if args else ''
                check_cmd = f"npx --version 2>/dev/null && echo 'NPX_OK' || echo 'NPX_MISSING'"
            elif command == 'node' and args:
                # For node scripts, check if the file exists
                script_path = args[0] if args else ''
                check_cmd = f"test -f {script_path} && echo 'SCRIPT_EXISTS' || echo 'SCRIPT_MISSING'"
            else:
                # Generic command check
                check_cmd = f"command -v {command} >/dev/null 2>&1 && echo 'COMMAND_OK' || echo 'COMMAND_MISSING'"
            
            exit_code, stdout, stderr = execute_command(client, check_cmd)
            status = stdout.strip()
            
            results[server_name] = {
                'command': command,
                'status': status,
                'installed': 'OK' in status or 'EXISTS' in status
            }
    
    return results


def check_config_yaml_integration(config: SSHConfig) -> str:
    """Check if config.yaml references MCP servers"""
    with ssh_connection(config) as client:
        command = "grep -i mcp ~/.hermes/config.yaml 2>/dev/null || echo 'NO_MCP_REFERENCES'"
        exit_code, stdout, stderr = execute_command(client, command)
        
        return stdout.strip()


def generate_next_steps(mcp_config: dict, installation_results: dict, config_yaml_status: str) -> list:
    """Generate next steps based on verification results"""
    steps = []
    
    # Check installation status
    missing_servers = [name for name, result in installation_results.items() if not result['installed']]
    
    if missing_servers:
        steps.append(f"Install missing MCP servers: {', '.join(missing_servers)}")
        steps.append("  Run: npm install -g " + " ".join([f"@modelcontextprotocol/server-{s}" for s in missing_servers if 'server-' in s]))
    
    # Check config.yaml integration
    if 'NO_MCP_REFERENCES' in config_yaml_status:
        steps.append("Add MCP server references to config.yaml")
        steps.append("  Ensure config.yaml includes mcp_servers.json reference")
    
    # Check environment variables
    steps.append("Set required environment variables:")
    steps.append("  - GITHUB_TOKEN for GitHub MCP")
    steps.append("  - SUPABASE_URL and SUPABASE_ANON_KEY for Supabase MCP")
    steps.append("  - NETLIFY_AUTH_TOKEN for Netlify MCP")
    
    steps.append("Restart Claude Desktop/Hermes for changes to take effect")
    
    return steps


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
    
    print(f"🔍 Verifying MCP configuration on {config.host}...")
    
    try:
        config.validate()
        
        # Get MCP configuration
        mcp_config = get_mcp_servers_config(config)
        
        if not mcp_config:
            print("❌ No MCP configuration found")
            print("   Run modify_config.py to create configuration")
            return 1
        
        print("✅ MCP configuration found")
        
        # Show configuration details
        servers = mcp_config.get('mcpServers', {})
        print(f"📋 Configured servers ({len(servers)}):")
        
        for server_name, server_config in servers.items():
            command = server_config.get('command', 'unknown')
            args = ' '.join(server_config.get('args', []))
            print(f"  - {server_name}: {command} {args}")
        
        # Check server installation
        print("\n🔧 Checking MCP server installation...")
        installation_results = check_mcp_server_installation(config, mcp_config)
        
        all_installed = True
        for server_name, result in installation_results.items():
            status_icon = "✅" if result['installed'] else "❌"
            print(f"  {status_icon} {server_name}: {result['status']}")
            if not result['installed']:
                all_installed = False
        
        # Check config.yaml integration
        print("\n📄 Checking config.yaml integration...")
        config_yaml_status = check_config_yaml_integration(config)
        
        if 'NO_MCP_REFERENCES' in config_yaml_status:
            print("  ⚠️  No MCP references found in config.yaml")
        else:
            print("  ✅ MCP references found in config.yaml")
            print(f"  📝 References: {config_yaml_status[:100]}...")
        
        # Generate next steps
        print("\n🚀 Next Steps:")
        next_steps = generate_next_steps(mcp_config, installation_results, config_yaml_status)
        
        for i, step in enumerate(next_steps, 1):
            print(f"  {i}. {step}")
        
        # Overall status
        print("\n📊 Verification Summary:")
        print(f"  ✅ Configuration: Present ({len(servers)} servers)")
        print(f"  {'✅' if all_installed else '❌'} Installation: {'All servers installed' if all_installed else 'Some servers missing'}")
        print(f"  {'✅' if 'NO_MCP_REFERENCES' not in config_yaml_status else '⚠️ '} Integration: {'Configured in config.yaml' if 'NO_MCP_REFERENCES' not in config_yaml_status else 'Not in config.yaml'}")
        
        if all_installed and 'NO_MCP_REFERENCES' not in config_yaml_status:
            print("\n🎉 All checks passed! MCP configuration is ready to use.")
        else:
            print("\n⚠️  Some issues found. Follow the next steps above.")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())