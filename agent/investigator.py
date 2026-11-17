import os
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# 定义一个全局变量，用来接收外部传进来的检索器
GLOBAL_INDEX = None


class AgentState(TypedDict):
    question: str
    search_query: str
    search_results: List[dict]
    retry_count: int
    answer: str


def get_llm():
    return ChatOpenAI(
        model="deepseek-chat",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )


def retrieve_node(state: AgentState):
    print(f"Agent 正在使用关键词 '{state['search_query']}' 检索代码...")
    if GLOBAL_INDEX is None:
        return {"search_results": []}

    # 调用真实的混合检索
    results = GLOBAL_INDEX.search_hybrid(state["search_query"], top_k=3)

    # 合并历史结果并去重
    existing_names = {r['name'] for r in state["search_results"]}
    new_results = [{"name": s['name'], "code": s['code']} for s, _ in results if s['name'] not in existing_names]

    return {"search_results": state["search_results"] + new_results}


def evaluate_node(state: AgentState):
    print("Agent 正在评估检索到的代码是否足够...")
    if state["retry_count"] >= 2:
        return {"search_query": "DONE"}  # 防止无限死循环

    llm = get_llm()
    context = "\n".join([f"函数名: {r['name']}\n代码:\n{r['code'][:500]}..." for r in state["search_results"]])

    prompt = f"""用户的问题是：{state['question']}

这是目前检索到的代码：
{context}

请问，这些代码足够回答用户的问题吗？
如果足够，请只回复："足够"。
如果不够，请回复一个新的搜索关键词（只输出关键词，不要带任何标点符号和解释），以便找到更多相关代码。"""

    response = llm.invoke(prompt).content.strip()

    if "足够" in response:
        return {"search_query": "DONE"}
    else:
        print(f"Agent 觉得不够，决定换个词再搜：{response}")
        return {"search_query": response, "retry_count": state["retry_count"] + 1}


def answer_node(state: AgentState):
    print("Agent 正在生成最终回答...")
    llm = get_llm()
    context = "\n".join([f"函数名: {r['name']}\n代码:\n{r['code']}" for r in state["search_results"]])

    prompt = f"""你是一个资深的代码分析助手。请根据以下参考代码片段，回答用户的问题。

用户问题：{state['question']}

参考代码：
{context}

要求：
1. 请用中文回答。
2. 如果参考代码不足以回答问题，请直接说“根据提供的代码无法回答”，不要编造。
3. 回答时请引用具体的函数名或类名，并尽量解释代码的逻辑。"""

    response = llm.invoke(prompt)
    return {"answer": response.content}


workflow = StateGraph(AgentState)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("evaluate", evaluate_node)
workflow.add_node("answer", answer_node)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "evaluate")

workflow.add_conditional_edges(
    "evaluate",
    lambda x: "answer" if x["search_query"] == "DONE" else "retrieve",
    {"answer": "answer", "retrieve": "retrieve"}
)

workflow.add_edge("answer", END)
agent_app = workflow.compile()


# 提供给外部的注入接口
def set_global_index(index):
    global GLOBAL_INDEX
    GLOBAL_INDEX = index
