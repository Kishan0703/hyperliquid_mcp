from typing import Any, Dict, List, Optional, Union, Literal

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

import mcp_tools  # type: ignore
import asyncio  # New import for running async logic if needed elsewhere

# -----------------------------
# Environment and client setup
# -----------------------------
load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
if not PRIVATE_KEY:
    raise RuntimeError("PRIVATE_KEY is not set in the environment (.env)")

# Initialize the authenticated Hyperliquid client(s)
# HYPER_CLIENTS is a dictionary containing "exch_client", "info_client", and "address"
try:
    # Set is_testnet=True if you want to use the testnet
    HYPER_CLIENTS = mcp_tools.init_hyperliquid_client(PRIVATE_KEY, is_testnet=False) # type: ignore[attr-defined]
    print(f"Hyperliquid Client Initialized. Address: {HYPER_CLIENTS['address']}")
except Exception as e:
    raise RuntimeError(
        f"Client initialization failed. Check Hyperliquid SDK and private key. Error: {e}"
    )


# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


# -----------------------------
# MCP models and endpoints
# -----------------------------


class ListToolsRequest(BaseModel):
    pass


class ToolParameter(BaseModel):
    name: str
    type_hint: str
    required: bool = True


class ToolSchema(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: List[ToolParameter]


class ListToolsResponse(BaseModel):
    tools: List[ToolSchema]

@app.post("/mcp/tools", response_model=ListToolsResponse)
def list_tools(_: ListToolsRequest) -> ListToolsResponse:
    tools: List[ToolSchema] = [
        ToolSchema(
            name="get_all_mids",
            description="Asynchronously fetch all available coins' mid prices from Hyperliquid. Returns coin symbols and their prices.",
            parameters=[],  # no parameters
        ),
        ToolSchema(
            name="place_limit_order",
            description="Asynchronously place a limit order on Hyperliquid. Requires the coin symbol, side ('buy'/'sell'), size, and a limit price.",
            parameters=[
                ToolParameter(name="coin", type_hint="str", required=True),
                ToolParameter(name="side", type_hint="str", required=True), 
                ToolParameter(name="size", type_hint="float", required=True),
                ToolParameter(name="limit_price", type_hint="float", required=True),
                ToolParameter(name="time_in_force", type_hint="str", required=False), # Added for advanced control
                ToolParameter(name="reduce_only", type_hint="bool", required=False), # Added for advanced control
            ],
        ),
    ]
    return ListToolsResponse(tools=tools)


class ExecuteToolRequest(BaseModel):
    toolName: str
    arguments: Optional[Dict[str, Any]] = None


class ExecuteToolResponse(BaseModel):
    ok: bool
    result: Optional[Union[Dict[str, Any], List[Any], str, float, int, bool]] = None
    error: Optional[str] = None

@app.post("/mcp/call", response_model=ExecuteToolResponse)
async def call_tool(body: ExecuteToolRequest) -> ExecuteToolResponse:
    """The main endpoint to execute tools defined in mcp_tools.py asynchronously."""
    tool_name = body.toolName
    args = body.arguments or {}

    try:
        if tool_name == "get_all_mids":
            # The tool function is now async and must be awaited
            result = await mcp_tools.get_all_mids(HYPER_CLIENTS)  # type: ignore
            return ExecuteToolResponse(ok=True, result=result)

        if tool_name == "place_limit_order":
            
            # --- Argument Validation and Extraction ---
            coin = args.get("coin")
            side = args.get("side")
            size = args.get("size")
            limit_price = args.get("limit_price")
            # Optional parameters with defaults
            time_in_force: Literal["Gtc", "Ioc", "Alo"] = args.get("time_in_force", "Gtc")
            reduce_only: bool = args.get("reduce_only", False)
            
            if side.lower() not in ["buy", "sell"]:
                 raise ValueError("Parameter 'side' must be 'buy' or 'sell'.")
            if time_in_force not in ["Gtc", "Ioc", "Alo"]:
                raise ValueError("Parameter 'time_in_force' must be 'Gtc', 'Ioc', or 'Alo'.")

            # The tool function is now async and must be awaited
            result = await mcp_tools.place_limit_order(
                HYPER_CLIENTS, 
                coin=coin, 
                side=side, 
                size=float(size), 
                limit_price=float(limit_price),
                time_in_force=time_in_force,
                reduce_only=reduce_only,
            ) # type: ignore
            return ExecuteToolResponse(ok=True, result=result)

        raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")

    except HTTPException:
        raise
    except Exception as exc: 
        # Catch all exceptions from the tool and return as an MCP error
        return ExecuteToolResponse(ok=False, error=f"Tool Execution Error: {str(exc)}")


# Optional: local dev entrypoint
if __name__ == "__main__":
    import uvicorn
    # Use an asynchronous worker for FastAPI
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)