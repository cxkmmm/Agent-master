import pytest
from pathlib import Path
from smart_agent.utils.datafile_tool import get_file_md5_hex, listdir_with_allowed_type
from smart_agent.utils.path_tool import get_abs_path, get_proj_root

def test_md5_changes_with_content(tmp_path: Path):
    """
    tmp_path 是 pytest 内置的 fixture，提供一个临时目录（pathlib.Path 对象），
    测试结束后自动清理，避免污染真实文件系统。
    """
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    #写入内容
    first.write_text("same", encoding="utf-8")
    second.write_text("different", encoding="utf-8")

    assert get_file_md5_hex(str(first)) == get_file_md5_hex(str(first))
    assert get_file_md5_hex(str(first)) != get_file_md5_hex(str(second))


def test_directory_filter_ignores_unsupported_files(tmp_path: Path):
    (tmp_path / "a.md").write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "c.csv").write_text("c", encoding="utf-8")

    files = listdir_with_allowed_type(str(tmp_path), ("md", "txt"))

    #Path(item).name 取每个路径的文件名部分（去掉目录）
    assert [Path(item).name for item in files] == ["a.md", "b.txt"]


def test_path_traversal_is_rejected():
    with pytest.raises(ValueError):
        get_abs_path("../../outside.txt")


def test_project_relative_path_is_resolved():
    assert Path(get_abs_path("data/knowledge")) == get_proj_root() / "data" / "knowledge"
