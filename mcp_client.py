import asyncio
import sys
import os
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_core.messages import AIMessage
import httpx
import time
from urllib.parse import urlparse

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
    # 增加重试次数和延迟
    max_retries = 3
    retry_delay = 2
    
    # 测试服务器是否可访问
    print("测试服务器连接...")
    url = "http://localhost:8000"
    
    try:
        async with httpx.AsyncClient() as client:
            # 先测试服务器基本连接
            try:
                resp = await client.get(f"{url}/docs", timeout=5.0)
                print(f"服务器文档访问状态: {resp.status_code}")
            except Exception as e:
                print(f"访问服务器文档失败: {str(e)}")
            
            # 测试SSE端点
            try:
                resp = await client.get(f"{url}/sse", timeout=1.0)
                print(f"SSE端点状态码: {resp.status_code}")
                print(f"SSE端点响应: {resp.text[:100]}...")  # 只显示前100个字符
            except Exception as e:
                print(f"访问SSE端点失败: {str(e)}")
    except Exception as e:
        print(f"服务器连接测试失败: {str(e)}")
    
    # 主要连接逻辑
    for attempt in range(max_retries):
        try:
            print(f"\n尝试 {attempt+1}/{max_retries} 连接到 weather 服务器...")
            
            from mcp.client.sse import sse_client
            
            # 创建会话时增加超时参数
            timeout = httpx.Timeout(10.0, connect=5.0)
            client = httpx.AsyncClient(timeout=timeout)
            
            # 修改端点路径，检查是否需要包含完整路径
            sse_url = f"{url}/sse"
            print(f"连接到SSE端点: {sse_url}")
            
            async with sse_client(sse_url) as (read, write):
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
                
            # 如果成功，跳出循环
            break
                
        except Exception as e:
            print(f"连接尝试 {attempt+1} 失败")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            import traceback
            print("详细错误信息:")
            traceback.print_exc()
            
            if attempt < max_retries - 1:
                print(f"等待 {retry_delay} 秒后重试...")
                await asyncio.sleep(retry_delay)
            else:
                print("已达到最大重试次数，放弃连接")

if __name__ == "__main__":
    # 使用asyncio.run作为入口点
    asyncio.run(main())
