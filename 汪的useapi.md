# 金融多模态知识库问答系统 - API 使用文档

## 📋 目录

- [快速开始](#快速开始)
- [API 接口列表](#api-接口列表)
- [接口详细说明](#接口详细说明)
- [调用示例](#调用示例)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)

---

## 🚀 快速开始

### 1. 启动 API 服务

在启动 API 服务前，请确保已经构建了知识库和向量索引。

#### 方法一：直接运行（推荐）

```bash
python api_server.py
```
然后访问API文档
http://localhost:8000/docs

#### 方法二：指定主机和端口

```python
# 修改 api_server.py 最后一行
if __name__ == "__main__":
    start_server(host="127.0.0.1", port=8080)
```

#### 方法三：使用 uvicorn 命令

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

参数说明：
- `--host`: 监听地址（`0.0.0.0` 表示所有网络接口，`127.0.0.1` 仅本地访问）
- `--port`: 监听端口（默认 8000）
- `--reload`: 开发模式，代码修改后自动重载

### 2. 验证服务是否启动

服务启动后，访问：http://localhost:8000

您应该看到类似以下的响应：

```json
{
  "message": "金融多模态知识库问答系统",
  "version": "1.0.0",
  "status": "running"
}
```

### 3. 查看 API 文档

FastAPI 自动生成交互式 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📑 API 接口列表

| 方法 | 路径 | 功能 | 说明 |
|------|------|------|------|
| GET | `/` | 系统信息 | 获取系统基本信息 |
| GET | `/health` | 健康检查 | 检查系统是否就绪 |
| POST | `/answer` | 单问题回答 | 回答单个问题 |
| POST | `/batch_answer` | 批量问题回答 | 批量回答多个问题 |
| GET | `/knowledge_base/stats` | 知识库统计 | 获取知识库统计信息 |

---

## 📖 接口详细说明

### 1. 获取系统信息

**接口**: `GET /`

**描述**: 获取系统基本信息和运行状态

**请求参数**: 无

**响应示例**:

```json
{
  "message": "金融多模态知识库问答系统",
  "version": "1.0.0",
  "status": "running"
}
```

---

### 2. 健康检查

**接口**: `GET /health`

**描述**: 检查系统是否就绪，可用于负载均衡器的健康检查

**请求参数**: 无

**响应示例**:

```json
{
  "status": "healthy",
  "ready": true
}
```

**状态说明**:
- `healthy`: 系统正常运行
- `unhealthy`: 系统未就绪或出现问题

---

### 3. 单问题回答

**接口**: `POST /answer`

**描述**: 回答单个金融问题，返回最相关的知识点

**请求体**:

```json
{
  "question": "如何开通手机银行？"
}
```

**请求参数说明**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | string | 是 | 用户的问题 |

**响应示例**:

```json
{
  "question": "如何开通手机银行？",
  "intent": "query",
  "knowledge_points": [
    "[第1页]\n招商银行手机银行使用说明...",
    "[第1页]\n中国银行 B2B 开通流程...",
    "[第1页]\n农业银行网上银行开通指南..."
  ],
  "metadata": {
    "intent_type": "query",
    "is_multi_intent": false,
    "is_reasoning": false,
    "is_summary": false,
    "is_financial": false
  }
}
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| question | string | 原始问题 |
| intent | string | 问题意图类型 |
| knowledge_points | array | 相关知识点列表（Top 3） |
| metadata | object | 元数据信息 |

**意图类型**:
- `query`: 普通查询
- `multi_intent`: 多意图问题
- `reasoning`: 推理问题
- `summary`: 摘要问题
- `financial`: 金融计算问题

---

### 4. 批量问题回答

**接口**: `POST /batch_answer`

**描述**: 批量回答多个问题，适合处理大量问题的场景

**请求体**:

```json
{
  "questions": [
    "如何开通手机银行？",
    "个人住房贷款流程和最新LPR利率",
    "总结一下企业网银的主要功能"
  ]
}
```

**请求参数说明**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| questions | array | 是 | 问题列表 |

**响应示例**:

```json
{
  "results": [
    {
      "question": "如何开通手机银行？",
      "intent": "query",
      "knowledge_points": ["...", "...", "..."],
      "metadata": {...}
    },
    {
      "question": "个人住房贷款流程和最新LPR利率",
      "intent": "multi_intent",
      "knowledge_points": ["...", "...", "..."],
      "metadata": {...}
    },
    {
      "question": "总结一下企业网银的主要功能",
      "intent": "summary",
      "knowledge_points": ["...", "...", "..."],
      "metadata": {...}
    }
  ],
  "total": 3
}
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| results | array | 回答结果列表 |
| total | integer | 问题总数 |

---

### 5. 知识库统计信息

**接口**: `GET /knowledge_base/stats`

**描述**: 获取知识库的统计信息

**请求参数**: 无

**响应示例**:

```json
{
  "total_documents": 63,
  "total_vectors": 63
}
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| total_documents | integer | 知识库中的文档总数 |
| total_vectors | integer | 向量索引中的向量总数 |

---

## 💻 调用示例

### Python 示例

#### 使用 requests 库

```python
import requests
import json

# API 基础URL
BASE_URL = "http://localhost:8000"

# 1. 健康检查
response = requests.get(f"{BASE_URL}/health")
print("健康检查:", response.json())

# 2. 单问题回答
question_data = {
    "question": "如何开通手机银行？"
}
response = requests.post(
    f"{BASE_URL}/answer",
    json=question_data,
    headers={"Content-Type": "application/json"}
)
result = response.json()
print("\n问题:", result["question"])
print("意图:", result["intent"])
print("知识点数量:", len(result["knowledge_points"]))
for i, kp in enumerate(result["knowledge_points"], 1):
    print(f"\n[知识点 {i}]")
    print(kp[:200] + "..." if len(kp) > 200 else kp)

# 3. 批量问题回答
batch_data = {
    "questions": [
        "如何开通手机银行？",
        "个人住房贷款流程和最新LPR利率",
        "总结一下企业网银的主要功能"
    ]
}
response = requests.post(
    f"{BASE_URL}/batch_answer",
    json=batch_data,
    headers={"Content-Type": "application/json"}
)
results = response.json()
print(f"\n批量处理结果: 共 {results['total']} 个问题")
for i, result in enumerate(results['results'], 1):
    print(f"\n问题 {i}: {result['question']}")
    print(f"意图: {result['intent']}")
    print(f"知识点数量: {len(result['knowledge_points'])}")

# 4. 获取知识库统计
response = requests.get(f"{BASE_URL}/knowledge_base/stats")
stats = response.json()
print(f"\n知识库统计:")
print(f"文档总数: {stats['total_documents']}")
print(f"向量总数: {stats['total_vectors']}")
```

#### 使用 httpx 库（异步）

```python
import httpx
import asyncio

async def main():
    BASE_URL = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # 单问题回答
        response = await client.post(
            f"{BASE_URL}/answer",
            json={"question": "如何开通手机银行？"}
        )
        result = response.json()
        print("问题:", result["question"])
        print("知识点数量:", len(result["knowledge_points"]))

# 运行异步代码
asyncio.run(main())
```

---

### JavaScript/Node.js 示例

#### 使用 fetch API (浏览器)

```javascript
const BASE_URL = "http://localhost:8000";

// 1. 健康检查
fetch(`${BASE_URL}/health`)
  .then(response => response.json())
  .then(data => console.log("健康状态:", data))
  .catch(error => console.error("错误:", error));

// 2. 单问题回答
const questionData = {
  question: "如何开通手机银行？"
};

fetch(`${BASE_URL}/answer`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify(questionData)
})
  .then(response => response.json())
  .then(result => {
    console.log("问题:", result.question);
    console.log("意图:", result.intent);
    console.log("知识点:", result.knowledge_points);
  })
  .catch(error => console.error("错误:", error));

// 3. 批量问题回答（使用 async/await）
async function batchAnswer() {
  const batchData = {
    questions: [
      "如何开通手机银行？",
      "个人住房贷款流程和最新LPR利率"
    ]
  };
  
  try {
    const response = await fetch(`${BASE_URL}/batch_answer`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(batchData)
    });
    
    const results = await response.json();
    console.log(`处理了 ${results.total} 个问题`);
    results.results.forEach((result, index) => {
      console.log(`问题 ${index + 1}:`, result.question);
      console.log(`意图:`, result.intent);
    });
  } catch (error) {
    console.error("错误:", error);
  }
}

batchAnswer();
```

#### 使用 axios 库 (Node.js)

```javascript
const axios = require('axios');

const BASE_URL = "http://localhost:8000";

// 单问题回答
async function answerQuestion(question) {
  try {
    const response = await axios.post(`${BASE_URL}/answer`, {
      question: question
    });
    
    console.log("问题:", response.data.question);
    console.log("意图:", response.data.intent);
    console.log("知识点数量:", response.data.knowledge_points.length);
    
    return response.data;
  } catch (error) {
    console.error("错误:", error.message);
    if (error.response) {
      console.error("状态码:", error.response.status);
      console.error("错误详情:", error.response.data);
    }
  }
}

// 批量问题回答
async function batchAnswerQuestions(questions) {
  try {
    const response = await axios.post(`${BASE_URL}/batch_answer`, {
      questions: questions
    });
    
    console.log(`处理了 ${response.data.total} 个问题`);
    return response.data.results;
  } catch (error) {
    console.error("错误:", error.message);
  }
}

// 使用示例
(async () => {
  await answerQuestion("如何开通手机银行？");
  
  const questions = [
    "个人住房贷款流程和最新LPR利率",
    "总结一下企业网银的主要功能"
  ];
  await batchAnswerQuestions(questions);
})();
```

---

### cURL 示例

#### 健康检查

```bash
curl http://localhost:8000/health
```

#### 单问题回答

```bash
curl -X POST "http://localhost:8000/answer" \
  -H "Content-Type: application/json" \
  -d '{"question":"如何开通手机银行？"}'
```

#### 批量问题回答

```bash
curl -X POST "http://localhost:8000/batch_answer" \
  -H "Content-Type: application/json" \
  -d '{
    "questions": [
      "如何开通手机银行？",
      "个人住房贷款流程和最新LPR利率"
    ]
  }'
```

#### 知识库统计

```bash
curl http://localhost:8000/knowledge_base/stats
```

---

### Java 示例

```java
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import com.google.gson.Gson;
import com.google.gson.JsonObject;

public class QAClient {
    private static final String BASE_URL = "http://localhost:8000";
    private static final HttpClient client = HttpClient.newHttpClient();
    private static final Gson gson = new Gson();
    
    public static void answerQuestion(String question) throws Exception {
        // 构建请求体
        JsonObject requestBody = new JsonObject();
        requestBody.addProperty("question", question);
        
        // 创建请求
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(BASE_URL + "/answer"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(gson.toJson(requestBody)))
            .build();
        
        // 发送请求
        HttpResponse<String> response = client.send(
            request, 
            HttpResponse.BodyHandlers.ofString()
        );
        
        // 解析响应
        JsonObject result = gson.fromJson(response.body(), JsonObject.class);
        System.out.println("问题: " + result.get("question").getAsString());
        System.out.println("意图: " + result.get("intent").getAsString());
        System.out.println("知识点数量: " + result.getAsJsonArray("knowledge_points").size());
    }
    
    public static void main(String[] args) throws Exception {
        answerQuestion("如何开通手机银行？");
    }
}
```

---

### C# 示例

```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

class QAClient
{
    private static readonly HttpClient client = new HttpClient();
    private const string BASE_URL = "http://localhost:8000";
    
    public static async Task AnswerQuestion(string question)
    {
        var requestBody = new { question = question };
        var json = JsonSerializer.Serialize(requestBody);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        
        var response = await client.PostAsync($"{BASE_URL}/answer", content);
        var responseBody = await response.Content.ReadAsStringAsync();
        
        var result = JsonSerializer.Deserialize<JsonElement>(responseBody);
        Console.WriteLine($"问题: {result.GetProperty("question").GetString()}");
        Console.WriteLine($"意图: {result.GetProperty("intent").GetString()}");
        Console.WriteLine($"知识点数量: {result.GetProperty("knowledge_points").GetArrayLength()}");
    }
    
    static async Task Main(string[] args)
    {
        await AnswerQuestion("如何开通手机银行？");
    }
}
```

---

## ⚠️ 错误处理

### HTTP 状态码

| 状态码 | 说明 | 处理方式 |
|--------|------|----------|
| 200 | 请求成功 | 正常处理响应 |
| 422 | 请求参数验证失败 | 检查请求体格式 |
| 500 | 服务器内部错误 | 查看日志，联系管理员 |
| 503 | 服务不可用（系统未就绪） | 等待系统初始化完成 |

### 错误响应示例

```json
{
  "detail": "系统未就绪"
}
```

### Python 错误处理示例

```python
import requests

BASE_URL = "http://localhost:8000"

def safe_answer_question(question):
    try:
        response = requests.post(
            f"{BASE_URL}/answer",
            json={"question": question},
            timeout=30  # 设置超时
        )
        
        # 检查状态码
        if response.status_code == 503:
            print("系统未就绪，请稍后重试")
            return None
        elif response.status_code == 422:
            print("请求参数错误:", response.json())
            return None
        elif response.status_code == 500:
            print("服务器错误:", response.json())
            return None
        
        response.raise_for_status()  # 检查其他错误
        return response.json()
        
    except requests.exceptions.Timeout:
        print("请求超时")
        return None
    except requests.exceptions.ConnectionError:
        print("无法连接到服务器，请检查服务是否启动")
        return None
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return None

# 使用
result = safe_answer_question("如何开通手机银行？")
if result:
    print("成功获取答案:", result["question"])
```

---

## 🎯 最佳实践

### 1. 系统初始化等待

在服务启动后，系统需要加载知识库和模型，建议等待几秒后再发送请求：

```python
import requests
import time

BASE_URL = "http://localhost:8000"

def wait_for_ready(max_retries=10, retry_interval=2):
    """等待系统就绪"""
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.json().get("ready"):
                print("系统已就绪！")
                return True
        except:
            pass
        
        print(f"等待系统就绪... ({i+1}/{max_retries})")
        time.sleep(retry_interval)
    
    print("系统未能就绪")
    return False

# 使用
if wait_for_ready():
    # 开始发送请求
    pass
```

### 2. 批量处理大量问题

如果有大量问题需要处理，建议分批发送：

```python
def process_large_batch(questions, batch_size=10):
    """分批处理大量问题"""
    results = []
    
    for i in range(0, len(questions), batch_size):
        batch = questions[i:i+batch_size]
        
        try:
            response = requests.post(
                f"{BASE_URL}/batch_answer",
                json={"questions": batch},
                timeout=60
            )
            
            if response.status_code == 200:
                batch_results = response.json()["results"]
                results.extend(batch_results)
                print(f"已处理 {len(results)}/{len(questions)} 个问题")
            else:
                print(f"批次 {i//batch_size + 1} 处理失败")
        
        except Exception as e:
            print(f"批次 {i//batch_size + 1} 发生错误: {str(e)}")
    
    return results

# 使用示例
questions = ["问题1", "问题2", ..., "问题100"]
results = process_large_batch(questions, batch_size=10)
```

### 3. 设置合理的超时时间

对于复杂问题，处理可能需要较长时间，建议设置合理的超时：

```python
# 单问题：30秒超时
response = requests.post(
    f"{BASE_URL}/answer",
    json={"question": question},
    timeout=30
)

# 批量问题：根据数量调整超时
timeout = 30 + len(questions) * 5  # 基础30秒 + 每个问题5秒
response = requests.post(
    f"{BASE_URL}/batch_answer",
    json={"questions": questions},
    timeout=timeout
)
```

### 4. 使用连接池提高性能

```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()

# 配置重试策略
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["HEAD", "GET", "POST"]
)

adapter = HTTPAdapter(
    max_retries=retry_strategy,
    pool_connections=10,
    pool_maxsize=10
)

session.mount("http://", adapter)
session.mount("https://", adapter)

# 使用 session 发送请求
response = session.post(
    f"{BASE_URL}/answer",
    json={"question": "如何开通手机银行？"}
)
```

### 5. 日志记录

建议记录所有请求和响应，便于调试和分析：

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def answer_with_logging(question):
    logging.info(f"发送问题: {question}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/answer",
            json={"question": question}
        )
        
        logging.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logging.info(f"意图类型: {result['intent']}")
            logging.info(f"知识点数量: {len(result['knowledge_points'])}")
            return result
        else:
            logging.error(f"请求失败: {response.text}")
            return None
            
    except Exception as e:
        logging.error(f"发生异常: {str(e)}")
        return None
```

---

## 🔧 高级配置

### 部署到生产环境

#### 使用 Gunicorn (推荐用于生产环境)

```bash
# 安装 gunicorn
pip install gunicorn

# 启动服务（4个工作进程）
gunicorn api_server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

#### 使用 Docker

创建 `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建和运行：

```bash
# 构建镜像
docker build -t qa-system .

# 运行容器
docker run -p 8000:8000 qa-system
```

#### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

---

## 📊 性能优化建议

1. **使用批量接口**: 对于多个问题，使用 `/batch_answer` 比多次调用 `/answer` 更高效

2. **缓存常见问题**: 在客户端缓存常见问题的答案，减少重复请求

3. **并发控制**: 避免同时发送过多请求，建议使用连接池和限流

4. **合理设置超时**: 根据问题复杂度设置不同的超时时间

5. **监控和日志**: 记录请求耗时，定期分析性能瓶颈

---

## 📞 联系支持

如有问题或建议，请通过以下方式联系：

- 查看项目文档: `README.md`, `USAGE.md`
- 查看日志文件: `logs/` 目录
- 提交 Issue 或 Pull Request

---

## 📝 更新日志

- **v1.0.0** (2024-11-13): 初始版本发布
  - 支持单问题和批量问题回答
  - 提供健康检查和统计信息接口
  - 完整的 API 文档和示例

---

**祝使用愉快！** 🎉

