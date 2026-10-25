# Implementation Plan: Post-Execution Animation Preservation (`save_animation_folder` Tool)

This plan outlines how to introduce a new MCP tool, `save_animation_folder`, that copies finalized animations from `media/manim_tmp` to a permanently named folder (e.g., `media/for_loop_till_5/`, `media/minimum_rotations_to_sort_array/`).

This design leaves `execute_manim_code` completely untouched and stateless, allowing the LLM to freely iterate and fix errors in scratch before committing a named copy.

---

## 1. Architectural Advantages

```
                                  [ User Request ]
                                         │
                                         ▼
                   +--------------------------------------------+
                   | Step 1: execute_manim_code(...)            |
                   |   - Renders directly into media/manim_tmp  |
                   |   - Scratchpad: safe to re-run and fix     |
                   |     syntax or layout errors iteratively    |
                   +--------------------------------------------+
                                         │ (On Success)
                                         ▼
                   +--------------------------------------------+
                   | Step 2: save_animation_folder(folder_name) |
                   |   - Sanitizes LLM-chosen snake_case name   |
                   |   - Copies media/manim_tmp/                |
                   |     -> media/<sanitized_name>/             |
                   |   - Preserves video + scene.py permanently |
                   +--------------------------------------------+
```

### Why this design is best:
1. **Zero Global State**: `execute_manim_code` does not track or hold session variables in memory. Each run uses `media/manim_tmp`.
2. **Scratchpad Iteration**: If the model makes a syntax mistake or overlapping shapes, it retries in `manim_tmp` without creating orphaned, half-broken folders.
3. **Preservation**: Successful animations are permanently organized by topic in `media/`.

---

## 2. Name Sanitization & Safety

Because `folder_name` is provided by the LLM, it must be sanitized against path traversal (`../`) and illegal filesystem characters:

```python
import re

def sanitize_folder_name(name: str) -> str:
    """Sanitize the animation folder name to safe snake_case."""
    if not name or not name.strip():
        return "saved_animation"
    
    clean = name.strip().lower()
    # Replace spaces and hyphens with underscores
    clean = re.sub(r'[\s\-]+', '_', clean)
    # Remove any character that is not alphanumeric or underscore
    clean = re.sub(r'[^a-z0-9_]', '', clean)
    # Collapse multiple underscores
    clean = re.sub(r'_+', '_', clean).strip('_')
    
    return clean[:64] or "saved_animation"
```

---

## 3. Concrete Implementation

### File: `src/manim_server.py`

Add `save_animation_folder` alongside the existing tools, preserving all existing comments, docstrings, and structure verbatim:

```python
import subprocess
import os
import shutil
import sys
import re

from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(ROOT_DIR, ".env")
load_dotenv(dotenv_path=ENV_FILE)

SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "").strip()
MANIM_EXECUTABLE = os.getenv("MANIM_EXECUTABLE")

TEMP_DIRS = {}
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")
os.makedirs(BASE_DIR, exist_ok=True) 

EXECUTE_TOOL_DESC = SYSTEM_PROMPT or "Execute the Manim code"

def sanitize_folder_name(name: str) -> str:
    """Sanitize the animation folder name to safe snake_case."""
    if not name or not name.strip():
        return "saved_animation"
    clean = name.strip().lower()
    clean = re.sub(r'[\s\-]+', '_', clean)
    clean = re.sub(r'[^a-z0-9_]', '', clean)
    clean = re.sub(r'_+', '_', clean).strip('_')
    return clean[:64] or "saved_animation"

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
        cmd = [MANIM_EXECUTABLE, "-p", script_path] if MANIM_EXECUTABLE else [sys.executable, "-m", "manim", "-p", script_path]
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
def save_animation_folder(folder_name: str) -> str:
    """Save and copy the current rendered animation from manim_tmp into a permanently named folder.

    Args:
        folder_name: Short, concise snake_case name representing the animation 
                     (e.g., 'for_loop_till_5', 'minimum_rotations_to_sort_array', 
                     'binary_search_tree').
    """
    tmpdir = os.path.join(BASE_DIR, "manim_tmp")

    if not os.path.exists(tmpdir) or not os.listdir(tmpdir):
        return "No animation found in manim_tmp to save. Run execute_manim_code successfully first."

    clean_name = sanitize_folder_name(folder_name)
    target_dir = os.path.join(BASE_DIR, clean_name)

    try:
        shutil.copytree(tmpdir, target_dir, dirs_exist_ok=True)
        return f"Successfully saved animation to: {target_dir}"
    except Exception as e:
        return f"Failed to save animation to {target_dir}. Error: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
```

---

## 4. Instructing the Model via `.env` (`SYSTEM_PROMPT`)

To ensure any model invokes `save_animation_folder` right after a successful execution, append workflow instructions to `SYSTEM_PROMPT` in `.env`:

```env
SYSTEM_PROMPT="
...
Workflow:
1. Generate the Manim code and call `execute_manim_code`.
2. If execution fails, review the error, fix the code, and retry with `execute_manim_code`.
3. Once the video has been generated successfully, call `save_animation_folder` with the shortest, most appropriate snake_case name for the concept (e.g., 'for_loop_till_5', 'binary_search_tree') to permanently save it.
"
```

---

## 5. Verification Checklist

- [ ] **Empty State Guard**: Call `save_animation_folder("test")` before any render; verify it reports that no animation is found in `manim_tmp`.
- [ ] **Sanitization**: Test names with spaces (`"For Loop 5"`) and path traversal (`"../../hack"`), ensuring they map safely to `media/for_loop_5` and `media/hack`.
- [ ] **Copy Completeness**: After a successful `execute_manim_code`, call `save_animation_folder("test_anim")` and verify `media/test_anim/` contains both `scene.py` and the `videos/` subfolder.
- [ ] **Subsequent Overwrite Isolation**: Render a second animation in `manim_tmp` and save it as `"test_anim_2"`; verify `media/test_anim/` is completely preserved.
- [ ] **Comments & Structure Integrity**: Verify 100% of existing comments in `src/manim_server.py` are unchanged.
