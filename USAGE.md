#交付之readme
# 金融多模态知识库构建与复杂问答检索系统 - 使用说明

## 项目简介

本项目是针对AiC2025赛题开发的金融多模态知识库构建与复杂问答检索系统，实现了以下核心功能：

1. **文档解析模块**：支持 `.docx`, `.pdf`, `.xlsx`, `.pptx`, `.txt`, `.md`, `.png`, `.jpeg` 等多种格式
2. **意图理解模块**：支持多意图拆解、推理问题、总结类问题识别
3. **检索与排序模块**：基于FAISS的向量检索，返回Top3知识点
4. **摘要生成模块**：基于TextRank算法的自动摘要
5. **多跳推理模块**：支持多步推理问题

## 系统要求

### 环境要求
- Python 3.10+
- Windows/Linux/MacOS

### 依赖库
所有依赖已列在 `requirements.txt` 文件中。

### OCR支持（可选）
如需解析图片文件，需要安装Tesseract-OCR：
- **Windows**: 下载安装 [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki)
- **Linux**: `sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim`
- **MacOS**: `brew install tesseract tesseract-lang`

安装后，修改 `config.py` 中的 `TESSERACT_CMD` 路径。

## 安装步骤

### 1. 克隆或下载项目
```bash
cd economic_QandA_2.0
```

### 2. 创建虚拟环境（推荐）
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/MacOS
source venv/bin/activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

**注意**：部分依赖（如detectron2）可能需要特殊安装步骤，如遇到问题可跳过，不影响核心功能。

### 4. 下载模型（首次运行自动下载）
首次运行时，系统会自动下载以下模型：
- `hfl/chinese-roberta-wwm-ext`（中文BERT）
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`（向量化模型）

## 使用方法

### 方式一：生成结果文件（推荐）

直接运行主脚本生成 `result.json`：

```bash
python generate_result.py
```

该脚本会：
1. 自动解析 `dataset/knowledge_base/` 目录下的所有文档
2. 构建向量索引
3. 读取 `dataset/queries/100条测试集（初赛）.xlsx`
4. 生成 `result.json` 文件

**首次运行**：会构建知识库和索引，耗时较长（约10-30分钟）
**后续运行**：直接加载已有索引，速度较快（约2-5分钟）

### 方式二：命令行交互

```bash
python main.py
```

运行后可以在代码中修改测试问题。

### 方式三：API服务

启动FastAPI服务器：

```bash
python api_server.py
```

服务器启动后访问：
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

**API接口示例**：

```bash
# 单个问题
curl -X POST "http://localhost:8000/answer" \
  -H "Content-Type: application/json" \
  -d '{"question": "请详细说明掌上银行中“基金”功能的主要服务内容以及进行基金认购的具体操作流程。"}'

# 批量问题
curl -X POST "http://localhost:8000/batch_answer" \
  -H "Content-Type: application/json" \
  -d '{"questions": ["问题1", "问题2", "问题3"]}'
```

## 项目结构

```
economic_QandA_2.0/
├── config.py                    # 配置文件
├── document_parser.py           # 文档解析模块
├── intent_understanding.py      # 意图理解模块
├── retrieval_ranking.py         # 检索与排序模块
├── summary_generator.py         # 摘要生成模块
├── main.py                      # 主程序
├── api_server.py               # API服务器
├── generate_result.py          # 结果生成脚本
├── requirements.txt            # 依赖列表
├── USAGE.md                    # 使用说明（本文件）
├── dataset/                    # 数据集目录
│   ├── knowledge_base/        # 知识库文档
│   └── queries/               # 测试问题集
├── output/                     # 输出目录（自动创建）
│   ├── parsed_knowledge/      # 解析后的知识库
│   ├── vector_db/             # 向量索引
│   └── system.log             # 系统日志
└── result.json                 # 最终结果文件
```

## 输出格式

### result.json 格式

符合赛题要求的JSON格式：

```json
[
  {
    "question_id": "Q20231001001",
    "knowledge_points": [
      "知识点1的文本内容（≤1500字）",
      "知识点2的文本内容（≤1500字）",
      "知识点3的文本内容（≤1500字）"
    ]
  },
  {
    "question_id": "Q20231001002",
    "knowledge_points": [
      "知识点1的文本内容",
      "知识点2的文本内容",
      "知识点3的文本内容"
    ]
  }
]
```

**格式说明**：
- 编码：UTF-8
- 结构：顶层为JSON数组
- 每项包含：`question_id` 和 `knowledge_points` 数组
- 知识点数量：最多3个
- 单知识点长度：≤1500字

## 功能特性

### 1. 多格式文档解析
- **DOCX**: 提取段落和表格
- **PDF**: 板式解析，提取文本和表格结构
- **Excel**: 提取表格数据和说明文字
- **PPTX**: 提取幻灯片内容和表格
- **图片**: OCR识别文字内容

### 2. 智能意图识别
- **多意图问题**: 自动拆解（如："流程和利率" → ["流程", "利率"]）
- **推理问题**: 识别条件推理（如："是否符合条件"）
- **总结问题**: 生成摘要（如："总结一下..."）
- **多跳问题**: 多步检索（如："需要满足哪些条件"）

### 3. 高效向量检索
- 基于FAISS的向量索引
- 使用sentence-transformers计算语义相似度
- 支持多跳检索和结果去重

### 4. 自动摘要生成
- 基于TextRank算法
- 自动提取关键句
- 控制摘要长度≤300字

## 配置说明

主要配置在 `config.py` 文件中：

```python
# 模型配置
BERT_MODEL_NAME = "hfl/chinese-roberta-wwm-ext"
SENTENCE_TRANSFORMER_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# 检索配置
TOP_K = 3                      # 返回Top3知识点
MAX_KNOWLEDGE_LENGTH = 1500    # 单知识点最大长度
MAX_SUMMARY_LENGTH = 300       # 摘要最大长度

# 相似度阈值
SIMILARITY_THRESHOLD = 0.3
```

## 性能优化建议

### 1. 首次运行优化
- 首次运行需要构建知识库和索引，建议在性能较好的机器上进行
- 可以单独运行 `document_parser.py` 先构建知识库

### 2. 后续运行优化
- 系统会自动保存索引，后续运行直接加载
- 如果文档没有变化，不需要重新构建

### 3. 内存优化
- 如果内存不足，可以减少批处理大小
- 在 `retrieval_ranking.py` 中调整 `batch_size` 参数

### 4. GPU加速（可选）
- 如果有GPU，可以安装 `faiss-gpu` 替代 `faiss-cpu`
- 安装 `torch` 的GPU版本以加速向量化

## 常见问题

### Q1: 模型下载失败
**解决方法**：
1. 使用国内镜像源
2. 手动下载模型到本地，修改 `config.py` 中的模型路径

### Q2: OCR识别失败
**解决方法**：
1. 确认已安装 Tesseract-OCR
2. 检查 `config.py` 中的 `TESSERACT_CMD` 路径是否正确
3. 确认已安装中文语言包

### Q3: 内存不足
**解决方法**：
1. 减少批处理大小
2. 使用更小的模型
3. 分批处理文档

### Q4: 检索结果不准确
**解决方法**：
1. 调整相似度阈值 `SIMILARITY_THRESHOLD`
2. 增加检索数量后重排序
3. 使用更大的向量化模型

## 技术方案说明

### 模型选择
- **基座模型**: `hfl/chinese-roberta-wwm-ext` (MIT协议)
- **向量模型**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (Apache 2.0协议)
- 均为开源模型，符合赛题要求

### 核心算法
1. **文档解析**: pdfplumber (板式解析), pytesseract (OCR)
2. **向量检索**: FAISS (Facebook AI Similarity Search)
3. **摘要生成**: TextRank (基于图的排序算法)
4. **意图识别**: 基于规则+关键词匹配

## 联系方式

如有问题，请查看：
- 系统日志: `output/system.log`
- 文档解析日志: `document_parser.log`

## 许可证

本项目使用的所有开源模型和库均遵守其原有许可证。
- 模型: MIT/Apache 2.0
- 依赖库: 各自许可证

---

**祝使用愉快！**

