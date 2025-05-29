# 天气信息与工具系统

这个项目集成了天气信息服务和自定义工具，使用LangGraph和MCP（Machine Communicating Protocol）框架，允许AI代理访问天气数据和执行基本计算功能。

## 项目组件

### 1. 天气服务器 (weather.py)

提供天气相关API工具：
- `get_alerts`: 获取美国州级天气警报
- `get_forecast`: 根据经纬度获取天气预报

通过MCP协议提供服务，使其他组件可以访问这些工具。

### 2. 自定义工具 (langgraph_tools.py)

提供一系列基础工具：
- **数学工具**：加法、减法、乘法、除法、平方根、幂运算
- **字符串工具**：字符串连接、转大写、转小写

这些工具使用LangChain的`@tool`装饰器定义，可以被AI代理调用。

### 3. MCP客户端 (mcp_client.py)

连接到天气服务器并使用其提供的工具。通过SSE（Server-Sent Events）协议与服务器通信，处理连接和重试逻辑。

### 4. 综合代理 (agent_with_diverse_tools.py)

结合自定义工具和天气服务器工具，创建一个功能丰富的AI代理。
- 使用LangGraph的React Agent架构
- 集成Moonshot API作为语言模型
- 可以回答数学问题和天气查询

## 使用方法

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

1. **启动天气服务器**
```bash
python weather/weather.py
```

2. **运行综合代理测试**
```bash
python weather/agent_with_diverse_tools.py
```

### 示例查询

AI代理可以处理以下类型的查询：

- 数学计算：
  - "计算 23 + 45 的结果"
  - "计算 16 的平方根" 
  - "计算 7 * 8 然后减去 10"

- 字符串处理：
  - "将 'hello world' 转换为大写"
  - "将 ['我', '爱', '中国'] 用空格连接起来"

- 天气信息：
  - "纽约州有什么天气警报？"
  - "旧金山的天气预报是什么？"
  - "加利福尼亚州有什么严重天气警报？"

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