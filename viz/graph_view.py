import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import os


def generate_dependency_graph(imports, output_file="dependency_graph.html"):
    """
    根据解析出的 import 关系，生成可视化的网络图
    """
    # 创建有向图
    G = nx.DiGraph()

    for imp in imports:
        # 提取源文件和目标模块的文件名（去掉路径和 .py 后缀，让图更干净）
        source = os.path.basename(imp["from"]).replace(".py", "")
        target = os.path.basename(imp["to"]).replace(".py", "")

        # 如果是内部模块导入，才加到图里
        if target and target != source:
            G.add_edge(source, target)

    if len(G.nodes) == 0:
        return None

    # 使用 pyvis 创建交互式网络图
    net = Network(height="500px", width="100%", bgcolor="#222222", font_color="white", directed=True)

    # 把 networkx 的图导入 pyvis
    net.from_nx(G)

    # 设置物理引擎，让节点可以动态调整位置
    net.repulsion()

    # 保存为 HTML
    net.save_graph(output_file)
    return output_file


def render_graph_in_streamlit(imports):
    """
    在 Streamlit 中渲染图
    """
    output_file = generate_dependency_graph(imports)

    if output_file and os.path.exists(output_file):
        # 读取生成的 HTML 并展示在网页上
        with open(output_file, 'r', encoding='utf-8') as f:
            html_data = f.read()
        components.html(html_data, height=520)
    else:
        import streamlit as st
        st.warning("没有找到足够的内部依赖关系来生成图（可能是单文件项目）。")