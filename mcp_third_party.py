# 加载智谱API密钥
import os
import asyncio
from dotenv import load_dotenv
from mcp.client.sse import sse_client
from mcp import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool

load_dotenv()

zhipu_api_key = os.getenv("ZHIPU_API_KEY")
if not zhipu_api_key:
    raise ValueError("请在.env文件中设置ZHIPU_API_KEY")

# 智谱Web搜索配置
zhipu_web_search_sse = {
  "mcpServers": {
    "zhipu-web-search-sse": {
      "url": f"https://open.bigmodel.cn/api/mcp/web_search/sse?Authorization={zhipu_api_key}"
    }
  }
}

# 将MCP服务器配置转换为LangGraph工具列表的函数
async def get_tools_from_mcp_server(server_config: Dict[str, Any], server_name: Optional[str] = None) -> List[BaseTool]:
    """
    从MCP服务器配置中获取LangGraph工具列表
    
    参数:
        server_config: MCP服务器配置字典
        server_name: 要连接的服务器名称，如果为None则使用配置中的第一个服务器
        
    返回:
        从MCP服务器加载的工具列表
    """
    # 如果未指定服务器名称，则使用配置中的第一个服务器
    if server_name is None:
        server_name = next(iter(server_config["mcpServers"].keys()))
    
    # 检查服务器是否存在于配置中
    if server_name not in server_config["mcpServers"]:
        raise ValueError(f"配置中未找到服务器: {server_name}")
    
    # 获取服务器URL
    server_url = server_config["mcpServers"][server_name]["url"]
    print(f"连接到MCP服务器 '{server_name}': {server_url}")
    
    # 连接到MCP服务器并加载工具
    try:
        async with sse_client(server_url) as (read, write):
            async with ClientSession(read, write) as session:
                print(f"初始化MCP连接到 '{server_name}'...")
                await session.initialize()
                
                print(f"从 '{server_name}' 加载工具...")
                tools = await load_mcp_tools(session)
                
                print(f"从 '{server_name}' 加载了 {len(tools)} 个工具")
                return tools
    except Exception as e:
        print(f"连接MCP服务器 '{server_name}' 失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

# 简化版函数，专门用于获取智谱Web搜索工具
async def get_zhipu_web_search_tools() -> List[BaseTool]:
    """
    获取智谱Web搜索MCP服务器提供的工具列表
    
    返回:
        智谱Web搜索工具列表
    """
    return await get_tools_from_mcp_server(zhipu_web_search_sse, "zhipu-web-search-sse")

# 测试函数
async def test_zhipu_tools():
    # 获取智谱Web搜索工具
    tools = await get_zhipu_web_search_tools()
    
    if not tools:
        print("未能获取到智谱Web搜索工具")
        return
    
    # 打印工具信息
    print(f"获取到 {len(tools)} 个智谱Web搜索工具:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # 创建模型
    model = ChatOpenAI(
        openai_api_base="https://api.moonshot.cn/v1",
        openai_api_key=os.getenv("MOONSHOT_API_KEY"),
        model_name="moonshot-v1-32k",
        temperature=0.7
    )
    
    # 创建agent
    agent = create_react_agent(model, tools)
    
    # 测试搜索查询
    test_query = "成都的天气怎么样？"

    print(f"\n测试搜索查询: '{test_query}'")
    
    try:
        agent_response = await agent.ainvoke(
            {"messages": [{"role": "user", "content": test_query}]}
        )
        
        # 提取最后一个AI消息
        messages = agent_response["messages"]
        ai_messages = [msg for msg in messages if isinstance(msg, AIMessage) and msg.content]
        
        if ai_messages:
            print(f"回答: {ai_messages[-1].content}")
        else:
            print("未找到AI回答")
    except Exception as e:
        print(f"处理查询时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

# 如何在其他代码中使用这些函数的示例
async def example_usage():
    # 获取智谱Web搜索工具
    zhipu_tools = await get_zhipu_web_search_tools()
    
    # 可以将这些工具与其他工具组合使用
    from langgraph_tools import add, multiply  # 假设这些是自定义的数学工具
    combined_tools = zhipu_tools + [add, multiply]
    
    # 使用组合工具创建Agent
    model = ChatOpenAI(
        openai_api_base="https://api.moonshot.cn/v1",
        openai_api_key=os.getenv("MOONSHOT_API_KEY"),
        model_name="moonshot-v1-32k"
    )
    agent = create_react_agent(model, combined_tools)
    
    # 现在Agent可以同时处理Web搜索和数学计算
    return agent

if __name__ == "__main__":
    print("测试智谱Web搜索工具...")
    asyncio.run(test_zhipu_tools())
