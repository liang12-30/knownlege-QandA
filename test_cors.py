"""
测试 CORS 配置是否正确
"""
import requests

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("🧪 测试 CORS 配置")
print("=" * 60)
print()

# 测试健康检查
print("1️⃣  测试健康检查接口...")
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")
    print("   ✅ 健康检查成功")
except Exception as e:
    print(f"   ❌ 失败: {str(e)}")

print()

# 测试 CORS 头
print("2️⃣  检查 CORS 响应头...")
try:
    response = requests.options(f"{BASE_URL}/health")
    headers = response.headers
    
    if 'Access-Control-Allow-Origin' in headers:
        print(f"   ✅ Access-Control-Allow-Origin: {headers['Access-Control-Allow-Origin']}")
    else:
        print("   ❌ 缺少 Access-Control-Allow-Origin 头")
    
    if 'Access-Control-Allow-Methods' in headers:
        print(f"   ✅ Access-Control-Allow-Methods: {headers['Access-Control-Allow-Methods']}")
    else:
        print("   ⚠️  未设置 Access-Control-Allow-Methods")
        
except Exception as e:
    print(f"   ❌ 失败: {str(e)}")

print()

# 测试问答接口
print("3️⃣  测试问答接口...")
try:
    response = requests.post(
        f"{BASE_URL}/answer",
        json={"question": "测试问题"},
        timeout=30
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   问题: {result['question']}")
        print(f"   意图: {result['intent']}")
        print("   ✅ 问答接口工作正常")
    else:
        print(f"   ⚠️  响应异常: {response.text}")
except Exception as e:
    print(f"   ❌ 失败: {str(e)}")

print()
print("=" * 60)
print("✅ 测试完成！")
print("=" * 60)
print()
print("💡 如果所有测试通过，前端应该可以正常连接了")
print("   请刷新 frontend.html 页面测试")

