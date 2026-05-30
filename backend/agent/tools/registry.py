import os

from backend.agent.fips_rules import CODE_EXTENSIONS
from backend.armoriq_shims import Tool

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}


def _resolve_repo_path(repo_path: str, relative_path: str = ".") -> str:
    base = os.path.abspath(repo_path)
    target = os.path.abspath(os.path.join(base, relative_path))
    if target != base and not target.startswith(base + os.sep):
        raise ValueError("Path escapes repository root")
    return target


def build_scan_tools(repo_path: str) -> list[Tool]:
    abs_repo = os.path.abspath(repo_path)

    def list_files_impl(subdirectory: str = ".") -> dict:
        try:
            scan_root = _resolve_repo_path(abs_repo, subdirectory)
        except ValueError as exc:
            return {"error": str(exc)}

        files: list[str] = []
        for root, dirs, filenames in os.walk(scan_root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for filename in filenames:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, abs_repo)
                files.append(rel_path.replace(os.sep, "/"))

        files.sort()
        return {"files": files, "count": len(files), "repo_path": abs_repo}

    def read_file_impl(path: str) -> dict:
        try:
            file_path = _resolve_repo_path(abs_repo, path)
        except ValueError as exc:
            return {"error": str(exc)}

        if not os.path.isfile(file_path):
            return {"error": f"File not found: {path}"}

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
                content = handle.read()
            return {"content": content, "path": path.replace(os.sep, "/"), "lines": len(content.splitlines())}
        except OSError as exc:
            return {"error": str(exc)}

    def parse_dependency_impl(manifest_path: str) -> dict:
        try:
            file_path = _resolve_repo_path(abs_repo, manifest_path)
        except ValueError as exc:
            return {"error": str(exc)}

        if not os.path.isfile(file_path):
            return {"error": f"Manifest not found: {manifest_path}"}

        dependencies = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
                if manifest_path.endswith("requirements.txt"):
                    for line in handle:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            parts = line.split("==")
                            dependencies.append({
                                "name": parts[0],
                                "version": parts[1] if len(parts) > 1 else "latest",
                            })
        except OSError as exc:
            return {"error": str(exc)}

        return {"dependencies": dependencies, "manifest": manifest_path.replace(os.sep, "/")}

    def report_finding_impl(
        file_path: str,
        category: str,
        finding: str,
        description: str,
        remediation: str,
        severity: str = "MED",
        line_number: int | str | None = None,
    ) -> dict:
        parsed_line: int | None = None
        if isinstance(line_number, int):
            parsed_line = line_number
        elif isinstance(line_number, str) and line_number.strip().isdigit():
            parsed_line = int(line_number.strip())

        return {
            "recorded": True,
            "file_path": file_path,
            "category": category.upper(),
            "finding": finding,
            "description": description,
            "remediation": remediation,
            "severity": severity.upper(),
            "line_number": parsed_line,
        }

    return [
        Tool(
            name="list_files",
            description="List files in the repository or a subdirectory",
            func=list_files_impl,
            parameters={
                "subdirectory": {
                    "type": "string",
                    "description": "Relative subdirectory to scan (default: repository root)",
                    "required": False,
                },
            },
        ),
        Tool(
            name="read_file",
            description="Read the contents of a repository file using a repo-relative path",
            func=read_file_impl,
            parameters={
                "path": {"type": "string", "description": "Repo-relative path to the file"},
            },
        ),
        Tool(
            name="parse_dependency",
            description="Parse a dependency manifest file such as requirements.txt",
            func=parse_dependency_impl,
            parameters={
                "manifest_path": {
                    "type": "string",
                    "description": "Repo-relative path to the dependency manifest",
                },
            },
        ),
        Tool(
            name="report_finding",
            description="Record a compliance violation found during your analysis",
            func=report_finding_impl,
            parameters={
                "file_path": {"type": "string", "description": "Repo-relative path where the issue was found"},
                "category": {
                    "type": "string",
                    "description": "CRYPTOGRAPHIC | CONTAINER | DEPENDENCY | ACCESS_CONTROL | HEADER",
                },
                "finding": {"type": "string", "description": "Short finding identifier, e.g. MD5, root_user, outdated"},
                "description": {"type": "string", "description": "What the violation is and why it matters"},
                "remediation": {"type": "string", "description": "Step-by-step fix recommendation"},
                "severity": {"type": "string", "description": "HIGH | MED | LOW", "required": False},
                "line_number": {"type": "integer", "description": "Line number if applicable", "required": False},
            },
        ),
    ]


def discover_scan_files(repo_path: str) -> list[str]:
    abs_repo = os.path.abspath(repo_path)
    discovered: list[str] = []

    for root, dirs, files in os.walk(abs_repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for filename in files:
            rel_path = os.path.relpath(os.path.join(root, filename), abs_repo).replace(os.sep, "/")
            ext = os.path.splitext(filename)[1].lower()
            if ext in CODE_EXTENSIONS or filename in {"Dockerfile", "requirements.txt", "package.json"}:
                discovered.append(rel_path)

    discovered.sort()
    return discovered
