"""从data/knowledge重建本地Chroma集合。
用法:
 没带 --yes 就只打印、不执行
python -m scripts.rebuild_knowledge --yes
"""
import argparse # 解析命令行参数
import shutil   ## 删除目录（rmtree）
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]  #获得当前文件的根目录
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  #将根目录加入到sys.path中

#导入项目内部的模块
from smart_agent.rag.vector_store import VectorStoreService  # noqa: E402
from smart_agent.utils.config_tool import chroma_config  # noqa: E402
from smart_agent.utils.path_tool import get_abs_path  # noqa: E402

#添加文件于向量库
def add_document():
    service = VectorStoreService()
    print(f"添加文件前向量库的数量：{service.vector_store._collection.count()}")
    service.load_documents()
    print(f"添加文件后向量库的数量：{service.vector_store._collection.count()}")

#对知识库重构
def main() -> None:
    """
    创建命令行解析器，定义 --yes 开关（store_true 表示不带值，出现即为 True）。
    为什么要有 --yes？因为重建会删除旧数据，属于危险操作，强制用户显式确认。
    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--yes",
        action="store_true",
        help="“在重建之前，请确认删除现有集合。”",
    )
    args = parser.parse_args()

    persist_dir = Path(get_abs_path(chroma_config["persist_directory"]))
    md5_path = Path(get_abs_path(chroma_config["md5_hex_path"]))

    # 没带 --yes 就只打印、不执行
    if not args.yes:
        print(f"Will remove: {persist_dir}")
        print(f"Will remove: {md5_path}")
        print("提示：命令结尾带上 --yes将会删除上述路径下的目录或者文件")
        return

    if persist_dir.exists():
        shutil.rmtree(persist_dir)   # 递归删除整个目录
    if md5_path.exists():
        md5_path.unlink()  # 删除单个文件

    service = VectorStoreService()
    service.load_documents()
    count = service.vector_store._collection.count()
    if count == 0:
        raise SystemExit(
        "没有索引任何块。请检查嵌入API / 网络以及data / knowledge下的文件。"
        )
    print(f"Rebuilt collection: {chroma_config['collection_name']} ({count} chunks)")



if __name__ == "__main__":

    #main()  #重构知识库
    add_document() #添加文件于向量库
    #print(sys.path[0])