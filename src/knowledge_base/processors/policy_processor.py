"""
政策法规数据智能处理和归类系统
基于文件名和内容进行自动分类和标准化处理
"""
import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from langchain_core.documents import Document
from utils.logger import logger
from knowledge_base.multi_format_processor import MultiFormatProcessor

class PolicyDataProcessor:
    """政策法规数据智能处理器"""
    
    def __init__(self):
        self.multi_format_processor = MultiFormatProcessor()
        
        # 地域层级分类
        self.region_hierarchy = {
            '中央': ['中共中央', '国务院', '中央办公厅', '国务院办公厅', '民政部', '司法部', '应急管理部', '人力资源社会保障部'],
            '省级': ['省人民政府', '省政府', '省委', '省办公厅', '省民政厅', '省司法厅', '省应急管理厅'],
            '市级': ['市人民政府', '市政府', '市委', '市办公室', '市民政局', '市司法局'],
            '区县级': ['区人民政府', '县人民政府', '区政府', '县政府', '区办公室', '县办公室'],
            '街道乡镇': ['街道', '镇人民政府', '乡人民政府', '街道办事处', '社区']
        }
        
        # 政策领域分类
        self.policy_categories = {
            '基层治理': [
                '基层治理', '社区治理', '村务公开', '居民自治', '网格化管理', 
                '基层党建', '社区建设', '村民自治', '基层减负', '治理体系'
            ],
            '社会救助': [
                '社会救助', '最低生活保障', '低保', '临时救助', '特困人员', 
                '困难群众', '救助供养', '兜底保障', '民生保障'
            ],
            '养老服务': [
                '养老服务', '居家养老', '社区养老', '养老机构', '老龄事业', 
                '养老保险', '老年人', '敬老', '养老体系'
            ],
            '平安建设': [
                '平安建设', '安全生产', '消防安全', '应急管理', '风险防控', 
                '安全监管', '应急救援', '防灾减灾', '公共安全'
            ],
            '矛盾纠纷调解': [
                '矛盾纠纷', '人民调解', '调解工作', '纠纷化解', '多元化解', 
                '诉调对接', '访调对接', '调解组织', '矛盾排查'
            ],
            '信访工作': [
                '信访工作', '信访条例', '信访事项', '信访局', '信访听证', 
                '信访复查', '信访督查', '信访维稳'
            ],
            '志愿服务': [
                '志愿服务', '志愿者', '志愿活动', '公益服务', '慈善事业', 
                '社会组织', '志愿团队'
            ],
            '公共服务': [
                '公共服务', '政务服务', '便民服务', '一网通办', '放管服', 
                '营商环境', '政务公开', '服务标准'
            ],
            '残疾人保障': [
                '残疾人', '残疾儿童', '康复救助', '残疾人就业', '残疾人保障', 
                '无障碍', '残联'
            ],
            '儿童保障': [
                '儿童', '困境儿童', '留守儿童', '孤儿', '儿童福利', 
                '儿童保护', '托育服务', '婴幼儿照护'
            ]
        }
        
        # 时间提取正则表达式
        self.time_patterns = [
            r'(\d{4})年',
            r'(\d{4})-(\d{4})年',
            r'(\d{4})—(\d{4})年',
            r'（(\d{4})年版）',
            r'（(\d{4})-(\d{4})年）',
            r'（(\d{4})—(\d{4})年）'
        ]
        
        # 地区提取正则表达式
        self.region_patterns = [
            r'(北京|上海|天津|重庆)市',
            r'(河北|山西|辽宁|吉林|黑龙江|江苏|浙江|安徽|福建|江西|山东|河南|湖北|湖南|广东|海南|四川|贵州|云南|陕西|甘肃|青海|台湾)省',
            r'(内蒙古|广西|西藏|宁夏|新疆).*自治区',
            r'(香港|澳门)特别行政区',
            r'(\w+)市(\w+)区',
            r'(\w+)县',
            r'(\w+)街道',
            r'(\w+)镇'
        ]
    
    def extract_metadata_from_filename(self, filename: str) -> Dict[str, Any]:
        """
        从文件名提取元数据
        
        Args:
            filename: 文件名
            
        Returns:
            提取的元数据字典
        """
        metadata = {
            'title': filename,
            'region': '未知',
            'region_level': '未知',
            'category': '政策法规',
            'time_period': '未知',
            'authority': '未知',
            'keywords': []
        }
        
        # 提取地区信息
        region_info = self._extract_region_from_filename(filename)
        metadata.update(region_info)
        
        # 提取时间信息
        time_info = self._extract_time_from_filename(filename)
        metadata.update(time_info)
        
        # 提取政策类别
        category = self._classify_policy_category(filename)
        metadata['category'] = category
        
        # 提取发布机关
        authority = self._extract_authority_from_filename(filename)
        metadata['authority'] = authority
        
        # 提取关键词
        keywords = self._extract_keywords_from_filename(filename)
        metadata['keywords'] = keywords
        
        return metadata
    
    def _extract_region_from_filename(self, filename: str) -> Dict[str, str]:
        """从文件名提取地区信息"""
        region_info = {'region': '未知', 'region_level': '未知'}
        
        # 检查各级行政区域
        for level, patterns in self.region_hierarchy.items():
            for pattern in patterns:
                if pattern in filename:
                    region_info['region_level'] = level
                    break
            if region_info['region_level'] != '未知':
                break
        
        # 提取具体地区名称
        for pattern in self.region_patterns:
            match = re.search(pattern, filename)
            if match:
                region_info['region'] = match.group(1) if match.group(1) else match.group(0)
                break
        
        return region_info
    
    def _extract_time_from_filename(self, filename: str) -> Dict[str, str]:
        """从文件名提取时间信息"""
        time_info = {'time_period': '未知', 'start_year': '', 'end_year': ''}
        
        for pattern in self.time_patterns:
            match = re.search(pattern, filename)
            if match:
                groups = match.groups()
                if len(groups) == 1:
                    # 单年份
                    time_info['time_period'] = groups[0]
                    time_info['start_year'] = groups[0]
                elif len(groups) == 2:
                    # 年份区间
                    time_info['time_period'] = f"{groups[0]}-{groups[1]}"
                    time_info['start_year'] = groups[0]
                    time_info['end_year'] = groups[1]
                break
        
        return time_info
    
    def _classify_policy_category(self, filename: str) -> str:
        """根据文件名分类政策领域"""
        filename_lower = filename.lower()
        
        # 计算每个类别的匹配分数
        category_scores = {}
        for category, keywords in self.policy_categories.items():
            score = 0
            for keyword in keywords:
                if keyword in filename_lower:
                    score += 1
            if score > 0:
                category_scores[category] = score
        
        # 返回得分最高的类别
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        return '政策法规'
    
    def _extract_authority_from_filename(self, filename: str) -> str:
        """提取发布机关"""
        # 常见发布机关模式
        authority_patterns = [
            r'(.*?人民政府)',
            r'(.*?政府办公厅)',
            r'(.*?民政局)',
            r'(.*?司法厅)',
            r'(.*?应急管理厅)',
            r'(.*?发展改革委)',
            r'(.*?财政厅)',
            r'(.*?人力资源.*?保障厅)'
        ]
        
        for pattern in authority_patterns:
            match = re.search(pattern, filename)
            if match:
                return match.group(1)
        
        return '未知机关'
    
    def _extract_keywords_from_filename(self, filename: str) -> List[str]:
        """从文件名提取关键词"""
        keywords = []
        
        # 从所有类别中提取匹配的关键词
        for category, category_keywords in self.policy_categories.items():
            for keyword in category_keywords:
                if keyword in filename:
                    keywords.append(keyword)
        
        return list(set(keywords))  # 去重
    
    def create_policy_taxonomy(self, data_dir: str) -> Dict[str, Any]:
        """
        创建政策分类体系
        
        Args:
            data_dir: 数据目录路径
            
        Returns:
            分类统计结果
        """
        taxonomy = {
            'total_files': 0,
            'by_format': {},
            'by_region_level': {},
            'by_category': {},
            'by_time_period': {},
            'by_region': {},
            'file_details': []
        }
        
        if not os.path.exists(data_dir):
            logger.warning(f"数据目录不存在: {data_dir}")
            return taxonomy
        
        # 遍历所有文件
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower()
                filename = Path(file).stem
                
                # 提取元数据
                metadata = self.extract_metadata_from_filename(filename)
                
                # 统计信息
                taxonomy['total_files'] += 1
                
                # 按格式统计
                taxonomy['by_format'][file_ext] = taxonomy['by_format'].get(file_ext, 0) + 1
                
                # 按地域层级统计
                level = metadata['region_level']
                taxonomy['by_region_level'][level] = taxonomy['by_region_level'].get(level, 0) + 1
                
                # 按类别统计
                category = metadata['category']
                taxonomy['by_category'][category] = taxonomy['by_category'].get(category, 0) + 1
                
                # 按时间统计
                time_period = metadata['time_period']
                taxonomy['by_time_period'][time_period] = taxonomy['by_time_period'].get(time_period, 0) + 1
                
                # 按地区统计
                region = metadata['region']
                taxonomy['by_region'][region] = taxonomy['by_region'].get(region, 0) + 1
                
                # 保存文件详情
                file_detail = {
                    'file_path': file_path,
                    'filename': filename,
                    'format': file_ext,
                    'metadata': metadata
                }
                taxonomy['file_details'].append(file_detail)
        
        logger.info(f"政策分类体系创建完成，共处理 {taxonomy['total_files']} 个文件")
        return taxonomy
    
    def create_processing_plan(self, taxonomy: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于分类结果创建处理计划
        
        Args:
            taxonomy: 分类统计结果
            
        Returns:
            处理计划
        """
        plan = {
            'priority_categories': [],
            'processing_batches': [],
            'quality_control': {},
            'indexing_strategy': {}
        }
        
        # 确定优先处理类别（按文件数量排序）
        sorted_categories = sorted(
            taxonomy['by_category'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        plan['priority_categories'] = [cat for cat, count in sorted_categories[:5]]
        
        # 创建批次处理计划
        batches = self._create_processing_batches(taxonomy['file_details'])
        plan['processing_batches'] = batches
        
        # 质量控制策略
        plan['quality_control'] = {
            '文件格式检查': '确保所有格式都能正确解析',
            '内容完整性': '检查提取的内容是否完整',
            '元数据准确性': '验证自动提取的元数据',
            '重复内容检测': '识别和处理重复或相似内容',
            '分类准确性': '人工抽检自动分类结果'
        }
        
        # 索引策略
        plan['indexing_strategy'] = {
            '层次化索引': '按地域层级-类别-时间建立索引',
            '关键词索引': '基于提取的关键词建立倒排索引',
            '语义索引': '使用向量嵌入建立语义索引',
            '关联索引': '建立政策间的关联关系索引'
        }
        
        return plan
    
    def _create_processing_batches(self, file_details: List[Dict]) -> List[Dict]:
        """创建批次处理计划"""
        batches = []
        
        # 按优先级分批
        # 批次1: 中央和省级重要政策
        batch1 = {
            'name': '核心政策批次',
            'priority': 1,
            'criteria': '中央和省级重要政策文件',
            'files': []
        }
        
        # 批次2: 市县级实施细则
        batch2 = {
            'name': '实施细则批次',
            'priority': 2,
            'criteria': '市县级具体实施办法',
            'files': []
        }
        
        # 批次3: 基层操作指南
        batch3 = {
            'name': '操作指南批次',
            'priority': 3,
            'criteria': '街道社区操作性文件',
            'files': []
        }
        
        # 分配文件到批次
        for file_detail in file_details:
            region_level = file_detail['metadata']['region_level']
            
            if region_level in ['中央', '省级']:
                batch1['files'].append(file_detail)
            elif region_level in ['市级', '区县级']:
                batch2['files'].append(file_detail)
            else:
                batch3['files'].append(file_detail)
        
        batches = [batch1, batch2, batch3]
        
        # 添加文件数量信息
        for batch in batches:
            batch['file_count'] = len(batch['files'])
        
        return batches
    
    def process_policy_documents(self, data_dir: str, output_dir: str = "./data/processed_policies") -> bool:
        """
        批量处理政策文档
        
        Args:
            data_dir: 原始数据目录
            output_dir: 处理后输出目录
            
        Returns:
            处理是否成功
        """
        try:
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 创建分类体系
            logger.info("创建政策分类体系...")
            taxonomy = self.create_policy_taxonomy(data_dir)
            
            # 保存分类结果
            with open(os.path.join(output_dir, 'policy_taxonomy.json'), 'w', encoding='utf-8') as f:
                json.dump(taxonomy, f, ensure_ascii=False, indent=2)
            
            # 创建处理计划
            logger.info("创建处理计划...")
            plan = self.create_processing_plan(taxonomy)
            
            # 保存处理计划
            with open(os.path.join(output_dir, 'processing_plan.json'), 'w', encoding='utf-8') as f:
                json.dump(plan, f, ensure_ascii=False, indent=2)
            
            # 按批次处理文档
            all_documents = []
            for batch in plan['processing_batches']:
                logger.info(f"处理 {batch['name']} ({batch['file_count']} 个文件)...")
                
                batch_documents = []
                for file_detail in batch['files']:
                    file_path = file_detail['file_path']
                    documents = self.multi_format_processor.process_file(file_path)
                    
                    # 增强元数据
                    for doc in documents:
                        doc.metadata.update(file_detail['metadata'])
                        doc.metadata['batch'] = batch['name']
                        doc.metadata['priority'] = batch['priority']
                    
                    batch_documents.extend(documents)
                
                all_documents.extend(batch_documents)
                
                # 保存批次结果
                batch_output = {
                    'batch_info': batch,
                    'documents_count': len(batch_documents),
                    'processing_time': datetime.now().isoformat()
                }
                
                batch_file = os.path.join(output_dir, f"batch_{batch['priority']}_result.json")
                with open(batch_file, 'w', encoding='utf-8') as f:
                    json.dump(batch_output, f, ensure_ascii=False, indent=2)
            
            # 保存所有处理后的文档
            self._save_processed_documents(all_documents, output_dir)
            
            logger.info(f"政策文档处理完成，共处理 {len(all_documents)} 个文档")
            return True
            
        except Exception as e:
            logger.error(f"处理政策文档失败: {e}")
            return False
    
    def _save_processed_documents(self, documents: List[Document], output_dir: str):
        """保存处理后的文档"""
        try:
            # 按类别分组保存
            category_groups = {}
            for doc in documents:
                category = doc.metadata.get('category', '其他')
                if category not in category_groups:
                    category_groups[category] = []
                category_groups[category].append(doc)
            
            # 保存各类别文档
            for category, docs in category_groups.items():
                category_dir = os.path.join(output_dir, 'by_category', category)
                os.makedirs(category_dir, exist_ok=True)
                
                # 转换为JSON格式
                docs_data = []
                for i, doc in enumerate(docs):
                    doc_data = {
                        'id': f"{category}_{i}",
                        'content': doc.page_content,
                        'metadata': doc.metadata
                    }
                    docs_data.append(doc_data)
                
                # 保存文件
                output_file = os.path.join(category_dir, f"{category}_documents.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(docs_data, f, ensure_ascii=False, indent=2)
            
            # 保存总体统计
            summary = {
                'total_documents': len(documents),
                'categories': {cat: len(docs) for cat, docs in category_groups.items()},
                'processing_time': datetime.now().isoformat()
            }
            
            with open(os.path.join(output_dir, 'processing_summary.json'), 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            logger.info(f"文档保存完成，共 {len(category_groups)} 个类别")
            
        except Exception as e:
            logger.error(f"保存处理后的文档失败: {e}")

if __name__ == "__main__":
    # 测试政策数据处理器
    processor = PolicyDataProcessor()
    
    # 创建分类体系
    data_dir = "./data/rules"
    if os.path.exists(data_dir):
        taxonomy = processor.create_policy_taxonomy(data_dir)
        
        print("=== 政策数据分析结果 ===")
        print(f"总文件数: {taxonomy['total_files']}")
        
        print("\n按格式分布:")
        for fmt, count in sorted(taxonomy['by_format'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {fmt}: {count} 个")
        
        print("\n按地域层级分布:")
        for level, count in sorted(taxonomy['by_region_level'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {level}: {count} 个")
        
        print("\n按政策类别分布:")
        for category, count in sorted(taxonomy['by_category'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {category}: {count} 个")
        
        print("\n按时间分布 (前10):")
        for time_period, count in sorted(taxonomy['by_time_period'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {time_period}: {count} 个")
        
        # 创建处理计划
        plan = processor.create_processing_plan(taxonomy)
        print(f"\n优先处理类别: {plan['priority_categories']}")
        
        print("\n批次处理计划:")
        for batch in plan['processing_batches']:
            print(f"  {batch['name']}: {batch['file_count']} 个文件")
    else:
        print(f"数据目录不存在: {data_dir}")