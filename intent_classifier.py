"""
增强版意图分类器
遵循原则：意图拆解 > 全文匹配
支持多意图识别、实体提取、查询拆解
"""
import re
from typing import List, Dict, Tuple
import jieba
import jieba.analyse
from loguru import logger


class EnhancedIntentClassifier:
    """
    增强的意图分类器
    
    功能：
    1. 识别问题类型（detail/multi_intent/reasoning/multi_hop/summary/long_text）
    2. 拆解多意图问题
    3. 提取金融实体
    4. 生成检索查询
    """
    
    def __init__(self):
        # 问题类型关键词模式
        self.intent_patterns = {
            'detail': ['什么', '哪些', '多少', '如何', '怎么', '怎样', '具体', '详细'],
            'multi_intent': ['和', '以及', '还有', '另外', '同时', '并且', '既...又'],
            'reasoning': ['是否', '能否', '可以', '符合', '满足', '达到', '合规', '允许'],
            'multi_hop': ['然后', '接着', '之后', '导致', '影响', '基于', '根据'],
            'summary': ['总结', '归纳', '概述', '整体', '全部', '汇总', '综述'],
            'comparison': ['对比', '比较', '区别', '差异', '优劣']
        }
        
        # 金融实体模式
        self.entity_patterns = {
            'amount': r'(\d+\.?\d*)\s*[万亿千百]*元',
            'percentage': r'(\d+\.?\d*)\s*%',
            'age': r'(\d+)\s*岁|年满\s*(\d+)',
            'time': r'\d{4}\s*年\s*\d{1,2}\s*月|\d{4}\s*年',
            'product': r'(理财|贷款|信用卡|保险|基金|债券|存款)',
            'bank': r'(中国[银行工商农业建设]|[工农中建交招商浦发]银行)',
            'term': r'(\d+)\s*(年|月|日|天)',
        }
        
        # 连接词（用于拆分多意图）
        self.connectors = ['和', '以及', '还有', '另外', '同时', '并且', '以及', '及']
        
        logger.info("增强版意图分类器初始化完成")
    
    def classify_with_decomposition(self, question: str) -> Dict:
        """
        分类并拆解问题（核心方法）
        
        流程：
        1. 预处理问题
        2. 识别主要意图
        3. 提取实体
        4. 拆解子意图
        5. 生成检索查询
        
        Args:
            question: 用户问题
            
        Returns:
            {
                'main_intent': str,  # 主要意图类型
                'sub_intents': List[str],  # 子意图列表
                'entities': Dict,  # 提取的实体
                'keywords': List[str],  # 关键词
                'decomposed_queries': List[str],  # 拆解后的查询列表
                'original_question': str  # 原始问题
            }
        """
        # 1. 预处理
        cleaned_question = self._preprocess_question(question)
        
        # 2. 分类主要意图
        main_intent = self._classify_main_intent(cleaned_question)
        
        # 3. 提取实体
        entities = self._extract_entities(cleaned_question)
        
        # 4. 提取关键词
        keywords = self._extract_keywords(cleaned_question)
        
        # 5. 意图拆解
        sub_intents, decomposed_queries = self._decompose_intents(
            cleaned_question, main_intent, entities, keywords
        )
        
        result = {
            'main_intent': main_intent,
            'sub_intents': sub_intents,
            'entities': entities,
            'keywords': keywords,
            'decomposed_queries': decomposed_queries,
            'original_question': question
        }
        
        logger.info(f"问题分类: 主意图={main_intent}, 子查询数={len(decomposed_queries)}")
        logger.debug(f"拆解结果: {decomposed_queries}")
        
        return result
    
    def _preprocess_question(self, question: str) -> str:
        """
        预处理问题
        
        操作：
        1. 去除特殊符号
        2. 去除语气词
        3. 标准化空格
        """
        # 去除语气词
        question = re.sub(r'[呢吗啊哦嗯呀]', '', question)
        
        # 标准化标点
        question = question.replace('？', '?').replace('！', '!')
        
        # 去除多余空格
        question = re.sub(r'\s+', ' ', question).strip()
        
        return question
    
    def _classify_main_intent(self, question: str) -> str:
        """
        分类主要意图
        
        优先级：
        1. 长度判断 (long_text)
        2. 模式匹配 (summary/reasoning/multi_intent等)
        3. 默认 (detail)
        """
        # 1. 长度判断
        if len(question) > 100:
            return 'long_text'
        
        # 2. 模式匹配计分
        scores = {}
        for intent, keywords in self.intent_patterns.items():
            score = sum(1 for kw in keywords if kw in question)
            if score > 0:
                scores[intent] = score
        
        # 3. 返回得分最高的
        if scores:
            main_intent = max(scores.items(), key=lambda x: x[1])[0]
            return main_intent
        
        # 4. 默认为细节查询
        return 'detail'
    
    def _extract_entities(self, question: str) -> Dict:
        """
        提取金融实体
        
        Returns:
            实体字典，键为实体类型，值为实体列表
        """
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, question)
            if matches:
                # 清理元组
                cleaned_matches = []
                for match in matches:
                    if isinstance(match, tuple):
                        # 取第一个非空元素
                        match = next((m for m in match if m), '')
                    if match:
                        cleaned_matches.append(match)
                
                if cleaned_matches:
                    entities[entity_type] = cleaned_matches
        
        return entities
    
    def _extract_keywords(self, question: str) -> List[str]:
        """
        提取关键词
        
        使用 jieba 的 TF-IDF 算法
        """
        keywords = jieba.analyse.extract_tags(question, topK=5, withWeight=False)
        return keywords
    
    def _decompose_intents(self, question: str, main_intent: str, 
                          entities: Dict, keywords: List[str]) -> Tuple[List[str], List[str]]:
        """
        意图拆解（核心逻辑）
        
        策略：
        1. multi_intent: 按连词拆分
        2. reasoning: 拆分为条件查询 + 规则查询
        3. multi_hop: 识别推理链，逐步查询
        4. summary: 生成主题查询
        5. detail: 生成精确查询 + 扩展查询
        
        Returns:
            (子意图列表, 拆解后的查询列表)
        """
        sub_intents = []
        decomposed_queries = []
        
        if main_intent == 'multi_intent':
            # 多意图拆分
            sub_intents, decomposed_queries = self._decompose_multi_intent(question)
        
        elif main_intent == 'reasoning':
            # 推理问题拆分
            sub_intents, decomposed_queries = self._decompose_reasoning(question, entities)
        
        elif main_intent == 'multi_hop':
            # 多跳问题拆分
            sub_intents, decomposed_queries = self._decompose_multi_hop(question, keywords)
        
        elif main_intent == 'summary':
            # 摘要问题
            decomposed_queries = [question, f"{' '.join(keywords)}"]
            sub_intents = ['summary', 'summary']
        
        elif main_intent == 'comparison':
            # 对比问题
            decomposed_queries = self._decompose_comparison(question)
            sub_intents = ['detail'] * len(decomposed_queries)
        
        else:
            # 细节问题：生成主查询 + 关键词查询
            decomposed_queries = [question]
            
            # 添加纯关键词查询（提高召回）
            if keywords:
                keyword_query = ' '.join(keywords)
                if keyword_query != question:
                    decomposed_queries.append(keyword_query)
            
            sub_intents = ['detail'] * len(decomposed_queries)
        
        # 如果没有拆分出查询，使用原问题
        if not decomposed_queries:
            decomposed_queries = [question]
            sub_intents = [main_intent]
        
        return sub_intents, decomposed_queries
    
    def _decompose_multi_intent(self, question: str) -> Tuple[List[str], List[str]]:
        """拆解多意图问题"""
        sub_intents = []
        queries = []
        
        # 按连接词拆分
        parts = [question]
        for connector in self.connectors:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(connector))
            parts = new_parts
        
        # 清理并保留有效部分
        for part in parts:
            part = part.strip('，。？！、')
            if len(part) >= 5:  # 至少5个字
                queries.append(part)
                sub_intents.append('detail')
        
        # 如果拆分结果太少，添加原问题
        if len(queries) < 2:
            queries = [question]
            sub_intents = ['multi_intent']
        
        logger.info(f"多意图拆分: {len(queries)} 个子查询")
        return sub_intents, queries
    
    def _decompose_reasoning(self, question: str, entities: Dict) -> Tuple[List[str], List[str]]:
        """拆解推理问题"""
        sub_intents = []
        queries = []
        
        # 提取条件部分
        # 例如："客户月收入8000元，负债2000元，申请50万信用贷款是否合规"
        # 拆分为：1) 信用贷款的合规条件  2) 月收入8000元负债2000元是否符合条件
        
        # 生成规则查询
        if '是否' in question or '能否' in question or '可以' in question:
            # 提取核心需求
            core_query = re.sub(r'(是否|能否|可以|吗)', '', question)
            core_query = re.sub(r'(客户|我|用户)', '', core_query)
            
            # 查询1：规则和标准
            rule_query = f"{core_query} 条件 标准 要求"
            queries.append(rule_query)
            sub_intents.append('rule')
            
            # 查询2：具体情况
            queries.append(question)
            sub_intents.append('reasoning')
        else:
            queries = [question]
            sub_intents = ['reasoning']
        
        logger.info(f"推理问题拆分: {len(queries)} 个子查询")
        return sub_intents, queries
    
    def _decompose_multi_hop(self, question: str, keywords: List[str]) -> Tuple[List[str], List[str]]:
        """拆解多跳问题"""
        # 多跳问题通常需要逐步检索
        # 例如："监管政策对理财产品风险评级的要求，我行对应产品有哪些"
        # 拆分为：1) 监管政策 理财产品 风险评级  2) 我行理财产品
        
        sub_intents = []
        queries = []
        
        # 尝试按逗号或顿号拆分
        if '，' in question or '、' in question:
            parts = re.split(r'[，、]', question)
            for part in parts:
                part = part.strip()
                if len(part) >= 5:
                    queries.append(part)
                    sub_intents.append('detail')
        
        # 如果没有拆分，使用关键词生成查询
        if not queries:
            queries = [question]
            if keywords:
                queries.append(' '.join(keywords[:3]))  # 前3个关键词
            sub_intents = ['detail'] * len(queries)
        
        logger.info(f"多跳问题拆分: {len(queries)} 个子查询")
        return sub_intents, queries
    
    def _decompose_comparison(self, question: str) -> List[str]:
        """拆解对比问题"""
        # 对比问题：分别查询两个对象
        queries = [question]
        
        # 尝试提取比较对象
        compare_patterns = [
            r'(.+)和(.+)的?(对比|比较|区别)',
            r'(对比|比较)(.+)和(.+)',
        ]
        
        for pattern in compare_patterns:
            match = re.search(pattern, question)
            if match:
                if len(match.groups()) >= 2:
                    obj1 = match.group(1).strip()
                    obj2 = match.group(2).strip()
                    
                    if obj1 and obj2:
                        queries = [obj1, obj2, question]
                        break
        
        return queries

