import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from code_parser.ast_parser import parse_repo
from retrieval.indexer import HybridIndex
# 注意这里我们多导入了一个 set_global_index
from agent.investigator import agent_app, set_global_index
from viz.graph_view import render_graph_in_streamlit

st.title("RepoQuest Lite - 代码理解助手")
st.write("目前完整阶段：RRF混合检索 + Agent 多步反思 + 依赖可视化。")

# ================= 侧边栏：解析与建索引 =================
repo_path = st.sidebar.text_input("请输入本地代码仓库的绝对路径", "D:\\pythoncode\\aiproject")

if st.sidebar.button("开始解析并建立索引"):
    with st.spinner("正在解析代码、下载模型并建立索引（首次运行可能较慢）..."):
        try:
            symbols, imports = parse_repo(repo_path)
            st.session_state["symbols"] = symbols
            st.session_state["imports"] = imports

            # 建立索引
            index = HybridIndex(symbols)
            st.session_state["index"] = index

            # 关键步骤：把索引注入给 Agent 的全局变量
            set_global_index(index)

            st.success(f"解析和建索成功！共找到 {len(symbols)} 个类和函数。")
        except Exception as e:
            st.error(f"解析失败: {e}")

# ================= 主界面 =================
if "symbols" in st.session_state:
    st.subheader("🔍 第一步：直接搜索代码")

    query = st.text_input("输入你想搜索的内容（比如：读取文件，或者 parse）：")

    if query:
        index = st.session_state["index"]
        results = index.search_hybrid(query, top_k=3)

        if results:
            st.write(f"找到了 {len(results)} 个相关结果（按 RRF 融合得分排序）：")

            for symbol, score in results:
                with st.expander(f"函数/类名: {symbol['name']}  (RRF得分: {score:.4f})"):
                    st.caption(f"文件: {symbol['file']}  第 {symbol['lineno']} 行")
                    st.code(symbol["code"], language="python")
        else:
            st.warning("没有找到相关的代码。")

    st.divider()

    # ================= Agent 问答区 =================
    st.subheader("🤖 第二步：Agent 多步调查问答")
    st.write("Agent 会根据你的问题自动搜索，如果觉得信息不够，它会自己换词再搜。")

    user_question = st.text_input("你想知道关于这个项目的什么？(比如：这个项目是怎么解析代码的？)")

    if st.button("让 Agent 调查并回答"):
        if not user_question:
            st.warning("请先在输入框里输入你的问题！")
        elif "index" not in st.session_state:
            st.warning("请先在左侧点击解析建立索引！")
        else:
            with st.spinner("Agent 正在多步调查中（看终端有惊喜）..."):
                try:
                    # 初始化状态
                    inputs = {
                        "question": user_question,
                        "search_query": user_question,  # 第一次直接用问题搜
                        "search_results": [],
                        "retry_count": 0,
                        "answer": ""
                    }

                    output = agent_app.invoke(inputs)

                    st.success("Agent 调查完毕，回答如下：")
                    st.info(output["answer"])

                    with st.expander("查看 Agent 最终找到的参考代码"):
                        for r in output["search_results"]:
                            st.code(r['code'], language="python")

                except Exception as e:
                    st.error(f"Agent 运行出错: {e}")

    st.divider()

    # ================= 可视化 =================
    st.subheader("🕸️ 第三步：代码依赖关系图")
    if "imports" in st.session_state:
        render_graph_in_streamlit(st.session_state["imports"])

    st.divider()

    # ================= 下拉框 =================
    st.subheader("📦 查看所有提取到的代码符号")
    symbols = st.session_state["symbols"]
    if symbols:
        symbol_names = [f"{s['name']} ({s['type']})" for s in symbols]
        selected = st.selectbox("选择查看详情：", symbol_names)
        idx = symbol_names.index(selected)
        st.code(symbols[idx]["code"], language="python")