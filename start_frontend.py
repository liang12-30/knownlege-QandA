"""
一键启动脚本
自动启动 API 服务并打开前端页面
"""
import subprocess
import webbrowser
import time
import os
import sys
import requests
from pathlib import Path


def check_api_ready(max_retries=20, retry_interval=1):
    """检查 API 是否就绪"""
    print("⏳ 等待 API 服务启动...")
    
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.json().get("ready"):
                print("✅ API 服务已就绪！")
                return True
        except:
            pass
        
        print(f"   等待中... ({i+1}/{max_retries})")
        time.sleep(retry_interval)
    
    print("❌ API 服务启动超时")
    return False


def main():
    print("=" * 60)
    print("🚀 金融多模态知识库问答系统 - 一键启动")
    print("=" * 60)
    print()
    
    # 检查必要文件
    if not Path("api_server.py").exists():
        print("❌ 错误：找不到 api_server.py")
        return
    
    if not Path("frontend.html").exists():
        print("❌ 错误：找不到 frontend.html")
        return
    
    # 检查知识库是否存在
    kb_path = Path("output/parsed_knowledge/knowledge_base.json")
    if not kb_path.exists():
        print("⚠️  警告：知识库不存在，请先运行 quick_start.py 构建知识库")
        choice = input("是否现在构建知识库？(y/n): ").strip().lower()
        if choice == 'y':
            print("\n🔨 正在构建知识库...")
            try:
                subprocess.run([sys.executable, "quick_start.py"], check=True)
            except subprocess.CalledProcessError:
                print("❌ 知识库构建失败")
                return
            print()
        else:
            print("❌ 无法启动：需要先构建知识库")
            return
    
    print("📚 知识库：已存在")
    print()
    
    # 启动 API 服务（后台进程）
    print("🔧 启动 API 服务...")
    try:
        # Windows
        if os.name == 'nt':
            api_process = subprocess.Popen(
                [sys.executable, "api_server.py"],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        # Unix/Linux/Mac
        else:
            api_process = subprocess.Popen(
                [sys.executable, "api_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
        print("✅ API 服务进程已启动 (PID: {})".format(api_process.pid))
        print()
        
    except Exception as e:
        print(f"❌ 启动 API 服务失败: {str(e)}")
        return
    
    # 等待 API 就绪
    if not check_api_ready():
        print("⚠️  API 服务未能在预期时间内就绪，但仍会打开前端页面")
    
    print()
    
    # 打开前端页面
    print("🌐 打开前端页面...")
    frontend_path = Path("frontend.html").absolute()
    
    try:
        # 使用默认浏览器打开
        webbrowser.open(f"file://{frontend_path}")
        print(f"✅ 前端页面已在浏览器中打开")
        print(f"   路径: {frontend_path}")
    except Exception as e:
        print(f"⚠️  自动打开失败: {str(e)}")
        print(f"   请手动打开: {frontend_path}")
    
    print()
    print("=" * 60)
    print("🎉 启动完成！")
    print("=" * 60)
    print()
    print("📋 服务信息：")
    print("   - API 地址: http://localhost:8000")
    print("   - API 文档: http://localhost:8000/docs")
    print("   - 前端页面: 已在浏览器中打开")
    print()
    print("💡 提示：")
    print("   - 如需查看 API 日志，请查看 API 服务窗口")
    print("   - 关闭此窗口将不会停止 API 服务")
    print("   - 要停止 API 服务，请关闭 API 服务窗口或使用 Ctrl+C")
    print()
    print("按任意键退出启动器...")
    
    try:
        input()
    except:
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 已取消启动")
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

