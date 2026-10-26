"""文件哈希与文档加载辅助函数"""
import hashlib
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from smart_agent.utils.log_tool import logger

#获取文件的md5
def get_file_md5_hex(file_path: str) -> str | None:
    path = Path(file_path)
    if not path.exists():
        logger.error("File does not exist: %s", path)
        return None
    if not path.is_file():
        logger.error("Path is not a file: %s", path)
        return None

    digest = hashlib.md5()
    try:
        #Path.open() 是 pathlib 提供的实例方法,和内置函数open一样
        with path.open("rb") as handle:
            while chunk := handle.read(4096):
                digest.update(chunk)
    except OSError:
        logger.exception("Failed to hash file: %s", path)
        return None
    return digest.hexdigest()

#返回所有符合条件的文件名
def listdir_with_allowed_type(path: str, allowed_types: tuple[str, ...]) -> tuple[str, ...]:
    """返回已排序的常规文件，其后缀在 allowed_types 之中。"""

    root = Path(path)
    if not root.is_dir():
        logger.error("Path is not a directory: %s", root)
        return ()

    suffixes = tuple(item.lower().lstrip(".") for item in allowed_types)

    #对文件进行排序
    files = sorted(
        str(item)
        for item in root.iterdir()
        if item.is_file() and item.suffix.lower().lstrip(".") in suffixes
    )
    return tuple(files)


def txt_loader(file_path: str, encoding: str = "utf-8") -> list[Document]:
    return TextLoader(file_path, encoding=encoding).load()


def pdf_loader(file_path: str, password: str | None = None) -> list[Document]:
    return PyPDFLoader(file_path, password=password).load()
