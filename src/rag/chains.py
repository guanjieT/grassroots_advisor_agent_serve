"""
RAG链实现
包含检索和生成功能
"""
from typing import List, Dict, Any, Optional, Generator
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from langchain_openai import ChatOpenAI

from knowledge_base.vector_store import VectorStoreManager
from utils.logger import logger
from config import config

class RAGChain:
    """RAG链封装类"""
    
    def __init__(self, vector_manager: Optional[VectorStoreManager] = None):
        """
        初始化RAG链
        
        Args:
            vector_manager: 向量数据库管理器
        """
        self.vector_manager = vector_manager or VectorStoreManager()
        
        # 初始化LLM
        self.llm = ChatTongyi(
            dashscope_api_key=config.DASHSCOPE_API_KEY,
            model=config.LLM_MODEL,
            temperature=config.DASHSCOPE_TEMPERATURE,
            max_tokens=config.DASHSCOPE_MAX_TOKENS
        )
        
        # 创建检索器
        self.retriever = self.vector_manager.get_retriever()
        
        # 创建提示模板
        self.prompt_template = self._create_prompt_template()
        
        # 创建RAG链
        self.rag_chain = self._create_rag_chain()
        
        logger.info("RAG链初始化完成")
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """创建提示模板"""
        
        system_prompt = """你是一位经验丰富的基层工作专家，专门为基层工作人员提供智能化的工作指导和建议。

你的主要任务：
1. 根据提供的成功案例，为当前问题提供具体、可操作的解决方案
2. 结合基层工作的实际情况，给出分步骤的处理建议
3. 提炼相关案例的成功经验，形成可复制的工作方法
4. 如果案例中没有直接相关的信息，可以结合常见的基层工作经验给出建议

回答要求：
- 语言通俗易懂，贴近基层工作实际
- 提供具体的操作步骤，而不是抽象的建议
- 注重实效性和可操作性
- 如果涉及多部门协作，要说明协调要点
- 提及案例来源，增加建议的可信度

参考案例信息：
{context}

请基于以上案例，为用户的问题提供专业、实用的解决建议。"""

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{question}")
        ])
        
        return prompt_template
    
    def _format_docs(self, docs: List[Document]) -> str:
        """格式化检索到的文档"""
        if not docs:
            return "未找到相关案例。"
        
        formatted_docs = []
        for i, doc in enumerate(docs, 1):
            title = doc.metadata.get('title', '未知标题')
            category = doc.metadata.get('category', '未知类别')
            content = doc.page_content
            
            formatted_doc = f"""
案例 {i}: {title}
领域: {category}
内容: {content}
"""
            formatted_docs.append(formatted_doc)
        
        return "\n" + "="*50 + "\n".join(formatted_docs)
    
    def _create_rag_chain(self):
        """创建RAG链"""
        
        # 检索并格式化文档
        def retrieve_and_format(question):
            # 使用新的 invoke 方法替代已弃用的 get_relevant_documents
            docs = self.retriever.invoke(question)
            return self._format_docs(docs)
        
        # 构建RAG链
        rag_chain = (
            {
                "context": RunnableLambda(retrieve_and_format),
                "question": RunnablePassthrough()
            }
            | self.prompt_template
            | self.llm
            | StrOutputParser()
        )
        
        return rag_chain
    
    def invoke(self, question: str) -> str:
        """
        调用RAG链生成回答
        
        Args:
            question: 用户问题
            
        Returns:
            生成的回答
        """
        try:
            logger.info(f"处理问题: {question}")
            
            # 调用RAG链
            response = self.rag_chain.invoke(question)
            
            logger.info("问题处理完成")
            return response
            
        except Exception as e:
            logger.error(f"RAG链调用失败: {e}")
            return f"抱歉，处理您的问题时出现错误: {str(e)}"
    

    def stream(self, question: str) -> Generator[str, None, None]:
        """
        流式输出回答；若底层模型不支持流式，将退化为一次性输出。
        """
        try:
            # 优先使用可流式的链
            for chunk in self.rag_chain.stream(question):
                # 确保 chunk 为字符串
                yield str(chunk)
        except Exception:
            # 退化为非流式
            yield self.invoke(question)

    def get_relevant_cases(self, question: str, k: int = 3) -> List[Document]:
        """
        获取相关案例（用于调试和展示）
        
        Args:
            question: 用户问题
            k: 返回案例数量
            
        Returns:
            相关案例列表
        """
        try:
            # 使用新的 invoke 方法替代已弃用的 get_relevant_documents
            docs = self.retriever.invoke(question)
            return docs[:k]
        except Exception as e:
            logger.error(f"获取相关案例失败: {e}")
            return []

class ConversationalRAGChain:
    """对话式RAG链，支持多轮对话"""
    
    def __init__(self, vector_manager: Optional[VectorStoreManager] = None):
        """
        初始化对话式RAG链
        
        Args:
            vector_manager: 向量数据库管理器
        """
        self.vector_manager = vector_manager or VectorStoreManager()
        
        # 初始化LLM
        self.llm = ChatTongyi(
            dashscope_api_key=config.DASHSCOPE_API_KEY,
            model=config.LLM_MODEL,
            temperature=config.DASHSCOPE_TEMPERATURE,
            max_tokens=config.DASHSCOPE_MAX_TOKENS
        )
        
        # 创建检索器
        self.retriever = self.vector_manager.get_retriever()
        
        # 创建对话提示模板
        self.conversational_prompt = self._create_conversational_prompt()
        
        # 对话历史
        self.chat_history = []
        
        logger.info("对话式RAG链初始化完成")
    
    def _create_conversational_prompt(self) -> ChatPromptTemplate:
        """创建对话式提示模板"""
        
        system_prompt = """你是一位资深的基层工作指导专家，专门为基层工作人员提供专业建议。

你具备以下能力：
1. 深度理解基层工作的复杂性和特殊性
2. 能够从成功案例中提炼可复制的工作方法
3. 提供贴合实际、具有可操作性的解决方案
4. 考虑基层工作的人情味和灵活性

在对话中，你需要：
- 结合历史对话内容，提供连贯的建议
- 参考相关案例，但不生搬硬套
- 重视实际效果，提供具体的操作指导
- 语言亲切、专业，易于理解

相关案例：
{context}"""

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        return prompt_template
    
    def _format_docs(self, docs: List[Document]) -> str:
        """格式化检索到的文档"""
        if not docs:
            return "未找到直接相关的案例，我将基于基层工作的一般经验为您提供建议。"
        
        formatted_docs = []
        for i, doc in enumerate(docs, 1):
            title = doc.metadata.get('title', '未知案例')
            category = doc.metadata.get('category', '未知领域')
            content = doc.page_content
            
            # 截取部分内容避免过长
            if len(content) > 300:
                content = content[:300] + "..."
            
            formatted_doc = f"案例{i}《{title}》({category}): {content}"
            formatted_docs.append(formatted_doc)
        
        return "\n\n".join(formatted_docs)
    
    def chat(self, question: str) -> str:
        """
        进行对话
        
        Args:
            question: 用户问题
            
        Returns:
            AI回答
        """
        try:
            logger.info(f"对话问题: {question}")
            
            # 检索相关文档
            # 使用新的 invoke 方法替代已弃用的 get_relevant_documents
            docs = self.retriever.invoke(question)
            context = self._format_docs(docs)
            
            # 构建输入
            chain_input = {
                "context": context,
                "chat_history": self.chat_history,
                "question": question
            }
            
            # 生成回答
            response = (
                self.conversational_prompt 
                | self.llm 
                | StrOutputParser()
            ).invoke(chain_input)
            
            # 更新对话历史
            self.chat_history.extend([
                HumanMessage(content=question),
                AIMessage(content=response)
            ])
            
            # 限制对话历史长度
            if len(self.chat_history) > 10:  # 保持最近5轮对话
                self.chat_history = self.chat_history[-10:]
            
            logger.info("对话回答生成完成")
            return response
            
        except Exception as e:
            logger.error(f"对话处理失败: {e}")
            return f"抱歉，处理您的问题时出现了错误: {str(e)}"

    def stream_chat(self, question: str) -> Generator[str, None, None]:
        """
        多轮对话模式的流式输出。流期间先缓冲完整回答，结束后再写入历史。
        """
        try:
            # 检索上下文
            docs = self.retriever.invoke(question)
            context = self._format_docs(docs)
            chain_input = {
                "context": context,
                "chat_history": self.chat_history,
                "question": question
            }
            full = []
            chain = (self.conversational_prompt | self.llm | StrOutputParser())
            for chunk in chain.stream(chain_input):
                chunk = str(chunk)
                full.append(chunk)
                yield chunk
            # 更新对话历史（在完成后一次性追加，避免在流式中反复变更状态）
            final_text = "".join(full)
            self.chat_history.extend([
                HumanMessage(content=question),
                AIMessage(content=final_text)
            ])
            if len(self.chat_history) > 10:
                self.chat_history = self.chat_history[-10:]
        except Exception as e:
            yield f"抱歉，流式输出时出现错误：{e}"

    
    def clear_history(self):
        """清除对话历史"""
        self.chat_history = []
        logger.info("对话历史已清除")
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        history = []
        for i in range(0, len(self.chat_history), 2):
            if i + 1 < len(self.chat_history):
                human_msg = self.chat_history[i]
                ai_msg = self.chat_history[i + 1]
                history.append({
                    "question": human_msg.content,
                    "answer": ai_msg.content
                })
        return history

if __name__ == "__main__":
    # 测试RAG链
    try:
        # 基础RAG链测试
        rag_chain = RAGChain()
        
        test_questions = [
            "如何处理邻里纠纷？",
            "社区停车难问题如何解决？",
            "如何提高政策宣传效果？"
        ]
        
        print("=== 基础RAG链测试 ===")
        for question in test_questions:
            print(f"\n问题: {question}")
            answer = rag_chain.invoke(question)
            print(f"回答: {answer[:200]}...")
        
        # 对话式RAG链测试
        print("\n=== 对话式RAG链测试 ===")
        conv_rag = ConversationalRAGChain()
        
        conv_questions = [
            "我们社区有邻里纠纷问题",
            "具体是噪音问题导致的",
            "应该怎么协调双方？"
        ]
        
        for question in conv_questions:
            print(f"\n问题: {question}")
            answer = conv_rag.chat(question)
            print(f"回答: {answer[:200]}...")
        
    except Exception as e:
        print(f"测试失败: {e}")
        logger.error(f"RAG链测试失败: {e}") 