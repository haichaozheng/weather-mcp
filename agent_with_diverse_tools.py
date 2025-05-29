from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
import asyncio
from langchain_core.messages import AIMessage
from langgraph_tools import add, multiply, subtract, divide, square_root, power, concatenate, to_uppercase, to_lowercase
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp.client.sse import sse_client
from mcp import ClientSession
from mcp_third_party import get_zhipu_web_search_tools

# 加载环境变量
load_dotenv()

# 获取自定义工具
def get_custom_tools():
    return [
        add,
        multiply,
        subtract,
        divide,
        square_root,
        power,
        concatenate,
        to_uppercase,
        to_lowercase
    ]

async def test_agent_with_all_tools():
    print("====== 开始测试 Agent 与综合工具 ======")
    
    # 创建模型
    model = ChatOpenAI(
        openai_api_base="https://api.moonshot.cn/v1",
        openai_api_key=os.getenv("MOONSHOT_API_KEY"),
        model_name="moonshot-v1-32k",
        temperature=0.7
    )
    
    # 获取自定义工具
    custom_tools = get_custom_tools()
    
    try:
        # 1. 连接到本地天气MCP服务器获取天气工具
        print("\n=== 连接本地天气服务器 ===")
        url = "http://localhost:8000"
        sse_url = f"{url}/sse"
        print(f"连接到本地MCP服务器: {sse_url}")
        
        weather_tools = []
        try:
            # 连接到MCP服务器
            async with sse_client(sse_url) as (read, write):
                async with ClientSession(read, write) as session:
                    # 初始化连接
                    print("初始化本地MCP连接...")
                    await session.initialize()
                    
                    # 加载MCP工具
                    print("加载本地天气工具...")
                    weather_tools = await load_mcp_tools(session)
                    print(f"加载了 {len(weather_tools)} 个本地天气工具")
        except Exception as e:
            print(f"连接本地天气服务器失败: {str(e)}")
            print("继续使用其他可用工具...")
        
        # 2. 获取智谱Web搜索工具
        print("\n=== 连接智谱Web搜索服务 ===")
        zhipu_tools = []
        try:
            print("获取智谱Web搜索工具...")
            zhipu_tools = await get_zhipu_web_search_tools()
            print(f"获取了 {len(zhipu_tools)} 个智谱Web搜索工具")
        except Exception as e:
            print(f"获取智谱Web搜索工具失败: {str(e)}")
            print("继续使用其他可用工具...")
        
        # 3. 合并所有工具
        all_tools = custom_tools + weather_tools + zhipu_tools
        print(f"\n总共整合了 {len(all_tools)} 个工具")
        
        # 创建agent
        print("创建包含所有工具的Agent...")
        agent = create_react_agent(model, all_tools)
        
        # 测试问题 - 包括数学计算、天气查询和Web搜索
        test_questions = [
            # 数学工具测试
            "计算 23 + 45 的结果",
            "将 'hello world' 转换为大写",
            "计算 16 的平方根",
            # 天气工具测试
            "are there any severe weather alerts in California?",
            "what's the weather forecast for New York City?",
            # 智谱Web搜索工具测试
            "中国最近的航天成就有哪些？",
            "2024年世界经济论坛的主要议题是什么？",
            "最新的人工智能研究进展有哪些？",
            # 组合测试
            "计算 7 * 8 然后减去 10，并查询一下上海的天气预报",
        ]
        
        # 逐个测试问题
        for i, question in enumerate(test_questions):
            print(f"\n测试 {i+1}: '{question}'")
            
            try:
                agent_response = await agent.ainvoke(
                    {"messages": [{"role": "user", "content": question}]}
                )
                
                # 提取最后一个AI消息
                messages = agent_response["messages"]
                ai_messages = [msg for msg in messages if isinstance(msg, AIMessage) and msg.content]
                
                if ai_messages:
                    print(f"回答: {ai_messages[-1].content}")
                else:
                    print("未找到AI回答")
            except Exception as e:
                print(f"处理问题时发生错误: {str(e)}")
                import traceback
                traceback.print_exc()
    
        print("\n====== 测试完成 ======")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

# 直接运行时的入口点
if __name__ == "__main__":
    # 确保先启动weather.py中的MCP服务器
    print("注意: 请确保已经启动了weather.py中的MCP服务器!")
    print("可以通过运行 'python weather/weather.py' 来启动服务器")
    print("等待3秒后开始连接...")
    import time
    time.sleep(3)
    
    # 运行测试
    asyncio.run(test_agent_with_all_tools())