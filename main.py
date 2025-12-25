import os
import time
from src.utils import load_corpus, clean_and_tokenize, extract_imagery_and_connectors
from src.model import MarkovChain, StructuredPoemGenerator

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "corpus")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def list_corpora():
    files = [f for f in os.listdir(CORPUS_DIR) if f.endswith(".txt")]
    return files


def main():
    # Defaults
    current_corpus = "haizi_full.txt"  # 默认使用扩展语料
    poem_length = 4
    markov_order = 2  # 马尔可夫阶数 (1-3)
    generation_mode = "structured"  # structured, markov
    model = None
    structured_model = None
    last_poem = None

    def load_models(corpus_file, order):
        """加载语料并训练模型"""
        nonlocal model, structured_model
        text = load_corpus(os.path.join(CORPUS_DIR, corpus_file))
        if text is None:
            return None, "无法加载语料库"
        
        tokens = clean_and_tokenize(text)
        if not tokens:
            return None, "语料库为空或分词失败"
        
        # 马尔可夫模型
        model = MarkovChain(order=order)
        model.train(tokens)
        
        # 结构化模型
        raw_lines = [line.strip() for line in text.split('\n') if line.strip()]
        _, _, token_data = extract_imagery_and_connectors(text)
        structured_model = StructuredPoemGenerator()
        structured_model.train(token_data, raw_lines)
        
        return tokens, None

    # Init Load
    print(f"正在加载 {current_corpus}...")
    tokens, error = load_models(current_corpus, markov_order)
    if error:
        print(f"错误: {error}")
        return

    while True:
        clear_screen()
        mode_names = {"structured": "结构化", "markov": "马尔可夫"}
        print("======== 现代诗生成器 (Modern Poem Generator) ========")
        print(f"当前风格 (Current Style): [{current_corpus}]")
        print(f"生成模式 (Mode): [{mode_names.get(generation_mode, generation_mode)}]")
        print(f"生成长度 (Length): [{poem_length} lines]")
        print(f"马尔可夫阶数 (Markov Order): [{markov_order}] (越低越随机)")
        print("======================================================")
        print("1. 切换风格 (Change Style)")
        print("2. 切换模式 (Change Mode)")
        print("3. 设定长度 (Set Length)")
        print("4. 调整阶数 (Change Order)")
        print("5. 生成诗歌 (Generate)")
        print("6. 保存上一首 (Save Output)")
        print("7. 退出 (Exit)")
        print("======================================================")

        choice = input("请输入选项 (Enter option): ").strip()

        if choice == "1":
            files = list_corpora()
            if not files:
                print("\n错误: corpus/ 目录下没有找到任何 .txt 文件")
                time.sleep(1)
                continue
            print("\n可用语料库:")
            for idx, f in enumerate(files):
                print(f"{idx + 1}. {f}")
            try:
                sel = int(input("选择序号: ")) - 1
                if 0 <= sel < len(files):
                    current_corpus = files[sel]
                    print(f"正在加载 {current_corpus}...")
                    tokens, error = load_models(current_corpus, markov_order)
                    if error:
                        print(f"错误: {error}")
                        time.sleep(1)
                        continue
                    print("模型已重新训练!")
                    time.sleep(1)
                else:
                    print("无效的序号")
                    time.sleep(1)
            except ValueError:
                print("请输入有效的数字")
                time.sleep(1)

        elif choice == "2":
            print("\n生成模式:")
            print("  1. structured - 结构化 (状语+展开+结尾)")
            print("  2. markov - 马尔可夫链 (经典随机游走)")
            try:
                mode_sel = input("选择模式 (1/2): ").strip()
                if mode_sel == "1":
                    generation_mode = "structured"
                    print("已切换到结构化模式")
                elif mode_sel == "2":
                    generation_mode = "markov"
                    print("已切换到马尔可夫模式")
                else:
                    print("无效选择")
                time.sleep(1)
            except Exception:
                pass

        elif choice == "3":
            try:
                l = int(input("请输入行数 (1-20): "))
                if 1 <= l <= 20:
                    poem_length = l
                else:
                    print("请输入 1-20 之间的数字")
                    time.sleep(1)
            except ValueError:
                print("请输入有效的数字")
                time.sleep(1)

        elif choice == "4":
            print("\n马尔可夫阶数说明:")
            print("  1阶: 最随机，可能产生无意义的组合")
            print("  2阶: 平衡随机性和连贯性 (推荐)")
            print("  3阶: 最连贯，但可能过于接近原文")
            try:
                new_order = int(input("请选择阶数 (1-3): "))
                if 1 <= new_order <= 3:
                    markov_order = new_order
                    # 重新训练模型
                    print(f"正在以 {markov_order} 阶重新训练模型...")
                    tokens, _ = load_models(current_corpus, markov_order)
                    print("模型已更新!")
                    time.sleep(1)
                else:
                    print("请输入 1-3 之间的数字")
                    time.sleep(1)
            except ValueError:
                print("请输入有效的数字")
                time.sleep(1)

        elif choice == "5":
            clear_screen()
            print("\n----- 生成结果 -----\n")
            if generation_mode == "structured":
                last_poem = structured_model.generate(expansion_count=poem_length)
                mode_label = "结构化"
            else:
                last_poem = model.generate(poem_length)
                mode_label = f"马尔可夫-{markov_order}阶"
            print(f"[{mode_label}]\n")
            print(last_poem)
            print("\n--------------------")
            input("\n按回车键继续...")

        elif choice == "6":
            if last_poem:
                fname = f"poem_{int(time.time())}.txt"
                fpath = os.path.join(OUTPUT_DIR, fname)
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(f"# 生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# 风格: {current_corpus} | 模式: {generation_mode}\n\n")
                    f.write(last_poem)
                print(f"已保存到 {fpath}")
                time.sleep(1)
            else:
                print("还没有生成诗歌！请先生成一首。")
                time.sleep(1)

        elif choice == "7":
            print("再见！Bye!")
            break


if __name__ == "__main__":
    main()
