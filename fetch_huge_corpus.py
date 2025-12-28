import json
import os
import glob
from pathlib import Path

# Configuration
SOURCE_DIR = r"d:\study\口订\modern_poem_generator\temp_corpus_src\yuxqiu_modern\China-modern-poetry\contemporary"
OUTPUT_FILE = r"d:\study\口订\modern_poem_generator\corpus\modern_huge.txt"


def fetch_huge_corpus():
    print(f"Searching for JSON files in: {SOURCE_DIR}")
    json_files = glob.glob(os.path.join(SOURCE_DIR, "*.json"))

    if not json_files:
        print("No JSON files found! Please check the directory path.")
        return

    print(f"Found {len(json_files)} JSON files.")

    total_poems = 0
    total_lines = 0
    all_content = []

    for json_file in json_files:
        print(f"Processing: {os.path.basename(json_file)}...")
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                print(f"Skipping {json_file}: Content is not a list.")
                continue

            for poem in data:
                paragraphs = poem.get("paragraphs")
                if paragraphs:
                    # paragraphs is typically a list of strings
                    if isinstance(paragraphs, list):
                        poem_text = "\n".join(
                            [p.strip() for p in paragraphs if p.strip()]
                        )
                        if poem_text:
                            all_content.append(poem_text)
                            total_poems += 1
                            total_lines += len(paragraphs)
                    elif isinstance(paragraphs, str):
                        if paragraphs.strip():
                            all_content.append(paragraphs.strip())
                            total_poems += 1
                            total_lines += 1

        except Exception as e:
            print(f"Error processing {json_file}: {e}")

    print(f"\nExtracted {total_poems} poems with approx {total_lines} lines.")

    # Save to output file
    if all_content:
        print(f"Saving to {OUTPUT_FILE}...")
        try:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                # Join poems with double newline
                f.write("\n\n".join(all_content))
            print("Successfully saved modern_huge.txt")
        except Exception as e:
            print(f"Error saving file: {e}")
    else:
        print("No content extracted.")


if __name__ == "__main__":
    fetch_huge_corpus()
