#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

// Supabase client setup
import { createClient } from "@supabase/supabase-js";

const server = new Server(
  {
    name: "supabase-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  },
);

let supabaseClient = null;

// Initialize Supabase client
function initSupabase() {
  const supabaseUrl = process.env.SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseKey) {
    console.error(
      "SUPABASE_URL and SUPABASE_ANON_KEY environment variables are required",
    );
    return false;
  }

  supabaseClient = createClient(supabaseUrl, supabaseKey);
  return true;
}

// Tool definitions
const tools = {
  query_table: {
    name: "query_table",
    description: "Query data from a Supabase table",
    inputSchema: {
      type: "object",
      properties: {
        table: {
          type: "string",
          description: "Table name to query",
        },
        columns: {
          type: "string",
          description: "Columns to select (comma-separated, * for all)",
        },
        filters: {
          type: "object",
          description: "Filter conditions as key-value pairs",
        },
        limit: {
          type: "number",
          description: "Maximum number of rows to return",
        },
      },
      required: ["table"],
    },
  },

  insert_row: {
    name: "insert_row",
    description: "Insert a row into a Supabase table",
    inputSchema: {
      type: "object",
      properties: {
        table: {
          type: "string",
          description: "Table name",
        },
        data: {
          type: "object",
          description: "Data to insert",
        },
      },
      required: ["table", "data"],
    },
  },

  update_row: {
    name: "update_row",
    description: "Update rows in a Supabase table",
    inputSchema: {
      type: "object",
      properties: {
        table: {
          type: "string",
          description: "Table name",
        },
        data: {
          type: "object",
          description: "Data to update",
        },
        filters: {
          type: "object",
          description: "Filter conditions to select rows to update",
        },
      },
      required: ["table", "data"],
    },
  },

  delete_row: {
    name: "delete_row",
    description: "Delete rows from a Supabase table",
    inputSchema: {
      type: "object",
      properties: {
        table: {
          type: "string",
          description: "Table name",
        },
        filters: {
          type: "object",
          description: "Filter conditions to select rows to delete",
        },
      },
      required: ["table", "filters"],
    },
  },

  list_tables: {
    name: "list_tables",
    description: "List all tables in the Supabase database",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },

  get_schema: {
    name: "get_schema",
    description: "Get schema information for a table",
    inputSchema: {
      type: "object",
      properties: {
        table: {
          type: "string",
          description: "Table name",
        },
      },
      required: ["table"],
    },
  },
};

// Tool handlers
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: Object.values(tools),
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (!supabaseClient && !initSupabase()) {
    throw new Error(
      "Supabase client not initialized. Check environment variables.",
    );
  }

  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "query_table": {
        let query = supabaseClient.from(args.table).select(args.columns || "*");

        if (args.filters) {
          Object.entries(args.filters).forEach(([key, value]) => {
            query = query.eq(key, value);
          });
        }

        if (args.limit) {
          query = query.limit(args.limit);
        }

        const { data, error } = await query;

        if (error) throw error;

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      }

      case "insert_row": {
        const { data, error } = await supabaseClient
          .from(args.table)
          .insert(args.data)
          .select();

        if (error) throw error;

        return {
          content: [
            {
              type: "text",
              text: `Inserted row: ${JSON.stringify(data[0], null, 2)}`,
            },
          ],
        };
      }

      case "update_row": {
        let query = supabaseClient.from(args.table).update(args.data);

        if (args.filters) {
          Object.entries(args.filters).forEach(([key, value]) => {
            query = query.eq(key, value);
          });
        }

        const { data, error } = await query.select();

        if (error) throw error;

        return {
          content: [
            {
              type: "text",
              text: `Updated ${data.length} row(s): ${JSON.stringify(data, null, 2)}`,
            },
          ],
        };
      }

      case "delete_row": {
        let query = supabaseClient.from(args.table).delete();

        if (args.filters) {
          Object.entries(args.filters).forEach(([key, value]) => {
            query = query.eq(key, value);
          });
        }

        const { data, error } = await query.select();

        if (error) throw error;

        return {
          content: [
            {
              type: "text",
              text: `Deleted ${data.length} row(s)`,
            },
          ],
        };
      }

      case "list_tables": {
        // Note: Supabase doesn't have a direct tables list API
        // This would require querying information_schema
        const { data, error } = await supabaseClient
          .from("information_schema.tables")
          .select("table_name")
          .eq("table_schema", "public");

        if (error) throw error;

        return {
          content: [
            {
              type: "text",
              text: `Tables: ${data.map((t) => t.table_name).join(", ")}`,
            },
          ],
        };
      }

      case "get_schema": {
        const { data, error } = await supabaseClient
          .from("information_schema.columns")
          .select("column_name, data_type, is_nullable")
          .eq("table_name", args.table)
          .eq("table_schema", "public");

        if (error) throw error;

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Supabase MCP server running on stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
