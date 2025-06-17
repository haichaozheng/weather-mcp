import shutil
import os
import subprocess
import asyncio
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

print("🔍 调试 npx 路径问题...")

# 检查 npx 路径
npx_path = shutil.which("npx")
print(f"Python 中的 npx 路径: {npx_path}")

# 检查环境变量
print(f"PATH 环境变量:")
for path in os.environ.get('PATH', '').split(os.pathsep):
    if 'node' in path.lower() or 'npm' in path.lower():
        print(f"  📁 {path}")

# 尝试直接调用
try:
    result = subprocess.run(['npx', '--version'], capture_output=True, text=True)
    print(f"✅ npx 版本: {result.stdout.strip()}")
except FileNotFoundError as e:
    print(f"❌ npx 调用失败: {e}")
    
    # 尝试常见的路径
    common_paths = [
        r"C:\Program Files\nodejs\npx.cmd",
        r"C:\Program Files (x86)\nodejs\npx.cmd", 
        r"C:\Users\{}\AppData\Roaming\npm\npx.cmd".format(os.getenv('USERNAME')),
        r"C:\Users\{}\AppData\Local\npm\npx.cmd".format(os.getenv('USERNAME')),
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            print(f"✅ 找到 npx: {path}")
            break
    else:
        print("❌ 在常见位置未找到 npx")

def test_npx_call():
    """测试不同的 npx 调用方式"""
    print("🧪 测试不同的 npx 调用方式...")
    
    # 方式1：使用 shell=True
    try:
        result = subprocess.run(['npx', '--version'], capture_output=True, text=True, shell=True)
        print(f"✅ 方式1 (shell=True) 成功: {result.stdout.strip()}")
        return "npx"
    except Exception as e:
        print(f"❌ 方式1 失败: {e}")
    
    # 方式2：使用完整路径
    try:
        npx_path = r"C:\Program Files\nodejs\npx.cmd"
        result = subprocess.run([npx_path, '--version'], capture_output=True, text=True)
        print(f"✅ 方式2 (完整路径) 成功: {result.stdout.strip()}")
        return npx_path
    except Exception as e:
        print(f"❌ 方式2 失败: {e}")
    
    # 方式3：完整路径 + shell=True
    try:
        npx_path = r"C:\Program Files\nodejs\npx.cmd"
        result = subprocess.run([npx_path, '--version'], capture_output=True, text=True, shell=True)
        print(f"✅ 方式3 (完整路径+shell) 成功: {result.stdout.strip()}")
        return npx_path
    except Exception as e:
        print(f"❌ 方式3 失败: {e}")
    
    return None

async def test_mcp_with_working_npx():
    """使用能工作的 npx 方式测试 MCP"""
    
    # 找到能工作的 npx 调用方式
    working_npx = test_npx_call()
    
    if not working_npx:
        print("❌ 没有找到能工作的 npx 调用方式")
        return
    
    print(f"\n🔧 使用 npx: {working_npx}")
    
    # 配置 MCP 客户端
    config = {
        "tavily-mcp": {
            "command": working_npx,
            "args": ["-y", "tavily-mcp"],
            "env": {
                "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY")
            },
            "transport": "stdio"
        }
    }
    
    try:
        print("🚀 创建 MCP 客户端...")
        client = MultiServerMCPClient(config)
        
        print("⏳ 等待服务器启动（30秒）...")
        await asyncio.sleep(30)
        
        print("🔧 尝试获取工具...")
        tools = client.get_tools()
        
        print(f"✅ 成功！获取到 {len(tools)} 个工具:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:100]}...")
            
        return tools
            
    except Exception as e:
        print(f"❌ MCP 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_mcp_with_working_npx())
