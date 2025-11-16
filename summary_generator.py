"""
摘要生成模块
使用TextRank算法生成摘要
"""
import re
from typing import List, Dict, Any, Tuple
import jieba
import jieba.analyse
from loguru import logger

import config


class TextRankSummarizer:
    """TextRank摘要生成器"""
    
    def __init__(self):
        """初始化摘要生成器"""
        # 使用jieba默认配置即可
        pass
    
    def summarize(self, text: str, max_length: int = None) -> str:
        """
        生成文本摘要
        
        Args:
            text: 输入文本
            max_length: 最大摘要长度
            
        Returns:
            摘要文本
        """
        if max_length is None:
            max_length = config.MAX_SUMMARY_LENGTH
        
        if not text or len(text) <= max_length:
            return text
        
        logger.info(f"开始生成摘要，原文长度: {len(text)}, 目标长度: {max_length}")
        
        # 分句
        sentences = self._split_sentences(text)
        
        if len(sentences) <= 3:
            # 句子太少，直接返回截断
            summary = text[:max_length]
            logger.info(f"句子数量少，直接截断")
            return summary
        
        # 使用TextRank提取关键句
        sentence_scores = self._textrank_sentences(sentences)
        
        # 按分数排序，选择Top句子
        sorted_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 选择关键句，直到达到长度限制
        selected_sentences = []
        total_length = 0
        
        for sent, score in sorted_sentences:
            if total_length + len(sent) <= max_length:
                selected_sentences.append((sent, sentences.index(sent)))
                total_length += len(sent)
            
            if total_length >= max_length * 0.8:  # 达到80%即可
                break
        
        # 按原文顺序排序
        selected_sentences.sort(key=lambda x: x[1])
        
        # 生成摘要
        summary = "".join([sent for sent, _ in selected_sentences])
        
        # 如果还是太长，强制截断
        if len(summary) > max_length:
            summary = summary[:max_length]
        
        logger.info(f"摘要生成完成，长度: {len(summary)}")
        return summary
    
    def summarize_multiple(self, texts: List[str], max_length: int = None) -> str:
        """
        合并多个文本并生成摘要
        
        Args:
            texts: 文本列表
            max_length: 最大摘要长度
            
        Returns:
            摘要文本
        """
        # 合并文本
        combined_text = "\n".join(texts)
        
        # 生成摘要
        return self.summarize(combined_text, max_length)
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        分句
        
        Args:
            text: 输入文本
            
        Returns:
            句子列表
        """
        # 使用正则表达式分句
        # 按句号、问号、感叹号、换行符分割
        sentences = re.split(r'[。！？\n]+', text)
        
        # 清理空句子和太短的句子
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
        
        return sentences
    
    def _textrank_sentences(self, sentences: List[str]) -> Dict[str, float]:
        """
        使用TextRank算法计算句子分数
        
        Args:
            sentences: 句子列表
            
        Returns:
            句子分数字典 {sentence: score}
        """
        # 计算句子的关键词
        sentence_keywords = {}
        for sent in sentences:
            # 使用jieba提取关键词
            keywords = jieba.analyse.extract_tags(sent, topK=10, withWeight=True)
            sentence_keywords[sent] = dict(keywords)
        
        # 构建句子相似度矩阵
        sentence_scores = {sent: 0.0 for sent in sentences}
        
        for i, sent1 in enumerate(sentences):
            for j, sent2 in enumerate(sentences):
                if i != j:
                    # 计算两个句子的相似度（基于关键词重叠）
                    similarity = self._calculate_similarity(
                        sentence_keywords.get(sent1, {}),
                        sentence_keywords.get(sent2, {})
                    )
                    sentence_scores[sent1] += similarity
        
        # 归一化分数
        max_score = max(sentence_scores.values()) if sentence_scores else 1.0
        if max_score > 0:
            sentence_scores = {k: v / max_score for k, v in sentence_scores.items()}
        
        return sentence_scores
    
    def _calculate_similarity(self, keywords1: Dict[str, float], keywords2: Dict[str, float]) -> float:
        """
        计算两个关键词集合的相似度
        
        Args:
            keywords1: 关键词1
            keywords2: 关键词2
            
        Returns:
            相似度分数
        """
        if not keywords1 or not keywords2:
            return 0.0
        
        # 计算交集权重
        common_keywords = set(keywords1.keys()) & set(keywords2.keys())
        
        if not common_keywords:
            return 0.0
        
        # 相似度 = 共同关键词的权重和
        similarity = sum(keywords1[k] + keywords2[k] for k in common_keywords)
        
        # 归一化
        total_weight = sum(keywords1.values()) + sum(keywords2.values())
        if total_weight > 0:
            similarity /= total_weight
        
        return similarity


class KeywordExtractor:
    """关键词提取器"""
    
    def __init__(self):
        """初始化关键词提取器"""
        pass
    
    def extract(self, text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        提取关键词
        
        Args:
            text: 输入文本
            top_k: 返回top k个关键词
            
        Returns:
            关键词列表 [(keyword, weight)]
        """
        # 使用jieba的TF-IDF提取关键词
        keywords = jieba.analyse.extract_tags(text, topK=top_k, withWeight=True)
        return keywords
    
    def extract_from_multiple(self, texts: List[str], top_k: int = 10) -> List[Tuple[str, float]]:
        """
        从多个文本中提取关键词
        
        Args:
            texts: 文本列表
            top_k: 返回top k个关键词
            
        Returns:
            关键词列表
        """
        # 合并文本
        combined_text = "\n".join(texts)
        
        # 提取关键词
        return self.extract(combined_text, top_k)


if __name__ == "__main__":
    # 测试代码
    summarizer = TextRankSummarizer()
    
    test_text = """
    个人住房贷款是指银行向借款人发放的用于购买自用普通住房的贷款。
    借款人申请个人住房贷款时必须提供担保。
    个人住房贷款主要有委托贷款、自营贷款和组合贷款三种。
    委托贷款是指住房公积金管理中心运用住房公积金，委托商业性银行发放的个人住房贷款。
    自营贷款是指以银行信贷资金为来源向购房者个人发放的贷款。
    组合贷款是指以住房公积金存款和信贷资金为来源向同一借款人发放的用于购买自用普通住房的贷款。
    贷款条件包括：有合法的身份证明；有稳定的经济收入，信用良好；有购买住房的合同或协议；
    提出贷款申请时，在建行有不低于购买住房所需资金30%的存款，若已作购房预付款支付给售房单位的，
    则需提供付款收据的原件和复印件；借款人同意以所购房屋及其权益作为抵押物。
    """
    
    summary = summarizer.summarize(test_text, max_length=150)
    print(f"原文长度: {len(test_text)}")
    print(f"摘要长度: {len(summary)}")
    print(f"摘要内容:\n{summary}")
    
    # 测试关键词提取
    extractor = KeywordExtractor()
    keywords = extractor.extract(test_text, top_k=5)
    print(f"\n关键词:")
    for keyword, weight in keywords:
        print(f"  {keyword}: {weight:.4f}")

