from armoriq.armorclaw import Tool
import os

def parse_dependency_impl(manifest_path: str) -> dict:
    # Simplified parser for requirements.txt or package.json
    try:
        if not os.path.exists(manifest_path):
            return {"error": f"Manifest not found: {manifest_path}"}
        
        dependencies = []
        with open(manifest_path, 'r') as f:
            if manifest_path.endswith('requirements.txt'):
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split('==')
                        dependencies.append({
                            "name": parts[0],
                            "version": parts[1] if len(parts) > 1 else "latest"
                        })
            # Add more parsers for package.json, pom.xml, etc.
        
        return {"dependencies": dependencies, "manifest": manifest_path}
    except Exception as e:
        return {"error": str(e)}

tool = Tool(
    name="parse_dependency",
    description="Parse a dependency manifest file (e.g., requirements.txt) to list packages",
    func=parse_dependency_impl,
    parameters={
        "manifest_path": {"type": "string", "description": "Path to the dependency manifest file"}
    }
)
