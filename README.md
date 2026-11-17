markdown

# RepoQuest Lite - 智能代码理解与调查助手

RepoQuest Lite 是一个基于 **Agentic RAG（智能体检索增强生成）** 架构的 Python 代码理解工具。它不仅能像传统工具一样解析代码结构，还能通过大语言模型（LLM）和 LangGraph 实现多步自我反思检索，帮助开发者快速读懂陌生项目。

## ✨ 核心亮点

- **AST 静态结构分析**：基于 Python 原生 `ast` 模块，精准提取代码中的类、函数、方法及其位置信息，并分析文件间的依赖关系。
- **RRF 混合检索**：结合 BM25 关键词匹配与 Sentence-Transformers 向量语义检索，并使用 **RRF（倒数排名融合）算法** 重新打分排序，大幅提升代码片段的召回准确率。
- **Agent 多步调查工作流**：基于 **LangGraph** 构建状态图。Agent 在检索代码后，会自我评估证据是否充足。如果不够，它会自动生成新的搜索关键词进行二次检索，直到收集足够信息再生成最终回答。
- **交互式依赖可视化**：使用 NetworkX 与 PyVis 将代码的 `import` 关系渲染为可交互的网络图，直观展示项目模块间的耦合情况。

## 🛠️ 技术栈

- **前端交互**：Streamlit
- **Agent 编排**：LangChain, LangGraph
- **大模型**：DeepSeek API (兼容 OpenAI 接口)
- **检索与向量化**：rank-bm25, sentence-transformers, scikit-learn
- **代码分析与可视化**：Python AST, NetworkX, PyVis

## 🚀 快速启动

1. 克隆项目并进入目录：
   ```bash
   git clone <你的仓库地址>
   cd aiproject

    创建虚拟环境并安装依赖：
    bash

    python -m venv venv
    # Windows 使用 venv\Scripts\activate
    source venv/bin/activate  
    pip install -r requirements.txt

    配置环境变量：
    在根目录创建 .env 文件，填入你的大模型 API Key：
    env

    OPENAI_API_KEY=sk-你的密钥
    OPENAI_BASE_URL=https://api.deepseek.com

    启动应用：
    bash

    streamlit run app.py

💡 使用指南

    在左侧边栏输入你想要分析的 Python 项目本地路径（例如 D:\pythoncode\aiproject）。

    点击 “开始解析并建立索引”，系统会自动完成代码解析和向量化。

    在搜索框输入关键词，或者直接向 Agent 提问（例如：“这个项目是怎么解析代码的？”）。

    观察终端日志，你可以看到 Agent 是如何进行多步思考和循环检索的。

🔮 未来优化方向

    支持更多编程语言（如 Java, C++）的 AST 解析。

    引入更细粒度的代码切片（Code Chunking）策略。

    接入本地大模型（如 Ollama）降低 API 成本。