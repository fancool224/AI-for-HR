#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台账数据加载 + 标准化

负责：
- 加载 Excel/CSV 文件
- 智能定位表头行（跳过标题/合并单元格）
- 字段名模糊匹配 → 标准字段名
- 日期/数值清洗
- 计算"司龄段"
- 多 sheet 合并（主动/被动分开存的情况）
"""

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# ============================================================
# 标准字段映射（用户字段名 → 标准字段名）
# ============================================================
FIELD_ALIASES = {
    "月份": ["月份", "month", "离职月份", "流失月份"],
    "类别": ["类别", "category", "员工类别", "类型"],
    "一级部门": ["一级部门", "level1_dept"],
    "二级部门": ["二级部门", "level2_dept", "子部门"],
    "门店": ["门店", "门店名", "门店名称", "store"],
    "全职兼职": ["全职兼职", "全/兼职", "用工类型"],
    "岗位": ["岗位", "职位", "position", "title"],
    "姓名": ["姓名", "员工姓名", "name"],
    "是否高潜": ["是否为高潜员工", "是否高潜", "高潜"],
    "入职日期": ["入职日期", "入职时间", "hire_date", "join_date"],
    "离岗日期": ["离岗日期", "离职日期", "离职时间", "leave_date", "exit_date"],
    "司龄（月）": ["司龄（月）", "司龄", "工龄", "在职月数", "服务月数"],
    "年龄": ["年龄", "age"],
    "联系方式": ["联系方式", "电话", "手机"],
    "学历": ["学历", "education"],
    "直接上级": ["直接上级"],
    "隔级上级": ["隔级上级"],
    "工作交接表": ["工作交接表", "工作交接", "交接"],
    "人员状态": ["人员状态"],
    "离职流程进度": ["离职流程进度", "离职进度"],
    "是否完成面谈": ["是否完成面谈", "是否面谈"],
    "社保是否解除": ["社保是否解除", "社保解除", "社保"],
    "是否正常": ["是否正常", "是否正常离职", "正常离职"],
    "流失类别": ["流失类别", "流失类型", "离职类型", "主动被动"],
    "流失原因": ["流失原因", "离职原因", "原因"],
    "流失原因分类": ["流失原因分类", "原因分类"],
    "员工本人离职面谈": ["员工本人离职面谈", "员工面谈", "员工本人意见"],
    "直接上级意见": ["直接上级意见"],
    "隔级上级意见": ["隔级上级意见"],
}

# 司龄分段（6段）
TENURE_BUCKETS = [
    ("<1月",     0,    1),
    ("1-3月",    1,    3),
    ("3-6月",    3,    6),
    ("6-12月",   6,    12),
    ("12-24月", 12,   24),
    ("24月+",   24, 10000),
]
TENURE_ORDER = [b[0] for b in TENURE_BUCKETS] + ["未知"]


# ============================================================
# 辅助函数
# ============================================================
def _to_datetime(x):
    if pd.isna(x):
        return pd.NaT
    if isinstance(x, datetime):
        return x
    if isinstance(x, (int, float)):
        try:
            return pd.to_datetime("1899-12-30") + timedelta(days=float(x))
        except Exception:
            return pd.NaT
    try:
        return pd.to_datetime(str(x), errors="coerce")
    except Exception:
        return pd.NaT


def _calc_tenure_months(hire, leave):
    if pd.isna(hire) or pd.isna(leave):
        return None
    days = (leave - hire).days
    if days < 0:
        return None
    return round(days / 30.4375, 2)


def _bucket_tenure(months):
    if months is None or pd.isna(months):
        return "未知"
    for label, lo, hi in TENURE_BUCKETS:
        if lo <= months < hi:
            return label
    return "未知"


def _bucket_age(age):
    if pd.isna(age):
        return "未知"
    try:
        a = int(age)
    except Exception:
        return "未知"
    if a < 25:
        return "<25"
    if a < 30:
        return "25-29"
    if a < 35:
        return "30-34"
    if a < 40:
        return "35-39"
    if a < 50:
        return "40-49"
    return "50+"


def _normalize_flow_type(x):
    if pd.isna(x):
        return "未知"
    s = str(x).strip()
    if any(k in s for k in ["主动", "辞职", "active"]):
        return "主动"
    if any(k in s for k in ["被动", "解除", "辞退", "开除", "passive"]):
        return "被动"
    return s


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """字段名模糊匹配到标准名。同名列保留第一个。"""
    col_map = {}
    cols_str = {c: str(c).strip() for c in df.columns}
    for std_name, aliases in FIELD_ALIASES.items():
        for c, c_str in cols_str.items():
            if c in col_map:
                continue
            for alias in aliases:
                if alias == c_str or alias in c_str or c_str in alias:
                    if std_name not in col_map.values():
                        col_map[c] = std_name
                        break
    df = df.rename(columns=col_map)
    df = df.loc[:, ~df.columns.duplicated(keep="first")]
    return df


def _smart_read_sheet(p, sn):
    """智能定位 sheet 表头行（跳过标题/合并单元格）"""
    raw = pd.read_excel(p, sheet_name=sn, header=None)
    header_row = None
    for i in range(min(10, len(raw))):
        row_vals = [str(v) for v in raw.iloc[i].fillna("").tolist()]
        joined = "".join(row_vals)
        if ("姓名" in joined and ("入职" in joined or "离岗" in joined)) \
           or ("序号" in joined and "月份" in joined and ("岗位" in joined or "部门" in joined)):
            header_row = i
            break
    if header_row is None:
        return None
    df = pd.read_excel(p, sheet_name=sn, header=header_row)
    return df.dropna(how="all")


# ============================================================
# 主入口
# ============================================================
def load_taizhang(path, sheet_name=None):
    """加载台账。支持三种情况：
    1. CSV/TSV
    2. Excel + 指定 sheet
    3. Excel 自动识别（含主动/被动分开sheet的合并）
    """
    p = Path(path)
    if p.suffix.lower() in [".csv", ".tsv"]:
        sep = "," if p.suffix.lower() == ".csv" else "\t"
        return pd.read_csv(p, sep=sep)

    xls = pd.ExcelFile(p)
    if sheet_name:
        df = _smart_read_sheet(p, sheet_name)
        return df if df is not None else pd.read_excel(p, sheet_name=sheet_name)

    # 自动模式：检测是否分开的"主动流失" + "被动流失" sheet
    active_sheets = [s for s in xls.sheet_names if "主动流失" in s]
    passive_sheets = [s for s in xls.sheet_names if "被动流失" in s]
    if active_sheets and passive_sheets:
        frames = []
        for sn in active_sheets:
            d = _smart_read_sheet(p, sn)
            if d is not None:
                d["流失类别"] = "主动"
                frames.append(d)
        for sn in passive_sheets:
            d = _smart_read_sheet(p, sn)
            if d is not None:
                d["流失类别"] = "被动"
                frames.append(d)
        if frames:
            return pd.concat(frames, ignore_index=True, sort=False)

    # 否则找最佳单 sheet
    candidates = []
    for s in xls.sheet_names:
        score = 0
        if any(k in s for k in ["流失台账", "流失明细", "离职明细", "人员流失分析"]):
            score = 3
        elif "流失" in s or "离职" in s:
            score = 1
        if score > 0:
            candidates.append((score, s))
    candidates.sort(reverse=True)
    sheets_to_try = [s for _, s in candidates] or [xls.sheet_names[0]]
    for sn in sheets_to_try:
        df = _smart_read_sheet(p, sn)
        if df is not None:
            return df
    return pd.read_excel(p, sheet_name=sheets_to_try[0])


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """标准化：列名映射 + 日期 + 司龄 + 流失类别 + 派生字段"""
    df = _normalize_columns(df)

    # 日期
    for col in ["入职日期", "离岗日期", "月份"]:
        if col in df.columns:
            df[col] = df[col].apply(_to_datetime)

    # 司龄
    if "司龄（月）" not in df.columns and "入职日期" in df.columns and "离岗日期" in df.columns:
        df["司龄（月）"] = df.apply(
            lambda r: _calc_tenure_months(r["入职日期"], r["离岗日期"]), axis=1
        )
    if "司龄（月）" not in df.columns:
        df["司龄（月）"] = None
    df["司龄段"] = df["司龄（月）"].apply(_bucket_tenure)

    # 年龄段
    if "年龄" in df.columns:
        df["年龄段"] = df["年龄"].apply(_bucket_age)
    else:
        df["年龄段"] = "未知"

    # 流失类别归一
    if "流失类别" in df.columns:
        df["流失类别"] = df["流失类别"].apply(_normalize_flow_type)
    else:
        df["流失类别"] = "未知"

    # 月份字符串
    if "月份" in df.columns and df["月份"].notna().any():
        df["月份_str"] = df["月份"].dt.strftime("%Y-%m")
    elif "离岗日期" in df.columns:
        df["月份_str"] = df["离岗日期"].dt.strftime("%Y-%m")
    else:
        df["月份_str"] = "未知"

    # 去空行
    if "姓名" in df.columns:
        df = df[df["姓名"].notna() & (df["姓名"].astype(str).str.strip() != "")]

    return df.reset_index(drop=True)
