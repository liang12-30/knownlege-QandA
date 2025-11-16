"""
混合检索器：BM25 + 语义向量检索
遵循原则：精准度 > 速度，解决答非所问问题
"""
import re
import math
import sys
from typing import List, Dict, Any
from collections import Counter
import jieba
import numpy as np
from loguru import logger

# 增加递归深度限制，避免jieba分词时超限
# 设置足够大的值以避免jieba和logger的递归问题
sys.setrecursionlimit(100000)

# 预先初始化jieba，避免首次使用时递归超限
try:
    logger.info("初始化jieba分词器...")
    jieba.initialize()
    logger.info("jieba分词器初始化完成")
except Exception as e:
    logger.warning(f"jieba初始化警告: {e}")


class BM25Retriever:
    """
    BM25 算法实现
    
    基于词频的检索算法，对中文分词后的文本进行检索
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Args:
            k1: 词频饱和度参数，默认1.5
            b: 文档长度归一化参数，默认0.75
        """
        self.k1 = k1
        self.b = b
        self.corpus = []
        self.doc_freqs = []
        self.idf = {}
        self.avg_doc_len = 0
        self.doc_ids = []
        
    def build_index(self, documents: List[Dict[str, Any]]):
        """
        构建BM25索引
        
        Args:
            documents: 文档列表，每个文档包含doc_id和content
        """
        logger.info(f"开始构建BM25索引，文档数：{len(documents)}")
        
        self.corpus = []
        self.doc_ids = []
        
        for doc in documents:
            doc_id = doc.get('doc_id', '')
            content = doc.get('content', '')
            
            # 截断过长文本，避免jieba递归超限
            if len(content) > 5000:
                content = content[:5000]
                logger.debug(f"文档 {doc_id} 内容过长，已截断至5000字")
            
            # 分词（使用try-catch防止异常）
            try:
                tokens = list(jieba.cut(content))
            except RecursionError:
                # 递归超限时使用简单分词（不使用logger避免再次递归）
                print(f"WARNING: 文档 {doc_id} 分词时递归超限，使用简单分词")
                # 回退到按空格和标点分词
                tokens = re.split(r'[\s，。！？；：、]+', content)
                tokens = [t for t in tokens if t]  # 过滤空字符串
            
            self.corpus.append(tokens)
            self.doc_ids.append(doc_id)
        
        # 计算文档频率
        self.doc_freqs = []
        for tokens in self.corpus:
            freq = Counter(tokens)
            self.doc_freqs.append(freq)
        
        # 计算IDF
        self._calculate_idf()
        
        # 计算平均文档长度
        self.avg_doc_len = sum(len(doc) for doc in self.corpus) / len(self.corpus)
        
        logger.info(f"BM25索引构建完成，平均文档长度：{self.avg_doc_len:.1f}")
    
    def _calculate_idf(self):
        """计算逆文档频率"""
        # 统计每个词在多少文档中出现
        df = Counter()
        for doc_freq in self.doc_freqs:
            for word in doc_freq.keys():
                df[word] += 1
        
        # 计算IDF: log((N - df + 0.5) / (df + 0.5))
        num_docs = len(self.corpus)
        self.idf = {}
        for word, freq in df.items():
            self.idf[word] = math.log((num_docs - freq + 0.5) / (freq + 0.5) + 1.0)
    
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        BM25检索
        
        Args:
            query: 查询字符串
            top_k: 返回top-k结果
            
        Returns:
            [(doc_id, score), ...]
        """
        # 截断过长查询
        if len(query) > 500:
            query = query[:500]
        
        # 查询分词（带异常处理）
        try:
            query_tokens = list(jieba.cut(query))
        except RecursionError:
            # 递归超限时使用简单分词（不使用logger避免再次递归）
            print("WARNING: 查询分词时递归超限，使用简单分词")
            # 按空格和标点分词
            query_tokens = re.split(r'[\s，。！？；：、]+', query)
            query_tokens = [t for t in query_tokens if t]
        
        query_freq = Counter(query_tokens)
        
        # 计算每个文档的BM25分数
        scores = []
        for i, doc_freq in enumerate(self.doc_freqs):
            score = 0.0
            doc_len = len(self.corpus[i])
            
            for word, q_freq in query_freq.items():
                if word not in doc_freq:
                    continue
                
                # 词频
                tf = doc_freq[word]
                
                # IDF
                idf = self.idf.get(word, 0)
                
                # 文档长度归一化
                norm = 1 - self.b + self.b * (doc_len / self.avg_doc_len)
                
                # BM25公式
                score += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * norm)
            
            scores.append({
                'doc_id': self.doc_ids[i],
                'doc_index': i,
                'bm25_score': score
            })
        
        # 排序
        scores.sort(key=lambda x: x['bm25_score'], reverse=True)
        
        return scores[:top_k]


class HybridRetriever:
    """
    混合检索器：BM25 + 向量语义检索
    
    策略：
    1. BM25检索 top-100
    2. 向量检索 top-100
    3. 加权融合（BM25:0.3, 向量:0.7）
    4. 重排序返回 top-k
    """
    
    def __init__(self, vector_retriever, bm25_weight: float = 0.3, semantic_weight: float = 0.7):
        """
        Args:
            vector_retriever: 向量检索器实例
            bm25_weight: BM25权重
            semantic_weight: 语义检索权重
        """
        self.vector_retriever = vector_retriever
        self.bm25_retriever = BM25Retriever()
        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight
        
        logger.info(f"混合检索器初始化：BM25权重={bm25_weight}, 语义权重={semantic_weight}")
    
    def build_index(self, documents: List[Dict[str, Any]]):
        """
        构建混合索引
        
        Args:
            documents: 文档列表
        """
        logger.info("开始构建混合检索索引...")
        
        # 构建BM25索引
        self.bm25_retriever.build_index(documents)
        
        logger.info("混合检索索引构建完成")
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        混合检索
        
        Args:
            query: 查询字符串
            top_k: 返回结果数
            
        Returns:
            检索结果列表
        """
        logger.info(f"混合检索：{query}")
        
        # 1. BM25检索
        bm25_results = self.bm25_retriever.search(query, top_k=100)
        bm25_scores = {r['doc_id']: r['bm25_score'] for r in bm25_results}
        
        # 归一化BM25分数（min-max归一化）
        if bm25_scores:
            max_bm25 = max(bm25_scores.values())
            min_bm25 = min(bm25_scores.values())
            if max_bm25 > min_bm25:
                bm25_scores = {
                    doc_id: (score - min_bm25) / (max_bm25 - min_bm25)
                    for doc_id, score in bm25_scores.items()
                }
        
        # 2. 向量语义检索（使用内部方法避免递归）
        semantic_results = self.vector_retriever._pure_vector_search(query, top_k=100)
        semantic_scores = {r['doc_id']: r['score'] for r in semantic_results}
        
        # 归一化语义分数
        if semantic_scores:
            max_sem = max(semantic_scores.values())
            min_sem = min(semantic_scores.values())
            if max_sem > min_sem:
                semantic_scores = {
                    doc_id: (score - min_sem) / (max_sem - min_sem)
                    for doc_id, score in semantic_scores.items()
                }
        
        # 3. 加权融合
        all_doc_ids = set(bm25_scores.keys()) | set(semantic_scores.keys())
        
        hybrid_scores = []
        for doc_id in all_doc_ids:
            bm25_score = bm25_scores.get(doc_id, 0)
            sem_score = semantic_scores.get(doc_id, 0)
            
            # 加权求和
            final_score = (
                self.bm25_weight * bm25_score + 
                self.semantic_weight * sem_score
            )
            
            hybrid_scores.append({
                'doc_id': doc_id,
                'hybrid_score': final_score,
                'bm25_score': bm25_score,
                'semantic_score': sem_score
            })
        
        # 4. 排序
        hybrid_scores.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        # 5. 获取完整文档信息并清理内容
        results = []
        for item in hybrid_scores[:top_k]:
            doc_id = item['doc_id']
            
            # 从向量检索器获取文档信息
            doc_info = self._get_doc_info(doc_id)
            if doc_info:
                # 清理内容
                content = doc_info.get('content', '')
                if hasattr(self.vector_retriever, 'clean_content'):
                    content = self.vector_retriever.clean_content(content)
                
                # 截断内容
                if len(content) > 1500:
                    content = content[:1500]
                
                doc_info['content'] = content
                doc_info['score'] = item['hybrid_score']  # 使用混合分数
                doc_info['hybrid_score'] = item['hybrid_score']
                doc_info['bm25_component'] = item['bm25_score']
                doc_info['semantic_component'] = item['semantic_score']
                
                # 确保包含来源信息
                doc_info['source_doc'] = doc_info.get('source_doc', doc_info.get('title', ''))
                doc_info['chunk_index'] = doc_info.get('chunk_index', 0)
                doc_info['chunk_type'] = doc_info.get('chunk_type', 'paragraph')
                
                results.append(doc_info)
        
        logger.info(f"混合检索完成，返回 {len(results)} 个结果")
        if results:
            top3_scores = [f"{r['hybrid_score']:.3f}" for r in results[:3]]
            logger.debug(f"Top3分数: {top3_scores}")
        
        return results
    
    def _get_doc_info(self, doc_id: str) -> Dict[str, Any]:
        """获取文档完整信息"""
        # 从向量检索器的映射中获取
        if hasattr(self.vector_retriever, 'id_to_knowledge'):
            for idx, doc in self.vector_retriever.id_to_knowledge.items():
                if doc.get('doc_id') == doc_id:
                    return doc.copy()
        return None

