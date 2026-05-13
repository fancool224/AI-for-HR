#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险群体扫描器

扫描 5 类风险信号：
1. 司龄结构性预警（<1月/1-3月 占比高）
2. 高潜流失（任何 1 个高潜流失 = 红色预警）
3. 同一直接上级下属流失集中（≥3人 = 管理质量信号）
4. 同一门店/部门流失集中（≥3人）
5. 流程合规预警（社保未解除、是否正常=否、面谈未完成占比高）
"""

import pandas as pd


def scan_risk_groups(df: pd.DataFrame, target_month: str):
    """返回风险预警列表 [{level, rule, actual, hint}]"""
    cur = df[df["月份_str"] == target_month].copy()
    alerts = []
    if cur.empty:
        return alerts

    total = len(cur)
    active = cur[cur["流失类别"] == "主动"]
    passive = cur[cur["流失类别"] == "被动"]

    # ---- 1. 司龄结构性预警 ----
    if "司龄段" in cur.columns:
        early_count = ((cur["司龄段"] == "<1月") | (cur["司龄段"] == "1-3月")).sum()
        if total > 0 and early_count / total > 0.30:
            alerts.append({
                "level": "🔴",
                "rule": "新员工闪退预警",
                "actual": f"司龄<3月 {early_count}/{total} ({early_count/total*100:.1f}%)",
                "threshold": "30%",
                "hint": "招聘匹配度/入职带教存在断点，建议核查最近 3 月入职批次",
            })
        super_early = (cur["司龄段"] == "<1月").sum()
        if super_early >= 2:
            alerts.append({
                "level": "🔴",
                "rule": "入职即流失",
                "actual": f"<1月流失 {super_early} 人",
                "threshold": "≥2人",
                "hint": "极高警报：可能是offer/入职体验严重断裂",
            })

    # ---- 2. 高潜流失 ----
    if "是否高潜" in cur.columns:
        hp_yes = cur[cur["是否高潜"].astype(str).str.contains("是|Y|y|高潜|TRUE", na=False)]
        if len(hp_yes) >= 1:
            names = ", ".join(hp_yes["姓名"].fillna("").astype(str).tolist()[:5])
            alerts.append({
                "level": "🔴",
                "rule": "高潜员工流失",
                "actual": f"{len(hp_yes)} 人 ({names})",
                "threshold": "≥1人",
                "hint": "高潜流失是组织最大损失，立即复盘并制定保留策略",
            })

    # ---- 3. 同一直接上级流失集中 ----
    if "直接上级" in cur.columns:
        leader_counts = cur[cur["直接上级"].notna()]["直接上级"].value_counts()
        for leader, cnt in leader_counts.items():
            if cnt >= 3:
                alerts.append({
                    "level": "🟠",
                    "rule": "同一直接上级下属流失集中",
                    "actual": f"{leader}: {cnt} 人",
                    "threshold": "≥3人",
                    "hint": "强管理质量信号，建议与该上级深度面谈",
                })

    # ---- 4. 同一门店/部门集中 ----
    if "门店" in cur.columns:
        store_counts = cur[cur["门店"].notna() &
                           (cur["门店"].astype(str).str.strip() != "")]["门店"].value_counts()
        for store, cnt in store_counts.items():
            if cnt >= 3:
                alerts.append({
                    "level": "🔴",
                    "rule": "单店流失集中",
                    "actual": f"{store}: {cnt} 人",
                    "threshold": "≥3人",
                    "hint": "门店级管理风险，建议店长面谈+下店巡检",
                })

    if "二级部门" in cur.columns:
        dept_counts = cur[cur["二级部门"].notna()]["二级部门"].value_counts()
        for dept, cnt in dept_counts.items():
            if total > 0 and cnt / total > 0.40:
                alerts.append({
                    "level": "🟠",
                    "rule": "单部门流失占比高",
                    "actual": f"{dept}: {cnt} 人 ({cnt/total*100:.1f}%)",
                    "threshold": "40%",
                    "hint": "重灾区，建议部门级专项",
                })

    # ---- 5. 流程合规预警 ----
    if "是否正常" in cur.columns:
        abnormal = cur[cur["是否正常"].astype(str).str.contains("否|N|n|不正常|FALSE", na=False)]
        if len(abnormal) > 0:
            alerts.append({
                "level": "🔴",
                "rule": "非正常离职",
                "actual": f"{len(abnormal)} 人",
                "threshold": "≥1人",
                "hint": "劳动风险预警，立即评估法律合规",
            })

    if "是否完成面谈" in cur.columns:
        not_interviewed = cur[cur["是否完成面谈"].astype(str).str.contains("否|N|n|未|FALSE", na=False)]
        if total > 0 and len(not_interviewed) / total > 0.20:
            alerts.append({
                "level": "🟡",
                "rule": "离职面谈覆盖率不足",
                "actual": f"未面谈 {len(not_interviewed)}/{total} ({len(not_interviewed)/total*100:.1f}%)",
                "threshold": "覆盖率<80%",
                "hint": "HR 自身过程指标，建议强制要求 100% 面谈覆盖",
            })

    if "社保是否解除" in cur.columns:
        sb_not = cur[cur["社保是否解除"].astype(str).str.contains("否|N|n|未|FALSE", na=False)]
        if len(sb_not) > 0:
            alerts.append({
                "level": "🟡",
                "rule": "社保未及时解除",
                "actual": f"{len(sb_not)} 人",
                "threshold": "≥1人",
                "hint": "合规风险，可能产生重复缴费",
            })

    # ---- 6. 被动流失主因预警 ----
    if "流失原因分类" in cur.columns and not passive.empty:
        fault = passive["流失原因分类"].astype(str).str.contains("违纪|违规|过失", na=False).sum()
        if len(passive) > 0 and fault / len(passive) > 0.25:
            alerts.append({
                "level": "🔴",
                "rule": "过失/违纪占被动流失偏高",
                "actual": f"{fault}/{len(passive)} ({fault/len(passive)*100:.1f}%)",
                "threshold": "25%",
                "hint": "招聘把关/试用期评估机制失灵",
            })

    return alerts
