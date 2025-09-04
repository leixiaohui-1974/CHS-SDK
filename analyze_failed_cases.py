import json

# 加载测试报告
with open('test_output/round_trip_test/summary_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 找出组件定义丢失的案例
failed_cases = [case for case in data['test_results']
                     if '重新生成的配置中没有组件定义' in case.get('consistency', {}).get('issues', [])]

print(f'组件定义丢失的案例数量: {len(failed_cases)}')
print('\n前5个案例:')
for i, case in enumerate(failed_cases[:5]):
    print(f'{i+1}. {case["config_path"]}')
    print(f'   得分: {case["consistency"]["overall_score"]}')
    print(f'   问题: {", ".join(case["consistency"]["issues"])}')
    print()

# 分析一个具体案例
if failed_cases:
    print('\n=== 分析第一个案例 ===')
    first_case = failed_cases[0]
    print(f'案例: {first_case["config_path"]}')
    print(f'组件得分: {first_case["consistency"]["components_score"]}')
    print(f'拓扑得分: {first_case["consistency"]["topology_score"]}')
    print(f'智能体得分: {first_case["consistency"]["agents_score"]}')
    print(f'仿真得分: {first_case["consistency"]["simulation_score"]}')