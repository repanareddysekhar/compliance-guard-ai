from backend.armoriq_shims import Tool
import os

def read_file_impl(path: str) -> dict:
    try:
        if not os.path.exists(path):
            return {"error": f"File not found: {path}"}
        
        with open(path, 'r') as f:
            content = f.read()
        return {"content": content, "path": path}
    except Exception as e:
        return {"error": str(e)}

tool = Tool(
    name="read_file",
    description="Read the contents of a file at the given path",
    func=read_file_impl,
    parameters={
        "path": {"type": "string", "description": "The absolute path to the file to read"}
    }
)
