import unittest
import os
import sys

# Add project root to path so we can import src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.model import MarkovChain, StructuredPoemGenerator
from src.utils import clean_and_tokenize, extract_imagery_and_connectors


class TestPoemGenerator(unittest.TestCase):

    def test_tokenize_simple(self):
        """Test if utility correctly tokenizes text"""
        text = "我爱北京天安门"
        tokens = clean_and_tokenize(text)
        # heavy dependency on jieba result, but roughly checking
        self.assertIn("北京", tokens)
        self.assertIn("天安门", tokens)

    def test_tokenize_newline(self):
        """Test if utility preserves newlines as tokens"""
        text = "第一行\n第二行"
        tokens = clean_and_tokenize(text)
        self.assertIn("\n", tokens)

    def test_markov_train_and_generate(self):
        """Test the core chain logic with a deterministic pattern"""
        # Pattern: A -> B -> C -> A ...
        # Tokens: A B C A B C
        # Order 1: A->B, B->C, C->A
        tokens = ["A", "B", "C", "A", "B", "C"]

        model = MarkovChain(order=1)
        model.train(tokens)

        # Determine if chain was built
        self.assertIn(("A",), model.chain)
        # 由于训练数据中 A->B 出现两次，所以 chain 中会有两个 "B"
        self.assertEqual(model.chain[("A",)], ["B", "B"])

        # Test Generation
        # It should generate a sequence of A B C ...
        output = model.generate(
            num_lines=1
        )  # Note: generate returns lines, our mock tokens don't have \n by default unless generated
        # Actually our generate_line logic stops at \n or max words.
        # Since no \n in chain, it will run until max_words (20).

        line = model.generate_line()
        self.assertTrue(
            line.startswith("ABC") or line.startswith("BCA") or line.startswith("CAB")
        )
        self.assertTrue(len(line) > 3)

    def test_generation_safety(self):
        """Test generation on empty model shouldn't crash"""
        model = MarkovChain()
        res = model.generate()
        # generate() 默认生成5行，每行都是 "Model not trained."
        self.assertIn("Model not trained.", res)

    def test_structured_generator(self):
        """Test StructuredPoemGenerator with sample data"""
        # 准备测试数据
        text = "在北方的夜晚\n我看见了星星\n大地沉默\n远方的灯火"
        raw_lines = [line.strip() for line in text.split('\n') if line.strip()]
        _, _, token_data = extract_imagery_and_connectors(text)
        
        # 训练模型
        gen = StructuredPoemGenerator()
        gen.train(token_data, raw_lines)
        
        # 检查统计信息
        stats = gen.get_stats()
        self.assertIn('意象词数量', stats)
        self.assertIn('结尾句数量', stats)
        
        # 测试生成
        poem = gen.generate(expansion_count=2)
        self.assertIsInstance(poem, str)
        self.assertTrue(len(poem) > 0)


if __name__ == "__main__":
    unittest.main()
