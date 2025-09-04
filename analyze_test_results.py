import json

# 读取测试结果
with open('test_output/round_trip_test/summary_report.json', encoding='utf-8') as f:
    data = json.load(f)

print('智能体相关问题:')
for issue, count in data['common_issues']:
    if '智能体数量不匹配' in issue:
        print(f'  {issue}: {count}次')

print(f'\n总体统计:')
print(f'  总测试数: {data["total_tests"]}')
print(f'  成功测试: {data["successful_tests"]}')
print(f'  失败测试: {data["failed_tests"]}')
print(f'  平均一致性得分: {data["average_consistency_score"]:.3f}')

# 统计智能体得分情况
agent_scores = []
for result in data['test_results']:
    if 'consistency' in result and 'agents_score' in result['consistency']:
        agent_scores.append(result['consistency']['agents_score'])

if agent_scores:
    print(f'\n智能体得分统计:')
    print(f'  平均智能体得分: {sum(agent_scores)/len(agent_scores):.3f}')
    print(f'  满分案例数: {sum(1 for score in agent_scores if score == 1.0)}')
    print(f'  零分案例数: {sum(1 for score in agent_scores if score == 0.0)}')