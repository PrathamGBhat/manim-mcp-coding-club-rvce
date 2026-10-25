# Implementation Plan: Isolated `.venv`, `requirements.txt`, & Model-Agnostic System Prompt

This plan outlines how to transition `manim-mcp-server` from global Python dependencies to a self-contained project virtual environment (`.venv`), accompanied by a `requirements.txt`, while eliminating the hardcoded `MANIM_EXECUTABLE` from `.env` and preserving the model-agnostic system prompt injection.

---

## 1. Problem & Goals

### Current Issues:
1. **Global Dependency Coupling**: The server currently relies on globally installed pip packages (`manim`, `mcp`, `python-dotenv`) in `C:\Users\ADMIN\AppData\Local\Programs\Python\Python314\`.
2. **Hardcoded Paths in `.env`**: `.env` currently contains a machine-specific executable path (`MANIM_EXECUTABLE="C:\...\Scripts\manim.exe"`).
3. **Reproducibility**: New users or different machines must figure out and manually install the correct dependency versions.

### Objectives:
1. **Isolated Virtual Environment (`.venv`)**: Create and manage all dependencies inside `.venv` in the project root.
2. **Explicit Dependency Manifest (`requirements.txt`)**: Document all project requirements with compatible versions.
3. **Zero Path Configuration**: In `src/manim_server.py`, invoke Manim directly via the active Python interpreter (`[sys.executable, "-m", "manim", ...]`), completely eliminating `MANIM_EXECUTABLE` from `.env`.
4. **Clean `.env`**: Dedicate `.env` solely to the model-agnostic `SYSTEM_PROMPT`.
5. **Git Hygiene**: Ignore `.venv` and `.env` in `.gitignore`.

---

## 2. Architecture & Execution Flow

```
+-----------------------------------------------------------------------------------+
| MCP Client (OpenCode / Claude Desktop / Cursor)                                    |
|   command: [ "<repo>/.venv/Scripts/python.exe", "<repo>/src/manim_server.py" ]    |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼ (Runs inside .venv)
+-----------------------------------------------------------------------------------+
| manim-mcp-server (Python Process)                                                 |
|                                                                                   |
|  1. sys.executable points to .venv/Scripts/python.exe                             |
|  2. Loads .env (SYSTEM_PROMPT)                                                    |
|  3. MCPServer(instructions=SYSTEM_PROMPT)                                         |
|  4. @mcp.tool(description=SYSTEM_PROMPT + docstring)                              |
|  5. execute_manim_code runs:                                                      |
|       subprocess.run([sys.executable, "-m", "manim", "-p", script_path])          |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
                     (Executes via .venv/Lib/site-packages/manim)
```

---

## 3. Step-by-Step Implementation

### Step 1: Create `requirements.txt`
In the project root, create `requirements.txt`:
```text
mcp>=1.0.0
manim
python-dotenv
```

---

### Step 2: Create and Populate `.venv`
Run the following commands in the workspace root:
```powershell
# 1. Create the virtual environment
python -m venv .venv

# 2. Upgrade pip and install project dependencies
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

### Step 3: Refactor `src/manim_server.py`
Remove `MANIM_EXECUTABLE` and replace the execution command with `sys.executable -m manim`:

```python
import subprocess
import os
import sys
import shutil

# --- 1. Load .env from Project Root ---
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(ROOT_DIR, ".env")

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ENV_FILE)
except ImportError:
    pass

SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "").strip()

# Optional override; defaults to running manim via the active environment interpreter
MANIM_EXECUTABLE = os.getenv("MANIM_EXECUTABLE", "")

# --- 2. Initialize MCP Server ---
try:
    from mcp.server.mcpserver import MCPServer as MCPServerClass  # v2
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServerClass      # v1 fallback

mcp = MCPServerClass("manim-server", instructions=SYSTEM_PROMPT or None)

TEMP_DIRS = {}
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")
os.makedirs(BASE_DIR, exist_ok=True)

EXECUTE_TOOL_DESC = "Execute the Manim animation code."
if SYSTEM_PROMPT:
    EXECUTE_TOOL_DESC += (
        f"\n\n### MANDATORY GUIDELINES & SYSTEM PROMPT FOR GENERATING MANIM CODE:\n"
        f"{SYSTEM_PROMPT}"
    )

# --- 3. Tool Definitions ---
@mcp.tool(description=EXECUTE_TOOL_DESC)
def execute_manim_code(manim_code: str) -> str:
    """Execute the Manim code"""
    tmpdir = os.path.join(BASE_DIR, "manim_tmp")
    os.makedirs(tmpdir, exist_ok=True)
    script_path = os.path.join(tmpdir, "scene.py")

    try:
        with open(script_path, "w", encoding="utf-8") as script_file:
            script_file.write(manim_code)

        # Use explicitly provided executable or default to current venv python -m manim
        if MANIM_EXECUTABLE:
            cmd = [MANIM_EXECUTABLE, "-p", script_path]
        else:
            cmd = [sys.executable, "-m", "manim", "-p", script_path]

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

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

---

### Step 4: Clean Up `.env`
Remove `MANIM_EXECUTABLE=...` so `.env` only holds configuration:
```env
SYSTEM_PROMPT="
Role & Instructions:
You are an expert in Manim (Community Edition) animation programming.
When generating code for execute_manim_code:
1. Always import manim using: from manim import *
2. Define a single main scene class that inherits from Scene (e.g. class GeneratedScene(Scene):).
3. Inside construct(self), add visual objects using self.play(...) or self.add(...).
4. Ensure all animations have explicit run times and sensible frame positioning (e.g. UP, DOWN, LEFT, RIGHT).
5. Never call interactive CLI prompts (input(), getpass()) or infinite loops.
6. Use modern Manim Community syntax (e.g., Create, Transform, FadeIn) rather than deprecated methods (ShowCreation).
7. Output pure executable Python code suitable for direct execution.
"
```

---

### Step 5: Update `.gitignore`
Ensure `.gitignore` contains:
```gitignore
*.pyc
__pycache__/
.venv/
.env
```

---

### Step 6: Update MCP Client Configs

#### OpenCode (`~/.config/opencode/opencode.jsonc`)
Point to the virtual environment's python executable:
```jsonc
    "manim": {
      "type": "local",
      "command": [
        "C:\\Users\\ADMIN\\OneDrive\\Desktop\\manim-mcp-server\\.venv\\Scripts\\python.exe",
        "C:\\Users\\ADMIN\\OneDrive\\Desktop\\manim-mcp-server\\src\\manim_server.py"
      ]
    }
```

#### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "manim-server": {
      "command": "C:\\Users\\ADMIN\\OneDrive\\Desktop\\manim-mcp-server\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\ADMIN\\OneDrive\\Desktop\\manim-mcp-server\\src\\manim_server.py"
      ]
    }
  }
}
```

---

## 4. Verification Checklist

- [ ] **Virtual Environment Integrity**: Ensure `.venv/Scripts/python.exe` exists and can run `python -m manim --help`.
- [ ] **Server Startup in `.venv`**: Execute `.\.venv\Scripts\python.exe src/manim_server.py` to verify imports and initialization.
- [ ] **Prompt Ingestion**: Verify `SYSTEM_PROMPT` is read from `.env` and attached to `execute_manim_code` tool metadata.
- [ ] **End-to-End Render Test**: Run a test render via `execute_manim_code` and confirm video renders in `src/media/manim_tmp`.
- [ ] **Client Connection**: Connect via OpenCode / Claude Desktop and verify the server operates normally.
