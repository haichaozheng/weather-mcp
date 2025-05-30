import os
import asyncio
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from typing import Any, List, Dict, Optional, Tuple
from dataclasses import dataclass

load_dotenv()

# 检查API密钥
moonshot_key = os.getenv("MOONSHOT_API_KEY")
zhipu_key = os.getenv("ZHIPU_API_KEY")

if not moonshot_key:
    print("错误：请在.env文件中设置MOONSHOT_API_KEY")
if not zhipu_key:
    print("警告：未找到ZHIPU_API_KEY，将跳过智谱Web搜索")

def get_mcp_config() -> Dict[str, Dict[str, str]]:
    """获取MCP配置"""
    config = {}
    
    # 天气服务器配置
    config["weather"] = {
        "url": "http://localhost:8000/sse",
        "transport": "sse",
    }
    
    # 智谱Web搜索配置（只在有API密钥时添加）
    if zhipu_key:
        config["zhipu-web-search"] = {
            "url": f"https://open.bigmodel.cn/api/mcp/web_search/sse?Authorization={zhipu_key}",
            "transport": "sse",
        }
    
    return config

@dataclass
class TaskConfig:
    """任务配置类 - 只包含问题列表"""
    questions: List[str]  # 测试问题列表

@dataclass
class AgentConfig:
    """智能体配置类"""
    llm: str = "moonshot-v1-32k"  # 语言模型名称
    tools: List[str] = None  # 可用工具列表
    max_steps: int = 3  # 最大工具调用次数
    max_iterations: int = 5  # 最大迭代次数
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = [
                "mcp-weather", "mcp-zhipu-web-search", 
                "add", "multiply", "subtract", "divide", 
                "square_root", "power", "concatenate", 
                "to_uppercase", "to_lowercase"
            ]

def parse_tools_config(tools: List[str]) -> Tuple[List[str], List[str]]:
    """解析工具配置，分离MCP工具和本地工具"""
    mcp_tools_names = []
    local_tools_names = []
    
    for tool_name in tools:
        if tool_name.startswith("mcp-"):
            config_key = tool_name[4:]  # 去掉"mcp-"前缀
            mcp_tools_names.append(config_key)
        else:
            local_tools_names.append(tool_name)
    
    return mcp_tools_names, local_tools_names

def load_local_tools(tool_names: List[str]) -> List[Any]:
    """加载本地工具"""
    custom_tools = []
    
    if not tool_names:
        return custom_tools
    
    try:
        from langgraph_tools import (
            add, multiply, subtract, divide, 
            square_root, power, concatenate, 
            to_uppercase, to_lowercase
        )
        
        local_tools_map = {
            "add": add, "multiply": multiply, "subtract": subtract,
            "divide": divide, "square_root": square_root, "power": power,
            "concatenate": concatenate, "to_uppercase": to_uppercase,
            "to_lowercase": to_lowercase
        }
        
        for tool_name in tool_names:
            if tool_name in local_tools_map:
                custom_tools.append(local_tools_map[tool_name])
                print(f"✓ 加载本地工具: {tool_name}")
            else:
                print(f"⚠️ 警告: 未找到本地工具 '{tool_name}'")
                
    except ImportError as e:
        print(f"❌ 导入本地工具失败: {e}")
    
    return custom_tools

def build_servers_config(mcp_tools_names: List[str]) -> Dict[str, Dict[str, str]]:
    """构建MCP服务器配置"""
    mcp_config = get_mcp_config()
    servers_config = {}
    
    for mcp_tool in mcp_tools_names:
        if mcp_tool in mcp_config:
            servers_config[mcp_tool] = mcp_config[mcp_tool]
            print(f"✓ 添加MCP服务器: {mcp_tool} -> {mcp_config[mcp_tool]['url']}")
        else:
            print(f"⚠️ 警告: 未找到MCP工具 '{mcp_tool}' 的配置")
    
    return servers_config

async def load_mcp_tools(servers_config: Dict[str, Dict[str, str]]) -> List[Any]:
    """加载MCP工具"""
    if not servers_config:
        print("ℹ️ 没有配置MCP服务器")
        return []
    
    try:
        async with MultiServerMCPClient(servers_config) as client:
            mcp_tools = client.get_tools()
            print(f"✓ 从MCP服务器加载了 {len(mcp_tools)} 个工具")
            return mcp_tools
    except Exception as e:
        print(f"❌ 连接MCP服务器失败: {e}")
        return []

def create_model(agent_config: AgentConfig) -> ChatOpenAI:
    """创建语言模型"""
    return ChatOpenAI(
        openai_api_base="https://api.moonshot.cn/v1",
        openai_api_key=moonshot_key,
        model_name=agent_config.llm,
        temperature=0.7  # 使用固定的temperature值
    )

def create_graph(model: ChatOpenAI, tools: List[Any]) -> Any:
    """创建LangGraph状态图"""
    def call_model(state: MessagesState):
        """模型调用节点"""
        response = model.bind_tools(tools).invoke(state["messages"])
        return {"messages": state["messages"] + [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("call_model", call_model)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "call_model")
    builder.add_conditional_edges("call_model", tools_condition)
    builder.add_edge("tools", "call_model")
    
    return builder.compile()

async def process_questions(graph: Any, questions: List[str]) -> Tuple[List[Dict], int]:
    """处理问题列表"""
    responses = []
    successful_tests = 0
    
    for i, question in enumerate(questions):
        print(f"\n=== 处理问题 {i+1}/{len(questions)}: {question} ===")
        
        try:
            response = await graph.ainvoke({
                "messages": [{"role": "user", "content": question}]
            })
            
            if response and "messages" in response:
                last_message = response["messages"][-1]
                print(f"回答: {last_message.content}")
                
                responses.append({
                    "question": question,
                    "answer": last_message.content,
                    "success": True
                })
                successful_tests += 1
            else:
                responses.append({
                    "question": question,
                    "answer": f"异常回答: {response}",
                    "success": False
                })
                
        except Exception as e:
            print(f"处理失败: {e}")
            responses.append({
                "question": question,
                "answer": f"错误: {str(e)}",
                "success": False
            })
    
    return responses, successful_tests

async def run_agent(task_config: TaskConfig, agent_config: AgentConfig) -> Dict[str, Any]:
    """运行智能体"""
    print(f"=== 启动智能体 ===")
    print(f"模型: {agent_config.llm}")
    print(f"工具: {agent_config.tools}")
    print(f"任务: {len(task_config.questions)} 个问题")
    
    try:
        # 1. 解析工具配置
        mcp_tools_names, local_tools_names = parse_tools_config(agent_config.tools)
        print(f"MCP工具: {mcp_tools_names}")
        print(f"本地工具: {local_tools_names}")
        
        # 2. 加载工具
        servers_config = build_servers_config(mcp_tools_names)
        mcp_tools = await load_mcp_tools(servers_config)
        local_tools = load_local_tools(local_tools_names)
        
        all_tools = mcp_tools + local_tools
        print(f"总共加载 {len(all_tools)} 个工具")
        
        if len(all_tools) == 0:
            return {"success": False, "error": "没有加载到任何工具"}
        
        # 3. 创建模型和图
        model = create_model(agent_config)
        graph = create_graph(model, all_tools)
        print("✓ LangGraph状态图构建完成")
        
        # 4. 处理问题
        responses, successful_tests = await process_questions(graph, task_config.questions)
        
        # 5. 返回结果
        result = {
            "success": True,
            "total_questions": len(task_config.questions),
            "successful_tests": successful_tests,
            "success_rate": successful_tests / len(task_config.questions),
            "responses": responses,
            "agent_config": agent_config,
            "task_config": task_config
        }
        
        print(f"\n=== 任务完成 ===")
        print(f"成功率: {successful_tests}/{len(task_config.questions)} ({result['success_rate']:.1%})")
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"运行智能体失败: {str(e)}",
            "agent_config": agent_config,
            "task_config": task_config
        }

# 默认配置
default_agent_config = AgentConfig(
    llm="moonshot-v1-32k",
    tools=["mcp-weather", "mcp-zhipu-web-search", "add", "multiply", "subtract", "divide", "square_root", "power", "concatenate", "to_uppercase", "to_lowercase"]
)

default_task_config = TaskConfig(
    questions=[
        "计算 (3 + 5) * 12 的结果",
        "计算 16 的平方根",
        "将 'hello world' 转换为大写",
        "2025年人工智能技术的最新发展有哪些？",
        "are there any severe weather alerts in California?",
    ]
)

async def main():
    """主函数"""
    return await run_agent(default_task_config, default_agent_config)

if __name__ == "__main__":
    print("🚀 启动LangGraph多工具智能体...")
    
    try:
        results = asyncio.run(main())
        if results["success"]:
            print(f"✅ 智能体运行成功！成功率: {results['success_rate']:.1%}")
        else:
            print(f"❌ 运行失败: {results.get('error', '未知错误')}")
    except Exception as e:
        print(f"💥 程序运行失败: {e}")