from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from smart_agent.model.factory import embed_model
from smart_agent.utils.config_tool import chroma_config
from smart_agent.utils.datafile_tool import (
    get_file_md5_hex,
    listdir_with_allowed_type,
    pdf_loader,
    txt_loader,
)
from smart_agent.utils.log_tool import logger
from smart_agent.utils.path_tool import get_abs_path


class VectorStoreService:
    def __init__(self):
        self.persist_directory = get_abs_path(chroma_config["persist_directory"])
        """
        parents=True:
        递归创建父目录。如果路径是 a/b/c 而 a、a/b 都不存在，
        也会一并创建。等价于命令行的 mkdir -p。若为 False（默认），父目录不存在会抛 FileNotFoundError
        exist_ok=True: 
        目录已存在时不报错。若为 False（默认），目录已存在会抛 FileExistsError
        """
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        self.vector_store = Chroma(
            collection_name=chroma_config["collection_name"],
            embedding_function=embed_model,
            persist_directory=self.persist_directory,
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_config["chunk_size"],
            chunk_overlap=chroma_config["chunk_overlap"],
            separators=chroma_config["separators"],
            length_function=len,
        )

    def get_retriever(self):
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": chroma_config["k"]},
        )
        return retriever

    def load_documents(self):
        """
        从数据文件夹内读取数据文件，转为向量存入向量库
        要计算文件的md5去重
        :return：None
        """
        md5_path = Path(get_abs_path(chroma_config["md5_hex_path"]))
        md5_path.parent.mkdir(parents=True, exist_ok=True)

        #检查文件md5是否已经在存储中
        def check_md5_hex(md5_for_check: str) -> bool:
            if not md5_path.exists():
                md5_path.touch()
                return False
            if not md5_for_check:
                return False
            ##Path.open() 是 pathlib 提供的实例方法,和内置函数open一样
            with md5_path.open("r", encoding="utf-8") as handle:
                return any(line.strip() == md5_for_check for line in handle)

        def save_md5_hex(md5_for_check: str):
            with md5_path.open("a", encoding="utf-8") as handle:
                handle.write(md5_for_check + "\n")

        #返回符合路径的文件对象
        def get_file_documents(read_path: str):
            if read_path.endswith((".txt", ".md")):
                return txt_loader(read_path)

            if read_path.endswith("pdf"):
                return pdf_loader(read_path)

            return []

        #返回所有符合条件的文件的路径
        allowed_files_path: tuple[str,...] = listdir_with_allowed_type(
            get_abs_path(chroma_config["data_path"]),
            tuple(chroma_config["allow_knowledge_file_type"]),
        )

        #处理每个符合条件的文件
        for path in allowed_files_path:
            # 获取文件的MD5
            md5_hex = get_file_md5_hex(path)

            if not md5_hex:
                logger.warning("跳过无法计算 MD5 的文件: %s", path)
                continue

            if check_md5_hex(md5_hex):
                logger.info("[加载知识库]%s 已存在，跳过", path)
                continue

            try:
                # 返回文件对象
                documents: list[Document] = get_file_documents(path)

                if not documents:
                    logger.warning(f"[加载知识库]{path}内没有有效文本内容，跳过")
                    continue

                #对文件进行切片
                split_document: list[Document] = self.splitter.split_documents(documents)

                if not split_document:
                    logger.warning(f"[加载知识库]{path}分片后没有有效文本内容，跳过")
                    continue

                # 将内容存入向量库
                self.vector_store.add_documents(split_document)

                # 记录这个已经处理好的文件的md5，避免下次重复加载
                save_md5_hex(md5_hex)

                logger.info(f"[加载知识库]{path} 内容加载成功")
            except Exception as e:
                # exc_info为True会记录详细的报错堆栈，如果为False仅记录报错信息本身
                logger.error(f"[加载知识库]{path}加载失败：{str(e)}", exc_info=True)
                continue
            
