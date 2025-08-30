# -*- coding: utf-8 -*-
import csv
import os

class DataLogger:
    """
    一个简单的数据记录器，用于将仿真数据保存到 CSV 文件。
    """
    def __init__(self, log_dir, file_name="sim_log.csv", headers=None):
        """
        初始化数据记录器。

        :param log_dir: 日志文件存储的目录。
        :param file_name: 日志文件的名称。
        :param headers: CSV文件的表头（列名）列表。
        """
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.log_path = os.path.join(log_dir, file_name)
        self.headers = headers if headers is not None else []
        self.data_buffer = []

        # 写入表头
        with open(self.log_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if self.headers:
                writer.writerow(self.headers)

    def log_step(self, data_row):
        """
        记录一步的数据。

        :param data_row: 要记录的数据行（列表或元组）。
        """
        if len(data_row) != len(self.headers):
            raise ValueError("数据行长度与表头长度不匹配。")
        self.data_buffer.append(data_row)

    def save(self):
        """
        将缓冲区中的所有数据写入文件。
        """
        with open(self.log_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(self.data_buffer)

        # 清空缓冲区
        self.data_buffer = []
        print(f"数据已保存到: {self.log_path}")

    def log_and_save_step(self, data_row):
        """
        记录一步数据并立即保存。
        适用于长时运行的仿真，避免数据丢失。
        """
        if len(data_row) != len(self.headers):
            raise ValueError("数据行长度与表头长度不匹配。")

        with open(self.log_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(data_row)
