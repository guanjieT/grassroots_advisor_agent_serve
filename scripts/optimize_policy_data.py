#!/usr/bin/env python3
"""
政策数据优化脚本
对政策法规数据进行清理、标准化和优化处理
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.knowledge_base.data_optimizer import DataOptimizer
from src.knowledge_base.data_quality_checker import DataQualityChecker
from src.utils.logger import logger

def main():
    """主函数"""
    print("🔧 政策数据优化工具")
    print("=" * 50)
    
    # 数据路径
    input_dir = "./data/rules"
    output_dir = "./data/optimized"
    
    if not os.path.exists(input_dir):
        print(f"❌ 输入目录不存在: {input_dir}")
        return
    
    try:
        # 初始化优化器
        print("1. 初始化数据优化器...")
        optimizer = DataOptimizer()
        
        # 初始化质量检查器
        print("2. 初始化质量检查器...")
        quality_checker = DataQualityChecker()
        
        # 检查原始数据质量
        print("3. 检查原始数据质量...")
        quality_report = quality_checker.check_directory_quality(input_dir)
        
        print(f"   发现文件: {quality_report.get('total_files', 0)} 个")
        print(f"   数据质量评分: {quality_report.get('overall_score', 0):.2f}/5.0")
        
        # 执行数据优化
        print("4. 执行数据优化...")
        optimization_result = optimizer.optimize_directory(input_dir, output_dir)
        
        if optimization_result.get('success', False):
            print("✅ 数据优化完成!")
            print(f"   处理文件: {optimization_result.get('processed_files', 0)} 个")
            print(f"   输出目录: {output_dir}")
            
            # 检查优化后数据质量
            print("5. 检查优化后数据质量...")
            optimized_quality = quality_checker.check_directory_quality(output_dir)
            
            print(f"   优化后质量评分: {optimized_quality.get('overall_score', 0):.2f}/5.0")
            
            # 生成优化报告
            print("6. 生成优化报告...")
            report_path = os.path.join(output_dir, "optimization_report.json")
            
            import json
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'original_quality': quality_report,
                    'optimization_result': optimization_result,
                    'optimized_quality': optimized_quality
                }, f, ensure_ascii=False, indent=2)
            
            print(f"   报告已保存: {report_path}")
            
        else:
            print(f"❌ 数据优化失败: {optimization_result.get('error', '未知错误')}")
    
    except Exception as e:
        print(f"❌ 优化过程出现错误: {e}")
        logger.error(f"数据优化失败: {e}")

if __name__ == "__main__":
    main()