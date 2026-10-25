# Manim MCP Server

## Features

- **Dynamic Execution**: Renders Manim Python scripts directly to a scratch directory (`media/manim_tmp`).
- **Permanent Saves**: Persist finalized animations into topic-based folders (`media/<name>/`) on demand.
- **Model-Agnostic**: Guided by built-in system prompt instructions embedded at server startup.
- **Self-Contained**: Isolated virtual environment (`venv`) with no global dependencies.

---

## Tools Provided

| Tool | Description |
| :--- | :--- |
| `execute_manim_code` | Executes Python Manim code and renders video to `media/manim_tmp`. |
| `save_animation_folder` | Copies rendered animation files to a permanent, named folder under `media/`. |
| `cleanup_manim_temp_dir` | Cleans up and removes temporary directories to free disk space. |

---

## Quickstart

### 1. Clone & Setup Environment

```bash
git clone https://github.com/PrathamGBhat/manim-mcp-coding-club-rvce.git
cd manim-mcp-coding-club-rvce

# Create and activate virtual environment
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# Linux / macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)

Ensure `.env` in the project root points to your Manim binary:

```env
MANIM_EXECUTABLE="/absolute/path/to/manim-mcp-coding-club-rvce/venv/Scripts/manim.exe"
```

---

## Client Configuration

### OpenCode (`~/.config/opencode/opencode.jsonc`)

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "manim": {
      "type": "local",
      "command": [
        "/absolute/path/to/venv/Scripts/python.exe",
        "/absolute/path/to/src/manim_server.py"
      ]
    }
  }
}
```

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "manim": {
      "command": "/absolute/path/to/venv/Scripts/python.exe",
      "args": [
        "/absolute/path/to/src/manim_server.py"
      ]
    }
  }
}
```

---

## Example Prompt

Once connected to your MCP client, prompt your assistant:

> "Generate a Manim animation demonstrating a binary search tree insertion. Render it and, once it looks good, save it as `binary_search_tree`."