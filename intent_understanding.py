"""
意图理解模块
处理多意图问题、推理问题、总结类问题
"""
import re
from typing import List, Dict, Any, Tuple
import jieba
import jieba.posseg as pseg
from loguru import logger


class IntentClassifier:
    """意图分类器"""
    
    def __init__(self):
        """初始化意图分类器"""
        # 定义意图类型
        self.intent_types = {
            'query': '查询',
            'reasoning': '推理',
            'summary': '总结',
            'multi_intent': '多意图',
            'multi_hop': '多跳'
        }
        
        # 多意图关键词（连接词）
        self.multi_intent_keywords = [
            '和', '与', '以及', '还有', '同时', '并且', '或者', '或',
            '、', '，', ',', '；', ';'
        ]
        
        # 推理关键词
        self.reasoning_keywords = [
            '是否', '能否', '可以吗', '合规', '符合', '满足',
            '达到', '需要', '条件', '要求', '资格',
            '判断', '分析', '评估', '计算'
        ]
        
        # 总结关键词
        self.summary_keywords = [
            '总结', '归纳', '概括', '汇总', '整理',
            '梳理', '列举', '有哪些', '包括', '介绍'
        ]
        
        # 多跳关键词（需要多步推理）
        self.multi_hop_keywords = [
            '需要满足哪些条件', '需要什么条件', '如何申请',
            '怎么办理', '流程是什么', '步骤'
        ]
        
        # 金融实体关键词（用于识别金融术语）
        self.financial_entities = [
            '贷款', '信用贷款', '住房贷款', '车贷', '房贷',
            '利率', 'LPR', '存款', '理财', '保险',
            '网银', '手机银行', '企业网银', '个人网银',
            '证券', '基金', '股票', '债券',
            '账户', '转账', '支付', '收款',
            '申请', '审批', '办理', '开通'
        ]
    
    def classify(self, question: str) -> Dict[str, Any]:
        """
        分类问题意图
        
        Args:
            question: 用户问题
            
        Returns:
            意图分类结果
        """
        logger.info(f"开始分析问题意图: {question}")
        
        result = {
            'question': question,
            'primary_intent': 'query',  # 默认为查询
            'sub_intents': [],
            'is_multi_intent': False,
            'is_reasoning': False,
            'is_summary': False,
            'is_multi_hop': False,
            'entities': [],
            'split_questions': []
        }
        
        # 1. 检测是否为多意图问题
        if self._is_multi_intent(question):
            result['is_multi_intent'] = True
            result['primary_intent'] = 'multi_intent'
            result['split_questions'] = self._split_multi_intent(question)
            result['sub_intents'] = [self._get_sub_intent(q) for q in result['split_questions']]
        
        # 2. 检测是否为推理问题
        if self._is_reasoning(question):
            result['is_reasoning'] = True
            if result['primary_intent'] == 'query':
                result['primary_intent'] = 'reasoning'
        
        # 3. 检测是否为总结类问题
        if self._is_summary(question):
            result['is_summary'] = True
            if result['primary_intent'] == 'query':
                result['primary_intent'] = 'summary'
        
        # 4. 检测是否为多跳问题
        if self._is_multi_hop(question):
            result['is_multi_hop'] = True
            if result['primary_intent'] == 'query':
                result['primary_intent'] = 'multi_hop'
        
        # 5. 提取金融实体
        result['entities'] = self._extract_entities(question)
        
        logger.info(f"意图分析完成: {result['primary_intent']}, "
                   f"多意图={result['is_multi_intent']}, "
                   f"推理={result['is_reasoning']}, "
                   f"总结={result['is_summary']}, "
                   f"多跳={result['is_multi_hop']}")
        
        return result
    
    def _is_multi_intent(self, question: str) -> bool:
        """判断是否为多意图问题"""
        # 检查是否包含连接词
        for keyword in self.multi_intent_keywords:
            if keyword in question:
                # 进一步验证：确保不是单纯的列举
                # 例如："A和B" vs "什么和什么"
                parts = question.split(keyword)
                if len(parts) >= 2 and len(parts[0]) > 3 and len(parts[1]) > 3:
                    return True
        return False
    
    def _is_reasoning(self, question: str) -> bool:
        """判断是否为推理问题"""
        for keyword in self.reasoning_keywords:
            if keyword in question:
                return True
        
        # 检查是否包含数字+条件的组合（如："月收入8000元，申请50万贷款"）
        if re.search(r'\d+.*[元万千百]', question) and any(k in question for k in ['申请', '贷款', '条件']):
            return True
        
        return False
    
    def _is_summary(self, question: str) -> bool:
        """判断是否为总结类问题"""
        for keyword in self.summary_keywords:
            if keyword in question:
                return True
        return False
    
    def _is_multi_hop(self, question: str) -> bool:
        """判断是否为多跳问题"""
        for keyword in self.multi_hop_keywords:
            if keyword in question:
                return True
        
        # 检查是否同时包含多个查询目标
        if self._is_reasoning(question) and any(k in question for k in ['条件', '要求', '资格']):
            return True
        
        return False
    
    def _split_multi_intent(self, question: str) -> List[str]:
        """
        拆分多意图问题
        
        Returns:
            子问题列表
        """
        sub_questions = []
        
        # 尝试按连接词拆分
        for keyword in self.multi_intent_keywords:
            if keyword in question:
                parts = question.split(keyword)
                if len(parts) >= 2:
                    # 清理和验证拆分结果
                    for part in parts:
                        part = part.strip()
                        if len(part) > 2:  # 过滤太短的片段
                            # 补充问号
                            if not part.endswith('?') and not part.endswith('？'):
                                part += '？'
                            sub_questions.append(part)
                    break
        
        # 如果拆分失败，返回原问题
        if not sub_questions:
            sub_questions = [question]
        
        return sub_questions
    
    def _get_sub_intent(self, question: str) -> str:
        """获取子问题的意图"""
        if self._is_reasoning(question):
            return 'reasoning'
        elif self._is_summary(question):
            return 'summary'
        else:
            return 'query'
    
    def _extract_entities(self, question: str) -> List[str]:
        """
        提取金融实体
        
        Returns:
            实体列表
        """
        entities = []
        
        # 1. 匹配预定义的金融实体
        for entity in self.financial_entities:
            if entity in question:
                entities.append(entity)
        
        # 2. 使用jieba提取名词短语
        words = pseg.cut(question)
        for word, flag in words:
            # 提取名词（n开头的词性）
            if flag.startswith('n') and len(word) > 1:
                if word not in entities:
                    entities.append(word)
        
        # 3. 提取数字+单位的组合（如："8000元"，"50万"）
        numbers = re.findall(r'\d+(?:\.\d+)?[元万千百亿兆年月日%％个人次]', question)
        entities.extend(numbers)
        
        return list(set(entities))  # 去重


class ReasoningEngine:
    """推理引擎"""
    
    def __init__(self):
        """初始化推理引擎"""
        # 定义推理规则（示例）
        self.reasoning_rules = {
            '信用贷款': {
                '月收入要求': 5000,  # 最低月收入
                '负债比例': 0.5,     # 最大负债比例
                '贷款倍数': 10        # 月收入的倍数
            }
        }
    
    def reason(self, question: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        执行推理
        
        Args:
            question: 问题
            context: 上下文知识
            
        Returns:
            推理结果
        """
        result = {
            'conclusion': '',
            'reasoning_steps': [],
            'evidence': []
        }
        
        # 提取问题中的数据
        income = self._extract_income(question)
        debt = self._extract_debt(question)
        loan_amount = self._extract_loan_amount(question)
        
        if income and loan_amount:
            # 执行推理
            steps = []
            
            # 步骤1：检查收入要求
            min_income = self.reasoning_rules['信用贷款']['月收入要求']
            if income >= min_income:
                steps.append(f"月收入{income}元 >= 最低要求{min_income}元，收入符合要求")
                income_ok = True
            else:
                steps.append(f"月收入{income}元 < 最低要求{min_income}元，收入不符合要求")
                income_ok = False
            
            # 步骤2：检查负债比例
            if debt:
                debt_ratio = debt / income
                max_debt_ratio = self.reasoning_rules['信用贷款']['负债比例']
                if debt_ratio <= max_debt_ratio:
                    steps.append(f"负债比例{debt_ratio:.2%} <= 最大允许{max_debt_ratio:.2%}，负债比例符合要求")
                    debt_ok = True
                else:
                    steps.append(f"负债比例{debt_ratio:.2%} > 最大允许{max_debt_ratio:.2%}，负债比例不符合要求")
                    debt_ok = False
            else:
                debt_ok = True
                steps.append("未提供负债信息，假设负债比例符合要求")
            
            # 步骤3：检查贷款额度
            max_loan = income * self.reasoning_rules['信用贷款']['贷款倍数']
            if loan_amount <= max_loan:
                steps.append(f"申请贷款{loan_amount}元 <= 最大额度{max_loan}元，贷款额度符合要求")
                amount_ok = True
            else:
                steps.append(f"申请贷款{loan_amount}元 > 最大额度{max_loan}元，贷款额度不符合要求")
                amount_ok = False
            
            # 得出结论
            if income_ok and debt_ok and amount_ok:
                result['conclusion'] = "符合信用贷款条件"
            else:
                result['conclusion'] = "不符合信用贷款条件"
            
            result['reasoning_steps'] = steps
        
        return result
    
    def _extract_income(self, text: str) -> float:
        """提取月收入"""
        match = re.search(r'月收入[\s]*(\d+(?:\.\d+)?)[元万]?', text)
        if match:
            value = float(match.group(1))
            if '万' in match.group(0):
                value *= 10000
            return value
        return None
    
    def _extract_debt(self, text: str) -> float:
        """提取负债"""
        match = re.search(r'负债[\s]*(\d+(?:\.\d+)?)[元万]?', text)
        if match:
            value = float(match.group(1))
            if '万' in match.group(0):
                value *= 10000
            return value
        return None
    
    def _extract_loan_amount(self, text: str) -> float:
        """提取贷款金额"""
        match = re.search(r'申请[\s]*(\d+(?:\.\d+)?)[元万]?[\s]*贷款', text)
        if match:
            value = float(match.group(1))
            if '万' in match.group(0):
                value *= 10000
            return value
        return None


if __name__ == "__main__":
    # 测试代码
    classifier = IntentClassifier()
    
    # 测试用例
    test_questions = [
        "个人住房贷款流程和最新LPR利率",
        "月收入8000元，负债2000元，申请50万信用贷款是否合规",
        "总结一下企业网银的主要功能",
        "如何开通手机银行？",
        "客户月收入8000元，申请50万贷款需满足哪些条件？"
    ]
    
    for question in test_questions:
        print(f"\n问题: {question}")
        result = classifier.classify(question)
        print(f"主要意图: {result['primary_intent']}")
        print(f"实体: {result['entities']}")
        if result['is_multi_intent']:
            print(f"子问题: {result['split_questions']}")

