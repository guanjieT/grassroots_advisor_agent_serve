"""
知识库加载器
负责加载和处理基层工作案例数据
"""
import os
import json
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader, 
    JSONLoader,
    DirectoryLoader
)
from utils.logger import logger
from config import config

class CaseLoader:
    """基层工作案例加载器"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
        )
    
    def load_from_json(self, file_path: str) -> List[Document]:
        """
        从JSON文件加载案例
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            Document列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cases = json.load(f)
            
            documents = []
            
            # 如果是单个案例对象
            if isinstance(cases, dict) and 'title' in cases:
                cases = [cases]
            # 如果是案例字典（key为案例ID）
            elif isinstance(cases, dict):
                cases = list(cases.values())
            
            for i, case in enumerate(cases):
                if isinstance(case, dict):
                    doc_content = self._format_case_content(case)
                    metadata = {
                        'source': file_path,
                        'case_id': case.get('id', f'case_{i}'),
                        'title': case.get('title', '未知标题'),
                        'category': case.get('category', '其他'),
                        'type': 'case'
                    }
                    documents.append(Document(
                        page_content=doc_content,
                        metadata=metadata
                    ))
            
            logger.info(f"从 {file_path} 加载了 {len(documents)} 个案例")
            return documents
            
        except Exception as e:
            logger.error(f"加载JSON文件失败 {file_path}: {e}")
            return []
    
    def load_from_text(self, file_path: str) -> List[Document]:
        """
        从文本文件加载案例
        
        Args:
            file_path: 文本文件路径
            
        Returns:
            Document列表
        """
        try:
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
            
            # 添加元数据
            for doc in documents:
                doc.metadata.update({
                    'source': file_path,
                    'type': 'text',
                    'title': os.path.basename(file_path)
                })
            
            logger.info(f"从 {file_path} 加载了 {len(documents)} 个文档")
            return documents
            
        except Exception as e:
            logger.error(f"加载文本文件失败 {file_path}: {e}")
            return []
    
    def load_from_directory(self, directory_path: str) -> List[Document]:
        """
        从目录加载所有案例文件
        
        Args:
            directory_path: 目录路径
            
        Returns:
            Document列表
        """
        if not os.path.exists(directory_path):
            logger.warning(f"目录不存在: {directory_path}")
            return []
        
        all_documents = []
        
        # 遍历目录中的所有文件
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                if file_ext == '.json':
                    docs = self.load_from_json(file_path)
                    all_documents.extend(docs)
                elif file_ext in ['.txt', '.md']:
                    docs = self.load_from_text(file_path)
                    all_documents.extend(docs)
        
        logger.info(f"从目录 {directory_path} 总共加载了 {len(all_documents)} 个文档")
        return all_documents
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        分割文档为较小的块
        
        Args:
            documents: 原始文档列表
            
        Returns:
            分割后的文档列表
        """
        try:
            split_docs = self.text_splitter.split_documents(documents)
            logger.info(f"文档分割完成: {len(documents)} -> {len(split_docs)} 个块")
            return split_docs
        except Exception as e:
            logger.error(f"文档分割失败: {e}")
            return documents
    
    def _format_case_content(self, case: Dict[str, Any]) -> str:
        """
        格式化案例内容
        
        Args:
            case: 案例字典
            
        Returns:
            格式化后的案例内容
        """
        content_parts = []
        
        # 标题
        if 'title' in case:
            content_parts.append(f"案例标题: {case['title']}")
        
        # 问题描述
        if 'problem' in case:
            content_parts.append(f"问题描述: {case['problem']}")
        
        # 涉及领域/分类
        if 'category' in case:
            content_parts.append(f"涉及领域: {case['category']}")
        
        # 解决步骤
        if 'steps' in case:
            if isinstance(case['steps'], list):
                steps_text = '\n'.join([f"{i+1}. {step}" for i, step in enumerate(case['steps'])])
                content_parts.append(f"解决步骤:\n{steps_text}")
            else:
                content_parts.append(f"解决步骤: {case['steps']}")
        
        # 结果
        if 'result' in case:
            content_parts.append(f"处理结果: {case['result']}")
        
        # 反思总结
        if 'reflection' in case:
            content_parts.append(f"经验总结: {case['reflection']}")
        
        # 关键词
        if 'keywords' in case:
            if isinstance(case['keywords'], list):
                keywords_text = ', '.join(case['keywords'])
            else:
                keywords_text = case['keywords']
            content_parts.append(f"关键词: {keywords_text}")
        
        return '\n\n'.join(content_parts)

def create_sample_cases(save_path: str = "./data/knowledge_base/sample_cases.json"):
    """
    创建示例案例数据
    
    Args:
        save_path: 保存路径
    """
    sample_cases = [
        {
            "id": "case_001",
            "title": "邻里纠纷调解成功案例",
            "category": "邻里纠纷",
            "problem": "两户居民因楼上装修噪音问题产生激烈冲突，多次争吵影响社区和谐。楼上住户进行装修，时间不规律，楼下住户有老人和婴儿，噪音影响严重。",
            "steps": [
                "及时介入，分别了解双方诉求和困难",
                "组织双方面对面沟通，创建理解氛围",
                "制定具体的装修时间表：工作日9-12点、14-17点",
                "建立微信群便于日常沟通协调",
                "定期回访了解执行情况"
            ],
            "result": "双方达成装修时间协议，矛盾得到化解，社区关系恢复和谐。",
            "reflection": "关键在于及时介入、耐心倾听、方案具体可执行，建立长效沟通机制。",
            "keywords": ["邻里纠纷", "装修噪音", "调解", "沟通协调", "时间管理"]
        },
        {
            "id": "case_002", 
            "title": "困难家庭救助申请快速办理",
            "category": "民生服务",
            "problem": "单亲母亲突发重病，家庭失去经济来源，孩子面临辍学风险，急需各类救助。",
            "steps": [
                "立即启动绿色通道，上门了解具体情况",
                "协调医院、民政、教育等多部门联动",
                "同时办理医疗救助、低保申请、教育资助",
                "联系社会组织和爱心企业提供额外帮助",
                "建立长期跟踪帮扶机制"
            ],
            "result": "三天内完成所有救助申请，孩子继续上学，家庭渡过难关。",
            "reflection": "多部门协作、急事急办、综合施策是关键，要建立长效帮扶不是一次性救助。",
            "keywords": ["困难救助", "多部门协作", "绿色通道", "综合施策", "长效帮扶"]
        },
        {
            "id": "case_003",
            "title": "老旧小区停车难问题解决",
            "category": "社区治理", 
            "problem": "老旧小区车位不足，车辆乱停乱放，影响通行和消防安全，居民意见很大。",
            "steps": [
                "组织居民代表大会，充分听取意见建议",
                "实地测量，制定停车位规划方案",
                "协调物业、交管部门，设置规范停车位",
                "建立停车自治管理小组，制定管理制度",
                "试行一段时间后根据效果优化调整"
            ],
            "result": "新增停车位30个，建立了自治管理制度，停车秩序明显改善。",
            "reflection": "居民参与是基础，科学规划是关键，自治管理是保障。",
            "keywords": ["停车管理", "社区治理", "居民自治", "科学规划", "制度建设"]
        },
        {
            "id": "case_004",
            "title": "政策宣传提高居民知晓率",
            "category": "政策宣传",
            "problem": "新出台的养老保险政策复杂，老年居民理解困难，参与率低。",
            "steps": [
                "制作通俗易懂的政策解读材料和图解",
                "组织政策宣讲会，邀请专家现场答疑",
                "设立政策咨询台，提供一对一服务",
                "利用社区广播、微信群等多渠道宣传",
                "组织志愿者入户走访，确保全覆盖"
            ],
            "result": "政策知晓率从30%提高到95%，参与率大幅提升。",
            "reflection": "要用老百姓听得懂的语言，多渠道宣传，确保信息传达到位。",
            "keywords": ["政策宣传", "通俗解读", "多渠道宣传", "入户走访", "全覆盖"]
        },
        {
            "id": "case_005",
            "title": "环境卫生整治长效管理",
            "category": "环境治理",
            "problem": "社区环境卫生反复反弹，垃圾分类执行不到位，居民环保意识有待提高。",
            "steps": [
                "深入调研找出卫生问题根源",
                "制定环境卫生管理制度和标准",
                "开展垃圾分类培训和环保教育",
                "建立卫生监督员队伍，定期检查",
                "设立奖惩机制，表彰先进、曝光后进"
            ],
            "result": "社区环境持续改善，垃圾分类准确率达到90%以上。",
            "reflection": "制度建设是基础，宣传教育是手段，长效管理是关键。",
            "keywords": ["环境治理", "垃圾分类", "制度建设", "宣传教育", "长效管理"]
        }
    ]
    
    # 确保目录存在
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # 保存示例案例
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(sample_cases, f, ensure_ascii=False, indent=2)
    
    logger.info(f"示例案例已保存到: {save_path}")

if __name__ == "__main__":
    # 创建示例案例
    create_sample_cases()
    
    # 测试加载器
    loader = CaseLoader()
    documents = loader.load_from_json("./data/knowledge_base/sample_cases.json")
    split_docs = loader.split_documents(documents)
    
    print(f"加载了 {len(documents)} 个案例，分割为 {len(split_docs)} 个文档块") 