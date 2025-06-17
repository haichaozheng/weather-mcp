import asyncio
import os
import logging
import subprocess
import time
import json
import shutil
from typing import List, Any, Dict
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_npx_works():
    """测试 npx 是否能正常工作"""
    try:
        # 在 Windows 上需要 shell=True
        result = subprocess.run(['npx', '--version'], 
                              capture_output=True, text=True, shell=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ npx 工作正常，版本: {result.stdout.strip()}")
            return True
    except Exception as e:
        print(f"❌ npx 测试失败: {e}")
    return False

async def test_manual_tavily():
    """手动测试 Tavily MCP - 使用正确的方式"""
    if not test_npx_works():
        print("❌ npx 不可用，跳过手动测试")
        return False
    
    print("\n🧪 手动测试 Tavily MCP...")
    
    env = os.environ.copy()
    env["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
    
    try:
        # 关键修复：在 Windows 上使用 shell=True
        process = subprocess.Popen(
            "npx -y tavily-mcp",  # 使用字符串而不是列表
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            shell=True,  # 关键：Windows 上需要这个
            bufsize=0
        )
        
        print("⏳ 等待 Tavily MCP 启动...")
        await asyncio.sleep(15)  # 给足够时间下载和启动
        
        if process.poll() is not None:
            print(f"❌ 进程已退出，返回码: {process.returncode}")
            stderr = process.stderr.read()
            if stderr:
                print(f"错误输出: {stderr}")
            return False
        
        print("✅ Tavily MCP 进程运行中")
        
        # 发送 JSON-RPC 请求
        requests = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"capabilities": {}}
            },
            {
                "jsonrpc": "2.0", 
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
        ]
        
        for req in requests:
            try:
                req_str = json.dumps(req) + "\n"
                print(f"📤 发送: {req['method']}")
                process.stdin.write(req_str)
                process.stdin.flush()
                
                # 读取响应
                response = process.stdout.readline()
                if response.strip():
                    print(f"📥 响应: {response.strip()}")
                    # 解析响应查看工具
                    if req['method'] == 'tools/list':
                        try:
                            resp_data = json.loads(response)
                            if 'result' in resp_data and 'tools' in resp_data['result']:
                                tools = resp_data['result']['tools']
                                print(f"🎉 找到 {len(tools)} 个工具!")
                                for tool in tools:
                                    print(f"  - {tool['name']}")
                                return True
                        except json.JSONDecodeError:
                            pass
                else:
                    print("📥 无响应")
                    
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ 通信错误: {e}")
        
    except Exception as e:
        print(f"❌ 手动测试失败: {e}")
    finally:
        if 'process' in locals() and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    
    return False

class CustomMCPClient:
    """自定义 MCP 客户端，处理 Windows 上的 shell 问题"""
    
    def __init__(self, config):
        self.config = config
        self.processes = {}
        
    async def start_servers(self):
        """启动所有服务器"""
        for server_name, server_config in self.config.items():
            if server_config.get("transport") == "stdio":
                await self._start_stdio_server(server_name, server_config)
    
    async def _start_stdio_server(self, name, config):
        """启动 stdio 服务器"""
        command = config["command"]
        args = config.get("args", [])
        env = os.environ.copy()
        env.update(config.get("env", {}))
        
        # 构建命令字符串（Windows 兼容）
        if isinstance(args, list):
            cmd_str = f"{command} {' '.join(args)}"
        else:
            cmd_str = f"{command} {args}"
        
        try:
            print(f"🚀 启动服务器 {name}: {cmd_str}")
            
            process = subprocess.Popen(
                cmd_str,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                shell=True,  # 关键：Windows 兼容
                bufsize=0
            )
            
            self.processes[name] = process
            
            # 等待启动
            await asyncio.sleep(10)
            
            if process.poll() is not None:
                stderr = process.stderr.read()
                print(f"❌ 服务器 {name} 启动失败: {stderr}")
                return False
            
            print(f"✅ 服务器 {name} 启动成功")
            return True
            
        except Exception as e:
            print(f"❌ 启动服务器 {name} 失败: {e}")
            return False
    
    async def get_tools(self, server_name):
        """从指定服务器获取工具"""
        if server_name not in self.processes:
            return []
        
        process = self.processes[server_name]
        if process.poll() is not None:
            print(f"❌ 服务器 {server_name} 已停止")
            return []
        
        try:
            # 发送工具列表请求
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            
            req_str = json.dumps(request) + "\n"
            process.stdin.write(req_str)
            process.stdin.flush()
            
            # 读取响应
            response = process.stdout.readline()
            if response.strip():
                resp_data = json.loads(response)
                if 'result' in resp_data and 'tools' in resp_data['result']:
                    return resp_data['result']['tools']
            
        except Exception as e:
            print(f"❌ 获取工具失败: {e}")
        
        return []
    
    def close(self):
        """关闭所有进程"""
        for name, process in self.processes.items():
            if process.poll() is None:
                print(f"🔌 关闭服务器 {name}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

async def test_custom_client():
    """测试自定义客户端"""
    print("\n🧪 测试自定义 MCP 客户端...")
    
    config = {
        "tavily-mcp": {
            "command": "npx",
            "args": ["-y", "tavily-mcp"],
            "env": {
                "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY")
            },
            "transport": "stdio"
        }
    }
    
    client = CustomMCPClient(config)
    
    try:
        # 启动服务器
        await client.start_servers()
        
        # 等待完全启动
        print("⏳ 等待服务器完全初始化...")
        await asyncio.sleep(20)
        
        # 获取工具
        tools = await client.get_tools("tavily-mcp")
        print(f"🎉 自定义客户端获取到 {len(tools)} 个工具:")
        
        for tool in tools:
            print(f"  - {tool['name']}: {tool.get('description', '')[:100]}...")
        
        return len(tools) > 0
        
    except Exception as e:
        print(f"❌ 自定义客户端测试失败: {e}")
        return False
    finally:
        client.close()

async def test_langchain_client_with_fixes():
    """测试 langchain 客户端（尝试修复）"""
    print("\n🧪 测试 LangChain MCP 客户端...")
    
    # 尝试不同的配置方式
    configs_to_try = [
        # 配置1：标准配置
        {
            "tavily-mcp": {
                "command": "npx",
                "args": ["-y", "tavily-mcp"],
                "env": {
                    "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY")
                },
                "transport": "stdio"
            }
        },
        # 配置2：完整路径
        {
            "tavily-mcp": {
                "command": r"C:\Program Files\nodejs\npx.cmd",
                "args": ["-y", "tavily-mcp"],
                "env": {
                    "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY")
                },
                "transport": "stdio"
            }
        }
    ]
    
    for i, config in enumerate(configs_to_try, 1):
        print(f"\n📋 尝试配置 {i}...")
        
        try:
            client = MultiServerMCPClient(config)
            
            # 等待更长时间
            print("⏳ 等待服务器启动（30秒）...")
            await asyncio.sleep(30)
            
            # 尝试获取工具
            tools = client.get_tools()
            print(f"✅ 配置 {i} 成功！获取到 {len(tools)} 个工具")
            
            if tools:
                for tool in tools:
                    print(f"  - {tool.name}")
                return True
            
        except Exception as e:
            print(f"❌ 配置 {i} 失败: {e}")
            continue
    
    return False

async def main():
    """主测试函数"""
    print("🚀 开始 MCP 综合测试...")
    
    # 检查环境
    if not os.getenv("TAVILY_API_KEY"):
        print("❌ TAVILY_API_KEY 未设置")
        return
    
    # 测试1：手动测试
    print("\n" + "="*60)
    print("1. 手动测试 Tavily MCP")
    print("="*60)
    manual_success = await test_manual_tavily()
    
    # 测试2：自定义客户端
    print("\n" + "="*60)
    print("2. 自定义客户端测试")
    print("="*60)
    custom_success = await test_custom_client()
    
    # 测试3：LangChain 客户端
    print("\n" + "="*60)
    print("3. LangChain 客户端测试") 
    print("="*60)
    langchain_success = await test_langchain_client_with_fixes()
    
    # 总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    print(f"手动测试: {'✅' if manual_success else '❌'}")
    print(f"自定义客户端: {'✅' if custom_success else '❌'}")
    print(f"LangChain 客户端: {'✅' if langchain_success else '❌'}")
    
    if custom_success:
        print("\n🎉 建议使用自定义客户端方案！")
    elif manual_success:
        print("\n💡 Tavily MCP 可以工作，但需要修复客户端集成")
    else:
        print("\n❌ 需要进一步调试 Tavily MCP 启动问题")

if __name__ == "__main__":
    asyncio.run(main())
