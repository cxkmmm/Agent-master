"""Retrieval-augmented generation service."""

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from smart_agent.model.factory import ChatModelFactory
from smart_agent.rag.vector_store import VectorStoreService
from smart_agent.utils.promptloader_tool import load_rag_prompt

def print_prompt_template(messages):
    print("模型总结的资料：")
    print(messages.to_string())
    return messages

def print_modelrag(messages):
    print("模型总结的资料：")
    print(messages.content)
    return messages

class RAGService:
    def __init__(self, vector_store=None, model=None):
        self.vector_store = vector_store or VectorStoreService()
        self.retriever = self.vector_store.get_retriever()
        #载入rag_summerize.txt
        self.prompt_template = PromptTemplate.from_template(load_rag_prompt())
        self.model = model or ChatModelFactory().generator()
        self.chain = self.prompt_template | print_prompt_template |self.model | print_modelrag |StrOutputParser()

    def retriever_docs(self, query: str) -> list[Document]:
        return self.retriever.invoke(query)

    def rag_summarize(self, query: str) -> str:
        docs = self.retriever_docs(query)      #检索匹配资料
        context_parts = []
        for index, doc in enumerate(docs, start=1):
            context_parts.append(
                f"参考资料{index}. {doc.page_content}\n"
                f"资料元数据：{doc.metadata}\n"
            )
        context = "\n".join(context_parts)  #返回匹配的资料
        return self.chain.invoke({"input": query, "context": context})  #调用链
