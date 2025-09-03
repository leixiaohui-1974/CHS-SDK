#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch
import base64
from io import BytesIO

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def test_chart_generation():
    """测试图表生成功能"""
    print("开始测试图表生成...")
    
    try:
        # 创建一个简单的图表
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 8)
        ax.axis('off')
        
        # 绘制一个矩形
        rect = FancyBboxPatch((2, 3), 6, 2, 
                            boxstyle="round,pad=0.1", 
                            facecolor='#3498db', edgecolor='black', linewidth=2)
        ax.add_patch(rect)
        
        # 添加文字
        ax.text(5, 4, '测试图表', ha='center', va='center', 
               fontsize=16, fontweight='bold', color='white')
        
        ax.set_title('图表生成测试', fontsize=16, fontweight='bold', pad=20)
        
        # 保存为base64字符串
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        print(f"图表生成成功！Base64长度: {len(image_base64)}")
        print(f"Base64前50个字符: {image_base64[:50]}...")
        
        return f"data:image/png;base64,{image_base64}"
        
    except Exception as e:
        print(f"图表生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_chart_generation()
    if result:
        print("测试成功！")
    else:
        print("测试失败！")