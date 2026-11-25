"""Beacon Readiness Office operational intelligence agent (ADK).

One LlmAgent with two tool families:
  * Curated Spanner Graph tools (tools.py) over the unified public + agency graph.
  * The hosted Data Commons MCP server, for live statistics that are not in Spanner.

Configuration (environment variables):
  GOOGLE_CLOUD_PROJECT  project for Spanner and Gemini (set automatically on Agent Runtime)
  SPANNER_INSTANCE      default dc-graph-demo
  SPANNER_DATABASE      default readiness_dcgraph
  AGENT_MODEL           default gemini-3.5-flash
  MODEL_LOCATION        Gemini endpoint location, default global
  DC_API_KEY            Data Commons API key (Secret Manager on Agent Runtime); no key = no live tools
  DC_MCP_URL            default https://api.datacommons.org/mcp
  DC_MCP_TOOLS          optional comma-separated allowlist of Data Commons MCP tool names
"""

from __future__ import annotations

import logging
import os

from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from google.genai import types

from . import jev, prompts, tools

log = logging.getLogger(__name__)

AGENT_MODEL = os.environ.get("AGENT_MODEL", "gemini-3.5-flash")
MODEL_LOCATION = os.environ.get("MODEL_LOCATION", "global")
DC_MCP_URL = os.environ.get("DC_MCP_URL", "https://api.datacommons.org/mcp")


class JevGatedMcpToolset(McpToolset):
  """JEV System-One gated MCP toolset (`Noul` gate).

  Skips opening a remote MCP session to `https://api.datacommons.org/mcp`
  when `jev.should_enable_live_dc(readonly_context)` evaluates to False (`Noul < 0.50`),
  eliminating ~5.5s of cold-start SSE handshake latency on Spanner Graph turns.
  """

  async def get_tools(self, readonly_context=None):
    if not jev.should_enable_live_dc(readonly_context):
      return []
    return await super().get_tools(readonly_context)


def _datacommons_toolsets() -> list:
  key = os.environ.get("DC_API_KEY", "").strip()
  if not key:
    log.warning("DC_API_KEY is not set: live Data Commons tools are disabled.")
    return []
  allow = [t.strip() for t in os.environ.get("DC_MCP_TOOLS", "").split(",") if t.strip()]
  return [
      JevGatedMcpToolset(
          connection_params=StreamableHTTPConnectionParams(
              url=DC_MCP_URL,
              headers={"X-API-Key": key},
              timeout=60,
              sse_read_timeout=120,
          ),
          tool_filter=allow or None,
          tool_name_prefix="datacommons",
          tool_list_cache_ttl_seconds=3600,
      )
  ]


root_agent = LlmAgent(
    name="beacon_readiness_agent",
    model=Gemini(
        model=AGENT_MODEL,
        client_kwargs={"enterprise": True, "location": MODEL_LOCATION},
        retry_options=types.HttpRetryOptions(attempts=4, initial_delay=1.0, max_delay=10.0),
    ),
    generate_content_config=types.GenerateContentConfig(
        temperature=0.1,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    ),
    before_model_callback=jev.before_model_jev_router,
    description=(
        "Beacon Readiness Office operational intelligence (powered by JEV System-One routing): "
        "evaluates disaster readiness, analyzes online assistance registration access across "
        "demographic groups, identifies unserved high-vulnerability communities using Spanner Graph, "
        "queries live Data Commons indicators, and coordinates mobile response team deployment."
    ),
    instruction=prompts.instruction,
    tools=[*tools.ALL_TOOLS, *_datacommons_toolsets()],
)
