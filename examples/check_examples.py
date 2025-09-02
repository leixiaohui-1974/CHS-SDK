#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from test_all_modes import AllModesRunner

def main():
    runner = AllModesRunner()
    print(f"发现 {len(runner.all_examples)} 个示例:")
    for i, example in enumerate(runner.all_examples, 1):
        print(f"  {i}. {example['path']} (类别: {example['category']})")

if __name__ == "__main__":
    main()