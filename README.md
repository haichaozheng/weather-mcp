# 天气信息与多源工具集成系统

这个项目展示了如何整合多种工具来源（自定义工具、本地MCP服务和第三方API）到一个统一的AI代理中，使用LangGraph框架和MCP协议，实现一个功能丰富的智能助手系统。

## 项目组件

### 1. 天气服务器 (weather.py)

提供天气相关API工具：
- `get_alerts`: 获取美国州级天气警报
- `get_forecast`: 根据经纬度获取天气预报

基于MCP协议实现的本地服务，提供实时天气信息访问。

### 2. 自定义工具 (langgraph_tools.py)

提供一系列基础工具：
- **数学工具**：加法、减法、乘法、除法、平方根、幂运算
- **字符串工具**：字符串连接、转大写、转小写

这些工具使用LangChain的`@tool`装饰器定义，可以被AI代理调用。

### 3. 第三方MCP工具 (mcp_third_party.py)

集成第三方MCP服务：
- **智谱Web搜索工具**：通过智谱AI提供的MCP接口获取实时Web搜索能力
- 提供了通用的MCP工具加载函数，便于扩展更多第三方服务

### 4. MCP客户端 (mcp_client.py)

连接到天气服务器并使用其提供的工具。通过SSE（Server-Sent Events）协议与服务器通信，处理连接和重试逻辑。

### 5. 综合代理 (agent_with_diverse_tools.py)

核心组件，整合所有来源的工具：
- **自定义本地工具**：数学计算、字符串处理
- **本地MCP服务工具**：天气查询服务
- **第三方MCP工具**：智谱Web搜索
- 使用LangGraph的React Agent架构
- 基于Moonshot API实现

## 使用方法

### 安装依赖

```bash
pip install -r requirements.txt
```

### 环境配置

在`.env`文件中设置以下变量：
- `MOONSHOT_API_KEY`: Moonshot API密钥（用于LLM）
- `ZHIPU_API_KEY`: 智谱API密钥（用于Web搜索服务）

### 启动服务

1. **启动天气服务器**
```bash
python weather/weather.py
```

2. **运行综合代理测试**
```bash
python weather/agent_with_diverse_tools.py
```

3. **测试智谱Web搜索工具**
```bash
python weather/mcp_third_party.py
```

## 示例查询

综合代理可以处理多种类型的查询：

- **数学计算**：
  - "计算 23 + 45 的结果"
  - "计算 16 的平方根" 
  - "计算 7 * 8 然后减去 10"

- **字符串处理**：
  - "将 'hello world' 转换为大写"
  - "将 ['我', '爱', '中国'] 用空格连接起来"

- **天气信息**：
  - "纽约州有什么天气警报？"
  - "旧金山的天气预报是什么？"
  - "加利福尼亚州有什么严重天气警报？"

- **Web搜索**：
  - "中国最近的航天成就有哪些？"
  - "2024年世界经济论坛的主要议题是什么？"
  - "最新的人工智能研究进展有哪些？"

- **混合查询**：
  - "计算 7 * 8 然后减去 10，并查询一下上海的天气预报"

## 系统特点

- **模块化设计**：各个工具源相互独立，便于维护和扩展
- **容错能力**：即使某个服务不可用，系统仍能使用其他可用工具
- **可扩展性**：容易添加新的工具源和功能
- **多源整合**：将不同来源和类型的工具统一到一个代理中

## 扩展方向

- 添加更多第三方MCP服务
- 实现工具调用的可视化界面
- 增加用户交互模式（如对话模式）
- 添加更多领域的专业工具

## 注意事项

- 确保在运行代理前先启动天气服务器
- 服务器默认在`localhost:8000`上运行
- 天气数据来自美国国家气象局(NWS)API
- 智谱Web搜索需要有效的API密钥

## 系统架构

## 技术栈

- Python 3.11+
- MCP (Model Control Protocol)
- FastMCP 服务器
- LangGraph + LangChain
- SSE (Server-Sent Events) 传输

## 安装

1. 克隆仓库：
   ```bash
   git clone https://github.com/haichaozheng/weather-mcp.git
   cd weather-mcp
   ```

2. 创建虚拟环境：
   ```bash
   # 使用 Python 标准库
   python -m venv weather_venv
   
   # 激活虚拟环境（Windows）
   weather_venv\Scripts\activate
   
   # 激活虚拟环境（Linux/Mac）
   source weather_venv/bin/activate
   ```

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

4. 配置环境变量：
   - 创建 `.env` 文件，参考 `.env.example` 文件格式
   - 添加必要的 API 密钥

## 项目结构
weather-mcp/
├── weather/
│ ├── weather.py # 主服务器文件
│ ├── mcp_client.py # 客户端测试文件
├── requirements.txt # 项目依赖
├── .env.example # 环境变量示例
└── README.md # 本文档
```

## 环境变量配置

项目使用 `.env` 文件存储环境变量和敏感信息。请按照以下步骤设置：

1. 复制环境变量模板文件：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填入您的实际配置：
   ```
   MOONSHOT_API_KEY=your_actual_api_key
   ```

3. 确保 `.env` 文件不会被提交到版本控制系统中

## 环境变量

在`.env`文件中设置以下变量：
- `MOONSHOT_API_KEY`: Moonshot API密钥

## 注意事项

- 确保在运行代理前先启动天气服务器
- 服务器默认在`localhost:8000`上运行
- 天气数据来自美国国家气象局(NWS)API