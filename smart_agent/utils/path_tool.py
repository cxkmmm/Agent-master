
"""
路径辅助函数。
所有项目相对路径均相对于仓库根目录解析。包含性检查可防止 API 调用方提供的路径逃逸出项目目录。
"""

from pathlib import Path

#返回仓库根目录
def get_proj_root() -> Path:
    """返回 smart_agent/utils/path_tool.py 对应的仓库根目录。"""

    return Path(__file__).resolve().parents[2]


#返回文件的绝对路径
def get_abs_path(rel_path: str) -> str:
    """将 rel_path 相对于项目根目录进行解析，并确保其位于项目根目录内。"""

    root = get_proj_root()
    target = (root / rel_path).resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"Path escapes the project root: {rel_path}")
    return str(target)


def ensure_dir(path: str) -> str:
    """如需要则创建 path，并返回该路径。"""

    Path(path).mkdir(parents=True, exist_ok=True)
    return path
