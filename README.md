# 现代诗生成器 (Modern Poem Generator)

基于马尔可夫链、意象链和结构化模板的中文现代诗生成器。支持命令行 (CLI) 和 Web 界面，拥有海子风格及海量现代诗语料库。

## 特性

- 🌐 **Web 界面**：提供现代化、响应式的浏览器操作界面。
- 📚 **海量语料**：内置约 4500 首现代诗（含海子、食指、北岛等名家作品）。
- 🎨 **多模态生成**：
  - **结构化生成**：基于语义结构的填词生成。
  - **意象链生成**：基于意象关联的流意识生成。
  - **马尔可夫链**：经典的概率统计生成。
- ✂️ **中文分词**：集成 jieba 进行精准中文分词。
- 💾 **诗歌保存**：支持一键保存生成的诗歌。

## 安装

```bash
pip install -r requirements.txt
```

## 使用

### 1. Web 界面 (推荐)

启动 Web 服务器：

```bash
python web_app.py
```

然后访问：[http://localhost:5000](http://localhost:5000)

### 2. 命令行 (CLI)

```bash
python main.py
```

## 项目结构

```
modern_poem_generator/
├── corpus/                 # 语料库目录
│   ├── haizi_full.txt      # 海子全集
│   └── modern_huge.txt     # 现代诗大语料 (4000+首)
├── output/                 # 生成的诗歌保存位置
├── src/
│   ├── model.py            # 生成模型核心代码
│   └── utils.py            # 工具函数
├── templates/              # Web 界面模板
│   └── index.html
├── web_app.py              # Flask Web 应用入口
├── main.py                 # CLI 主程序入口
├── fetch_huge_corpus.py    # 语料抓取工具
└── requirements.txt        # 依赖列表
```

## 技术细节

- **多模型融合**：结合了统计概率（马尔可夫）与规则模板（结构化生成），使生成的诗歌既有随机性又有一定的语法结构。
- **意象提取**：自动分析语料库中的意象词（名词、形容词），构建意象关联图。
