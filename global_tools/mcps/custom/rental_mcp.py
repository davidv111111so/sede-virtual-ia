#!/usr/bin/env python3
"""
Rental Management MCP Server

This MCP server provides rental management capabilities for rental websites.
"""

import json
import sys
import os
import sqlite3
from datetime import datetime
from typing import Dict, Any
import uuid

class RentalManagementMCPServer:
    def __init__(self):
        self.db_path = "rental_management.db"
        self.init_database()
        
        self.tools = {
            "list_properties": {
                "name": "list_properties",
                "description": "List all rental properties",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Filter by status",
                            "enum": ["available", "rented", "maintenance", "all"]
                        }
                    }
                }
            },
            "add_property": {
                "name": "add_property",
                "description": "Add a new rental property",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "address": {"type": "string", "description": "Property address"},
                        "city": {"type": "string", "description": "City"},
                        "state": {"type": "string", "description": "State"},
                        "monthly_rent": {"type": "number", "description": "Monthly rent"},
                        "bedrooms": {"type": "number", "description": "Number of bedrooms"},
                        "bathrooms": {"type": "number", "description": "Number of bathrooms"}
                    },
                    "required": ["address", "city", "state", "monthly_rent"]
                }
            },
            "add_tenant": {
                "name": "add_tenant",
                "description": "Add a new tenant",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "first_name": {"type": "string", "description": "First name"},
                        "last_name": {"type": "string", "description": "Last name"},
                        "email": {"type": "string", "description": "Email address"},
                        "phone": {"type": "string", "description": "Phone number"}
                    },
                    "required": ["first_name", "last_name", "email"]
                }
            },
            "create_lease": {
                "name": "create_lease",
                "description": "Create a lease agreement",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "property_id": {"type": "string", "description": "Property ID"},
                        "tenant_id": {"type": "string", "description": "Tenant ID"},
                        "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                        "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                        "monthly_rent": {"type": "number", "description": "Monthly rent"}
                    },
                    "required": ["property_id", "tenant_id", "start_date", "end_date", "monthly_rent"]
                }
            },
            "record_payment": {
                "name": "record_payment",
                "description": "Record a rental payment",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "lease_id": {"type": "string", "description": "Lease ID"},
                        "amount": {"type": "number", "description": "Payment amount"},
                        "payment_date": {"type": "string", "description": "Payment date (YYYY-MM-DD)"}
                    },
                    "required": ["lease_id", "amount", "payment_date"]
                }
            }
        }

    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS properties (
                id TEXT PRIMARY KEY,
                address TEXT NOT NULL,
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                monthly_rent REAL NOT NULL,
                bedrooms INTEGER,
                bathrooms REAL,
                status TEXT DEFAULT 'available',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tenants (
                id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leases (
                id TEXT PRIMARY KEY,
                property_id TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                monthly_rent REAL NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY,
                lease_id TEXT NOT NULL,
                amount REAL NOT NULL,
                payment_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def list_tools(self):
        return list(self.tools.values())

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")
        
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {"tools": self.list_tools()}
            }
        
        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            try:
                result = self.execute_tool(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32603,
                        "message": f"Tool execution failed: {str(e)}"
                    }
                }
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "list_properties":
            return self._list_properties(arguments)
        elif tool_name == "add_property":
            return self._add_property(arguments)
        elif tool_name == "add_tenant":
            return self._add_tenant(arguments)
        elif tool_name == "create_lease":
            return self._create_lease(arguments)
        elif tool_name == "record_payment":
            return self._record_payment(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def _list_properties(self, args: Dict[str, Any]) -> Dict[str, Any]:
        status = args.get("status", "all")
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status == "all":
            cursor.execute("SELECT * FROM properties ORDER BY created_at DESC")
        else:
            cursor.execute("SELECT * FROM properties WHERE status = ? ORDER BY created_at DESC", (status,))
        
        rows = cursor.fetchall()
        properties = [dict(row) for row in rows]
        conn.close()
        
        return {
            "properties": properties,
            "count": len(properties),
            "status": status
        }

    def _add_property(self, args: Dict[str, Any]) -> Dict[str, Any]:
        property_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO properties (id, address, city, state, monthly_rent, bedrooms, bathrooms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            property_id,
            args["address"],
            args["city"],
            args["state"],
            args["monthly_rent"],
            args.get("bedrooms"),
            args.get("bathrooms")
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "property_id": property_id,
            "message": "Property added successfully",
            "address": args["address"]
        }

    def _add_tenant(self, args: Dict[str, Any]) -> Dict[str, Any]:
        tenant_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tenants (id, first_name, last_name, email, phone)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            tenant_id,
            args["first_name"],
            args["last_name"],
            args["email"],
            args.get("phone")
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "tenant_id": tenant_id,
            "message": "Tenant added successfully",
            "name": f"{args['first_name']} {args['last_name']}"
        }

    def _create_lease(self, args: Dict[str, Any]) -> Dict[str, Any]:
        lease_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO leases (id, property_id, tenant_id, start_date, end_date, monthly_rent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            lease_id,
            args["property_id"],
            args["tenant_id"],
            args["start_date"],
            args["end_date"],
            args["monthly_rent"]
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "lease_id": lease_id,
            "message": "Lease created successfully",
            "start_date": args["start_date"],
            "end_date": args["end_date"]
        }

    def _record_payment(self, args: Dict[str, Any]) -> Dict[str, Any]:
        payment_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO payments (id, lease_id, amount, payment_date)
            VALUES (?, ?, ?, ?)
        ''', (
            payment_id,
            args["lease_id"],
            args["amount"],
            args["payment_date"]
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "payment_id": payment_id,
            "message": "Payment recorded successfully",
            "amount": args["amount"],
            "date": args["payment_date"]
        }


def main():
    """Main entry point"""
    server = RentalManagementMCPServer()
    
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"}
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    main()