"""
检索与排序模块
使用FAISS向量检索，返回Top3知识点，含字数截断功能
"""
import os
import json
import re
import numpy as np
from typing import List, Dict, Any, Tuple
import faiss
from sentence_transformers import SentenceTransformer
from loguru import logger

import config
from hybrid_retriever import HybridRetriever  # 新增：混合检索器


class VectorRetriever:
    """向量检索器"""
    
    @staticmethod
    def clean_content(content: str) -> str:
        """
        清理知识点内容，去除页码标记和优化格式
        
        Args:
            content: 原始内容
            
        Returns:
            清理后的内容
        """
        if not content:
            return content
        
        # 1. 去除页码标记，如 [第1页]、[第2页]、[页1-0] 等
        content = re.sub(r'\[第?\s*\d+\s*页\s*\]', '', content)
        content = re.sub(r'\[页\s*\d+-\d+\]', '', content)
        content = re.sub(r'\[.*?-页\d+-\d+\]', '', content)
        
        # 2. 去除多余的空白行（超过2个连续换行替换为2个）
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 3. 合并短行（行末不是标点符号且下一行不是空行或标题时合并）
        lines = content.split('\n')
        merged_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 如果当前行为空，保留
            if not line:
                merged_lines.append(line)
                i += 1
                continue
            
            # 检查是否需要合并下一行
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                
                # 如果当前行很短（<20字）且不以标点结束，且下一行不为空且不是标题
                if (len(line) < 50 and 
                    next_line and 
                    not line.endswith(('。', '！', '？', '：', '；', '.', '!', '?', ':', ';')) and
                    not next_line.startswith(('一、', '二、', '三、', '四、', '五、', 
                                             '1.', '2.', '3.', '4.', '5.',
                                             '（一）', '（二）', '（三）', '第一', '第二'))):
                    # 合并当前行和下一行
                    merged_lines.append(line + next_line)
                    i += 2
                    continue
            
            merged_lines.append(line)
            i += 1
        
        content = '\n'.join(merged_lines)
        
        # 4. 去除行首行尾空白
        lines = [line.strip() for line in content.split('\n')]
        content = '\n'.join(lines)
        
        # 5. 去除开头和结尾的多余换行
        content = content.strip()
        
        return content
    
    def __init__(self, model_name: str = None):
        """
        初始化检索器
        
        Args:
            model_name: sentence-transformer模型名称
        """
        if model_name is None:
            model_name = config.SENTENCE_TRANSFORMER_MODEL
        
        logger.info(f"加载向量化模型: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # FAISS索引
        self.index = None
        self.knowledge_base = []
        self.embeddings = None
        
        # 知识点ID映射
        self.id_to_knowledge = {}
        
        # 混合检索器（BM25 + 语义）
        self.hybrid_retriever = None
        if config.USE_HYBRID_RETRIEVAL:
            self.hybrid_retriever = HybridRetriever(
                vector_retriever=self,
                bm25_weight=config.BM25_WEIGHT,
                semantic_weight=config.SEMANTIC_WEIGHT
            )
    
    def build_index(self, knowledge_base: List[Dict[str, Any]]):
        """
        构建FAISS索引
        
        Args:
            knowledge_base: 知识库列表
        """
        logger.info(f"开始构建向量索引，知识库大小: {len(knowledge_base)}")
        
        self.knowledge_base = knowledge_base
        
        # 提取所有文档内容
        documents = []
        for idx, doc in enumerate(knowledge_base):
            content = doc.get('content', '')
            if content:
                # 如果内容太长，先截取用于向量化（避免超出模型限制）
                content_for_embedding = content[:2000]  # 取前2000字符
                documents.append(content_for_embedding)
                self.id_to_knowledge[idx] = doc
            else:
                documents.append("")
                logger.warning(f"文档 {doc.get('title', 'unknown')} 内容为空")
        
        # 批量向量化
        logger.info("开始向量化文档...")
        self.embeddings = self.model.encode(
            documents, 
            show_progress_bar=True,
            batch_size=32
        )
        
        # 构建FAISS索引
        dimension = self.embeddings.shape[1]
        logger.info(f"向量维度: {dimension}")
        
        # 使用IndexFlatIP（内积）进行相似度计算
        # 先归一化向量，使得内积等价于余弦相似度
        faiss.normalize_L2(self.embeddings)
        
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(self.embeddings)
        
        logger.info(f"FAISS索引构建完成，共 {self.index.ntotal} 个向量")
        
        # 构建混合检索索引
        if self.hybrid_retriever:
            self.hybrid_retriever.build_index(self.knowledge_base)
            logger.info("混合检索索引构建完成")
    
    def search(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        检索相关知识点
        
        Args:
            query: 查询问题
            top_k: 返回top k个结果
            
        Returns:
            检索结果列表 [{content, score, doc_id}]
        """
        if top_k is None:
            top_k = config.TOP_K
        
        if self.index is None:
            logger.error("FAISS索引未构建，请先调用build_index()")
            return []
        
        # 如果启用混合检索，使用BM25+语义混合
        if config.USE_HYBRID_RETRIEVAL and self.hybrid_retriever:
            logger.info(f"使用混合检索（BM25+语义）: {query}")
            return self.hybrid_retriever.search(query, top_k=top_k)
        
        # 否则使用纯向量检索
        return self._pure_vector_search(query, top_k)
    
    def _pure_vector_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """
        纯向量检索（内部方法，供hybrid_retriever调用）
        
        Args:
            query: 查询问题
            top_k: 返回top k个结果
            
        Returns:
            检索结果列表
        """
        logger.info(f"纯向量检索: query长度={len(query)}, top_k={top_k}")
        
        # 向量化查询
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # 搜索
        scores, indices = self.index.search(query_embedding, top_k)
        
        # 整理结果
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx in self.id_to_knowledge:
                # 添加相似度过滤
                if score < config.SIMILARITY_THRESHOLD:
                    logger.debug(f"相似度过低，跳过: score={score:.3f}")
                    continue
                
                doc = self.id_to_knowledge[idx]
                
                # 截断内容（最多1500字）
                content = doc.get('content', '')
                
                # 清理内容格式
                content = self.clean_content(content)
                
                if len(content) > config.MAX_KNOWLEDGE_LENGTH:
                    content = content[:config.MAX_KNOWLEDGE_LENGTH]
                
                results.append({
                    'content': content,
                    'score': float(score),
                    'doc_id': doc.get('doc_id', ''),
                    'title': doc.get('title', ''),
                    'type': doc.get('type', ''),
                    # 新增：来源信息
                    'source_doc': doc.get('source_doc', doc.get('title', '')),  # 源文档名称
                    'chunk_index': doc.get('chunk_index', 0),  # 片段索引
                    'chunk_type': doc.get('chunk_type', 'paragraph')  # 片段类型
                })
        
        logger.info(f"纯向量检索完成，返回 {len(results)} 个结果")
        return results[:top_k]  # 确保只返回 top_k 个结果
    
    def search_with_strategy(self, intent_result: Dict, top_k: int = None) -> List[Dict[str, Any]]:
        """
        基于意图的多策略检索（核心新增功能）
        
        不同问题类型使用不同检索策略：
        - detail: 精确匹配 + 关键词增强
        - multi_intent: 分步检索 + 结果合并
        - reasoning: 规则检索 + 实体匹配
        - multi_hop: 逐步扩展检索
        - summary: 主题聚合检索
        - long_text: 摘要后检索
        
        遵循原则：意图拆解 > 全文匹配
        
        Args:
            intent_result: 意图分析结果（来自EnhancedIntentClassifier）
            top_k: 返回的结果数量
            
        Returns:
            检索结果列表
        """
        if top_k is None:
            top_k = config.TOP_K
        
        main_intent = intent_result['main_intent']
        decomposed_queries = intent_result['decomposed_queries']
        keywords = intent_result.get('keywords', [])
        
        logger.info(f"使用策略: {main_intent}, 查询数: {len(decomposed_queries)}")
        
        if main_intent == 'detail':
            # 细节问题：精确匹配 + 关键词增强
            return self._search_detail(decomposed_queries[0], keywords, top_k)
        
        elif main_intent == 'multi_intent':
            # 多意图：分步检索后合并
            return self._search_multi_intent(decomposed_queries, top_k)
        
        elif main_intent == 'reasoning':
            # 推理问题：规则检索
            return self._search_reasoning(decomposed_queries, keywords, top_k)
        
        elif main_intent == 'multi_hop':
            # 多跳检索
            return self.multi_hop_search(decomposed_queries, top_k)
        
        elif main_intent == 'summary':
            # 摘要：广泛检索后聚合
            return self._search_summary(decomposed_queries[0], keywords, top_k * 2)
        
        elif main_intent == 'comparison':
            # 对比：分别检索两个对象
            return self._search_comparison(decomposed_queries, top_k)
        
        else:
            # 默认向量检索
            return self.search(decomposed_queries[0], top_k)
    
    def _search_detail(self, query: str, keywords: List[str], top_k: int) -> List[Dict[str, Any]]:
        """
        细节类问题：精确匹配 + 关键词增强
        
        策略：
        1. 向量检索获取候选
        2. 关键词匹配度加权
        3. 实体匹配度加权
        """
        # 检索更多候选（2倍）
        results = self.search(query, top_k * 2)
        
        if config.USE_KEYWORD_BOOST:
            # 关键词增强
            for result in results:
                content = result.get('content', '')
                
                # 计算关键词匹配度
                keyword_match_count = sum(1 for kw in keywords if kw in content)
                keyword_boost = keyword_match_count * config.KEYWORD_BOOST_WEIGHT
                
                # 更新分数
                result['score'] += keyword_boost
                result['keyword_matches'] = keyword_match_count
            
            # 重新排序
            results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:top_k]
    
    def _search_multi_intent(self, queries: List[str], top_k: int) -> List[Dict[str, Any]]:
        """
        多意图检索：分别检索后合并去重
        
        策略：
        1. 对每个子查询单独检索
        2. 合并结果并去重
        3. 按分数排序
        """
        all_results = []
        seen_doc_ids = set()
        
        # 对每个子查询检索
        per_query_top_k = max(2, top_k // len(queries))  # 每个查询至少2个
        
        for query in queries:
            results = self.search(query, top_k=per_query_top_k)
            
            for result in results:
                doc_id = result['doc_id']
                if doc_id not in seen_doc_ids:
                    seen_doc_ids.add(doc_id)
                    all_results.append(result)
        
        # 按分数排序
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        logger.info(f"多意图检索: {len(queries)}个查询 → {len(all_results)}个结果")
        return all_results[:top_k]
    
    def _search_reasoning(self, queries: List[str], keywords: List[str], 
                         top_k: int) -> List[Dict[str, Any]]:
        """
        推理问题检索：查找规则和条件
        
        策略：
        1. 检索规则和标准
        2. 检索具体案例
        3. 合并结果
        """
        all_results = []
        seen_doc_ids = set()
        
        for query in queries:
            results = self.search(query, top_k=3)
            
            for result in results:
                doc_id = result['doc_id']
                if doc_id not in seen_doc_ids:
                    seen_doc_ids.add(doc_id)
                    # 标记为规则类或案例类
                    content = result.get('content', '')
                    if any(word in content for word in ['条件', '要求', '标准', '规定']):
                        result['result_type'] = 'rule'
                    else:
                        result['result_type'] = 'case'
                    all_results.append(result)
        
        # 优先返回规则类结果
        all_results.sort(key=lambda x: (x.get('result_type') == 'rule', x['score']), reverse=True)
        
        return all_results[:top_k]
    
    def _search_summary(self, query: str, keywords: List[str], top_k: int) -> List[Dict[str, Any]]:
        """
        摘要问题检索：广泛检索相关内容
        
        策略：
        1. 使用关键词扩展查询
        2. 检索更多结果
        3. 后续由摘要模块处理
        """
        # 使用关键词查询（更广泛）
        keyword_query = ' '.join(keywords) if keywords else query
        
        # 检索更多结果（用于摘要）
        results = self.search(keyword_query, top_k)
        
        # 如果结果不足，用原查询补充
        if len(results) < top_k:
            additional = self.search(query, top_k - len(results))
            seen_ids = {r['doc_id'] for r in results}
            for r in additional:
                if r['doc_id'] not in seen_ids:
                    results.append(r)
        
        return results
    
    def _search_comparison(self, queries: List[str], top_k: int) -> List[Dict[str, Any]]:
        """
        对比问题检索：分别检索对比对象
        
        策略：
        1. 分别检索两个对比对象
        2. 合并结果
        3. 保持平衡
        """
        all_results = []
        seen_doc_ids = set()
        
        # 为每个对比对象检索
        per_object_top_k = max(1, top_k // len(queries))
        
        for query in queries:
            results = self.search(query, top_k=per_object_top_k)
            
            for result in results:
                doc_id = result['doc_id']
                if doc_id not in seen_doc_ids:
                    seen_doc_ids.add(doc_id)
                    result['compare_object'] = query
                    all_results.append(result)
        
        return all_results[:top_k]
    
    def multi_hop_search(self, queries: List[str], top_k: int = None) -> List[Dict[str, Any]]:
        """
        多跳检索
        
        Args:
            queries: 多个查询问题
            top_k: 每个查询返回的结果数
            
        Returns:
            合并后的检索结果
        """
        if top_k is None:
            top_k = config.TOP_K
        
        logger.info(f"执行多跳检索，查询数: {len(queries)}")
        
        all_results = []
        seen_doc_ids = set()
        
        for query in queries:
            results = self.search(query, top_k=top_k)
            
            # 去重（避免重复文档）
            for result in results:
                doc_id = result['doc_id']
                if doc_id not in seen_doc_ids:
                    seen_doc_ids.add(doc_id)
                    all_results.append(result)
        
        # 重新排序（按分数）
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        # 返回Top K
        return all_results[:top_k]
    
    def save_index(self, index_path: str = None):
        """
        保存FAISS索引
        
        Args:
            index_path: 索引文件路径
        """
        if index_path is None:
            index_path = config.FAISS_INDEX_PATH
        
        if self.index is None:
            logger.error("FAISS索引未构建")
            return
        
        # 保存FAISS索引
        faiss.write_index(self.index, index_path)
        
        # 保存知识库映射
        mapping_path = index_path.replace('.index', '_mapping.json')
        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump({
                'knowledge_base': self.knowledge_base,
                'id_to_knowledge': {str(k): v for k, v in self.id_to_knowledge.items()}
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"索引已保存到: {index_path}")
        logger.info(f"映射已保存到: {mapping_path}")
    
    def load_index(self, index_path: str = None):
        """
        加载FAISS索引
        
        Args:
            index_path: 索引文件路径
        """
        if index_path is None:
            index_path = config.FAISS_INDEX_PATH
        
        if not os.path.exists(index_path):
            logger.error(f"索引文件不存在: {index_path}")
            return False
        
        # 加载FAISS索引
        self.index = faiss.read_index(index_path)
        
        # 加载知识库映射
        mapping_path = index_path.replace('.index', '_mapping.json')
        with open(mapping_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.knowledge_base = data['knowledge_base']
            self.id_to_knowledge = {int(k): v for k, v in data['id_to_knowledge'].items()}
        
        logger.info(f"索引加载完成，共 {self.index.ntotal} 个向量")
        return True


class RankingOptimizer:
    """排序优化器"""
    
    def __init__(self):
        """初始化排序优化器"""
        pass
    
    def rerank(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        重排序检索结果
        
        Args:
            query: 查询问题
            results: 检索结果
            
        Returns:
            重排序后的结果
        """
        # 简单实现：基于相似度分数排序
        # 可以扩展：考虑文档新鲜度、完整性等因素
        
        # 过滤低分结果
        filtered_results = [
            r for r in results 
            if r['score'] >= config.SIMILARITY_THRESHOLD
        ]
        
        # 按分数降序排序
        filtered_results.sort(key=lambda x: x['score'], reverse=True)
        
        return filtered_results
    
    def diversify(self, results: List[Dict[str, Any]], top_k: int = None) -> List[Dict[str, Any]]:
        """
        结果多样化（避免返回相似的文档）
        
        Args:
            results: 检索结果
            top_k: 返回数量
            
        Returns:
            多样化后的结果
        """
        if top_k is None:
            top_k = config.TOP_K
        
        if len(results) <= top_k:
            return results
        
        # 简单实现：基于文档类型多样化
        diversified = []
        seen_types = set()
        
        # 第一轮：每种类型取一个
        for result in results:
            doc_type = result.get('type', 'unknown')
            if doc_type not in seen_types:
                diversified.append(result)
                seen_types.add(doc_type)
                if len(diversified) >= top_k:
                    return diversified
        
        # 第二轮：按分数补充
        for result in results:
            if result not in diversified:
                diversified.append(result)
                if len(diversified) >= top_k:
                    return diversified
        
        return diversified[:top_k]


if __name__ == "__main__":
    # 测试代码
    from document_parser import KnowledgeBaseBuilder
    
    # 加载知识库
    builder = KnowledgeBaseBuilder()
    knowledge_path = os.path.join(config.PARSED_KNOWLEDGE_DIR, "knowledge_base.json")
    
    if os.path.exists(knowledge_path):
        builder.load_from_json(knowledge_path)
        
        # 构建向量索引
        retriever = VectorRetriever()
        retriever.build_index(builder.knowledge_base)
        
        # 保存索引
        retriever.save_index()
        
        # 测试检索
        test_queries = [
            "如何开通手机银行？",
            "企业网银的主要功能有哪些？",
            "个人住房贷款流程"
        ]
        
        for query in test_queries:
            print(f"\n查询: {query}")
            results = retriever.search(query, top_k=3)
            for i, result in enumerate(results, 1):
                print(f"{i}. [{result['title']}] 分数: {result['score']:.4f}")
                print(f"   内容: {result['content'][:100]}...")
    else:
        print(f"请先运行 document_parser.py 构建知识库")

