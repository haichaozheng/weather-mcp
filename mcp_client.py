import asyncio
import sys
import os
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_core.messages import AIMessage

# 核心修复：在程序最开始设置正确的事件循环策略
# if sys.platform == 'win32':
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

model = ChatOpenAI(
    openai_api_base="https://api.moonshot.cn/v1",
    openai_api_key=os.getenv("MOONSHOT_API_KEY"),
    model_name="moonshot-v1-32k",
    temperature=0.7
)

async def main():
    try:
        # 修改为使用HTTP/SSE传输 - 避免stdio问题
        print("启动 weather 服务器...")
        
        # 先确保weather服务器以SSE模式运行
        # 在weather.py中需要修改：mcp.run(transport='sse')
        
        from mcp.client.sse import sse_client
        
        print("连接到 weather 服务器...")
        async with sse_client("http://localhost:8000/sse") as (read, write):
            from mcp import ClientSession
            async with ClientSession(read, write) as session:
                print("初始化连接...")
                await session.initialize()
                
                print("加载工具...")
                tools = await load_mcp_tools(session)
                
                print("创建agent...")
                agent = create_react_agent(model, tools)
                
                # 定义多个测试问题
                test_questions = [
                    "what is the weather alerting in NY?",
                    "what is the weather forecast for New York City?",
                    "are there any severe weather alerts in California?",
                    "what's the weather like in Miami right now?",
                    "is there any flooding in Texas?"
                ]
                
                # 逐个测试问题并提取回答
                for i, question in enumerate(test_questions):
                    print(f"\n测试 {i+1}: '{question}'")
                    
                    agent_response = await agent.ainvoke(
                        {"messages": [{"role": "user", "content": question}]}
                    )
                    
                    # 提取最后一个有内容的 AIMessage
                    messages = agent_response["messages"]
                    ai_messages = [msg for msg in messages if isinstance(msg, AIMessage) and msg.content]
                    
                    if ai_messages:
                        print(f"回答: {ai_messages[-1].content}")
                    else:
                        print("未找到AI回答")
                
    except Exception as e:
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        import traceback
        print("详细错误信息:")
        traceback.print_exc()

if __name__ == "__main__":
    # 使用asyncio.run作为入口点
    asyncio.run(main())
