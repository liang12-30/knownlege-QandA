"""
FastAPI接口服务
提供RESTful API接口
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
from loguru import logger

from main import QASystem


# 创建FastAPI应用
app = FastAPI(
    title="金融多模态知识库问答系统",
    description="AiC2025赛题：金融知识库构建与复杂问答检索系统",
    version="1.0.0"
)

# 配置 CORS（跨域资源共享）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（开发环境）
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有请求头
)

# 全局问答系统实例
qa_system = None


# 请求模型
class QuestionRequest(BaseModel):
    """单个问题请求"""
    question: str


class BatchQuestionRequest(BaseModel):
    """批量问题请求"""
    questions: List[str]


# 响应模型
class AnswerResponse(BaseModel):
    """回答响应"""
    question: str
    intent: str
    knowledge_points: List[str]
    metadata: Dict[str, Any]


class BatchAnswerResponse(BaseModel):
    """批量回答响应"""
    results: List[AnswerResponse]
    total: int


@app.on_event("startup")
async def startup_event():
    """启动时初始化系统"""
    global qa_system
    
    logger.info("启动问答系统...")
    qa_system = QASystem()
    
    # 初始化（不重建知识库，使用已有的）
    qa_system.initialize(rebuild_knowledge=False)
    
    logger.info("问答系统启动完成！")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "金融多模态知识库问答系统",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    if qa_system and qa_system.is_ready:
        return {"status": "healthy", "ready": True}
    else:
        return {"status": "unhealthy", "ready": False}


@app.post("/answer", response_model=AnswerResponse)
async def answer_question(request: QuestionRequest):
    """
    回答单个问题
    
    Args:
        request: 问题请求
        
    Returns:
        回答结果
    """
    if not qa_system or not qa_system.is_ready:
        raise HTTPException(status_code=503, detail="系统未就绪")
    
    try:
        result = qa_system.answer(request.question)
        return result
    except Exception as e:
        logger.error(f"回答问题失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch_answer", response_model=BatchAnswerResponse)
async def batch_answer_questions(request: BatchQuestionRequest):
    """
    批量回答问题
    
    Args:
        request: 批量问题请求
        
    Returns:
        批量回答结果
    """
    if not qa_system or not qa_system.is_ready:
        raise HTTPException(status_code=503, detail="系统未就绪")
    
    try:
        results = qa_system.batch_answer(request.questions)
        return {
            "results": results,
            "total": len(results)
        }
    except Exception as e:
        logger.error(f"批量回答问题失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/knowledge_base/stats")
async def get_knowledge_base_stats():
    """获取知识库统计信息"""
    if not qa_system or not qa_system.is_ready:
        raise HTTPException(status_code=503, detail="系统未就绪")
    
    return {
        "total_documents": len(qa_system.knowledge_builder.knowledge_base),
        "total_vectors": qa_system.retriever.index.ntotal if qa_system.retriever.index else 0
    }


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """
    启动API服务器
    
    Args:
        host: 主机地址
        port: 端口号
    """
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()

