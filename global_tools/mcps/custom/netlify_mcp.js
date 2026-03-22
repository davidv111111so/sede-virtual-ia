#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

// Netlify API client
import fetch from "node-fetch";

const server = new Server(
  {
    name: "netlify-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  },
);

const NETLIFY_API_BASE = "https://api.netlify.com/api/v1";

// Tool definitions
const tools = {
  list_sites: {
    name: "list_sites",
    description: "List all Netlify sites",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },

  get_site: {
    name: "get_site",
    description: "Get details of a specific site",
    inputSchema: {
      type: "object",
      properties: {
        site_id: {
          type: "string",
          description: "Site ID",
        },
      },
      required: ["site_id"],
    },
  },

  create_site: {
    name: "create_site",
    description: "Create a new site",
    inputSchema: {
      type: "object",
      properties: {
        name: {
          type: "string",
          description: "Site name",
        },
        custom_domain: {
          type: "string",
          description: "Custom domain (optional)",
        },
      },
      required: ["name"],
    },
  },

  deploy_site: {
    name: "deploy_site",
    description: "Deploy a site from a directory",
    inputSchema: {
      type: "object",
      properties: {
        site_id: {
          type: "string",
          description: "Site ID",
        },
        dir: {
          type: "string",
          description: "Directory to deploy",
        },
      },
      required: ["site_id", "dir"],
    },
  },

  list_deploys: {
    name: "list_deploys",
    description: "List deploys for a site",
    inputSchema: {
      type: "object",
      properties: {
        site_id: {
          type: "string",
          description: "Site ID",
        },
        limit: {
          type: "number",
          description: "Maximum number of deploys to return",
        },
      },
      required: ["site_id"],
    },
  },

  get_deploy: {
    name: "get_deploy",
    description: "Get details of a specific deploy",
    inputSchema: {
      type: "object",
      properties: {
        deploy_id: {
          type: "string",
          description: "Deploy ID",
        },
      },
      required: ["deploy_id"],
    },
  },

  rollback_deploy: {
    name: "rollback_deploy",
    description: "Rollback to a previous deploy",
    inputSchema: {
      type: "object",
      properties: {
        site_id: {
          type: "string",
          description: "Site ID",
        },
        deploy_id: {
          type: "string",
          description: "Deploy ID to rollback to",
        },
      },
      required: ["site_id", "deploy_id"],
    },
  },
};

// Helper function for Netlify API requests
async function netlifyRequest(endpoint, options = {}) {
  const token = process.env.NETLIFY_AUTH_TOKEN;

  if (!token) {
    throw new Error("NETLIFY_AUTH_TOKEN environment variable is required");
  }

  const url = `${NETLIFY_API_BASE}${endpoint}`;
  const headers = {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `Netlify API error: ${response.status} ${response.statusText} - ${errorText}`,
    );
  }

  return response.json();
}

// Tool handlers
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: Object.values(tools),
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "list_sites": {
        const sites = await netlifyRequest("/sites");

        return {
          content: [
            {
              type: "text",
              text: `Sites:\n${sites.map((site) => `- ${site.name} (${site.id}): ${site.url}`).join("\n")}`,
            },
          ],
        };
      }

      case "get_site": {
        const site = await netlifyRequest(`/sites/${args.site_id}`);

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(site, null, 2),
            },
          ],
        };
      }

      case "create_site": {
        const siteData = {
          name: args.name,
        };

        if (args.custom_domain) {
          siteData.custom_domain = args.custom_domain;
        }

        const site = await netlifyRequest("/sites", {
          method: "POST",
          body: JSON.stringify(siteData),
        });

        return {
          content: [
            {
              type: "text",
              text: `Created site: ${site.name} (${site.id})\nURL: ${site.url}`,
            },
          ],
        };
      }

      case "deploy_site": {
        // Note: Actual deployment would require file upload
        // This is a simplified version
        const deploy = await netlifyRequest(`/sites/${args.site_id}/deploys`, {
          method: "POST",
          body: JSON.stringify({
            dir: args.dir,
            draft: false,
          }),
        });

        return {
          content: [
            {
              type: "text",
              text: `Deploy started: ${deploy.id}\nStatus: ${deploy.state}\nURL: ${deploy.deploy_ssl_url}`,
            },
          ],
        };
      }

      case "list_deploys": {
        const deploys = await netlifyRequest(`/sites/${args.site_id}/deploys`);

        const limitedDeploys = args.limit
          ? deploys.slice(0, args.limit)
          : deploys;

        return {
          content: [
            {
              type: "text",
              text: `Deploys for site ${args.site_id}:\n${limitedDeploys.map((deploy) => `- ${deploy.id}: ${deploy.state} (${deploy.created_at})`).join("\n")}`,
            },
          ],
        };
      }

      case "get_deploy": {
        const deploy = await netlifyRequest(`/deploys/${args.deploy_id}`);

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(deploy, null, 2),
            },
          ],
        };
      }

      case "rollback_deploy": {
        const rollback = await netlifyRequest(
          `/sites/${args.site_id}/rollback`,
          {
            method: "POST",
            body: JSON.stringify({
              deploy_id: args.deploy_id,
            }),
          },
        );

        return {
          content: [
            {
              type: "text",
              text: `Rollback initiated to deploy ${args.deploy_id}\nNew deploy: ${rollback.id}`,
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
  console.error("Netlify MCP server running on stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
