import subprocess
import os
import shutil
import sys
import re

from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")
os.makedirs(MEDIA_DIR, exist_ok=True)
ENV_FILE = os.path.join(ROOT_DIR, ".env")
load_dotenv(dotenv_path=ENV_FILE)

MANIM_EXECUTABLE = os.getenv("MANIM_EXECUTABLE", "manim")
INSTRUCTIONS = os.getenv("INSTRUCTIONS", "").strip()

# Initialize MCP Server
try:
    from mcp.server.mcpserver import MCPServer as MCPServerClass  # v2
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServerClass      # v1 fallback

mcp = MCPServerClass("manim-server", instructions=INSTRUCTIONS or None)


def sanitize_folder_name(name: str) -> str:
    """Sanitize the animation folder name to safe snake_case."""
    
    if not name or not name.strip():
        return "saved_animation"
    clean = name.strip().lower()
    clean = re.sub(r'[\s\-]+', '_', clean)
    clean = re.sub(r'[^a-z0-9_]', '', clean)
    clean = re.sub(r'_+', '_', clean).strip('_')
    return clean[:64] or "saved_animation"

@mcp.tool(description="Copies the currently rendered animation files and video from the temporary directory (media/manim_tmp) into a permanently named folder under media/.")
def save_animation_folder(folder_name: str) -> str:
    """Save and copy the current rendered animation from manim_tmp into a permanently named folder."""
    
    tmpdir = os.path.join(MEDIA_DIR, "manim_tmp")

    if not os.path.exists(tmpdir) or not os.listdir(tmpdir):
        return "No animation found in manim_tmp to save. Run execute_manim_code first."

    clean_name = sanitize_folder_name(folder_name)
    target_dir = os.path.join(MEDIA_DIR, clean_name)

    try:
        shutil.copytree(tmpdir, target_dir, dirs_exist_ok=True)
        return f"Successfully saved animation to: {target_dir}"
    except Exception as e:
        return f"Failed to save animation to {target_dir}. Error: {str(e)}"


@mcp.tool(description="Cleans up and removes the specified Manim temporary directory after execution to free up disk space.")
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


@mcp.tool(description="Executes a Python Manim script and renders the output animation video to the temporary directory (media/manim_tmp).")
def execute_manim_code(manim_code: str) -> str:
    """Execute the Manim code"""

    tmpdir = os.path.join(MEDIA_DIR, "manim_tmp") 
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
            print(f"Check the generated video at: {tmpdir}")
            return f"Execution successful. Video generated at: {tmpdir}"
        else:
            error_output = f"Execution failed:\n{result.stderr}"
            if INSTRUCTIONS:
                error_output += (
                    f"\n\n[System Guidelines Reminder for Correction]:\n{INSTRUCTIONS}"
                )
            return error_output

    except Exception as e:
        return f"Error during execution: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
