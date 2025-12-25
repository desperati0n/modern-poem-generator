# Development Log - Modern Poem Generator

## 快速参考

### 项目路径
- **项目根目录**: `d:\study\口订\modern_poem_generator`
- **Python 环境**: `D:\study\口订\.venv\Scripts\python.exe`
- **语料库目录**: `corpus/`
- **输出目录**: `output/`

### 核心文件
| 文件 | 用途 |
|------|------|
| `main.py` | CLI 命令行版本（7个菜单选项，支持切换模式）|
| `gui.py` | Windows GUI 版本 (tkinter) |
| `src/model.py` | 所有生成模型 (MarkovChain, ImageryChain, StructuredPoemGenerator) |
| `src/utils.py` | 工具函数 (load_corpus, clean_and_tokenize, extract_imagery_and_connectors) |
| `run_tests.py` | 单元测试（5个测试用例）|
| `fetch_haizi.py` | 从本地 haizi_repo 提取诗歌的脚本 |

### 语料库
| 文件 | 内容 |
|------|------|
| `corpus/haizi.txt` | 原始 8 首海子诗 |
| `corpus/haizi_full.txt` | 扩展语料 - 240首诗，48272字符（已清洗，无数字/英文标点）|

### 三种生成模式
1. **structured (结构化)**: 状语短语 + 展开*N + 结尾
2. **imagery (意象链)**: 名词作意象，其它词连接意象 (仅GUI)
3. **markov (马尔可夫)**: 经典 n-gram 随机游走

### 运行命令
```powershell
# 运行 GUI（后台）
cd "d:\study\口订\modern_poem_generator"
Start-Process -FilePath "D:\study\口订\.venv\Scripts\pythonw.exe" -ArgumentList "gui.py"

# 运行 CLI
& "D:\study\口订\.venv\Scripts\python.exe" main.py

# 运行测试
& "D:\study\口订\.venv\Scripts\python.exe" run_tests.py
```

### 词性标签 (jieba.posseg)
用于识别意象词（名词类）：
```python
NOUN_POS_TAGS = {'n', 'nr', 'ns', 'nt', 'nz', 'ng', 'nrt', 'nrfg', 's', 't'}
# n=名词, nr=人名, ns=地名, nt=机构, nz=其他专名, s=处所, t=时间
```

### 结构化生成器视角（StructuredPoemGenerator.ADVERBIAL_PATTERNS）
- 时间、处所、方式、条件、程度、范围、肯定、否定、对象、情况

---

## 2025-12-24: 结构化生成器 & 语料库扩展

### 1. 语料库扩展
- 从 GitHub (haitai/haizi) 克隆海子诗集
- 使用 `fetch_haizi.py` 提取 240 首诗，48272 字符
- 清洗处理：去除数字、英文标点、中文括号

### 2. ImageryChain 模型
- 将词汇分为**意象词**（名词）和**连接词**（其它）
- 生成逻辑：意象 → 连接 → 意象 → 连接...
- 每行最多 3 个意象词

### 3. StructuredPoemGenerator 模型
- **结构**: 状语短语 + 展开*4 + 结尾
- **10种视角**: 时间、处所、方式、条件、程度、范围、肯定、否定、对象、情况
- **学习机制**: 从语料中提取符合模式的短语
- **方法**:
  - `generate_opening()` - 生成状语开头
  - `generate_expansion()` - 用意象词+连接词展开
  - `generate_ending()` - 从语料中选结尾句
  - `generate(expansion_count)` - 完整诗歌

### 4. GUI 更新
- 新增"structured"模式选项
- 加载时同时训练三个模型
- 状态栏显示意象词和结尾句数量

---

## 2025-12-24: Project Initialization & Beta Release

### 1. Architecture Design

- **Core Logic**: Decided to use a **Markov Chain (Order-2)** model. It balances randomness with local coherence, making it suitable for "abstract" modern poetry.
- **Language Support**: Integrated `jieba` for Chinese word segmentation. This is crucial because Chinese words are not space-separated like English.

### 2. "Haizi Style" Beta

- **Corpus**: Created `corpus/haizi.txt` containing classic poems like "Facing the Sea, with Spring Blossoms" (面朝大海，春暖花开) and "Asian Copper" (亚洲铜).
- **Goal**: The model learns 2-gram transitions (e.g., "面朝" -> "大海") to generate text that "feels" like Haizi but is completely new.

### 3. Implementation Details

- **`src/model.py`**:
  - Implemented `train(tokens)`: Builds a dictionary mapping `(word1, word2) -> [next_word, ...]`.
  - Implemented `generate()`: Performs a random walk on the chain. Added logic to handle newlines as tokens to preserve stanza structures.
- **`src/utils.py`**:
  - `clean_and_tokenize`: Handles file reading. Crucially, it treats `\n` as a distinct token so the model learns when to break lines.
- **`main.py`**:
  - Built an interactive CLI.
  - Features: Corpus selection, custom line count, file saving.

### 4. Current Status

- [x] Core generation logic working.
- [x] "Haizi" corpus ready.
- [x] CLI Menu working.
- [x] Auto-tests implemented.
- [x] Adjustable Markov order (1-3).
- [x] Enhanced error handling.
- [x] Output saved to dedicated `output/` folder.
- [x] `requirements.txt` added.
- [x] **GUI 版本 (tkinter)**
- [x] **ImageryChain 意象链模型**
- [x] **StructuredPoemGenerator 结构化生成器**
- [x] **扩展语料库 (240首海子诗)**

### 5. Next Steps

- [ ] Add more corpora (e.g., Xu Zhimo, Gu Cheng) - **需要手动收集语料**.
- [ ] Add "theme word" feature to guide generation.
- [ ] Support Markdown/HTML output format.
- [ ] 优化结构化生成器的短语学习
