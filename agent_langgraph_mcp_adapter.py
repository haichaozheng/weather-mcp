import os
import sys
import asyncio
import logging
import warnings
import atexit
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

load_dotenv()

# 设置logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 完全屏蔽所有警告
warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")

# 设置事件循环策略（Windows专用）
if os.name == 'nt':  # Windows
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

moonshot_key = os.getenv("MOONSHOT_API_KEY")

# 在程序退出时彻底屏蔽所有输出
def cleanup_on_exit():
    """程序退出时的清理函数"""
    try:
        sys.stderr = open(os.devnull, 'w')
    except:
        pass

# 注册退出时的清理函数
atexit.register(cleanup_on_exit)

def get_mcp_config():
    """获取MCP配置"""
    config = {}
    
    # 检查API密钥
    zhipu_key = os.getenv("ZHIPU_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    logger.info(f"🔑 ZHIPU_API_KEY 状态: {'已设置' if zhipu_key else '未设置'}")
    logger.info(f"🔑 TAVILY_API_KEY 状态: {'已设置' if tavily_key else '未设置'}")
    
    # 智谱Web搜索配置（SSE传输）
    if zhipu_key:
        config["zhipu-web-search"] = {
            "url": f"https://open.bigmodel.cn/api/mcp/web_search/sse?Authorization={zhipu_key}",
            "transport": "sse",
        }
        logger.info("✓ 添加智谱Web搜索配置")
    
    # Tavily MCP配置（stdio传输）
    if tavily_key:
        config["tavily-mcp"] = {
            "command": "npx",
            "args": ["-y", "tavily-mcp"],
            "env": {"TAVILY_API_KEY": tavily_key},
            "transport": "stdio"
        }
        logger.info("✓ 添加Tavily搜索配置")
    
    logger.info(f"📋 MCP配置总数: {len(config)}")
    return config

async def get_mcp_tools():
    """
    获取MCP工具列表 - 修复版本兼容性
    
    Returns:
        tuple: (tools, client) - 工具列表和MCP客户端实例
    """
    try:
        config = get_mcp_config()
        if not config:
            logger.warning("📭 没有可用的MCP配置")
            return [], None
            
        logger.info(f"🔌 开始连接MCP服务器，配置数量: {len(config)}")
        
        # 创建MCP客户端
        client = MultiServerMCPClient(config)
        
        # 方式1：直接获取工具（推荐） - 根据react.py修正
        try:
            mcp_tools = await client.get_tools()  # 🔧 修复：确实需要 await
            logger.info(f"✓ 使用方式1成功，从MCP服务器加载了 {len(mcp_tools)} 个工具")
            logger.info(f"🔍 工具列表: {mcp_tools}")
            
            # 详细日志输出工具信息
            for i, tool in enumerate(mcp_tools, 1):
                tool_name = getattr(tool, 'name', 'unknown')
                tool_desc = getattr(tool, 'description', 'No description')[:100]
                logger.info(f"  - 工具 {i}: {tool_name}")
                logger.info(f"    描述: {tool_desc}...")
            
            return mcp_tools, client
            
        except Exception as e1:
            logger.warning(f"⚠️ 方式1失败: {e1}")
            
            # 方式2：使用session方式（备用）
            try:
                all_tools = []
                for server_name in config.keys():
                    logger.info(f"🔗 尝试连接服务器: {server_name}")
                    async with client.session(server_name) as session:
                        # 这里需要根据实际的session API来获取工具
                        # 具体实现可能需要根据文档调整
                        pass
                logger.info(f"✓ 使用方式2成功，加载了 {len(all_tools)} 个工具")
                return all_tools, client
            except Exception as e2:
                logger.error(f"❌ 方式2也失败: {e2}")
                raise e2
                
    except Exception as e:
        logger.error(f"❌ 连接MCP服务器失败: {e}")
        logger.warning("🔄 将返回空工具列表")
        return [], None

def create_agent_with_tools(tools, model_name: str = "kimi-latest"):
    """
    使用工具创建智能体
    
    Args:
        tools: 工具列表
        model_name: 模型名称，默认为 kimi-latest
        
    Returns:
        智能体实例
    """
    try:
        if not tools:
            logger.warning("❌ 没有可用的工具")
            return None
            
        logger.info(f"🤖 正在创建智能体，使用模型: {model_name}")
        logger.info(f"🔧 可用工具数量: {len(tools)}")
        
        # 创建模型
        model = ChatOpenAI(
            openai_api_base="https://api.moonshot.cn/v1",
            openai_api_key=moonshot_key,
            model_name=model_name,
            temperature=0.7
        )
        
        # 创建代理
        agent = create_react_agent(model, tools)
        logger.info("✅ 智能体创建成功")
        
        return agent
        
    except Exception as e:
        logger.error(f"❌ 创建智能体失败: {e}")
        return None

async def query_agent(agent, client, query: str):
    """
    使用智能体处理查询 - 修复客户端管理
    
    Args:
        agent: 智能体实例
        client: MCP客户端实例
        query: 用户查询
        
    Returns:
        智能体的回答
    """
    try:
        if not agent:
            return "❌ 智能体未创建"
            
        logger.info(f"🔍 处理查询: {query}")
        
        # 🔧 修复：如果client存在，使用上下文管理器
        if client:
            async with client:
                result = await agent.ainvoke({
                    "messages": [{"role": "user", "content": query}]
                })
        else:
            # 如果没有client（比如只使用本地工具），直接调用
            result = await agent.ainvoke({
                "messages": [{"role": "user", "content": query}]
            })
            
        # 提取回答
        if result and "messages" in result:
            last_message = result["messages"][-1]
            answer = last_message.content if hasattr(last_message, 'content') else str(last_message)
            logger.info("✅ 查询处理完成")
            return answer
        else:
            return str(result)
                
    except Exception as e:
        logger.error(f"❌ 查询处理失败: {e}")
        return f"处理失败: {e}"

# 便捷函数 - 整合版本
async def create_mcp_agent(query: str, model_name: str = "kimi-latest"):
    """
    创建MCP智能体并处理查询（整合版本）
    
    Args:
        query: 用户查询
        model_name: 模型名称，默认为 kimi-latest
        
    Returns:
        智能体的回答
    """
    # 获取工具
    tools, client = await get_mcp_tools()  # 保持这个 await，因为函数本身是异步的
    if not tools:
        return "❌ 无法获取MCP工具"
    
    # 创建智能体
    agent = create_agent_with_tools(tools, model_name)
    if not agent:
        return "❌ 无法创建智能体"
    
    # 处理查询
    return await query_agent(agent, client, query)

# 批处理多个查询
async def batch_queries(queries: list, model_name: str = "kimi-latest"):
    """
    批量处理多个查询（优化版本 - 复用工具和智能体）
    
    Args:
        queries: 查询列表
        model_name: 模型名称
        
    Returns:
        结果列表
    """
    results = []
    
    # 一次性获取工具和创建智能体
    tools, client = await get_mcp_tools()  # 保持这个 await
    if not tools:
        return [{"query": query, "answer": "❌ 无法获取MCP工具"} for query in queries]
    
    agent = create_agent_with_tools(tools, model_name)
    if not agent:
        return [{"query": query, "answer": "❌ 无法创建智能体"} for query in queries]
    
    # 🔧 如果有MCP客户端，在整个批处理过程中保持连接
    if client:
        async with client:
            for i, query in enumerate(queries, 1):
                print(f"\n🤖 处理查询 {i}/{len(queries)}: {query}")
                print("=" * 60)
                
                try:
                    # 直接调用agent，不再使用query_agent（避免重复的上下文管理）
                    result = await agent.ainvoke({
                        "messages": [{"role": "user", "content": query}]
                    })
                    
                    # 提取回答
                    if result and "messages" in result:
                        last_message = result["messages"][-1]
                        answer = last_message.content if hasattr(last_message, 'content') else str(last_message)
                    else:
                        answer = str(result)
                        
                except Exception as e:
                    answer = f"处理失败: {e}"
                    logger.error(f"❌ 查询处理失败: {e}")
                
                print(f"📝 回答: {answer}")
                print("\n" + "="*60)
                
                results.append({"query": query, "answer": answer})
                
                # 避免频繁调用，稍作延迟
                if i < len(queries):
                    await asyncio.sleep(2)
    else:
        # 没有MCP客户端的情况
        for i, query in enumerate(queries, 1):
            print(f"\n🤖 处理查询 {i}/{len(queries)}: {query}")
            print("=" * 60)
            
            answer = await query_agent(agent, None, query)
            print(f"📝 回答: {answer}")
            print("\n" + "="*60)
            
            results.append({"query": query, "answer": answer})
            
            if i < len(queries):
                await asyncio.sleep(2)
    
    return results

# 交互式聊天
async def interactive_chat(model_name: str = "kimi-latest"):
    """
    交互式聊天模式（优化版本 - 复用工具和智能体）
    
    Args:
        model_name: 模型名称
    """
    print("🤖 MCP智能体已启动！输入 'quit' 或 'exit' 退出")
    print("=" * 50)
    
    # 一次性获取工具和创建智能体
    tools, client = await get_mcp_tools()  # 保持这个 await
    if not tools:
        print("❌ 无法获取MCP工具，退出...")
        return
    
    agent = create_agent_with_tools(tools, model_name)
    if not agent:
        print("❌ 无法创建智能体，退出...")
        return
    
    print("✅ 智能体准备就绪！")
    
    # 🔧 如果有MCP客户端，在整个聊天过程中保持连接
    if client:
        async with client:
            await _chat_loop(agent, None)  # 传入None因为已经在上下文中
    else:
        await _chat_loop(agent, None)

async def _chat_loop(agent, client):
    """聊天循环逻辑"""
    while True:
        try:
            query = input("\n💬 请输入您的问题: ").strip()
            
            if query.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！")
                break
                
            if not query:
                continue
                
            print("\n🔍 正在处理...")
            
            # 直接调用agent（因为已经在MCP客户端的上下文中）
            result = await agent.ainvoke({
                "messages": [{"role": "user", "content": query}]
            })
            
            # 提取回答
            if result and "messages" in result:
                last_message = result["messages"][-1]
                answer = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                answer = str(result)
                
            print(f"\n📝 回答: {answer}")
            print("\n" + "="*50)
            
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")

# 测试函数
async def test_agent():
    """测试智能体功能"""
    test_queries = [
        "搜索人工智能最新发展",
        "查询Python异步编程教程",
        "搜索2025年技术趋势"
    ]
    
    print("🚀 开始批量测试...")
    results = await batch_queries(test_queries)
    
    print(f"\n📊 测试完成，共处理 {len(results)} 个查询")

def safe_run(coro):
    """安全运行协程"""
    try:
        return asyncio.run(coro)
    except Exception as e:
        logger.error(f"运行时错误: {e}")

if __name__ == "__main__":
    print("选择运行模式:")
    print("1. 单次查询测试")
    print("2. 批量查询测试") 
    print("3. 交互式聊天")
    
    choice = input("请选择 (1/2/3): ").strip()
    
    if choice == "1":
        query = input("请输入查询: ").strip()
        if query:
            async def single_test():
                answer = await create_mcp_agent(query)
                print(f"\n📝 回答: {answer}")
            safe_run(single_test())
        
    elif choice == "2":
        safe_run(test_agent())
        
    elif choice == "3":
        safe_run(interactive_chat())
        
    else:
        print("🚀 运行默认测试...")
        safe_run(test_agent())