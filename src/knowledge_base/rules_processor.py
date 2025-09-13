"""
法规政策处理器
负责处理和集成法规政策文件到知识库
"""
import os
import json
import zipfile
import rarfile
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from utils.logger import logger
from config import config

class RulesProcessor:
    """法规政策处理器"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "；", "，", " ", ""]
        )
        self.rules_base_path = "./data/rules"
        self.processed_rules_path = "./data/processed_rules"
        
        # 确保处理后的文件目录存在
        os.makedirs(self.processed_rules_path, exist_ok=True)
    
    def extract_all_archives(self) -> bool:
        """
        解压所有压缩文件
        
        Returns:
            是否解压成功
        """
        try:
            logger.info("开始解压法规政策文件...")
            
            # 遍历所有文件
            for root, dirs, files in os.walk(self.rules_base_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file)[1].lower()
                    
                    if file_ext == '.zip':
                        self._extract_zip(file_path)
                    elif file_ext == '.rar':
                        self._extract_rar(file_path)
            
            logger.info("所有压缩文件解压完成")
            return True
            
        except Exception as e:
            logger.error(f"解压文件失败: {e}")
            return False
    
    def _extract_zip(self, zip_path: str):
        """解压ZIP文件"""
        try:
            extract_dir = os.path.splitext(zip_path)[0]
            if not os.path.exists(extract_dir):
                # 尝试不同的编码方式
                encodings = ['utf-8', 'gbk', 'cp936', None]
                extracted = False
                
                for encoding in encodings:
                    try:
                        if encoding:
                            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                # 手动处理文件名编码
                                for member in zip_ref.namelist():
                                    try:
                                        # 尝试用指定编码解码文件名
                                        decoded_name = member.encode('cp437').decode(encoding)
                                        zip_ref.extract(member, extract_dir)
                                    except:
                                        # 如果解码失败，使用原始文件名
                                        zip_ref.extract(member, extract_dir)
                        else:
                            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                zip_ref.extractall(extract_dir)
                        
                        extracted = True
                        logger.info(f"解压ZIP文件: {zip_path} (编码: {encoding or 'default'})")
                        break
                    except Exception as e:
                        continue
                
                if not extracted:
                    logger.warning(f"ZIP文件解压失败，跳过: {zip_path}")
                    
        except Exception as e:
            logger.error(f"解压ZIP文件失败 {zip_path}: {e}")
    
    def _extract_rar(self, rar_path: str):
        """解压RAR文件"""
        try:
            extract_dir = os.path.splitext(rar_path)[0]
            if not os.path.exists(extract_dir):
                with rarfile.RarFile(rar_path) as rar_ref:
                    rar_ref.extractall(extract_dir)
                logger.info(f"解压RAR文件: {rar_path}")
        except Exception as e:
            logger.error(f"解压RAR文件失败 {rar_path}: {e}")
    
    def process_excel_files(self) -> List[Document]:
        """
        处理Excel文件（北大法宝数据）
        
        Returns:
            处理后的文档列表
        """
        documents = []
        
        try:
            # 查找所有Excel文件
            excel_files = []
            for root, dirs, files in os.walk(self.rules_base_path):
                for file in files:
                    if file.endswith(('.xlsx', '.xls')):
                        excel_files.append(os.path.join(root, file))
            
            logger.info(f"找到 {len(excel_files)} 个Excel文件")
            
            for excel_file in excel_files:
                docs = self._process_single_excel(excel_file)
                documents.extend(docs)
            
            logger.info(f"从Excel文件处理得到 {len(documents)} 个文档")
            return documents
            
        except Exception as e:
            logger.error(f"处理Excel文件失败: {e}")
            return []
    
    def _process_single_excel(self, excel_path: str) -> List[Document]:
        """处理单个Excel文件"""
        documents = []
        
        try:
            # 从文件名推断类别
            filename = os.path.basename(excel_path)
            category = self._extract_category_from_filename(filename)
            
            # 读取Excel文件
            df = pd.read_excel(excel_path)
            
            # 处理每一行数据
            for index, row in df.iterrows():
                doc_content = self._format_excel_row(row, category)
                if doc_content:
                    metadata = {
                        'source': excel_path,
                        'category': category,
                        'type': 'regulation',
                        'row_index': index,
                        'filename': filename
                    }
                    
                    # 添加具体的法规信息到metadata
                    if '标题' in row and pd.notna(row['标题']):
                        metadata['title'] = str(row['标题'])
                    if '发布机关' in row and pd.notna(row['发布机关']):
                        metadata['authority'] = str(row['发布机关'])
                    if '发布日期' in row and pd.notna(row['发布日期']):
                        metadata['publish_date'] = str(row['发布日期'])
                    
                    documents.append(Document(
                        page_content=doc_content,
                        metadata=metadata
                    ))
            
            logger.info(f"处理Excel文件 {filename}: {len(documents)} 个文档")
            
        except Exception as e:
            logger.error(f"处理Excel文件失败 {excel_path}: {e}")
        
        return documents
    
    def _extract_category_from_filename(self, filename: str) -> str:
        """从文件名提取类别"""
        category_mapping = {
            '基层治理': '基层治理',
            '社会治理': '社会治理',
            '矛盾纠纷': '矛盾纠纷调解',
            '信访工作': '信访工作',
            '网格化管理': '网格化管理',
            '平安建设': '平安建设',
            '民生保障': '民生保障',
            '志愿服务': '志愿服务',
            '公共服务': '公共服务'
        }
        
        for key, value in category_mapping.items():
            if key in filename:
                return value
        
        return '法规政策'
    
    def _format_excel_row(self, row: pd.Series, category: str) -> str:
        """格式化Excel行数据"""
        content_parts = []
        
        # 标题
        if '标题' in row and pd.notna(row['标题']):
            content_parts.append(f"法规标题: {row['标题']}")
        
        # 发布机关
        if '发布机关' in row and pd.notna(row['发布机关']):
            content_parts.append(f"发布机关: {row['发布机关']}")
        
        # 发布日期
        if '发布日期' in row and pd.notna(row['发布日期']):
            content_parts.append(f"发布日期: {row['发布日期']}")
        
        # 效力级别
        if '效力级别' in row and pd.notna(row['效力级别']):
            content_parts.append(f"效力级别: {row['效力级别']}")
        
        # 主要内容
        content_fields = ['主要内容', '内容', '正文', '条文内容', '摘要']
        for field in content_fields:
            if field in row and pd.notna(row[field]):
                content_parts.append(f"主要内容: {row[field]}")
                break
        
        # 适用范围
        if '适用范围' in row and pd.notna(row['适用范围']):
            content_parts.append(f"适用范围: {row['适用范围']}")
        
        # 关键词
        if '关键词' in row and pd.notna(row['关键词']):
            content_parts.append(f"关键词: {row['关键词']}")
        
        # 类别
        content_parts.append(f"法规类别: {category}")
        
        return '\n\n'.join(content_parts) if content_parts else ""
    
    def process_text_files(self) -> List[Document]:
        """
        处理文本文件（政策补充数据）
        
        Returns:
            处理后的文档列表
        """
        documents = []
        
        try:
            # 查找所有文本文件
            text_files = []
            for root, dirs, files in os.walk(self.rules_base_path):
                for file in files:
                    if file.endswith(('.txt', '.md')):
                        text_files.append(os.path.join(root, file))
            
            logger.info(f"找到 {len(text_files)} 个文本文件")
            
            for text_file in text_files:
                docs = self._process_single_text_file(text_file)
                documents.extend(docs)
            
            logger.info(f"从文本文件处理得到 {len(documents)} 个文档")
            return documents
            
        except Exception as e:
            logger.error(f"处理文本文件失败: {e}")
            return []
    
    def _process_single_text_file(self, text_path: str) -> List[Document]:
        """处理单个文本文件"""
        documents = []
        
        try:
            # 从路径推断地区和类别
            path_parts = text_path.split(os.sep)
            region = self._extract_region_from_path(path_parts)
            
            # 读取文件内容
            with open(text_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if content.strip():
                filename = os.path.basename(text_path)
                metadata = {
                    'source': text_path,
                    'type': 'policy',
                    'region': region,
                    'category': '地方政策',
                    'title': os.path.splitext(filename)[0],
                    'filename': filename
                }
                
                documents.append(Document(
                    page_content=content,
                    metadata=metadata
                ))
            
        except Exception as e:
            logger.error(f"处理文本文件失败 {text_path}: {e}")
        
        return documents
    
    def _extract_region_from_path(self, path_parts: List[str]) -> str:
        """从路径提取地区信息"""
        for part in path_parts:
            if '省' in part or '市' in part or '自治区' in part:
                # 提取省市名称
                for region in ['北京', '上海', '天津', '重庆', '河北', '山西', '辽宁', 
                              '吉林', '黑龙江', '江苏', '浙江', '安徽', '福建', '江西',
                              '山东', '河南', '湖北', '湖南', '广东', '广西', '海南',
                              '四川', '贵州', '云南', '西藏', '陕西', '甘肃', '青海',
                              '宁夏', '新疆', '内蒙古']:
                    if region in part:
                        return region
        return '未知地区'
    
    def create_rules_knowledge_base(self) -> List[Document]:
        """
        创建法规政策知识库
        
        Returns:
            所有处理后的文档列表
        """
        try:
            logger.info("开始创建法规政策知识库...")
            
            # 1. 解压所有压缩文件
            self.extract_all_archives()
            
            # 2. 处理Excel文件（北大法宝数据）
            excel_docs = self.process_excel_files()
            
            # 3. 处理文本文件（政策补充数据）
            text_docs = self.process_text_files()
            
            # 4. 合并所有文档
            all_documents = excel_docs + text_docs
            
            # 5. 分割文档
            split_documents = self.text_splitter.split_documents(all_documents)
            
            logger.info(f"法规政策知识库创建完成: {len(all_documents)} 个原始文档, {len(split_documents)} 个分割文档")
            
            # 6. 保存处理结果
            self._save_processed_documents(split_documents)
            
            return split_documents
            
        except Exception as e:
            logger.error(f"创建法规政策知识库失败: {e}")
            return []
    
    def _save_processed_documents(self, documents: List[Document]):
        """保存处理后的文档"""
        try:
            # 转换为JSON格式保存
            docs_data = []
            for i, doc in enumerate(documents):
                doc_data = {
                    'id': f'rule_{i}',
                    'content': doc.page_content,
                    'metadata': doc.metadata
                }
                docs_data.append(doc_data)
            
            save_path = os.path.join(self.processed_rules_path, 'processed_rules.json')
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(docs_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"处理后的文档已保存到: {save_path}")
            
        except Exception as e:
            logger.error(f"保存处理后的文档失败: {e}")

if __name__ == "__main__":
    # 测试法规政策处理器
    processor = RulesProcessor()
    documents = processor.create_rules_knowledge_base()
    
    if documents:
        print(f"成功处理 {len(documents)} 个法规政策文档")
        
        # 显示一些示例
        for i, doc in enumerate(documents[:3]):
            print(f"\n=== 文档 {i+1} ===")
            print(f"类别: {doc.metadata.get('category', '未知')}")
            print(f"来源: {doc.metadata.get('source', '未知')}")
            print(f"内容预览: {doc.page_content[:200]}...")
    else:
        print("法规政策处理失败")