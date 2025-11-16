"""
快速启动脚本
自动检测环境并执行完整流程
"""
import os
import sys
import time
from loguru import logger


def check_environment():
    """检查环境"""
    print("\n" + "="*60)
    print("步骤1: 检查环境")
    print("="*60)
    
    issues = []
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"\nPython版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 10):
        issues.append("Python版本需要 >= 3.10")
    else:
        print("[OK] Python版本符合要求")
    
    # 检查必要的库
    required_packages = [
        'docx', 'PyPDF2', 'pdfplumber', 'pandas', 'openpyxl',
        'PIL', 'jieba', 'numpy', 'transformers', 'sentence_transformers',
        'faiss', 'fastapi', 'loguru'
    ]
    
    missing_packages = []
    
    print("\n检查依赖包...")
    for package in required_packages:
        try:
            if package == 'docx':
                import docx
            elif package == 'PIL':
                from PIL import Image
            else:
                __import__(package.replace('-', '_'))
            print(f"[OK] {package}")
        except ImportError:
            print(f"[X] {package} (缺失)")
            missing_packages.append(package)
    
    if missing_packages:
        issues.append(f"缺少依赖包: {', '.join(missing_packages)}")
        print(f"\n请运行: pip install -r requirements.txt")
    
    # 检查数据集
    import config
    
    print("\n检查数据集...")
    if os.path.exists(config.KNOWLEDGE_BASE_DIR):
        files = os.listdir(config.KNOWLEDGE_BASE_DIR)
        doc_files = [f for f in files if not f.startswith('.')]
        print(f"[OK] 知识库目录存在，包含 {len(doc_files)} 个文件")
    else:
        issues.append(f"知识库目录不存在: {config.KNOWLEDGE_BASE_DIR}")
    
    if issues:
        print("\n" + "!"*60)
        print("发现以下问题:")
        for issue in issues:
            print(f"  - {issue}")
        print("!"*60)
        return False
    else:
        print("\n" + "="*60)
        print("[OK] 环境检查通过")
        print("="*60)
        return True


def build_knowledge_base():
    """构建知识库"""
    print("\n" + "="*60)
    print("步骤2: 构建知识库")
    print("="*60)
    
    import config
    from document_parser import KnowledgeBaseBuilder
    
    knowledge_path = os.path.join(config.PARSED_KNOWLEDGE_DIR, "knowledge_base.json")
    
    # 检查是否已存在
    if os.path.exists(knowledge_path):
        print(f"\n发现已有知识库: {knowledge_path}")
        choice = input("是否重新构建？(y/N): ").strip().lower()
        
        if choice != 'y':
            print("跳过构建，使用已有知识库")
            return True
    
    print("\n开始解析文档...")
    print("(这可能需要几分钟时间，请耐心等待)")
    
    try:
        builder = KnowledgeBaseBuilder()
        knowledge_base = builder.build_from_directory(config.KNOWLEDGE_BASE_DIR)
        
        if not knowledge_base:
            print("[X] 知识库为空")
            return False
        
        # 保存
        builder.save_to_json(knowledge_path)
        
        print(f"\n[OK] 知识库构建完成")
        print(f"  - 文档数量: {len(knowledge_base)}")
        print(f"  - 保存位置: {knowledge_path}")
        
        return True
        
    except Exception as e:
        print(f"\n[X] 构建失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def build_vector_index():
    """构建向量索引"""
    print("\n" + "="*60)
    print("步骤3: 构建向量索引")
    print("="*60)
    
    import config
    from document_parser import KnowledgeBaseBuilder
    from retrieval_ranking import VectorRetriever
    
    # 检查是否已存在
    if os.path.exists(config.FAISS_INDEX_PATH):
        print(f"\n发现已有索引: {config.FAISS_INDEX_PATH}")
        choice = input("是否重新构建？(y/N): ").strip().lower()
        
        if choice != 'y':
            print("跳过构建，使用已有索引")
            return True
    
    print("\n开始构建向量索引...")
    print("(首次运行会下载模型，可能需要较长时间)")
    
    try:
        # 加载知识库
        builder = KnowledgeBaseBuilder()
        knowledge_path = os.path.join(config.PARSED_KNOWLEDGE_DIR, "knowledge_base.json")
        builder.load_from_json(knowledge_path)
        
        # 构建索引
        retriever = VectorRetriever()
        retriever.build_index(builder.knowledge_base)
        
        # 保存索引
        retriever.save_index()
        
        print(f"\n[OK] 向量索引构建完成")
        print(f"  - 向量数量: {retriever.index.ntotal}")
        print(f"  - 保存位置: {config.FAISS_INDEX_PATH}")
        
        return True
        
    except Exception as e:
        print(f"\n[X] 构建失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def generate_results():
    """生成结果"""
    print("\n" + "="*60)
    print("步骤4: 生成结果文件")
    print("="*60)
    
    print("\n开始处理测试问题...")
    
    try:
        import generate_result
        
        # 执行主函数
        generate_result.main()
        
        print(f"\n[OK] 结果文件生成完成")
        print(f"  - 文件位置: result.json")
        
        return True
        
    except Exception as e:
        print(f"\n[X] 生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("金融多模态知识库问答系统 - 快速启动")
    print("="*60)
    
    start_time = time.time()
    
    # 步骤1: 检查环境
    if not check_environment():
        print("\n请先解决环境问题")
        return
    
    # 步骤2: 构建知识库
    if not build_knowledge_base():
        print("\n知识库构建失败，无法继续")
        return
    
    # 步骤3: 构建向量索引
    if not build_vector_index():
        print("\n向量索引构建失败，无法继续")
        return
    
    # 步骤4: 生成结果
    if not generate_results():
        print("\n结果生成失败")
        return
    
    # 完成
    elapsed_time = time.time() - start_time
    
    print("\n" + "="*60)
    print("[OK] 全部完成！")
    print("="*60)
    print(f"\n总耗时: {elapsed_time/60:.1f} 分钟")
    print(f"\n结果文件: result.json")
    print("\n后续使用:")
    print("  - 运行测试: python test_system.py")
    print("  - 启动API: python api_server.py")
    print("  - 重新生成: python generate_result.py")
    print("\n详细说明请查看: USAGE.md")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n\n发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

