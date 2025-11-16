"""
主程序入口
整合所有模块，提供统一的问答接口

升级内容（遵循赛题解决思路）：
1. 细粒度知识分块（800字片段，100字重叠）
2. 增强意图理解（多意图拆解、实体提取）
3. 多策略检索（细节/推理/多跳/摘要等）
4. 中文金融模型优化
"""
import os
import json
from typing import List, Dict, Any
from loguru import logger

import config
from document_parser import KnowledgeBaseBuilder
from intent_understanding import IntentClassifier, ReasoningEngine
from intent_classifier import EnhancedIntentClassifier  # 新增：增强版意图分类
from retrieval_ranking import VectorRetriever, RankingOptimizer
from summary_generator import TextRankSummarizer


class QASystem:
    """金融问答系统"""
    
    def __init__(self):
        """初始化问答系统"""
        logger.add(config.LOG_FILE, rotation="10 MB")
        logger.info("=" * 60)
        logger.info("初始化金融问答系统（增强版）...")
        logger.info("=" * 60)
        
        # 初始化各模块
        self.knowledge_builder = KnowledgeBaseBuilder()
        self.intent_classifier = IntentClassifier()  # 保留旧版（兼容）
        self.enhanced_intent_classifier = EnhancedIntentClassifier()  # 新增：增强版
        self.reasoning_engine = ReasoningEngine()
        self.retriever = VectorRetriever()
        self.ranking_optimizer = RankingOptimizer()
        self.summarizer = TextRankSummarizer()
        
        self.is_ready = False
        logger.info("所有模块初始化完成")
    
    def initialize(self, rebuild_knowledge: bool = False):
        """
        初始化系统
        
        Args:
            rebuild_knowledge: 是否重新构建知识库
        """
        knowledge_path = os.path.join(config.PARSED_KNOWLEDGE_DIR, "knowledge_base.json")
        
        # 1. 构建/加载知识库
        if rebuild_knowledge or not os.path.exists(knowledge_path):
            logger.info("开始构建知识库...")
            self.knowledge_builder.build_from_directory(config.KNOWLEDGE_BASE_DIR)
            self.knowledge_builder.save_to_json(knowledge_path)
        else:
            logger.info("加载已有知识库...")
            self.knowledge_builder.load_from_json(knowledge_path)
        
        # 2. 构建/加载向量索引
        if rebuild_knowledge or not os.path.exists(config.FAISS_INDEX_PATH):
            logger.info("开始构建向量索引...")
            self.retriever.build_index(self.knowledge_builder.knowledge_base)
            self.retriever.save_index()
        else:
            logger.info("加载已有向量索引...")
            self.retriever.load_index()
        
        self.is_ready = True
        logger.info("系统初始化完成！")
    
    def answer(self, question: str) -> Dict[str, Any]:
        """
        回答问题
        
        Args:
            question: 用户问题
            
        Returns:
            回答结果
        """
        if not self.is_ready:
            logger.error("系统未初始化")
            return {
                'question': question,
                'error': '系统未初始化'
            }
        
        logger.info(f"\n{'='*50}")
        logger.info(f"收到问题: {question}")
        
        # 1. 增强版意图理解（多意图拆解、实体提取）
        intent_result = self.enhanced_intent_classifier.classify_with_decomposition(question)
        main_intent = intent_result['main_intent']
        sub_intents = intent_result.get('sub_intents', [])
        decomposed_queries = intent_result.get('decomposed_queries', [question])
        
        logger.info(f"意图分析: {main_intent} | 子查询: {len(decomposed_queries)}")
        logger.info(f"实体: {intent_result.get('entities', {})}")
        logger.info(f"关键词: {intent_result.get('keywords', [])}")
        
        # 2. 使用多策略检索（根据意图选择策略）
        if config.USE_MULTI_STRATEGY:
            # 新方法：多策略检索
            search_results = self.retriever.search_with_strategy(intent_result, top_k=config.TOP_K)
        else:
            # 旧方法：简单向量检索（兼容）
            search_results = self.retriever.search(question, top_k=config.TOP_K)
        
        # 3. 整理知识点（包含内容和来源信息）
        knowledge_points_with_source = []
        for r in search_results[:config.TOP_K]:
            kp = {
                'content': r['content'],
                'source': {
                    'document': r.get('source_doc', r.get('title', '未知文档')),
                    'type': r.get('type', '未知类型'),
                    'chunk_index': r.get('chunk_index', 0),
                    'chunk_type': r.get('chunk_type', 'paragraph')
                },
                'score': r.get('score', 0),
                # 如果是混合检索，包含详细分数
                'score_details': {
                    'total': r.get('score', 0),
                    'bm25': r.get('bm25_component', 0),
                    'semantic': r.get('semantic_component', 0)
                } if 'bm25_component' in r else None
            }
            knowledge_points_with_source.append(kp)
        
        # 提取纯文本内容（用于摘要等）
        knowledge_points = [kp['content'] for kp in knowledge_points_with_source]
        
        # 4. 如果是摘要类问题，进行摘要处理
        if main_intent == 'summary' and knowledge_points:
            logger.info("检测到摘要问题，生成摘要...")
            combined_text = '\n\n'.join(knowledge_points)
            summary = self.summarizer.summarize(combined_text, max_sentences=5)
            if summary:
                # 摘要作为第一个知识点
                summary_kp = {
                    'content': summary,
                    'source': {'document': '系统生成摘要', 'type': 'summary'},
                    'score': 1.0
                }
                knowledge_points_with_source = [summary_kp] + knowledge_points_with_source[:2]
                knowledge_points = [summary] + knowledge_points[:2]
        
        # 5. 整理结果
        result = {
            'question': question,
            'intent': main_intent,
            'knowledge_points': knowledge_points[:config.TOP_K],  # 纯文本内容（向后兼容）
            'knowledge_points_detailed': knowledge_points_with_source[:config.TOP_K],  # 新增：包含来源的详细信息
            'metadata': {
                'main_intent': main_intent,
                'sub_intents': sub_intents,
                'decomposed_queries': decomposed_queries,
                'entities': intent_result.get('entities', {}),
                'keywords': intent_result.get('keywords', []),
                'search_scores': [r.get('score', 0) for r in search_results[:config.TOP_K]],
                'retrieval_method': 'hybrid' if config.USE_HYBRID_RETRIEVAL else 'semantic'
            }
        }
        
        logger.info(f"问题处理完成，返回 {len(result['knowledge_points'])} 个知识点")
        logger.info(f"检索分数: {result['metadata']['search_scores']}")
        return result
    
    def _handle_query(self, intent_result: Dict[str, Any]) -> List[str]:
        """处理普通查询"""
        question = intent_result['question']
        
        # 检索
        results = self.retriever.search(question, top_k=config.TOP_K)
        
        # 排序优化
        results = self.ranking_optimizer.rerank(question, results)
        
        # 提取内容
        knowledge_points = [r['content'] for r in results[:config.TOP_K]]
        
        return knowledge_points
    
    def _handle_multi_intent(self, intent_result: Dict[str, Any]) -> List[str]:
        """处理多意图问题"""
        split_questions = intent_result['split_questions']
        
        logger.info(f"多意图问题，拆分为 {len(split_questions)} 个子问题")
        
        all_knowledge_points = []
        
        for sub_question in split_questions:
            # 检索每个子问题
            results = self.retriever.search(sub_question, top_k=2)  # 每个子问题返回2个
            
            for result in results:
                if result['content'] not in all_knowledge_points:
                    all_knowledge_points.append(result['content'])
        
        # 返回Top3
        return all_knowledge_points[:config.TOP_K]
    
    def _handle_multi_hop(self, intent_result: Dict[str, Any]) -> List[str]:
        """处理多跳问题"""
        question = intent_result['question']
        
        logger.info("执行多跳检索")
        
        # 策略：将问题拆分为多个查询
        # 例如："客户月收入8000元，申请50万贷款需满足哪些条件？"
        # 拆分为：["贷款条件", "客户资质要求"]
        
        queries = [question]  # 主查询
        
        # 添加实体相关的查询
        for entity in intent_result['entities'][:2]:  # 最多2个实体
            entity_query = f"{entity}相关要求"
            queries.append(entity_query)
        
        # 多跳检索
        results = self.retriever.multi_hop_search(queries, top_k=config.TOP_K)
        
        # 提取内容
        knowledge_points = [r['content'] for r in results[:config.TOP_K]]
        
        return knowledge_points
    
    def _handle_reasoning(self, intent_result: Dict[str, Any]) -> List[str]:
        """处理推理问题"""
        question = intent_result['question']
        
        logger.info("执行推理")
        
        # 先检索相关知识
        results = self.retriever.search(question, top_k=5)
        
        # 执行推理
        reasoning_result = self.reasoning_engine.reason(question, results)
        
        # 组织知识点
        knowledge_points = []
        
        # 添加推理结论
        if reasoning_result['conclusion']:
            conclusion_text = f"【推理结论】\n{reasoning_result['conclusion']}\n"
            if reasoning_result['reasoning_steps']:
                conclusion_text += "\n【推理步骤】\n"
                for i, step in enumerate(reasoning_result['reasoning_steps'], 1):
                    conclusion_text += f"{i}. {step}\n"
            knowledge_points.append(conclusion_text)
        
        # 添加相关知识作为依据
        for result in results[:2]:  # 添加最相关的2个知识点作为依据
            knowledge_points.append(f"【相关知识】\n{result['content']}")
        
        return knowledge_points[:config.TOP_K]
    
    def _handle_summary(self, intent_result: Dict[str, Any]) -> List[str]:
        """处理总结类问题"""
        question = intent_result['question']
        
        logger.info("执行总结")
        
        # 检索相关文档（多一些）
        results = self.retriever.search(question, top_k=5)
        
        # 提取内容
        contents = [r['content'] for r in results]
        
        # 生成摘要
        summary = self.summarizer.summarize_multiple(contents, max_length=config.MAX_SUMMARY_LENGTH)
        
        # 返回摘要 + 原始知识点
        knowledge_points = [f"【总结】\n{summary}"]
        
        # 添加部分原始知识点作为补充
        for result in results[:2]:
            knowledge_points.append(result['content'])
        
        return knowledge_points[:config.TOP_K]
    
    def batch_answer(self, questions: List[str]) -> List[Dict[str, Any]]:
        """
        批量回答问题
        
        Args:
            questions: 问题列表
            
        Returns:
            回答结果列表
        """
        results = []
        
        for i, question in enumerate(questions, 1):
            logger.info(f"\n处理第 {i}/{len(questions)} 个问题")
            result = self.answer(question)
            results.append(result)
        
        return results


def main():
    """主函数"""
    # 创建问答系统
    qa_system = QASystem()
    
    # 初始化系统（首次运行需要构建知识库）
    qa_system.initialize(rebuild_knowledge=True)
    
    # 测试问题
    test_questions = [
        "请详细说明掌上银行中“基金”功能的主要服务内容以及进行基金认购的具体操作流程。",
        "中国太保在2023年中期业绩报告中如何描述其“大区域”战略在大湾区的具体实施路径？",
        "上海浦东发展银行公司网银的“账户设置”功能中，“单笔支付限额”栏位设置为“0”时表示什么？",
        "为什么丰收e网企业网上银行建议企业尽量不要设置单人即可完成转账的授权模式？",
        "请总结建行网银盾安装使用手册中附录部分涵盖的主要内容和目的。"
    ]
    
    # 批量回答
    results = qa_system.batch_answer(test_questions)
    
    # 打印结果
    for i, result in enumerate(results, 1):
        print(f"\n{'='*60}")
        print(f"问题 {i}: {result['question']}")
        print(f"意图: {result['intent']}")
        print(f"检索方式: {result['metadata'].get('retrieval_method', 'unknown')}")
        print(f"\n知识点:")
        
        # 使用详细的知识点信息（包含来源）
        for j, kp_detail in enumerate(result.get('knowledge_points_detailed', []), 1):
            print(f"\n[知识点 {j}]")
            
            # 打印来源信息
            source = kp_detail.get('source', {})
            print(f"【来源】文档: {source.get('document', '未知')}")
            print(f"       类型: {source.get('type', '未知')}")
            print(f"       片段: 第{source.get('chunk_index', 0)+1}段")
            print(f"【得分】{kp_detail.get('score', 0):.4f}")
            
            # 如果有混合检索详细分数
            score_details = kp_detail.get('score_details')
            if score_details:
                print(f"       (BM25: {score_details.get('bm25', 0):.4f}, 语义: {score_details.get('semantic', 0):.4f})")
            
            # 打印内容
            print(f"【内容】")
            kp = kp_detail['content']
            # 处理特殊字符，避免Windows终端编码错误
            kp_safe = kp.encode('gbk', errors='ignore').decode('gbk')
            kp_text = kp_safe[:300] + "..." if len(kp_safe) > 300 else kp_safe
            print(kp_text)


if __name__ == "__main__":
    main()

