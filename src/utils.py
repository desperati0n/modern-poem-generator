import jieba
import jieba.posseg as pseg
import re
import os


def load_corpus(filepath):
    """Reads text file and returns raw string."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def clean_and_tokenize(text):
    """
    Cleans text and uses jieba to tokenize.
    Returns a list of tokens.
    We keep newlines as tokens to preserve poem structure.
    """
    # Normalize newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # We want to treat newlines as distinct tokens to learn line breaks
    # Strategy: Replace \n with a special placeholder, tokenize, then putting it back or just handle it
    # Easier: Split by lines, tokenize each line, add a newline token at end of each line

    lines = text.split("\n")
    tokens = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Segment line
        line_tokens = jieba.lcut(line)
        tokens.extend(line_tokens)
        tokens.append("\n")

    return tokens


# 名词词性标记（jieba posseg）
NOUN_POS_TAGS = {
    'n',    # 普通名词
    'nr',   # 人名
    'ns',   # 地名
    'nt',   # 机构名
    'nz',   # 其他专名
    'ng',   # 名词性语素
    'nrt',  # 音译人名
    'nrfg', # 人名
    's',    # 处所词
    't',    # 时间词
}


def tokenize_with_pos(text):
    """
    使用词性标注分词，返回 (tokens, pos_tags) 两个列表
    tokens: 词语列表
    pos_tags: 对应的词性标记列表
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    
    tokens = []
    pos_tags = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 词性标注分词
        words = pseg.lcut(line)
        for word, pos in words:
            tokens.append(word)
            pos_tags.append(pos)
        
        tokens.append("\n")
        pos_tags.append("x")  # 标点符号类
    
    return tokens, pos_tags


def extract_imagery_and_connectors(text):
    """
    从文本中提取意象词（名词）和连接词（其他词）
    返回:
        imagery: set of nouns (意象)
        connectors: set of other words (连接词)
        token_data: list of (word, pos, is_imagery) 用于训练
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    
    imagery = set()       # 意象词集合
    connectors = set()    # 连接词集合
    token_data = []       # (word, pos, is_imagery)
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        words = pseg.lcut(line)
        for word, pos in words:
            is_imagery = pos in NOUN_POS_TAGS
            
            if is_imagery:
                imagery.add(word)
            else:
                # 过滤掉纯标点
                if word.strip() and not re.match(r'^[，。、；：？！""''（）\\s]+$', word):
                    connectors.add(word)
            
            token_data.append((word, pos, is_imagery))
        
        # 换行符
        token_data.append(("\n", "x", False))
    
    return imagery, connectors, token_data
