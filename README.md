# Weather MCP Service

一个基于 Model Control Protocol (MCP) 的天气信息服务，提供天气预报和警报查询功能。

## 功能

- 获取美国各州的天气警报（`get_alerts`）
- 通过经纬度查询天气预报（`get_forecast`）

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

## 使用方法

1. 启动 Weather 服务器：
   ```bash
   python weather/weather.py
   ```
   服务器将在 http://localhost:8000 上启动，使用 SSE 传输。

2. 在另一个终端窗口中运行客户端：
   ```bash
   python weather/mcp_client.py
   ```
   客户端将连接到服务器并执行一系列天气查询测试。

## API 功能

### 天气警报查询

```python
get_alerts(state: str) -> str
```
- `state`: 两字母美国州代码（例如：CA, NY）
- 返回：该州的活跃天气警报列表

### 天气预报查询

```python
get_forecast(latitude: float, longitude: float) -> str
```
- `latitude`: 位置纬度
- `longitude`: 位置经度
- 返回：该位置的天气预报

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