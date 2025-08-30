# -*- coding: utf-8 -*-
import json
import os

def load_config(file_path):
    """
    从 JSON 文件加载配置。

    :param file_path: 配置文件的路径。
    :return: 包含配置的字典。
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"配置文件未找到: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
