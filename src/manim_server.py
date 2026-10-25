import subprocess
import os
import shutil
import sys

from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(ROOT_DIR, ".env")
load_dotenv(dotenv_path=ENV_FILE)

SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "").strip()
MANIM_EXECUTABLE = os.getenv("MANIM_EXECUTABLE", "manim")

TEMP_DIRS = {}
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")
os.makedirs(BASE_DIR, exist_ok=True) 

EXECUTE_TOOL_DESC = SYSTEM_PROMPT or "Execute the Manim code"

# Initialize MCP Server
try:
    from mcp.server.mcpserver import MCPServer as MCPServerClass  # v2
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServerClass      # v1 fallback

mcp = MCPServerClass("manim-server", instructions=SYSTEM_PROMPT or None)


@mcp.tool()
def cleanup_manim_temp_dir(directory: str) -> str:
    """Clean up the specified Manim temporary directory after execution."""

    try:
        if os.path.exists(directory):
            shutil.rmtree(directory)
            return f"Cleanup successful for directory: {directory}"
        else:
            return f"Directory not found: {directory}"
    except Exception as e:
        return f"Failed to clean up directory: {directory}. Error: {str(e)}"


@mcp.tool(description=EXECUTE_TOOL_DESC)
def execute_manim_code(manim_code: str) -> str:
    """Execute the Manim code"""

    tmpdir = os.path.join(BASE_DIR, "manim_tmp") 
    os.makedirs(tmpdir, exist_ok=True)
    script_path = os.path.join(tmpdir, "scene.py")
    
    try:

        # Write the Manim script to the temp directory
        with open(script_path, "w", encoding="utf-8") as script_file:
            script_file.write(manim_code)
        
        # Execute Manim with the correct path
        cmd = [MANIM_EXECUTABLE, "-p", script_path]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=tmpdir
        )

        if result.returncode == 0:
            TEMP_DIRS[tmpdir] = True
            print(f"Check the generated video at: {tmpdir}")
            return f"Execution successful. Video generated at: {tmpdir}"
        else:
            error_output = f"Execution failed:\n{result.stderr}"
            if SYSTEM_PROMPT:
                error_output += (
                    f"\n\n[System Guidelines Reminder for Correction]:\n{SYSTEM_PROMPT}"
                )
            return error_output

    except Exception as e:
        return f"Error during execution: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
