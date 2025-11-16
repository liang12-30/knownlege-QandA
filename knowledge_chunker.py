"""
知识分块模块
实现细粒度知识切分，提高检索精准度
遵循原则：碎片精准度 > 检索速度
"""
import re
from typing import List, Dict, Tuple
import jieba.analyse
from loguru import logger


class KnowledgeChunker:
    """
    知识分块器：将文档切分为细粒度片段
    
    策略：
    1. 按标题层级分块（一、二、三级标题）
    2. 按表格边界分块
    3. 按段落语义分块
    4. 控制每块大小在 chunk_size 范围内（800字）
    5. 保留上下文重叠（overlap 100字）
    """
    
    def __init__(self, chunk_size: int = 800, overlap: int = 100):
        """
        Args:
            chunk_size: 每个片段的目标大小（字符数）默认800
            overlap: 片段间重叠大小，保持上下文连贯性，默认100
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        
        # 标题模式识别
        self.title_patterns = [
            r'^第?[一二三四五六七八九十百千]+[章节条款项]',  # 第一章、第二节
            r'^[一二三四五六七八九十]+、',  # 一、二、三、
            r'^\d+\.',  # 1. 2. 3.
            r'^（[一二三四五六七八九十]+）',  # （一）（二）
            r'^\([一二三四五六七八九十]+\)',  # (一)(二)
            r'^\d+\)\s',  # 1) 2)
            r'^\d+）',  # 1）2）
        ]
    
    def chunk_by_structure(self, content: str, title: str) -> List[Dict]:
        """
        基于文档结构进行智能分块
        
        Args:
            content: 文档内容
            title: 文档标题
            
        Returns:
            分块结果列表，每块包含：
            - chunk_content: 片段内容
            - chunk_title: 片段标题
            - chunk_type: 片段类型（title_section/table/paragraph）
            - keywords: 关键词列表
            - entities: 实体列表
        """
        chunks = []
        
        # 清理内容
        content = self._preprocess_content(content)
        
        # 分行处理
        lines = content.split('\n')
        
        current_chunk = ""
        current_title = title
        current_type = "paragraph"
        chunk_count = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if not line:
                continue
            
            # 检测标题
            is_title = self._is_title_line(line)
            
            # 检测表格
            is_table = self._is_table_line(line)
            
            # 如果遇到新标题或表格，且当前块有内容，保存当前块
            if (is_title or is_table) and current_chunk:
                if len(current_chunk) >= 200:  # 至少200字才保存
                    chunk_dict = self._create_chunk(
                        current_chunk, 
                        current_title, 
                        current_type,
                        title,
                        chunk_count
                    )
                    chunks.append(chunk_dict)
                    chunk_count += 1
                
                current_chunk = ""
            
            # 更新当前标题和类型
            if is_title:
                current_title = line
                current_type = "title_section"
            elif is_table:
                current_type = "table"
            else:
                current_type = "paragraph"
            
            # 添加到当前块
            current_chunk += line + "\n"
            
            # 如果当前块太大，需要切分
            if len(current_chunk) >= self.chunk_size:
                chunk_dict = self._create_chunk(
                    current_chunk, 
                    current_title, 
                    current_type,
                    title,
                    chunk_count
                )
                chunks.append(chunk_dict)
                chunk_count += 1
                
                # 保留重叠部分（保持上下文连贯）
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text
        
        # 保存最后一块
        if current_chunk and len(current_chunk) >= 200:
            chunk_dict = self._create_chunk(
                current_chunk, 
                current_title, 
                current_type,
                title,
                chunk_count
            )
            chunks.append(chunk_dict)
        
        logger.info(f"文档 '{title}' 切分为 {len(chunks)} 个片段")
        return chunks
    
    def _preprocess_content(self, content: str) -> str:
        """预处理内容"""
        # 去除多余空白行
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content
    
    def _is_title_line(self, line: str) -> bool:
        """判断是否为标题行"""
        for pattern in self.title_patterns:
            if re.match(pattern, line):
                return True
        
        # 额外判断：短行且不以标点结尾
        if len(line) < 30 and not line.endswith(('。', '！', '？', '；', '.', '!', '?', ';', '，', ',')):
            # 检查是否包含标题关键词
            title_keywords = ['概述', '简介', '说明', '流程', '步骤', '要求', '规定', '办法', '指南', '手册']
            if any(kw in line for kw in title_keywords):
                return True
        
        return False
    
    def _is_table_line(self, line: str) -> bool:
        """判断是否为表格行"""
        # 检测表格标记
        if '[表格-' in line or '[表-' in line:
            return True
        
        # 检测表格分隔符（多个|符号）
        if line.count('|') >= 3:
            return True
        
        return False
    
    def _get_overlap_text(self, text: str) -> str:
        """获取重叠文本（保留最后overlap字符）"""
        if len(text) <= self.overlap:
            return text
        
        # 从后往前找句子边界
        overlap_start = len(text) - self.overlap
        
        # 尝试在句号、问号、感叹号处切分
        for i in range(overlap_start, len(text)):
            if text[i] in ('。', '！', '？', '.', '!', '?'):
                return text[i+1:].strip()
        
        # 如果找不到句子边界，直接截取
        return text[-self.overlap:]
    
    def _create_chunk(self, content: str, chunk_title: str, 
                     chunk_type: str, doc_title: str, chunk_index: int) -> Dict:
        """
        创建知识片段
        
        Args:
            content: 片段内容
            chunk_title: 片段标题
            chunk_type: 片段类型
            doc_title: 原文档标题
            chunk_index: 片段索引
            
        Returns:
            知识片段字典
        """
        content = content.strip()
        
        # 提取关键词（用于后续检索增强）
        keywords = jieba.analyse.extract_tags(content, topK=10, withWeight=False)
        
        # 提取实体（金融实体识别）
        entities = self._extract_financial_entities(content)
        
        # 计算片段重要性（基于关键词密度）
        importance_score = self._calculate_importance(content, keywords)
        
        return {
            'chunk_content': content,
            'chunk_title': chunk_title,
            'doc_title': doc_title,
            'chunk_type': chunk_type,
            'chunk_index': chunk_index,
            'keywords': keywords,
            'entities': entities,
            'importance_score': importance_score,
            'length': len(content)
        }
    
    def _extract_financial_entities(self, text: str) -> List[str]:
        """
        提取金融实体
        
        实体类型：
        - 金额：数字+单位
        - 百分比：数字+%
        - 日期：年月日
        - 产品名称：理财、贷款、信用卡等
        - 机构名称：银行、保险公司等
        """
        entities = []
        
        # 金融关键词模式
        patterns = {
            'amount': r'(\d+\.?\d*)\s*[万亿千百]*元',
            'percentage': r'(\d+\.?\d*)\s*%',
            'rate': r'(\d+\.?\d*)\s*[个百]*[基点|BP|bp]',
            'date': r'\d{4}\s*年\s*\d{1,2}\s*月|\d{4}\s*年',
            'product': r'(理财产品|信用卡|贷款|保险|基金|债券|股票|期货)',
            'bank': r'(中国[银行工商农业建设交通招商]银行|[工农中建交招商浦发民生兴业光大华夏平安]银行|太保|太平洋保险|中国人寿)',
            'account': r'(账户|账号|卡号|户名)',
            'term': r'(\d+)\s*(年|月|日|天|周)',
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                # 格式化实体
                for match in matches[:5]:  # 每类最多5个
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else match[1] if len(match) > 1 else ''
                    if match:
                        entities.append(f"{entity_type}:{match}")
        
        return entities[:20]  # 总共最多20个实体
    
    def _calculate_importance(self, content: str, keywords: List[str]) -> float:
        """
        计算片段重要性得分
        
        因素：
        1. 关键词密度
        2. 包含数字和金额
        3. 包含标题关键词
        """
        score = 0.0
        
        # 关键词密度
        keyword_count = sum(content.count(kw) for kw in keywords)
        score += keyword_count * 0.1
        
        # 包含数字或金额
        if re.search(r'\d+', content):
            score += 0.5
        
        # 包含重要关键词
        important_keywords = ['流程', '步骤', '要求', '条件', '标准', '金额', '利率', '期限']
        for kw in important_keywords:
            if kw in content:
                score += 0.3
        
        return min(score, 5.0)  # 最高5分
    
    def chunk_table(self, table_content: str, table_title: str) -> Dict:
        """
        专门处理表格内容
        
        表格策略：
        1. 保留表头信息
        2. 提取数值关系
        3. 转化为文字描述
        """
        # 提取关键词
        keywords = jieba.analyse.extract_tags(table_content, topK=10)
        
        # 提取实体
        entities = self._extract_financial_entities(table_content)
        
        return {
            'chunk_content': table_content,
            'chunk_title': f"{table_title} [表格]",
            'chunk_type': 'table',
            'keywords': keywords,
            'entities': entities,
            'importance_score': 2.0  # 表格通常比较重要
        }

