import ast
from pathlib import Path


def parse_file(filepath: Path):
    """
    解析单个 Python 文件，提取类、函数和导入关系
    """
    # 读取文件内容
    try:
        source = filepath.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
    except Exception as e:
        # 如果文件有语法错误或者读不了，直接跳过
        return [], []

    symbols = []
    imports = []

    # 遍历 AST 的节点
    for node in ast.walk(tree):
        # 提取类、普通函数、异步函数
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append({
                "name": node.name,
                "type": type(node).__name__,
                "lineno": node.lineno,
                "file": str(filepath),
                # ast.get_source_segment 可以精准截取这段代码的源码
                "code": ast.get_source_segment(source, node) or "",
            })
        # 提取 import 语句
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({"from": str(filepath), "to": alias.name})
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append({"from": str(filepath), "to": node.module})

    return symbols, imports


def parse_repo(root_dir: str):
    """
    遍历整个仓库目录，提取所有 Python 文件的符号
    """
    root_path = Path(root_dir)
    all_symbols = []
    all_imports = []

    # rglob('*.py') 会递归查找所有子文件夹里的 py 文件
    for py_file in root_path.rglob("*.py"):
        # 跳过虚拟环境文件夹，不然会把第三方库的代码也解析进去
        if ".venv" in py_file.parts or "venv" in py_file.parts:
            continue

        syms, imps = parse_file(py_file)
        all_symbols.extend(syms)
        all_imports.extend(imps)

    return all_symbols, all_imports


# 这一段是给我们在终端里单独测试用的
if __name__ == "__main__":
    # 我们可以先拿自己刚写的 app.py 测试一下
    print("正在解析当前目录...")
    symbols, imports = parse_repo(".")

    print(f"\n找到 {len(symbols)} 个类和函数：")
    for s in symbols:
        print(f" - [{s['type']}] {s['name']} (第 {s['lineno']} 行) 来自 {s['file']}")