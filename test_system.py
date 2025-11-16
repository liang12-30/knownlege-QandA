"""
系统测试脚本
测试各个模块的功能
"""
import os
import sys
from loguru import logger

import config


def test_document_parser():
    """测试文档解析模块"""
    print("\n" + "="*60)
    print("测试1: 文档解析模块")
    print("="*60)
    
    from document_parser import DocumentParser, KnowledgeBaseBuilder
    
    parser = DocumentParser()
    
    # 测试单个文件
    test_files = []
    
    # 查找测试文件
    if os.path.exists(config.KNOWLEDGE_BASE_DIR):
        import glob
        for ext in ['.pdf', '.docx', '.xlsx']:
            files = glob.glob(os.path.join(config.KNOWLEDGE_BASE_DIR, f"*{ext}"))
            if files:
                test_files.append(files[0])  # 取第一个文件测试
                break
    
    if test_files:
        for file_path in test_files[:1]:  # 只测试一个文件
            print(f"\n解析文件: {os.path.basename(file_path)}")
            result = parser.parse(file_path)
            
            if result:
                print(f"✓ 解析成功")
                print(f"  - 文档ID: {result['doc_id']}")
                print(f"  - 标题: {result['title']}")
                print(f"  - 类型: {result['type']}")
                print(f"  - 内容长度: {len(result.get('content', ''))}")
                print(f"  - 内容预览: {result.get('content', '')[:100]}...")
            else:
                print(f"✗ 解析失败")
    else:
        print("⚠ 未找到测试文件")
    
    # 测试知识库构建
    print("\n构建知识库（解析前5个文件）...")
    builder = KnowledgeBaseBuilder()
    
    if os.path.exists(config.KNOWLEDGE_BASE_DIR):
        import glob
        all_files = []
        for ext in parser.supported_formats:
            all_files.extend(glob.glob(os.path.join(config.KNOWLEDGE_BASE_DIR, f"*{ext}")))
        
        # 只解析前5个文件用于测试
        for i, file_path in enumerate(all_files[:5], 1):
            print(f"  [{i}/5] {os.path.basename(file_path)}")
            result = parser.parse(file_path)
            if result:
                builder.knowledge_base.append(result)
        
        print(f"✓ 知识库构建完成，共 {len(builder.knowledge_base)} 个文档")
        return builder
    else:
        print(f"✗ 知识库目录不存在: {config.KNOWLEDGE_BASE_DIR}")
        return None


def test_intent_understanding():
    """测试意图理解模块"""
    print("\n" + "="*60)
    print("测试2: 意图理解模块")
    print("="*60)
    
    from intent_understanding import IntentClassifier
    
    classifier = IntentClassifier()
    
    test_questions = [
        ("普通查询", "如何开通手机银行？"),
        ("多意图", "个人住房贷款流程和最新LPR利率"),
        ("推理", "月收入8000元，负债2000元，申请50万信用贷款是否合规"),
        ("总结", "总结一下企业网银的主要功能"),
        ("多跳", "客户月收入8000元，申请50万贷款需满足哪些条件？")
    ]
    
    for test_type, question in test_questions:
        print(f"\n[{test_type}] {question}")
        result = classifier.classify(question)
        
        print(f"  意图: {result['primary_intent']}")
        print(f"  实体: {result['entities'][:5]}")  # 只显示前5个
        
        if result['is_multi_intent']:
            print(f"  子问题: {result['split_questions']}")
        
        if result['is_reasoning']:
            print(f"  ✓ 推理问题")
        
        if result['is_summary']:
            print(f"  ✓ 总结问题")
        
        if result['is_multi_hop']:
            print(f"  ✓ 多跳问题")


def test_retrieval_ranking(builder):
    """测试检索与排序模块"""
    print("\n" + "="*60)
    print("测试3: 检索与排序模块")
    print("="*60)
    
    if not builder or not builder.knowledge_base:
        print("⚠ 跳过测试（需要先构建知识库）")
        return None
    
    from retrieval_ranking import VectorRetriever
    
    print("\n构建向量索引...")
    retriever = VectorRetriever()
    retriever.build_index(builder.knowledge_base)
    print(f"✓ 索引构建完成，共 {retriever.index.ntotal} 个向量")
    
    # 测试检索
    test_queries = [
        "如何开通手机银行？",
        "企业网银的主要功能",
        "个人住房贷款流程"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        results = retriever.search(query, top_k=3)
        
        for i, result in enumerate(results, 1):
            print(f"  [{i}] 分数: {result['score']:.4f}")
            print(f"      标题: {result['title']}")
            print(f"      类型: {result['type']}")
            print(f"      内容: {result['content'][:80]}...")
    
    return retriever


def test_summary_generator():
    """测试摘要生成模块"""
    print("\n" + "="*60)
    print("测试4: 摘要生成模块")
    print("="*60)
    
    from summary_generator import TextRankSummarizer
    
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
    
    print(f"\n原文长度: {len(test_text)}")
    
    summary = summarizer.summarize(test_text, max_length=150)
    
    print(f"摘要长度: {len(summary)}")
    print(f"摘要内容:\n{summary}")


def test_full_system():
    """测试完整系统"""
    print("\n" + "="*60)
    print("测试5: 完整系统集成测试")
    print("="*60)
    
    from main import QASystem
    
    print("\n初始化问答系统...")
    qa_system = QASystem()
    
    # 使用已有索引（如果存在）
    print("加载/构建知识库和索引...")
    qa_system.initialize(rebuild_knowledge=False)
    
    if not qa_system.is_ready:
        print("✗ 系统初始化失败")
        return
    
    print("✓ 系统初始化成功")
    
    # 测试问题
    test_questions = [
        "如何开通手机银行？",
        "个人住房贷款流程和最新LPR利率"
    ]
    
    for question in test_questions:
        print(f"\n问题: {question}")
        result = qa_system.answer(question)
        
        print(f"意图: {result['intent']}")
        print(f"知识点数量: {len(result['knowledge_points'])}")
        
        for i, kp in enumerate(result['knowledge_points'], 1):
            print(f"\n[知识点 {i}] (长度: {len(kp)})")
            print(kp[:150] + "..." if len(kp) > 150 else kp)


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("金融多模态知识库问答系统 - 测试脚本")
    print("="*60)
    
    try:
        # 测试1: 文档解析
        builder = test_document_parser()
        
        # 测试2: 意图理解
        test_intent_understanding()
        
        # 测试3: 检索与排序
        retriever = test_retrieval_ranking(builder)
        
        # 测试4: 摘要生成
        test_summary_generator()
        
        # 测试5: 完整系统
        if builder and retriever:
            test_full_system()
        else:
            print("\n⚠ 跳过完整系统测试（需要先构建知识库）")
        
        print("\n" + "="*60)
        print("测试完成！")
        print("="*60)
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

