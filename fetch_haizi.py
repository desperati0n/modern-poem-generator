"""
海子诗歌提取脚本
从本地 haizi_repo 目录提取诗歌文本
"""

import os
import re
import glob
from html.parser import HTMLParser


class PoemExtractor(HTMLParser):
    """从 HTML 中提取诗歌文本"""
    
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.in_blockquote = False
        self.in_p = False
        self.depth = 0
    
    def handle_starttag(self, tag, attrs):
        if tag == 'blockquote':
            self.in_blockquote = True
            self.depth += 1
        elif tag == 'p' and self.in_blockquote:
            self.in_p = True
        elif tag == 'br':
            self.text_parts.append('\n')
    
    def handle_endtag(self, tag):
        if tag == 'blockquote':
            self.depth -= 1
            if self.depth <= 0:
                self.in_blockquote = False
                self.depth = 0
        elif tag == 'p':
            self.in_p = False
            self.text_parts.append('\n')
    
    def handle_data(self, data):
        if self.in_blockquote:
            text = data.strip()
            if text:
                # 过滤掉一些不需要的内容
                if not any(skip in text for skip in ['〖', '〗', '&gt;', '——————', '————————', '*']):
                    self.text_parts.append(text)
    
    def get_text(self):
        result = ''.join(self.text_parts)
        # 清理
        result = re.sub(r'　+', '', result)  # 移除全角空格
        result = re.sub(r'\n\s*\n\s*\n+', '\n\n', result)  # 合并多余空行
        result = re.sub(r'^\s+', '', result, flags=re.MULTILINE)  # 移除行首空白
        
        # 过滤数字和英文标点
        result = re.sub(r'\d+', '', result)  # 移除所有数字
        result = re.sub(r'[.?!,;:\'\"\(\)\[\]{}]+', '', result)  # 移除英文标点
        result = re.sub(r'[（）【】]+', '', result)  # 移除中文括号
        
        # 移除日期行（如 "1984.10" 变成空行后的残留）
        result = re.sub(r'^\s*$', '', result, flags=re.MULTILINE)  # 移除空行
        result = re.sub(r'\n\n+', '\n\n', result)  # 合并多余空行
        
        return result.strip()


def extract_poem_from_file(filepath):
    """从 HTML 文件提取诗歌文本"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        parser = PoemExtractor()
        parser.feed(content)
        return parser.get_text()
    except Exception as e:
        print(f"  [错误] {filepath}: {e}")
        return ""


def main():
    print("=" * 50)
    print("海子诗歌提取脚本 (本地版)")
    print("=" * 50)
    
    base_dir = os.path.join(os.path.dirname(__file__), "haizi_repo")
    
    if not os.path.exists(base_dir):
        print("错误: haizi_repo 目录不存在，请先运行:")
        print("  git clone https://github.com/haitai/haizi.git haizi_repo")
        return
    
    # 收集所有诗歌 HTML 文件
    htm_files = []
    
    # 短诗 1983-1986 (01 目录)
    htm_files.extend(sorted(glob.glob(os.path.join(base_dir, "01", "*.htm"))))
    
    # 短诗 1987-1989 (03 目录)
    htm_files.extend(sorted(glob.glob(os.path.join(base_dir, "03", "*.htm"))))
    
    print(f"找到 {len(htm_files)} 个诗歌文件\n")
    
    all_poems = []
    
    for i, filepath in enumerate(htm_files, 1):
        filename = os.path.basename(filepath)
        print(f"[{i}/{len(htm_files)}] 提取: {filename}")
        
        poem = extract_poem_from_file(filepath)
        if poem and len(poem) > 30:
            all_poems.append(poem)
            print(f"  ✓ 提取 {len(poem)} 字符")
        else:
            print(f"  - 内容太短或为空，跳过")
    
    print("\n" + "=" * 50)
    print(f"提取完成！成功: {len(all_poems)}/{len(htm_files)}")
    
    # 保存到 corpus 目录
    output_path = os.path.join(os.path.dirname(__file__), "corpus", "haizi_full.txt")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(all_poems))
    
    total_chars = sum(len(p) for p in all_poems)
    print(f"已保存到: {output_path}")
    print(f"总诗歌数: {len(all_poems)}")
    print(f"总字符数: {total_chars}")
    
    # 删除临时仓库 (可选)
    # import shutil
    # shutil.rmtree(base_dir)
    # print("已清理临时文件")


if __name__ == "__main__":
    main()
