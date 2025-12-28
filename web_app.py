"""
现代诗生成器 - Web 应用版本
使用 Flask 提供 Web 界面
"""

import os
import time
from flask import Flask, render_template, jsonify, request
from src.utils import load_corpus, clean_and_tokenize, extract_imagery_and_connectors
from src.model import MarkovChain, ImageryChain, StructuredPoemGenerator

app = Flask(__name__)

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORPUS_DIR = os.path.join(BASE_DIR, "corpus")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 全局模型存储
models = {
    "markov": None,
    "imagery": None,
    "structured": None,
    "current_corpus": "haizi_full.txt",
    "markov_order": 2,
}


def load_models(corpus_file, order=2):
    """加载语料并训练所有模型"""
    try:
        filepath = os.path.join(CORPUS_DIR, corpus_file)
        text = load_corpus(filepath)

        if text is None:
            return False, "无法加载语料库"

        # 保存原始诗行
        raw_lines = [line.strip() for line in text.split("\n") if line.strip()]

        # 普通分词
        tokens = clean_and_tokenize(text)
        if not tokens:
            return False, "语料库为空或分词失败"

        # 训练马尔可夫模型
        models["markov"] = MarkovChain(order=order)
        models["markov"].train(tokens)

        # 提取意象和连接词
        imagery, connectors, token_data = extract_imagery_and_connectors(text)

        # 训练意象模型
        models["imagery"] = ImageryChain()
        models["imagery"].train(token_data)

        # 训练结构化模型
        models["structured"] = StructuredPoemGenerator()
        models["structured"].train(token_data, raw_lines)

        models["current_corpus"] = corpus_file
        models["markov_order"] = order

        return True, "模型加载成功"
    except Exception as e:
        return False, f"加载失败: {str(e)}"


@app.route("/")
def index():
    """主页"""
    return render_template("index.html")


@app.route("/api/corpus/list")
def list_corpus():
    """获取语料库列表"""
    try:
        files = [f for f in os.listdir(CORPUS_DIR) if f.endswith(".txt")]
        return jsonify(
            {"success": True, "corpus_list": files, "current": models["current_corpus"]}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/corpus/load", methods=["POST"])
def load_corpus_api():
    """加载语料库"""
    data = request.json
    corpus_file = data.get("corpus", "haizi_full.txt")
    order = data.get("order", 2)

    success, message = load_models(corpus_file, order)

    if success:
        stats = models["structured"].get_stats()
        return jsonify({"success": True, "message": message, "stats": stats})
    else:
        return jsonify({"success": False, "error": message})


@app.route("/api/generate", methods=["POST"])
def generate_poem():
    """生成诗歌"""
    data = request.json
    mode = data.get("mode", "structured")
    num_lines = data.get("num_lines", 4)

    try:
        if mode == "structured":
            if models["structured"] is None:
                return jsonify({"success": False, "error": "模型未加载"})
            poem = models["structured"].generate(expansion_count=num_lines)
            mode_label = "结构化"
        elif mode == "imagery":
            if models["imagery"] is None:
                return jsonify({"success": False, "error": "模型未加载"})
            poem = models["imagery"].generate(num_lines, max_imagery_per_line=3)
            mode_label = "意象链"
        else:  # markov
            if models["markov"] is None:
                return jsonify({"success": False, "error": "模型未加载"})
            poem = models["markov"].generate(num_lines)
            mode_label = f"马尔可夫-{models['markov_order']}阶"

        return jsonify(
            {
                "success": True,
                "poem": poem,
                "mode_label": mode_label,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/save", methods=["POST"])
def save_poem():
    """保存诗歌"""
    data = request.json
    poem = data.get("poem", "")

    if not poem:
        return jsonify({"success": False, "error": "没有诗歌内容"})

    try:
        fname = f"poem_{int(time.time())}.txt"
        fpath = os.path.join(OUTPUT_DIR, fname)

        with open(fpath, "w", encoding="utf-8") as f:
            f.write(f"# 生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 风格: {models['current_corpus']}\n\n")
            f.write(poem)

        return jsonify({"success": True, "filename": fname, "path": fpath})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/stats")
def get_stats():
    """获取统计信息"""
    if models["structured"]:
        stats = models["structured"].get_stats()
        stats["current_corpus"] = models["current_corpus"]
        stats["markov_order"] = models["markov_order"]
        return jsonify({"success": True, "stats": stats})
    else:
        return jsonify({"success": False, "error": "模型未加载"})


if __name__ == "__main__":
    # 初始化加载默认语料库
    print("正在加载默认语料库...")
    success, message = load_models("haizi_full.txt", 2)
    if success:
        print(f"✓ {message}")
    else:
        print(f"✗ {message}")

    print("\n" + "=" * 50)
    print("🎨 现代诗生成器 Web 应用")
    print("=" * 50)
    print("📍 访问地址: http://localhost:5000")
    print("🛑 按 Ctrl+C 停止服务器")
    print("=" * 50 + "\n")

    app.run(debug=True, host="0.0.0.0", port=5000)
