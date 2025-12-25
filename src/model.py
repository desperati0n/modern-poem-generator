import random


class MarkovChain:
    def __init__(self, order=2):
        self.order = order
        self.chain = {}
        self.starts = []  # Keys that can start a line

    def train(self, tokens):
        """
        Builds the Markov Chain from a list of tokens.
        """
        if len(tokens) < self.order:
            return

        # Record the first key as a valid start
        first_key = tuple(tokens[: self.order])
        self.starts.append(first_key)

        for i in range(len(tokens) - self.order):
            # Current state (tuple of length 'order')
            current = tuple(tokens[i : i + self.order])
            # Next token
            next_token = tokens[i + self.order]

            # Add to chain
            if current not in self.chain:
                self.chain[current] = []
            self.chain[current].append(next_token)

            # If the current state ends with a newline, the NEXT state is a start of a new line
            # logic: if tokens[i] was '\n', then tokens[i+1]... starts a line?
            # Actually simplest way: if the token *before* the current key was \n, then this key is a start.
            # But here we are iterating i.
            # If tokens[i-1] was \n, then tokens[i:i+order] is a start.
            if i > 0 and tokens[i - 1] == "\n":
                self.starts.append(current)

    def generate_line(self):
        """Generates a single line of poetry"""
        if not self.chain:
            return "Model not trained."

        # Pick a random starting point
        if self.starts:
            current = random.choice(self.starts)
        else:
            current = random.choice(list(self.chain.keys()))

        words = list(current)

        # Walk the chain
        # Safety break to prevent infinite lines if \n is missing
        max_words = 20
        count = 0

        while count < max_words:
            if current not in self.chain:
                break

            next_word = random.choice(self.chain[current])

            if next_word == "\n":
                break

            words.append(next_word)
            # Shift window: (1, 2) -> (2, 3)
            current = tuple(words[-self.order :])
            count += 1

        return "".join(words)

    def generate(self, num_lines=5):
        """Generates a poem with num_lines"""
        poem = []
        for _ in range(num_lines):
            line = self.generate_line()
            # Avoid empty lines
            if line.strip():
                poem.append(line)
        return "\n".join(poem)


class ImageryChain:
    """
    基于意象的诗歌生成模型
    
    核心思想：
    - 意象词（名词）作为诗歌的核心锚点
    - 连接词（动词、形容词等）将意象串联起来
    - 学习 意象→连接→意象 的转移模式
    """
    
    def __init__(self):
        self.imagery = set()           # 所有意象词
        self.connectors = set()        # 所有连接词
        
        # 转移概率表
        self.imagery_to_connector = {} # 意象 -> [可能的连接词...]
        self.connector_to_imagery = {} # 连接词 -> [可能的意象...]
        self.imagery_to_imagery = {}   # 意象 -> [可能的下一个意象...] (直接相邻的情况)
        
        # 句首意象
        self.line_starters = []
        
        # 连接词序列（多个连接词连续出现的情况）
        self.connector_sequences = {}  # 连接词 -> [下一个连接词...]
    
    def train(self, token_data):
        """
        训练模型
        token_data: list of (word, pos, is_imagery) from extract_imagery_and_connectors
        """
        if not token_data:
            return
        
        # 收集所有意象和连接词
        for word, pos, is_imagery in token_data:
            if word == "\n":
                continue
            if is_imagery:
                self.imagery.add(word)
            else:
                self.connectors.add(word)
        
        # 构建转移关系
        prev_word = None
        prev_is_imagery = None
        is_line_start = True
        
        for word, pos, is_imagery in token_data:
            if word == "\n":
                is_line_start = True
                prev_word = None
                prev_is_imagery = None
                continue
            
            # 记录句首意象
            if is_line_start and is_imagery:
                self.line_starters.append(word)
            is_line_start = False
            
            # 建立转移关系
            if prev_word is not None:
                if prev_is_imagery and not is_imagery:
                    # 意象 -> 连接词
                    if prev_word not in self.imagery_to_connector:
                        self.imagery_to_connector[prev_word] = []
                    self.imagery_to_connector[prev_word].append(word)
                    
                elif not prev_is_imagery and is_imagery:
                    # 连接词 -> 意象
                    if prev_word not in self.connector_to_imagery:
                        self.connector_to_imagery[prev_word] = []
                    self.connector_to_imagery[prev_word].append(word)
                    
                elif prev_is_imagery and is_imagery:
                    # 意象 -> 意象 (直接相邻)
                    if prev_word not in self.imagery_to_imagery:
                        self.imagery_to_imagery[prev_word] = []
                    self.imagery_to_imagery[prev_word].append(word)
                    
                else:
                    # 连接词 -> 连接词
                    if prev_word not in self.connector_sequences:
                        self.connector_sequences[prev_word] = []
                    self.connector_sequences[prev_word].append(word)
            
            prev_word = word
            prev_is_imagery = is_imagery
    
    def generate_line(self, max_imagery=3):
        """
        生成一行诗
        max_imagery: 一行最多包含几个意象
        """
        if not self.imagery:
            return "模型未训练"
        
        # 选择起始意象
        if self.line_starters:
            current_imagery = random.choice(self.line_starters)
        else:
            current_imagery = random.choice(list(self.imagery))
        
        line_parts = [current_imagery]
        imagery_count = 1
        
        while imagery_count < max_imagery:
            # 尝试找连接词
            connector_seq = []
            
            if current_imagery in self.imagery_to_connector:
                connector = random.choice(self.imagery_to_connector[current_imagery])
                connector_seq.append(connector)
                
                # 可能有连续的连接词
                while connector in self.connector_sequences and random.random() < 0.6:
                    next_conn = random.choice(self.connector_sequences[connector])
                    connector_seq.append(next_conn)
                    connector = next_conn
                
                line_parts.extend(connector_seq)
                
                # 找下一个意象
                last_connector = connector_seq[-1]
                if last_connector in self.connector_to_imagery:
                    next_imagery = random.choice(self.connector_to_imagery[last_connector])
                    line_parts.append(next_imagery)
                    current_imagery = next_imagery
                    imagery_count += 1
                else:
                    # 没有对应意象，随机选一个
                    if random.random() < 0.5 and self.imagery:
                        next_imagery = random.choice(list(self.imagery))
                        line_parts.append(next_imagery)
                        current_imagery = next_imagery
                        imagery_count += 1
                    else:
                        break
                        
            elif current_imagery in self.imagery_to_imagery:
                # 意象直接相邻
                next_imagery = random.choice(self.imagery_to_imagery[current_imagery])
                line_parts.append(next_imagery)
                current_imagery = next_imagery
                imagery_count += 1
            else:
                # 没有后续，结束
                break
        
        return "".join(line_parts)
    
    def generate(self, num_lines=5, max_imagery_per_line=3):
        """生成多行诗"""
        poem = []
        for _ in range(num_lines):
            line = self.generate_line(max_imagery=max_imagery_per_line)
            if line.strip() and line != "模型未训练":
                poem.append(line)
        return "\n".join(poem) if poem else "模型未训练"
    
    def get_stats(self):
        """返回模型统计信息"""
        return {
            "意象词数量": len(self.imagery),
            "连接词数量": len(self.connectors),
            "意象→连接 关系": len(self.imagery_to_connector),
            "连接→意象 关系": len(self.connector_to_imagery),
            "句首意象数量": len(set(self.line_starters)),
        }


class StructuredPoemGenerator:
    """
    结构化诗歌生成器
    
    诗歌结构：
    1. 状语短语（开篇，设定情境）
    2. 展开 × 4（从不同角度展开意象）
    3. 结尾（收束）
    
    展开角度：情况、时间、处所、方式、条件、对象、肯定、否定、范围、程度
    """
    
    # 状语模板词库（用于构建不同角度的句子）
    ADVERBIAL_PATTERNS = {
        "时间": ["在……时", "当……", "……之后", "……之前", "那一夜", "今夜", "黎明", "黄昏", "春天", "秋天", "冬天"],
        "处所": ["在……", "从……", "向……", "……之上", "……之中", "……深处", "远方", "故乡", "天边", "大地上"],
        "方式": ["像……一样", "如同……", "仿佛……", "默默地", "静静地", "缓缓地", "轻轻地", "悄悄地"],
        "条件": ["如果……", "假如……", "只要……", "除非……", "一旦……"],
        "程度": ["更……", "最……", "多么……", "如此……", "这般……", "无比……"],
        "范围": ["所有的……", "一切……", "唯有……", "只有……", "全部的……"],
        "肯定": ["是……", "正是……", "必然……", "一定……", "终将……"],
        "否定": ["不是……", "并非……", "没有……", "不曾……", "再也不……", "永远不……"],
        "对象": ["给……", "向……", "对……", "为了……", "关于……"],
        "情况": ["于是……", "就这样……", "因此……", "然而……", "但是……"],
    }
    
    # 结尾模式
    ENDING_PATTERNS = [
        "而我……",
        "只剩下……",
        "这就是……",
        "从此……",
        "永远……",
        "直到……",
        "最后……",
    ]
    
    def __init__(self):
        self.imagery_chain = None
        self.imagery = set()
        self.connectors = set()
        
        # 从语料中学习的短语库
        self.learned_phrases = {
            "时间": [],
            "处所": [],
            "方式": [],
            "条件": [],
            "程度": [],
            "范围": [],
            "肯定": [],
            "否定": [],
            "对象": [],
            "情况": [],
        }
        
        # 学习的意象组合
        self.imagery_combinations = []
        
        # 学习的结尾句
        self.endings = []
    
    def train(self, token_data, raw_lines):
        """
        训练模型
        token_data: 词性标注数据
        raw_lines: 原始诗行列表（用于学习完整短语）
        """
        # 训练意象链
        from src.utils import NOUN_POS_TAGS
        
        for word, pos, is_imagery in token_data:
            if word == "\n":
                continue
            if is_imagery:
                self.imagery.add(word)
            else:
                self.connectors.add(word)
        
        # 从原始诗行中学习短语模式
        self._learn_phrases_from_lines(raw_lines)
        
        # 学习意象组合
        self._learn_imagery_combinations(token_data)
    
    def _learn_phrases_from_lines(self, lines):
        """从诗行中学习不同类型的短语"""
        
        time_keywords = ["夜", "晨", "黎明", "黄昏", "春", "夏", "秋", "冬", "今", "昨", "明", "月", "日", "年", "时"]
        place_keywords = ["在", "从", "向", "里", "中", "上", "下", "旁", "边", "处", "乡", "城", "山", "海", "河", "天", "地"]
        manner_keywords = ["像", "如", "仿佛", "似", "般", "地"]
        condition_keywords = ["如果", "假如", "只要", "除非", "若"]
        degree_keywords = ["更", "最", "多么", "如此", "这般", "无比", "极"]
        scope_keywords = ["所有", "一切", "唯有", "只有", "全部", "每"]
        positive_keywords = ["是", "正是", "必然", "一定", "终将", "就是"]
        negative_keywords = ["不", "没", "无", "非", "莫", "勿", "别"]
        object_keywords = ["给", "向", "对", "为", "关于", "属于"]
        situation_keywords = ["于是", "就这样", "因此", "然而", "但是", "所以", "却"]
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 4:
                continue
            
            # 检测并分类短语
            if any(k in line for k in time_keywords):
                self.learned_phrases["时间"].append(line)
            if any(k in line for k in place_keywords):
                self.learned_phrases["处所"].append(line)
            if any(k in line for k in manner_keywords):
                self.learned_phrases["方式"].append(line)
            if any(k in line for k in condition_keywords):
                self.learned_phrases["条件"].append(line)
            if any(k in line for k in degree_keywords):
                self.learned_phrases["程度"].append(line)
            if any(k in line for k in scope_keywords):
                self.learned_phrases["范围"].append(line)
            if any(k in line for k in positive_keywords):
                self.learned_phrases["肯定"].append(line)
            if any(k in line for k in negative_keywords):
                self.learned_phrases["否定"].append(line)
            if any(k in line for k in object_keywords):
                self.learned_phrases["对象"].append(line)
            if any(k in line for k in situation_keywords):
                self.learned_phrases["情况"].append(line)
            
            # 学习结尾（较短的、有终结感的句子）
            ending_keywords = ["而我", "只剩", "这就是", "从此", "永远", "直到", "最后", "终于", "就这样"]
            if any(k in line for k in ending_keywords) or (len(line) < 15 and line.endswith(("了", "去", "来", "着"))):
                self.endings.append(line)
    
    def _learn_imagery_combinations(self, token_data):
        """学习意象组合模式"""
        current_combination = []
        
        for word, pos, is_imagery in token_data:
            if word == "\n":
                if len(current_combination) >= 2:
                    self.imagery_combinations.append(current_combination.copy())
                current_combination = []
            elif is_imagery:
                current_combination.append(word)
    
    def generate_opening(self):
        """生成开篇状语短语"""
        # 优先从时间、处所、方式中选择
        opening_types = ["时间", "处所", "方式"]
        
        for t in opening_types:
            if self.learned_phrases[t]:
                return random.choice(self.learned_phrases[t])
        
        # 后备：用意象生成
        if self.imagery:
            img = random.choice(list(self.imagery))
            patterns = ["在{}的深处", "当{}沉默", "{}之上"]
            return random.choice(patterns).format(img)
        
        return "在远方"
    
    def generate_expansion(self, perspective):
        """
        生成展开句
        perspective: 展开角度（时间/处所/方式/条件/程度/范围/肯定/否定/对象/情况）
        """
        # 优先使用学习到的短语
        if self.learned_phrases[perspective]:
            return random.choice(self.learned_phrases[perspective])
        
        # 后备：用意象 + 连接词生成
        if self.imagery and self.connectors:
            img1 = random.choice(list(self.imagery))
            img2 = random.choice(list(self.imagery))
            conn = random.choice(list(self.connectors))
            
            templates = {
                "时间": "{}的时候，{}{}",
                "处所": "在{}里，{}{}",
                "方式": "像{}一样，{}{}",
                "条件": "如果有{}，就有{}",
                "程度": "多么{}的{}",
                "范围": "所有的{}都是{}",
                "肯定": "{}正是{}",
                "否定": "没有{}，也没有{}",
                "对象": "给{}的{}",
                "情况": "于是{}和{}",
            }
            
            template = templates.get(perspective, "{}{}{}".format(img1, conn, img2))
            if "{}" in template:
                return template.format(img1, conn, img2) if template.count("{}") == 3 else template.format(img1, img2)
        
        return ""
    
    def generate_ending(self):
        """生成结尾句"""
        if self.endings:
            return random.choice(self.endings)
        
        if self.imagery:
            img = random.choice(list(self.imagery))
            patterns = [
                "而我只有{}",
                "只剩下{}在远方",
                "这就是{}的全部",
                "从此与{}为伴",
                "永远属于{}",
            ]
            return random.choice(patterns).format(img)
        
        return "而我沉默"
    
    def generate(self, expansion_count=4):
        """
        生成结构化诗歌
        
        结构：
        - 开篇（状语短语）
        - 展开 × expansion_count（从不同角度）
        - 结尾
        """
        poem_lines = []
        
        # 1. 开篇
        opening = self.generate_opening()
        poem_lines.append(opening)
        poem_lines.append("")  # 空行分隔
        
        # 2. 展开（从不同角度选择）
        perspectives = list(self.learned_phrases.keys())
        random.shuffle(perspectives)
        
        used_perspectives = []
        for i in range(expansion_count):
            # 选择一个未用过的角度
            perspective = perspectives[i % len(perspectives)]
            used_perspectives.append(perspective)
            
            expansion = self.generate_expansion(perspective)
            if expansion:
                poem_lines.append(expansion)
        
        poem_lines.append("")  # 空行分隔
        
        # 3. 结尾
        ending = self.generate_ending()
        poem_lines.append(ending)
        
        return "\n".join(poem_lines)
    
    def get_stats(self):
        """返回统计信息"""
        phrase_counts = {k: len(v) for k, v in self.learned_phrases.items()}
        return {
            "意象词数量": len(self.imagery),
            "连接词数量": len(self.connectors),
            "学习的短语": phrase_counts,
            "结尾句数量": len(self.endings),
            "意象组合数量": len(self.imagery_combinations),
        }

