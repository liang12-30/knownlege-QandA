"""
生成最终结果文件
读取测试集，生成result.json
"""
import os
import json
import pandas as pd
from typing import List, Dict, Any
from loguru import logger
from tqdm import tqdm

import config
from main import QASystem


def load_test_queries(file_path: str) -> List[Dict[str, str]]:
    """
    加载测试问题集
    
    Args:
        file_path: 测试集文件路径（Excel）
        
    Returns:
        测试问题列表 [{"question_id": "Q001", "question": "问题内容"}]
    """
    logger.info(f"加载测试集: {file_path}")
    
    # 读取Excel文件
    df = pd.read_excel(file_path)
    
    # 提取问题
    queries = []
    for _, row in df.iterrows():
        # 假设Excel有两列：question_id 和 question
        # 根据实际Excel格式调整
        question_id = row.get('question_id') or row.get('编号') or row.get('ID')
        question_text = row.get('question') or row.get('问题') or row.get('内容')
        
        if question_id and question_text:
            queries.append({
                'question_id': str(question_id),
                'question': str(question_text)
            })
    
    logger.info(f"加载完成，共 {len(queries)} 个问题")
    return queries


def generate_result_json(qa_system: QASystem, test_queries: List[Dict[str, str]], output_path: str):
    """
    生成result.json文件
    
    Args:
        qa_system: 问答系统实例
        test_queries: 测试问题列表
        output_path: 输出文件路径
    """
    logger.info("开始生成结果文件...")
    
    results = []
    
    # 批量处理问题
    for query_info in tqdm(test_queries, desc="处理问题"):
        question_id = query_info['question_id']
        question = query_info['question']
        
        try:
            # 回答问题
            answer_result = qa_system.answer(question)
            
            # 提取知识点（Top3）
            knowledge_points = answer_result['knowledge_points'][:config.TOP_K]
            
            # 确保知识点不超过1500字
            knowledge_points = [
                kp[:config.MAX_KNOWLEDGE_LENGTH] if len(kp) > config.MAX_KNOWLEDGE_LENGTH else kp
                for kp in knowledge_points
            ]
            
            # 构建结果对象
            result_item = {
                'question_id': question_id,
                'knowledge_points': knowledge_points
            }
            
            results.append(result_item)
            
        except Exception as e:
            logger.error(f"处理问题 {question_id} 失败: {str(e)}")
            # 失败时返回空知识点
            results.append({
                'question_id': question_id,
                'knowledge_points': []
            })
    
    # 保存到JSON文件（UTF-8编码）
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"结果文件已保存: {output_path}")
    logger.info(f"共处理 {len(results)} 个问题")
    
    # 验证结果格式
    validate_result_json(output_path)


def validate_result_json(file_path: str):
    """
    验证result.json格式是否符合要求
    
    Args:
        file_path: 结果文件路径
    """
    logger.info("验证结果文件格式...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # 检查顶层结构
    if not isinstance(results, list):
        logger.error("顶层结构必须是JSON数组")
        return False
    
    # 检查每个结果项
    for i, item in enumerate(results):
        # 检查必要字段
        if 'question_id' not in item:
            logger.error(f"第 {i+1} 项缺少 question_id 字段")
            return False
        
        if 'knowledge_points' not in item:
            logger.error(f"第 {i+1} 项缺少 knowledge_points 字段")
            return False
        
        # 检查knowledge_points是否为数组
        if not isinstance(item['knowledge_points'], list):
            logger.error(f"第 {i+1} 项的 knowledge_points 必须是数组")
            return False
        
        # 检查知识点数量（应该≤3）
        if len(item['knowledge_points']) > config.TOP_K:
            logger.warning(f"第 {i+1} 项的知识点数量超过 {config.TOP_K}")
        
        # 检查知识点长度（应该≤1500）
        for j, kp in enumerate(item['knowledge_points']):
            if len(kp) > config.MAX_KNOWLEDGE_LENGTH:
                logger.warning(f"第 {i+1} 项的第 {j+1} 个知识点超过 {config.MAX_KNOWLEDGE_LENGTH} 字")
    
    logger.info("结果文件格式验证通过！")
    logger.info(f"- 总问题数: {len(results)}")
    logger.info(f"- 编码: UTF-8")
    logger.info(f"- 格式: JSON数组")
    
    return True


def main():
    """主函数"""
    # 创建问答系统
    logger.info("初始化问答系统...")
    qa_system = QASystem()
    
    # 初始化系统
    # 首次运行设置rebuild_knowledge=True
    # 后续运行可以设置为False以节省时间
    qa_system.initialize(rebuild_knowledge=False)
    
    # 加载测试集
    test_file = os.path.join(config.QUERIES_DIR, "100条测试集（初赛）.xlsx")
    
    if not os.path.exists(test_file):
        logger.error(f"测试集文件不存在: {test_file}")
        
        # 使用示例问题
        logger.info("使用示例问题进行测试...")
        test_queries = [
            {"question_id": "Q001", "question": "如何开通手机银行？"},
            {"question_id": "Q002", "question": "个人住房贷款流程和最新LPR利率"},
            {"question_id": "Q003", "question": "月收入8000元，负债2000元，申请50万信用贷款是否合规"},
            {"question_id": "Q004", "question": "总结一下企业网银的主要功能"},
            {"question_id": "Q005", "question": "客户月收入8000元，申请50万贷款需满足哪些条件？"}
        ]
    else:
        test_queries = load_test_queries(test_file)
    
    # 生成结果文件
    generate_result_json(qa_system, test_queries, config.RESULT_FILE)
    
    logger.info("完成！")


if __name__ == "__main__":
    main()

