"""
系统配置文件
"""
import os

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 数据集路径
DATASET_DIR = os.path.join(PROJECT_ROOT, "dataset")
KNOWLEDGE_BASE_DIR = os.path.join(DATASET_DIR, "knowledge_base")
QUERIES_DIR = os.path.join(DATASET_DIR, "queries")

# 输出路径
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
PARSED_KNOWLEDGE_DIR = os.path.join(OUTPUT_DIR, "parsed_knowledge")
RESULT_FILE = os.path.join(PROJECT_ROOT, "result.json")

# 向量库路径
VECTOR_DB_DIR = os.path.join(OUTPUT_DIR, "vector_db")
FAISS_INDEX_PATH = os.path.join(VECTOR_DB_DIR, "knowledge.index")

# 模型配置
# 使用中文金融BERT模型（意图理解）
BERT_MODEL_NAME = "hfl/chinese-roberta-wwm-ext"

# 向量模型配置（检索用）
# ============ 模型选择（根据效果选择） ============
# 推荐使用以下模型之一：

# 【推荐】选项1：BGE - 中文效果最佳，适合金融领域
SENTENCE_TRANSFORMER_MODEL = "BAAI/bge-large-zh-v1.5"

# 选项2：text2vec - 轻量级，速度快
# SENTENCE_TRANSFORMER_MODEL = "shibing624/text2vec-base-chinese"

# 选项3：text2vec-large - 平衡效果和速度
# SENTENCE_TRANSFORMER_MODEL = "GanymedeNil/text2vec-large-chinese"

# 选项4：多语言模型（不推荐用于中文）
# SENTENCE_TRANSFORMER_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# 选项5：SimCSE（如需测试）
# SENTENCE_TRANSFORMER_MODEL = "princeton-nlp/sup-simcse-bert-base-uncased"

# OCR配置
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Windows默认路径
# Linux/Mac用户请修改为: "/usr/bin/tesseract"

# 检索配置（核心参数）
TOP_K = 3  # 返回Top3知识点
MAX_KNOWLEDGE_LENGTH = 1500  # 单知识点最大长度
MAX_SUMMARY_LENGTH = 300  # 摘要最大长度

# 知识分块配置（优化后）
CHUNK_SIZE = 500  # 每个知识片段大小（字符）从800调整为500，更精准
CHUNK_OVERLAP = 150  # 片段间重叠大小，从100提高到150，保持更好的上下文连贯性

# 相似度阈值（提高以确保精准度）
SIMILARITY_THRESHOLD = 0.5  # 从0.3提高到0.5，遵循精准度>速度原则

# 检索策略配置（新增）
USE_MULTI_STRATEGY = True  # 是否使用多策略检索
USE_KEYWORD_BOOST = True  # 是否使用关键词增强
KEYWORD_BOOST_WEIGHT = 0.15  # 关键词匹配权重

# 混合检索配置（BM25 + 语义）
# 注意：如果遇到递归深度错误，可以暂时设为False，只使用语义检索
USE_HYBRID_RETRIEVAL = True  # 是否使用混合检索（强烈推荐）
BM25_WEIGHT = 0.3  # BM25权重
SEMANTIC_WEIGHT = 0.7  # 语义检索权重

# 日志配置
LOG_FILE = os.path.join(OUTPUT_DIR, "system.log")

# 创建必要的目录
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PARSED_KNOWLEDGE_DIR, exist_ok=True)
os.makedirs(VECTOR_DB_DIR, exist_ok=True)

