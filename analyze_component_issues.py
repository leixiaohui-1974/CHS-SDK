import json

# 加载测试报告
with open('test_output/round_trip_test/summary_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('最常见的问题:')
for issue, count in data['common_issues']:
    print(f'{issue}: {count}次')

print('\n组件定义丢失的案例:')
component_issues = [case for case in data['test_results'] 
                   if any('没有组件定义' in issue for issue in case['consistency']['issues'])]
print(f'共{len(component_issues)}个案例')

print('\n前10个组件定义丢失的案例:')
for i, case in enumerate(component_issues[:10]):
    print(f'{i+1}. {case["config_path"]}')
    print(f'   配置类型: {case["config_type"]}')
    print(f'   组件得分: {case["consistency"]["components_score"]}')
    print(f'   问题: {case["consistency"]["issues"]}')
    print()

print('\n连接定义丢失的案例:')
connection_issues = [case for case in data['test_results'] 
                    if any('没有连接定义' in issue for issue in case['consistency']['issues'])]
print(f'共{len(connection_issues)}个案例')

print('\n前5个连接定义丢失的案例:')
for i, case in enumerate(connection_issues[:5]):
    print(f'{i+1}. {case["config_path"]}')
    print(f'   配置类型: {case["config_type"]}')
    print(f'   拓扑得分: {case["consistency"]["topology_score"]}')
    print(f'   问题: {case["consistency"]["issues"]}')
    print()