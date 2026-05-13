#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
试用期评估预警筛选脚本
从腾讯文档读取数据，筛选未来7天内需要评估的人员
"""

import csv
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 评估轮次配置：(日期列, 结果列, 轮次名称)
EVAL_COLS = [
    (17, 18, '第一次'),
    (19, 20, '第二次'),
    (21, 22, '第三次'),
    (23, 24, '第四次'),
    (25, 26, '第五次'),
]

def parse_date(date_str):
    """解析日期字符串，支持多种格式"""
    if not date_str or not date_str.strip():
        return None

    date_str = date_str.strip()
    formats = [
        '%Y/%m/%d',  # 2026/05/13
        '%Y-%m-%d',  # 2026-05-13
        '%Y年%m月%d日',  # 2026年05月13日
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def get_responsible(dept1):
    """根据一级部门分配责任人"""
    if dept1 and dept1 in ('销售中心', '培训部'):
        return '李鹏'
    return '曲雅如'

def filter_evaluations(csv_file, target_date=None, days_ahead=7):
    """
    筛选需要评估的人员

    Args:
        csv_file: CSV文件路径
        target_date: 目标日期（datetime对象），默认为今天
        days_ahead: 提前天数，默认7天

    Returns:
        list: 符合条件的记录列表
    """
    if target_date is None:
        target_date = datetime.now().date()
    else:
        target_date = target_date.date() if isinstance(target_date, datetime) else target_date

    end_date = target_date + timedelta(days=days_ahead)

    results = []

    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)  # 跳过表头

        for row in reader:
            # 确保行长度足够
            if len(row) <= 16:
                continue

            # 条件1: 转正状态（列15）为空
            status = row[15].strip() if len(row) > 15 else ''
            if status:  # 已转正/已流失等，跳过
                continue

            # 获取基本信息
            dept1 = row[1].strip() if len(row) > 1 else ''
            dept2 = row[2].strip() if len(row) > 2 else ''
            name = row[5].strip() if len(row) > 5 else ''

            if not name:
                continue

            # 检查所有评估轮次
            for date_col, result_col, round_name in EVAL_COLS:
                if len(row) <= date_col:
                    continue

                date_str = row[date_col].strip()
                eval_date = parse_date(date_str)

                if eval_date is None:
                    continue

                eval_date = eval_date.date()

                # 条件2: 评估日期在 [今天, 今天+7天] 范围内
                if target_date <= eval_date <= end_date:
                    # 条件3: 评估结果为"待评估"或为空
                    eval_result = row[result_col].strip() if len(row) > result_col else ''
                    if not eval_result or eval_result in ('待评估', '催办中'):
                        responsible = get_responsible(dept1)

                        results.append({
                            'responsible': responsible,
                            'dept1': dept1,
                            'dept2': dept2,
                            'name': name,
                            'round': round_name,
                            'eval_date': eval_date.strftime('%Y/%m/%d'),
                            'eval_result': eval_result if eval_result else '待评估',
                            'sort_key': (responsible, eval_date, name)
                        })

    # 去重（同一员工同一轮次可能多次匹配）
    seen = set()
    unique_results = []
    for item in results:
        key = (item['name'], item['round'])
        if key not in seen:
            seen.add(key)
            unique_results.append(item)

    # 排序：责任人 -> 评估日期 -> 姓名
    unique_results.sort(key=lambda x: x['sort_key'])
    return unique_results

def format_output(results):
    """格式化输出提醒消息"""
    if not results:
        return "📋 试用期评估提醒\n未来7天内无到期评估。"

    # 按责任人分组
    grouped = {}
    for item in results:
        resp = item['responsible']
        if resp not in grouped:
            grouped[resp] = []
        grouped[resp].append(item)

    # 生成输出
    lines = ["📋 试用期评估提醒", "以下员工试用期评估即将到期，请及时处理：", ""]

    for responsible in sorted(grouped.keys()):
        items = grouped[responsible]
        for item in items:
            line = f"{item['responsible']} - {item['dept1']} - {item['dept2']} - {item['name']} - {item['round']} - {item['eval_date']} - {item['eval_result']}"
            lines.append(line)
        lines.append("")  # 责任人之间空行

    return "\n".join(lines).strip()

def main():
    """主函数"""
    # 获取CSV文件路径
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        # 默认路径
        csv_file = 'eval_data.csv'

    # 检查文件是否存在
    if not Path(csv_file).exists():
        print(f"错误：文件不存在 - {csv_file}", file=sys.stderr)
        print(f"用法: python {sys.argv[0]} [CSV文件路径]", file=sys.stderr)
        sys.exit(1)

    # 筛选数据
    print(f"正在读取文件: {csv_file}")
    results = filter_evaluations(csv_file)

    # 输出结果
    output = format_output(results)
    print("\n" + output)

    # 保存到文件
    output_file = f"probation_reminder_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)
    print(f"\n结果已保存到: {output_file}")

    # 返回统计信息
    print(f"\n统计：共 {len(results)} 条待评估记录")
    if results:
        responsible_count = {}
        for item in results:
            resp = item['responsible']
            responsible_count[resp] = responsible_count.get(resp, 0) + 1
        for resp, count in sorted(responsible_count.items()):
            print(f"  - {resp}: {count} 条")

if __name__ == '__main__':
    main()
