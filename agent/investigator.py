import os
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 加载 .env 里的密钥
load_dotenv()


# 定义 Agent 的记忆/状态
class AgentState(TypedDict):
    question: str
    search_results: List[dict]
    answer: str


def retrieve_node(state: AgentState):
    # 这里的逻辑是：把上一环节搜出来的代码，整理成格式
    print("Agent 正在整理检索到的代码...")
    return {"search_results": state["search_results"]}


def answer_node(state: AgentState):
    print("Agent 正在呼叫大模型生成回答...")

    # 显式指定 API Key 和 Base URL（从 .env 文件中读取）
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")

    if not api_key:
        return {"answer": "报错：没有找到 OPENAI_API_KEY，请检查 .env 文件是否配置正确。"}

    # 初始化大模型 (使用 deepseek-chat 或 deepseek-flash)
    # DeepSeek 官方目前兼容这两种模型名，temperature=0 表示不让它乱发挥，保持严谨
    llm = ChatOpenAI(
        model="deepseek-chat",
        temperature=0,
        api_key=api_key,
        base_url=base_url
    )

    # 把问题和搜到的代码拼成 Prompt
    context = "\n".join([f"函数名: {r['name']}\n代码:\n{r['code']}" for r in state["search_results"]])

    prompt = f"""你是一个资深的代码分析助手。
请根据以下参考代码片段，回答用户的问题。

用户问题：{state['question']}

参考代码：
{context}

要求：
1. 请用中文回答。
2. 如果参考代码不足以回答问题，请直接说“根据提供的代码无法回答”，不要编造。
3. 回答时请引用具体的函数名或类名，并尽量解释代码的逻辑。"""

    try:
        response = llm.invoke(prompt)
        return {"answer": response.content}
    except Exception as e:
        return {"answer": f"调用大模型时出错: {e}"}


# 构建 LangGraph 状态图
workflow = StateGraph(AgentState)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("answer", answer_node)
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "answer")
workflow.add_edge("answer", END)

# 编译成可以执行的 app
agent_app = workflow.compile()