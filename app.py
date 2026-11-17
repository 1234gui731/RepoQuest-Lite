import streamlit as st
import sys
import os

# 把当前目录加入系统路径，防止找不到自定义模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from code_parser.ast_parser import parse_repo
from retrieval.indexer import HybridIndex
from agent.investigator import agent_app

st.title("RepoQuest Lite - 代码理解助手")
st.write("目前完整阶段：混合检索 + AI Agent 分析。")

# ================= 侧边栏：解析与建索引 =================
repo_path = st.sidebar.text_input("请输入本地代码仓库的绝对路径", "D:\\pythoncode\\aiproject")

if st.sidebar.button("开始解析并建立索引"):
    with st.spinner("正在解析代码、下载模型并建立索引（首次运行可能较慢）..."):
        try:
            # 1. 解析代码
            symbols, imports = parse_repo(repo_path)
            st.session_state["symbols"] = symbols

            # 2. 建立混合索引
            st.session_state["index"] = HybridIndex(symbols)
            st.success(f"解析和建索成功！共找到 {len(symbols)} 个类和函数。")
        except Exception as e:
            st.error(f"解析失败: {e}")

# ================= 主界面 =================
if "symbols" in st.session_state:
    st.subheader("🔍 第一步：搜索代码")

    # 搜索框
    query = st.text_input("输入你想搜索的内容（比如：读取文件，或者 parse）：")

    if query:
        index = st.session_state["index"]
        # 这里我们调用混合检索
        results = index.search_hybrid(query, top_k=3)

        if results:
            st.write(f"找到了 {len(results)} 个相关结果：")

            # 用折叠面板展示搜出来的代码
            for symbol, score in results:
                with st.expander(f"函数/类名: {symbol['name']}  (相关度: {score:.2f})"):
                    st.caption(f"文件: {symbol['file']}  第 {symbol['lineno']} 行")
                    st.code(symbol["code"], language="python")

            # ================= 第二步：AI Agent 问答区 =================
            st.divider()
            st.subheader("🤖 第二步：让 AI 解释这些代码")
            st.write("Agent 会阅读上面搜出来的代码，然后回答你的问题。")

            user_question = st.text_input("你想知道关于这些代码的什么？(比如：这个函数的作用是什么？怎么调用的？)")

            if st.button("让 Agent 回答"):
                if not user_question:
                    st.warning("请先在输入框里输入你的问题！")
                else:
                    with st.spinner("Agent 正在阅读代码并思考..."):
                        try:
                            # 把问题和搜到的结果打包喂给 LangGraph Agent
                            inputs = {
                                "question": user_question,
                                # 把元组 (symbol, score) 里的 symbol 提取出来
                                "search_results": [{"name": s['name'], "code": s['code']} for s, _ in results]
                            }

                            # 运行 Agent
                            output = agent_app.invoke(inputs)

                            st.success("AI 回答：")
                            st.info(output["answer"])
                        except Exception as e:
                            st.error(f"Agent 运行出错: {e}")
        else:
            st.warning("没有找到相关的代码，换个词试试？")

    st.divider()

    # ================= 备用：下拉框查看全部代码 =================
    st.subheader("📦 查看所有提取到的代码符号")
    symbols = st.session_state["symbols"]
    if symbols:
        symbol_names = [f"{s['name']} ({s['type']})" for s in symbols]
        selected = st.selectbox("选择查看详情：", symbol_names)
        idx = symbol_names.index(selected)
        st.code(symbols[idx]["code"], language="python")