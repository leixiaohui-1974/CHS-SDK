#!/usr/bin/env python3
"""
导出所有文档的脚本
将项目中的所有Markdown文档打包到一个zip文件中
"""

import os
import zipfile
from pathlib import Path

def collect_docs(root_dir):
    """收集所有Markdown文档"""
    docs = []
    
    # 定义需要收集文档的目录
    doc_dirs = [
        'docs',
        'docs/examples',
        'docs/water_system',
        'docs/generated_notebooks'
    ]
    
    # 收集指定目录中的文档
    for doc_dir in doc_dirs:
        dir_path = Path(root_dir) / doc_dir
        if dir_path.exists():
            for file_path in dir_path.rglob('*.md'):
                docs.append(file_path)
    
    # 收集根目录下的Markdown文件
    root_md_files = list(Path(root_dir).glob('*.md'))
    docs.extend(root_md_files)
    
    return docs

def create_docs_zip(docs, output_path):
    """创建包含所有文档的zip文件"""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for doc_path in docs:
            # 获取相对于项目根目录的路径
            arcname = doc_path.relative_to(Path(__file__).parent.parent)
            zipf.write(doc_path, arcname)
    
    print(f"成功导出 {len(docs)} 个文档到 {output_path}")

def main():
    root_dir = Path(__file__).parent.parent
    output_path = root_dir / 'exported_docs.zip'
    
    docs = collect_docs(root_dir)
    create_docs_zip(docs, output_path)

if __name__ == '__main__':
    main()