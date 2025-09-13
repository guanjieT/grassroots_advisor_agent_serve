"""
政策数据质量检查和优化工具
检测数据质量问题并提供优化建议
"""
import os
import json
import hashlib
from typing import List, Dict, Any, Set, Tuple
from collections import Counter, defaultdict
from pathlib import Path
from difflib import SequenceMatcher
from utils.logger import logger

class DataQualityChecker:
    """数据质量检查器"""
    
    def __init__(self):
        self.quality_issues = {
            'duplicate_files': [],
            'similar_content': [],
            'missing_metadata': [],
            'format_issues': [],
            'encoding_issues': [],
            'empty_files': [],
            'naming_inconsistencies': [],
            'temporal_gaps': [],
            'regional_coverage_gaps': []
        }
        
        # 文件名规范化规则
        self.naming_rules = {
            'forbidden_chars': ['/', '\\', ':', '*', '?', '"', '<', '>', '|'],
            'max_length': 255,
            'preferred_separators': ['_', '-'],
            'date_formats': ['YYYY', 'YYYY-MM', 'YYYY-MM-DD']
        }
    
    def check_data_quality(self, data_dir: str) -> Dict[str, Any]:
        """
        全面检查数据质量
        
        Args:
            data_dir: 数据目录路径
            
        Returns:
            质量检查报告
        """
        logger.info("开始数据质量检查...")
        
        # 收集所有文件信息
        file_info = self._collect_file_info(data_dir)
        
        # 执行各项检查
        self._check_duplicate_files(file_info)
        self._check_similar_content(file_info)
        self._check_missing_metadata(file_info)
        self._check_format_issues(file_info)
        self._check_encoding_issues(file_info)
        self._check_empty_files(file_info)
        self._check_naming_inconsistencies(file_info)
        self._check_temporal_gaps(file_info)
        self._check_regional_coverage(file_info)
        
        # 生成质量报告
        quality_report = self._generate_quality_report(file_info)
        
        logger.info("数据质量检查完成")
        return quality_report
    
    def _collect_file_info(self, data_dir: str) -> List[Dict[str, Any]]:
        """收集文件信息"""
        file_info = []
        
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                file_path = os.path.join(root, file)
                
                try:
                    stat = os.stat(file_path)
                    
                    info = {
                        'path': file_path,
                        'name': file,
                        'stem': Path(file).stem,
                        'suffix': Path(file).suffix.lower(),
                        'size': stat.st_size,
                        'mtime': stat.st_mtime,
                        'hash': self._calculate_file_hash(file_path),
                        'encoding': self._detect_encoding(file_path),
                        'content_preview': self._get_content_preview(file_path)
                    }
                    
                    file_info.append(info)
                    
                except Exception as e:
                    logger.warning(f"无法获取文件信息 {file_path}: {e}")
        
        return file_info
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception:
            return ""
    
    def _detect_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        try:
            # 尝试常见编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'ascii']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        f.read(1000)  # 读取前1000字符测试
                        return encoding
                except UnicodeDecodeError:
                    continue
            
            return 'unknown'
        except Exception:
            return 'unknown'
    
    def _get_content_preview(self, file_path: str, max_chars: int = 500) -> str:
        """获取文件内容预览"""
        try:
            # 只处理文本文件
            if Path(file_path).suffix.lower() in ['.txt', '.md']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(max_chars)
                    return content
        except Exception:
            pass
        return ""
    
    def _check_duplicate_files(self, file_info: List[Dict[str, Any]]):
        """检查重复文件"""
        hash_groups = defaultdict(list)
        
        for info in file_info:
            if info['hash']:
                hash_groups[info['hash']].append(info)
        
        for hash_val, files in hash_groups.items():
            if len(files) > 1:
                self.quality_issues['duplicate_files'].append({
                    'hash': hash_val,
                    'files': [f['path'] for f in files],
                    'count': len(files)
                })
    
    def _check_similar_content(self, file_info: List[Dict[str, Any]]):
        """检查相似内容"""
        text_files = [info for info in file_info if info['content_preview']]
        
        for i, file1 in enumerate(text_files):
            for file2 in text_files[i+1:]:
                similarity = SequenceMatcher(
                    None, 
                    file1['content_preview'], 
                    file2['content_preview']
                ).ratio()
                
                if similarity > 0.8:  # 80%以上相似度
                    self.quality_issues['similar_content'].append({
                        'file1': file1['path'],
                        'file2': file2['path'],
                        'similarity': similarity
                    })
    
    def _check_missing_metadata(self, file_info: List[Dict[str, Any]]):
        """检查缺失元数据"""
        for info in file_info:
            issues = []
            
            # 检查文件名是否包含基本信息
            filename = info['stem']
            
            # 检查是否包含时间信息
            if not any(char.isdigit() for char in filename):
                issues.append('缺少时间信息')
            
            # 检查是否包含地区信息
            region_keywords = ['市', '省', '区', '县', '街道', '镇', '社区']
            if not any(keyword in filename for keyword in region_keywords):
                issues.append('缺少地区信息')
            
            # 检查是否包含政策类型信息
            policy_keywords = ['办法', '规定', '意见', '通知', '方案', '条例']
            if not any(keyword in filename for keyword in policy_keywords):
                issues.append('缺少政策类型信息')
            
            if issues:
                self.quality_issues['missing_metadata'].append({
                    'file': info['path'],
                    'issues': issues
                })
    
    def _check_format_issues(self, file_info: List[Dict[str, Any]]):
        """检查格式问题"""
        format_stats = Counter(info['suffix'] for info in file_info)
        
        # 检查不常见格式
        common_formats = {'.txt', '.docx', '.doc', '.pdf', '.xlsx', '.xls', '.csv'}
        
        for info in file_info:
            if info['suffix'] not in common_formats and info['suffix']:
                self.quality_issues['format_issues'].append({
                    'file': info['path'],
                    'format': info['suffix'],
                    'issue': '不常见格式'
                })
    
    def _check_encoding_issues(self, file_info: List[Dict[str, Any]]):
        """检查编码问题"""
        for info in file_info:
            encoding = info.get('encoding', 'unknown')
            
            if encoding in ['unknown', None]:
                self.quality_issues['encoding_issues'].append({
                    'file': info['path'],
                    'issue': '无法检测编码'
                })
            elif encoding.lower() not in ['utf-8', 'ascii']:
                self.quality_issues['encoding_issues'].append({
                    'file': info['path'],
                    'encoding': encoding,
                    'issue': '非UTF-8编码'
                })
    
    def _check_empty_files(self, file_info: List[Dict[str, Any]]):
        """检查空文件"""
        for info in file_info:
            if info['size'] == 0:
                self.quality_issues['empty_files'].append({
                    'file': info['path'],
                    'issue': '文件为空'
                })
            elif info['size'] < 100:  # 小于100字节
                self.quality_issues['empty_files'].append({
                    'file': info['path'],
                    'size': info['size'],
                    'issue': '文件过小'
                })
    
    def _check_naming_inconsistencies(self, file_info: List[Dict[str, Any]]):
        """检查命名不一致"""
        for info in file_info:
            filename = info['name']
            issues = []
            
            # 检查禁用字符
            for char in self.naming_rules['forbidden_chars']:
                if char in filename:
                    issues.append(f'包含禁用字符: {char}')
            
            # 检查文件名长度
            if len(filename) > self.naming_rules['max_length']:
                issues.append('文件名过长')
            
            # 检查是否有空格（建议用下划线或连字符）
            if ' ' in filename:
                issues.append('建议用下划线或连字符替代空格')
            
            if issues:
                self.quality_issues['naming_inconsistencies'].append({
                    'file': info['path'],
                    'issues': issues
                })
    
    def _check_temporal_gaps(self, file_info: List[Dict[str, Any]]):
        """检查时间覆盖缺口"""
        # 从文件名提取年份
        years = set()
        for info in file_info:
            filename = info['stem']
            # 简单的年份提取
            import re
            year_matches = re.findall(r'20\d{2}', filename)
            years.update(year_matches)
        
        if years:
            year_list = sorted([int(y) for y in years])
            
            # 检查连续性
            for i in range(len(year_list) - 1):
                if year_list[i+1] - year_list[i] > 1:
                    gap_years = list(range(year_list[i] + 1, year_list[i+1]))
                    self.quality_issues['temporal_gaps'].append({
                        'missing_years': gap_years,
                        'before': year_list[i],
                        'after': year_list[i+1]
                    })
    
    def _check_regional_coverage(self, file_info: List[Dict[str, Any]]):
        """检查地区覆盖情况"""
        # 统计各地区文件数量
        region_stats = defaultdict(int)
        
        for info in file_info:
            filename = info['stem']
            
            # 简单的地区提取
            regions = ['北京', '上海', '天津', '重庆', '河北', '山西', '辽宁', '吉林', '黑龙江']
            
            found_region = False
            for region in regions:
                if region in filename:
                    region_stats[region] += 1
                    found_region = True
                    break
            
            if not found_region:
                region_stats['其他'] += 1
        
        # 检查覆盖不均衡
        if region_stats:
            avg_count = sum(region_stats.values()) / len(region_stats)
            
            for region, count in region_stats.items():
                if count < avg_count * 0.3:  # 低于平均值30%
                    self.quality_issues['regional_coverage_gaps'].append({
                        'region': region,
                        'count': count,
                        'average': avg_count,
                        'issue': '覆盖不足'
                    })
    
    def _generate_quality_report(self, file_info: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成质量报告"""
        total_files = len(file_info)
        total_size = sum(info['size'] for info in file_info)
        
        # 计算质量分数
        total_issues = sum(len(issues) for issues in self.quality_issues.values())
        quality_score = max(0, 100 - (total_issues / total_files * 10)) if total_files > 0 else 100
        
        report = {
            'summary': {
                'total_files': total_files,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'quality_score': round(quality_score, 2),
                'total_issues': total_issues
            },
            'issues': self.quality_issues,
            'recommendations': self._generate_recommendations(),
            'file_statistics': self._generate_file_statistics(file_info)
        }
        
        return report
    
    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """生成改进建议"""
        recommendations = []
        
        if self.quality_issues['duplicate_files']:
            recommendations.append({
                'category': '重复文件',
                'priority': 'high',
                'action': '删除或合并重复文件，保留最新版本',
                'benefit': '减少存储空间，避免数据冗余'
            })
        
        if self.quality_issues['encoding_issues']:
            recommendations.append({
                'category': '编码问题',
                'priority': 'medium',
                'action': '将所有文件转换为UTF-8编码',
                'benefit': '确保文本正确显示，避免乱码'
            })
        
        if self.quality_issues['naming_inconsistencies']:
            recommendations.append({
                'category': '命名规范',
                'priority': 'medium',
                'action': '统一文件命名规范，使用标准分隔符',
                'benefit': '提高文件管理效率，便于自动化处理'
            })
        
        if self.quality_issues['missing_metadata']:
            recommendations.append({
                'category': '元数据缺失',
                'priority': 'high',
                'action': '补充文件名中的时间、地区、类型信息',
                'benefit': '提高数据可检索性和分类准确性'
            })
        
        if self.quality_issues['temporal_gaps']:
            recommendations.append({
                'category': '时间覆盖',
                'priority': 'low',
                'action': '收集缺失年份的政策文件',
                'benefit': '完善时间序列，支持历史趋势分析'
            })
        
        return recommendations
    
    def _generate_file_statistics(self, file_info: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成文件统计信息"""
        if not file_info:
            return {
                'format_distribution': {},
                'size_statistics': {'min': 0, 'max': 0, 'avg': 0},
                'encoding_distribution': {}
            }
            
        format_stats = Counter(info['suffix'] for info in file_info)
        size_stats = {
            'min': min(info['size'] for info in file_info),
            'max': max(info['size'] for info in file_info),
            'avg': sum(info['size'] for info in file_info) / len(file_info)
        }
        
        return {
            'format_distribution': dict(format_stats),
            'size_statistics': size_stats,
            'encoding_distribution': Counter(info.get('encoding', 'unknown') for info in file_info)
        }
    
    def save_quality_report(self, report: Dict[str, Any], output_path: str):
        """保存质量报告"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"质量报告已保存到: {output_path}")
        except Exception as e:
            logger.error(f"保存质量报告失败: {e}")