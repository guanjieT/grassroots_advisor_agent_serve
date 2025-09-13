"""
政策数据优化和重组工具
根据质量检查结果自动优化数据结构
"""
import os
import shutil
import json
import re
from typing import Dict, List, Any, Tuple
from pathlib import Path
from collections import defaultdict
from utils.logger import logger
from .data_quality_checker import DataQualityChecker

class DataOptimizer:
    """数据优化器"""
    
    def __init__(self):
        self.quality_checker = DataQualityChecker()
        
        # 标准化的目录结构
        self.standard_structure = {
            '01_中央政策': {
                '法律法规': [],
                '部委规章': [],
                '政策文件': []
            },
            '02_省级政策': {
                '省级法规': [],
                '省政府规章': [],
                '实施细则': []
            },
            '03_市级政策': {
                '市级规章': [],
                '实施办法': [],
                '工作方案': []
            },
            '04_区县政策': {
                '区县规定': [],
                '具体措施': [],
                '操作指南': []
            },
            '05_街道社区': {
                '社区规定': [],
                '工作流程': [],
                '服务指南': []
            }
        }
        
        # 政策领域分类
        self.policy_domains = {
            '基层治理': ['社区治理', '网格化管理', '基层党建', '村务公开'],
            '民生保障': ['社会救助', '养老服务', '残疾人保障', '儿童保障'],
            '社会治理': ['平安建设', '矛盾纠纷调解', '信访工作', '志愿服务'],
            '公共服务': ['政务服务', '便民服务', '营商环境', '服务标准']
        }
    
    def optimize_data_structure(self, source_dir: str, target_dir: str) -> Dict[str, Any]:
        """
        优化数据结构
        
        Args:
            source_dir: 源数据目录
            target_dir: 目标优化目录
            
        Returns:
            优化结果报告
        """
        logger.info("开始数据结构优化...")
        
        # 1. 质量检查
        quality_report = self.quality_checker.check_data_quality(source_dir)
        
        # 2. 创建标准目录结构
        self._create_standard_structure(target_dir)
        
        # 3. 文件分类和重组
        classification_result = self._classify_and_reorganize_files(source_dir, target_dir)
        
        # 4. 处理重复文件
        dedup_result = self._handle_duplicate_files(quality_report, target_dir)
        
        # 5. 标准化文件名
        rename_result = self._standardize_filenames(target_dir)
        
        # 6. 生成索引文件
        index_result = self._generate_index_files(target_dir)
        
        # 7. 创建优化报告
        optimization_report = {
            'quality_report': quality_report,
            'classification_result': classification_result,
            'deduplication_result': dedup_result,
            'rename_result': rename_result,
            'index_result': index_result,
            'summary': self._generate_optimization_summary(
                quality_report, classification_result, dedup_result, rename_result
            )
        }
        
        logger.info("数据结构优化完成")
        return optimization_report
    
    def _create_standard_structure(self, target_dir: str):
        """创建标准目录结构"""
        logger.info("创建标准目录结构...")
        
        # 创建主目录
        os.makedirs(target_dir, exist_ok=True)
        
        # 创建层级目录
        for level_dir, categories in self.standard_structure.items():
            level_path = os.path.join(target_dir, level_dir)
            os.makedirs(level_path, exist_ok=True)
            
            # 创建分类子目录
            for category in categories:
                category_path = os.path.join(level_path, category)
                os.makedirs(category_path, exist_ok=True)
        
        # 创建领域分类目录
        domain_dir = os.path.join(target_dir, '按领域分类')
        os.makedirs(domain_dir, exist_ok=True)
        
        for domain, subcategories in self.policy_domains.items():
            domain_path = os.path.join(domain_dir, domain)
            os.makedirs(domain_path, exist_ok=True)
            
            for subcategory in subcategories:
                subcat_path = os.path.join(domain_path, subcategory)
                os.makedirs(subcat_path, exist_ok=True)
        
        # 创建时间分类目录
        time_dir = os.path.join(target_dir, '按时间分类')
        os.makedirs(time_dir, exist_ok=True)
        
        # 创建近几年的目录
        current_year = 2025
        for year in range(2015, current_year + 1):
            year_path = os.path.join(time_dir, str(year))
            os.makedirs(year_path, exist_ok=True)
    
    def _classify_and_reorganize_files(self, source_dir: str, target_dir: str) -> Dict[str, Any]:
        """分类和重组文件"""
        logger.info("开始文件分类和重组...")
        
        classification_stats = {
            'total_processed': 0,
            'successfully_classified': 0,
            'failed_classification': 0,
            'by_level': defaultdict(int),
            'by_domain': defaultdict(int),
            'by_year': defaultdict(int)
        }
        
        failed_files = []
        
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                source_path = os.path.join(root, file)
                classification_stats['total_processed'] += 1
                
                try:
                    # 分析文件属性
                    file_info = self._analyze_file_attributes(source_path)
                    
                    # 确定目标路径
                    target_paths = self._determine_target_paths(file_info, target_dir)
                    
                    # 复制文件到多个分类目录
                    for target_path in target_paths:
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        shutil.copy2(source_path, target_path)
                    
                    # 更新统计
                    classification_stats['successfully_classified'] += 1
                    classification_stats['by_level'][file_info['level']] += 1
                    classification_stats['by_domain'][file_info['domain']] += 1
                    classification_stats['by_year'][file_info['year']] += 1
                    
                except Exception as e:
                    logger.warning(f"文件分类失败 {source_path}: {e}")
                    classification_stats['failed_classification'] += 1
                    failed_files.append({
                        'file': source_path,
                        'error': str(e)
                    })
        
        return {
            'statistics': dict(classification_stats),
            'failed_files': failed_files
        }
    
    def _analyze_file_attributes(self, file_path: str) -> Dict[str, str]:
        """分析文件属性"""
        filename = Path(file_path).stem
        
        # 确定行政层级
        level = self._determine_admin_level(filename)
        
        # 确定政策领域
        domain = self._determine_policy_domain(filename)
        
        # 提取年份
        year = self._extract_year(filename)
        
        # 确定地区
        region = self._extract_region(filename)
        
        # 确定文档类型
        doc_type = self._determine_document_type(filename)
        
        return {
            'level': level,
            'domain': domain,
            'year': year,
            'region': region,
            'doc_type': doc_type,
            'original_name': filename
        }
    
    def _determine_admin_level(self, filename: str) -> str:
        """确定行政层级"""
        level_keywords = {
            '中央': ['国务院', '中央', '全国', '国家', '部委'],
            '省级': ['省', '自治区', '直辖市', '省政府', '省委'],
            '市级': ['市', '市政府', '市委', '地级市'],
            '区县': ['区', '县', '区政府', '县政府'],
            '街道社区': ['街道', '社区', '乡镇', '村']
        }
        
        for level, keywords in level_keywords.items():
            if any(keyword in filename for keyword in keywords):
                return level
        
        return '未分类'
    
    def _determine_policy_domain(self, filename: str) -> str:
        """确定政策领域"""
        domain_keywords = {
            '基层治理': ['社区治理', '网格化', '基层党建', '村务', '居务', '自治'],
            '民生保障': ['社会救助', '养老', '残疾人', '儿童', '低保', '救济'],
            '社会治理': ['平安', '矛盾', '纠纷', '调解', '信访', '维稳', '志愿'],
            '公共服务': ['政务服务', '便民', '营商环境', '服务标准', '办事']
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in filename for keyword in keywords):
                return domain
        
        return '其他'
    
    def _extract_year(self, filename: str) -> str:
        """提取年份"""
        year_pattern = r'20\d{2}'
        matches = re.findall(year_pattern, filename)
        
        if matches:
            return matches[0]  # 返回第一个匹配的年份
        
        return '未知'
    
    def _extract_region(self, filename: str) -> str:
        """提取地区信息"""
        regions = [
            '北京', '上海', '天津', '重庆', '河北', '山西', '辽宁', '吉林', '黑龙江',
            '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南',
            '广东', '广西', '海南', '四川', '贵州', '云南', '西藏', '陕西', '甘肃',
            '青海', '宁夏', '新疆', '内蒙古'
        ]
        
        for region in regions:
            if region in filename:
                return region
        
        return '未知'
    
    def _determine_document_type(self, filename: str) -> str:
        """确定文档类型"""
        doc_types = {
            '法律法规': ['法', '条例', '法规'],
            '规章制度': ['规章', '制度', '规定', '办法'],
            '政策文件': ['意见', '通知', '方案', '计划'],
            '工作指南': ['指南', '手册', '流程', '标准']
        }
        
        for doc_type, keywords in doc_types.items():
            if any(keyword in filename for keyword in keywords):
                return doc_type
        
        return '其他文档'
    
    def _determine_target_paths(self, file_info: Dict[str, str], target_dir: str) -> List[str]:
        """确定目标路径"""
        target_paths = []
        original_name = file_info['original_name']
        
        # 1. 按行政层级分类
        level_mapping = {
            '中央': '01_中央政策',
            '省级': '02_省级政策',
            '市级': '03_市级政策',
            '区县': '04_区县政策',
            '街道社区': '05_街道社区'
        }
        
        if file_info['level'] in level_mapping:
            level_dir = level_mapping[file_info['level']]
            doc_type = file_info['doc_type']
            
            # 根据文档类型选择子目录
            if doc_type in ['法律法规', '规章制度', '政策文件']:
                subdir = list(self.standard_structure[level_dir].keys())[0]
            else:
                subdir = list(self.standard_structure[level_dir].keys())[-1]
            
            target_path = os.path.join(target_dir, level_dir, subdir, f"{original_name}.txt")
            target_paths.append(target_path)
        
        # 2. 按领域分类
        if file_info['domain'] in self.policy_domains:
            domain_path = os.path.join(target_dir, '按领域分类', file_info['domain'])
            
            # 选择合适的子分类
            subcategories = self.policy_domains[file_info['domain']]
            subcategory = subcategories[0]  # 默认选择第一个
            
            target_path = os.path.join(domain_path, subcategory, f"{original_name}.txt")
            target_paths.append(target_path)
        
        # 3. 按时间分类
        if file_info['year'] != '未知':
            time_path = os.path.join(target_dir, '按时间分类', file_info['year'])
            target_path = os.path.join(time_path, f"{original_name}.txt")
            target_paths.append(target_path)
        
        return target_paths
    
    def _handle_duplicate_files(self, quality_report: Dict[str, Any], target_dir: str) -> Dict[str, Any]:
        """处理重复文件"""
        logger.info("处理重复文件...")
        
        duplicate_files = quality_report['issues']['duplicate_files']
        processed_count = 0
        removed_count = 0
        
        for duplicate_group in duplicate_files:
            files = duplicate_group['files']
            
            if len(files) > 1:
                # 保留最新的文件，删除其他重复文件
                files_with_mtime = []
                for file_path in files:
                    try:
                        mtime = os.path.getmtime(file_path)
                        files_with_mtime.append((file_path, mtime))
                    except OSError:
                        continue
                
                if files_with_mtime:
                    # 按修改时间排序，保留最新的
                    files_with_mtime.sort(key=lambda x: x[1], reverse=True)
                    keep_file = files_with_mtime[0][0]
                    
                    for file_path, _ in files_with_mtime[1:]:
                        try:
                            if os.path.exists(file_path):
                                os.remove(file_path)
                                removed_count += 1
                                logger.info(f"删除重复文件: {file_path}")
                        except OSError as e:
                            logger.warning(f"删除文件失败 {file_path}: {e}")
                
                processed_count += 1
        
        return {
            'processed_groups': processed_count,
            'removed_files': removed_count
        }
    
    def _standardize_filenames(self, target_dir: str) -> Dict[str, Any]:
        """标准化文件名"""
        logger.info("标准化文件名...")
        
        renamed_count = 0
        failed_renames = []
        
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                old_path = os.path.join(root, file)
                
                try:
                    # 生成标准化文件名
                    new_filename = self._generate_standard_filename(file, root)
                    new_path = os.path.join(root, new_filename)
                    
                    if old_path != new_path and not os.path.exists(new_path):
                        os.rename(old_path, new_path)
                        renamed_count += 1
                        logger.debug(f"重命名: {file} -> {new_filename}")
                
                except Exception as e:
                    failed_renames.append({
                        'file': old_path,
                        'error': str(e)
                    })
        
        return {
            'renamed_count': renamed_count,
            'failed_renames': failed_renames
        }
    
    def _generate_standard_filename(self, filename: str, directory: str) -> str:
        """生成标准化文件名"""
        # 提取文件信息
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        
        # 从目录路径推断分类信息
        dir_parts = directory.split(os.sep)
        
        # 构建标准文件名: [层级]_[地区]_[类别]_[时间]_[原始名称]
        parts = []
        
        # 添加层级信息
        if '01_中央政策' in dir_parts:
            parts.append('中央')
        elif '02_省级政策' in dir_parts:
            parts.append('省级')
        elif '03_市级政策' in dir_parts:
            parts.append('市级')
        elif '04_区县政策' in dir_parts:
            parts.append('区县')
        elif '05_街道社区' in dir_parts:
            parts.append('街道')
        
        # 添加地区信息（从原文件名提取）
        region = self._extract_region(stem)
        if region != '未知':
            parts.append(region)
        
        # 添加类别信息
        domain = self._determine_policy_domain(stem)
        if domain != '其他':
            parts.append(domain)
        
        # 添加时间信息
        year = self._extract_year(stem)
        if year != '未知':
            parts.append(year)
        
        # 清理原始文件名
        clean_name = re.sub(r'[^\w\u4e00-\u9fff\-_]', '_', stem)
        clean_name = re.sub(r'_+', '_', clean_name).strip('_')
        
        # 组合标准文件名
        if parts:
            standard_name = '_'.join(parts) + '_' + clean_name
        else:
            standard_name = clean_name
        
        # 限制文件名长度
        if len(standard_name) > 200:
            standard_name = standard_name[:200]
        
        return standard_name + suffix
    
    def _generate_index_files(self, target_dir: str) -> Dict[str, Any]:
        """生成索引文件"""
        logger.info("生成索引文件...")
        
        index_files_created = []
        
        # 为每个主要目录生成索引
        for root, dirs, files in os.walk(target_dir):
            if files and len(files) > 5:  # 只为包含较多文件的目录生成索引
                index_content = self._create_directory_index(root, files)
                index_path = os.path.join(root, 'README.md')
                
                try:
                    with open(index_path, 'w', encoding='utf-8') as f:
                        f.write(index_content)
                    index_files_created.append(index_path)
                except Exception as e:
                    logger.warning(f"创建索引文件失败 {index_path}: {e}")
        
        # 创建总体索引
        main_index_path = os.path.join(target_dir, 'INDEX.md')
        main_index_content = self._create_main_index(target_dir)
        
        try:
            with open(main_index_path, 'w', encoding='utf-8') as f:
                f.write(main_index_content)
            index_files_created.append(main_index_path)
        except Exception as e:
            logger.warning(f"创建主索引文件失败: {e}")
        
        return {
            'index_files_created': len(index_files_created),
            'index_files': index_files_created
        }
    
    def _create_directory_index(self, directory: str, files: List[str]) -> str:
        """创建目录索引"""
        dir_name = os.path.basename(directory)
        
        content = f"# {dir_name} 目录索引\n\n"
        content += f"**目录路径**: {directory}\n"
        content += f"**文件数量**: {len(files)}\n"
        content += f"**生成时间**: {self._get_current_time()}\n\n"
        
        content += "## 文件列表\n\n"
        
        # 按文件名排序
        sorted_files = sorted(files)
        
        for i, file in enumerate(sorted_files, 1):
            file_path = os.path.join(directory, file)
            try:
                file_size = os.path.getsize(file_path)
                file_size_kb = round(file_size / 1024, 2)
                content += f"{i}. **{file}** ({file_size_kb} KB)\n"
            except OSError:
                content += f"{i}. **{file}**\n"
        
        return content
    
    def _create_main_index(self, target_dir: str) -> str:
        """创建主索引"""
        content = "# 政策法规数据库索引\n\n"
        content += f"**数据库路径**: {target_dir}\n"
        content += f"**生成时间**: {self._get_current_time()}\n\n"
        
        content += "## 目录结构\n\n"
        
        # 统计各目录的文件数量
        dir_stats = {}
        total_files = 0
        
        for root, dirs, files in os.walk(target_dir):
            if files:
                rel_path = os.path.relpath(root, target_dir)
                if rel_path != '.':
                    dir_stats[rel_path] = len(files)
                    total_files += len(files)
        
        content += f"**总文件数**: {total_files}\n\n"
        
        # 按目录层级组织
        for dir_path, file_count in sorted(dir_stats.items()):
            level = dir_path.count(os.sep)
            indent = "  " * level
            content += f"{indent}- **{os.path.basename(dir_path)}** ({file_count} 个文件)\n"
        
        content += "\n## 使用说明\n\n"
        content += "1. 按行政层级浏览：01_中央政策 → 02_省级政策 → 03_市级政策 → 04_区县政策 → 05_街道社区\n"
        content += "2. 按政策领域浏览：按领域分类目录\n"
        content += "3. 按时间浏览：按时间分类目录\n"
        content += "4. 每个目录都有对应的 README.md 索引文件\n"
        
        return content
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _generate_optimization_summary(self, quality_report: Dict, classification_result: Dict, 
                                     dedup_result: Dict, rename_result: Dict) -> Dict[str, Any]:
        """生成优化总结"""
        return {
            'original_files': quality_report['summary']['total_files'],
            'original_size_mb': quality_report['summary']['total_size_mb'],
            'quality_score_before': quality_report['summary']['quality_score'],
            'files_processed': classification_result['statistics']['total_processed'],
            'files_successfully_classified': classification_result['statistics']['successfully_classified'],
            'duplicate_files_removed': dedup_result['removed_files'],
            'files_renamed': rename_result['renamed_count'],
            'optimization_improvements': [
                '创建了标准化的目录结构',
                '实现了多维度文件分类',
                '清理了重复文件',
                '标准化了文件命名',
                '生成了完整的索引系统'
            ]
        }
    
    def save_optimization_report(self, report: Dict[str, Any], output_path: str):
        """保存优化报告"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"优化报告已保存到: {output_path}")
        except Exception as e:
            logger.error(f"保存优化报告失败: {e}")