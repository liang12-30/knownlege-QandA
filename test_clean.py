"""
测试内容清理功能
"""
import re

def clean_content(content: str) -> str:
    """
    清理知识点内容，去除页码标记和优化格式
    """
    if not content:
        return content
    
    # 1. 去除页码标记
    content = re.sub(r'\[第?\s*\d+\s*页\s*\]', '', content)
    content = re.sub(r'\[页\s*\d+-\d+\]', '', content)
    content = re.sub(r'\[.*?-页\d+-\d+\]', '', content)
    
    # 2. 去除多余的空白行
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # 3. 合并短行
    lines = content.split('\n')
    merged_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            merged_lines.append(line)
            i += 1
            continue
        
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            
            if (len(line) < 50 and 
                next_line and 
                not line.endswith(('。', '！', '？', '：', '；', '.', '!', '?', ':', ';')) and
                not next_line.startswith(('一、', '二、', '三、', '四、', '五、', 
                                         '1.', '2.', '3.', '4.', '5.',
                                         '（一）', '（二）', '（三）', '第一', '第二'))):
                merged_lines.append(line + next_line)
                i += 2
                continue
        
        merged_lines.append(line)
        i += 1
    
    content = '\n'.join(merged_lines)
    
    # 4. 去除行首行尾空白
    lines = [line.strip() for line in content.split('\n')]
    content = '\n'.join(lines)
    
    # 5. 去除开头和结尾的多余换行
    content = content.strip()
    
    return content


# 测试示例
test_text = """[第1页]
中国银行
手机银行
开通流程
[第2页]
第一步
下载APP
第二步
注册账号
[第3页]
完成实名认证
绑定银行卡
"""

print("=" * 60)
print("原始文本：")
print("=" * 60)
print(test_text)
print()

cleaned = clean_content(test_text)

print("=" * 60)
print("清理后的文本：")
print("=" * 60)
print(cleaned)
print()

print("✅ 清理完成！")
print(f"原始长度: {len(test_text)} 字符")
print(f"清理后长度: {len(cleaned)} 字符")
print(f"减少了: {len(test_text) - len(cleaned)} 字符")

