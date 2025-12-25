"""
现代诗生成器 - Windows GUI 版本
使用 tkinter 构建图形界面
"""

import os
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from src.utils import load_corpus, clean_and_tokenize, extract_imagery_and_connectors
from src.model import MarkovChain, ImageryChain, StructuredPoemGenerator

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORPUS_DIR = os.path.join(BASE_DIR, "corpus")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


class PoemGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("现代诗生成器 - 海子风格")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # 设置窗口图标（如果有的话）
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # 模型相关变量
        self.model = None
        self.imagery_model = None  # 意象模型
        self.structured_model = None  # 结构化模型
        self.tokens = None
        self.token_data = None  # 词性标注数据
        self.raw_lines = []  # 原始诗行
        self.current_corpus = tk.StringVar(value="haizi.txt")
        self.poem_length = tk.IntVar(value=4)
        self.markov_order = tk.IntVar(value=2)
        self.generation_mode = tk.StringVar(value="structured")  # 默认结构化模式
        self.last_poem = ""
        
        # 创建界面
        self.create_widgets()
        
        # 初始化加载语料库
        self.load_model()
    
    def create_widgets(self):
        """创建所有界面组件"""
        
        # ===== 顶部控制区 =====
        control_frame = ttk.LabelFrame(self.root, text="设置", padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # 第一行：语料库选择
        row1 = ttk.Frame(control_frame)
        row1.pack(fill="x", pady=2)
        
        ttk.Label(row1, text="风格/语料库:").pack(side="left", padx=(0, 5))
        self.corpus_combo = ttk.Combobox(row1, textvariable=self.current_corpus, 
                                          state="readonly", width=20)
        self.corpus_combo['values'] = self.get_corpus_list()
        self.corpus_combo.pack(side="left", padx=(0, 10))
        self.corpus_combo.bind("<<ComboboxSelected>>", lambda e: self.load_model())
        
        # 第二行：长度和阶数
        row2 = ttk.Frame(control_frame)
        row2.pack(fill="x", pady=5)
        
        ttk.Label(row2, text="生成行数:").pack(side="left", padx=(0, 5))
        length_spin = ttk.Spinbox(row2, from_=1, to=20, width=5, 
                                   textvariable=self.poem_length)
        length_spin.pack(side="left", padx=(0, 20))
        
        ttk.Label(row2, text="生成模式:").pack(side="left", padx=(0, 5))
        mode_combo = ttk.Combobox(row2, textvariable=self.generation_mode, 
                                   state="readonly", width=12)
        mode_combo['values'] = ["structured", "imagery", "markov"]
        mode_combo.pack(side="left", padx=(0, 10))
        
        # 模式说明
        ttk.Label(row2, text="(结构化/意象链/马尔可夫)", 
                  foreground="gray").pack(side="left")
        
        # 第三行：马尔可夫阶数（仅 markov 模式用）
        row3 = ttk.Frame(control_frame)
        row3.pack(fill="x", pady=2)
        
        ttk.Label(row3, text="马尔可夫阶数:").pack(side="left", padx=(0, 5))
        order_combo = ttk.Combobox(row3, textvariable=self.markov_order, 
                                    state="readonly", width=5)
        order_combo['values'] = [1, 2, 3]
        order_combo.pack(side="left", padx=(0, 10))
        order_combo.bind("<<ComboboxSelected>>", lambda e: self.load_model())
        
        ttk.Label(row3, text="(1=最随机, 2=平衡, 3=最连贯) - 仅 markov 模式生效", 
                  foreground="gray").pack(side="left")
        
        # ===== 按钮区 =====
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        self.generate_btn = ttk.Button(btn_frame, text="🎲 生成诗歌", 
                                        command=self.generate_poem)
        self.generate_btn.pack(side="left", padx=(0, 10))
        
        self.save_btn = ttk.Button(btn_frame, text="💾 保存", 
                                    command=self.save_poem)
        self.save_btn.pack(side="left", padx=(0, 10))
        
        self.copy_btn = ttk.Button(btn_frame, text="📋 复制", 
                                    command=self.copy_poem)
        self.copy_btn.pack(side="left", padx=(0, 10))
        
        self.clear_btn = ttk.Button(btn_frame, text="🗑️ 清空", 
                                     command=self.clear_output)
        self.clear_btn.pack(side="left")
        
        # ===== 输出区 =====
        output_frame = ttk.LabelFrame(self.root, text="生成结果", padding=10)
        output_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 文本框 + 滚动条
        text_frame = ttk.Frame(output_frame)
        text_frame.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.output_text = tk.Text(text_frame, wrap="word", font=("Microsoft YaHei", 14),
                                    yscrollcommand=scrollbar.set, padx=10, pady=10)
        self.output_text.pack(fill="both", expand=True)
        scrollbar.config(command=self.output_text.yview)
        
        # 设置文本样式
        self.output_text.tag_configure("poem", foreground="#2c3e50", 
                                        spacing1=5, spacing3=5)
        self.output_text.tag_configure("separator", foreground="#bdc3c7")
        
        # ===== 状态栏 =====
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                                relief="sunken", anchor="w")
        status_bar.pack(fill="x", padx=10, pady=(0, 5))
    
    def get_corpus_list(self):
        """获取语料库列表"""
        try:
            files = [f for f in os.listdir(CORPUS_DIR) if f.endswith(".txt")]
            return files if files else ["haizi.txt"]
        except:
            return ["haizi.txt"]
    
    def load_model(self):
        """加载语料库并训练模型"""
        corpus_file = self.current_corpus.get()
        order = self.markov_order.get()
        
        self.status_var.set(f"正在加载 {corpus_file}...")
        self.root.update()
        
        try:
            filepath = os.path.join(CORPUS_DIR, corpus_file)
            text = load_corpus(filepath)
            
            if text is None:
                messagebox.showerror("错误", f"无法加载语料库: {corpus_file}")
                return
            
            # 保存原始诗行（用于结构化模型）
            self.raw_lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # 普通分词（用于马尔可夫模型）
            self.tokens = clean_and_tokenize(text)
            if not self.tokens:
                messagebox.showerror("错误", "语料库为空或分词失败")
                return
            
            # 训练马尔可夫模型
            self.model = MarkovChain(order=order)
            self.model.train(self.tokens)
            
            # 提取意象和连接词（用于意象模型）
            imagery, connectors, token_data = extract_imagery_and_connectors(text)
            self.token_data = token_data
            
            # 训练意象模型
            self.imagery_model = ImageryChain()
            self.imagery_model.train(token_data)
            
            # 训练结构化模型
            self.structured_model = StructuredPoemGenerator()
            self.structured_model.train(token_data, self.raw_lines)
            
            # 显示统计信息
            stats = self.structured_model.get_stats()
            self.status_var.set(
                f"已加载: {corpus_file} | 意象: {stats['意象词数量']} | 结尾句: {stats['结尾句数量']}"
            )
        except Exception as e:
            messagebox.showerror("错误", f"加载失败: {str(e)}")
            self.status_var.set("加载失败")
    
    def generate_poem(self):
        """生成诗歌"""
        mode = self.generation_mode.get()
        
        # 检查模型是否已加载
        if mode == "structured" and self.structured_model is None:
            messagebox.showwarning("提示", "请先加载语料库")
            return
        if mode == "imagery" and self.imagery_model is None:
            messagebox.showwarning("提示", "请先加载语料库")
            return
        if mode == "markov" and self.model is None:
            messagebox.showwarning("提示", "请先加载语料库")
            return
        
        num_lines = self.poem_length.get()
        
        self.status_var.set("正在生成...")
        self.root.update()
        
        try:
            if mode == "structured":
                # 使用结构化生成器（状语+展开+结尾）
                self.last_poem = self.structured_model.generate(expansion_count=num_lines)
                mode_label = "结构化"
            elif mode == "imagery":
                # 使用意象链生成
                self.last_poem = self.imagery_model.generate(num_lines, max_imagery_per_line=3)
                mode_label = "意象链"
            else:
                # 使用马尔可夫链生成
                self.last_poem = self.model.generate(num_lines)
                mode_label = f"马尔可夫-{self.markov_order.get()}阶"
            
            # 添加分隔线和模式标签
            self.output_text.insert("end", f"─── [{mode_label}] ───\n", "separator")
            self.output_text.insert("end", self.last_poem + "\n\n", "poem")
            
            # 滚动到底部
            self.output_text.see("end")
            
            self.status_var.set(f"生成完成 - {num_lines} 行 ({mode_label})")
        except Exception as e:
            messagebox.showerror("错误", f"生成失败: {str(e)}")
            self.status_var.set("生成失败")
    
    def save_poem(self):
        """保存诗歌"""
        if not self.last_poem:
            messagebox.showinfo("提示", "还没有生成诗歌，请先点击生成按钮")
            return
        
        # 默认文件名
        default_name = f"poem_{int(time.time())}.txt"
        
        filepath = filedialog.asksaveasfilename(
            initialdir=OUTPUT_DIR,
            initialfile=default_name,
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"# 生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# 风格: {self.current_corpus.get()} | 阶数: {self.markov_order.get()}\n\n")
                    f.write(self.last_poem)
                
                self.status_var.set(f"已保存: {os.path.basename(filepath)}")
                messagebox.showinfo("成功", f"诗歌已保存到:\n{filepath}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def copy_poem(self):
        """复制到剪贴板"""
        if not self.last_poem:
            messagebox.showinfo("提示", "还没有生成诗歌")
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(self.last_poem)
        self.status_var.set("已复制到剪贴板")
    
    def clear_output(self):
        """清空输出"""
        self.output_text.delete("1.0", "end")
        self.last_poem = ""
        self.status_var.set("已清空")


def main():
    root = tk.Tk()
    
    # 设置 DPI 感知（Windows 10+）
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    app = PoemGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
