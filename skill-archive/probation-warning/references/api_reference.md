# 腾讯文档 API 参考

本文档说明如何使用腾讯文档 API 读取"试用期评估台账"数据。

## API 工具

### 1. 获取所有记录

**工具：**`mcp__tencent-docs__smartsheet_get_records`

**参数：**
```python
{
  "docid": "DVmp5RkRXSk9ZWkVY",
  "sheet_id": "000001"
}
```

**返回：** 所有记录的数组，每条记录包含字段名和值

### 2. 搜索记录（推荐）

**工具：**`mcp__企业微信文档__smartsheet_get_records`

支持条件筛选，可减少数据传输量。

**参数：**
```python
{
  "docid": "DVmp5RkRXSk9ZWkVY",
  "sheet_id": "000001",
  "view_id": "",  # 可选，指定视图
  "filters": []    # 可选，筛选条件
}
```

## 数据类型说明

### 日期字段

腾讯文档中的日期字段返回格式可能为：
- 字符串：`"2026/05/13"`
- 时间戳：整数（需要转换）

**处理方法：**
```python
import datetime

def parse_tencent_date(value):
    """解析腾讯文档日期"""
    if isinstance(value, (int, float)):
        # 时间戳（毫秒）
        return datetime.datetime.fromtimestamp(value / 1000)

    if isinstance(value, str):
        # 字符串格式
        for fmt in ['%Y/%m/%d', '%Y-%m-%d']:
            try:
                return datetime.datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue

    return None
```

### 文本字段

文本字段直接返回字符串，需要注意：
- 空值可能是 `""` 或 `None`
- 前后可能有空格，需要 `strip()`
- 换行符可能以 `\n` 形式存在

## 完整数据处理流程

### Step 1: 获取原始数据

```python
# 调用 API 获取记录
records = call_api(
    "mcp__tencent-docs__smartsheet_get_records",
    docid="DVmp5RkRXSk9ZWkVY",
    sheet_id="000001"
)
```

### Step 2: 转换为 CSV 格式（可选）

如需使用 `filter_eval.py` 脚本，需先转换为 CSV：

```python
import csv

def records_to_csv(records, output_file):
    """将API返回的记录转换为CSV"""
    if not records:
        return

    # 获取所有字段名
    fieldnames = records[0].keys()

    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

# 使用
records_to_csv(records, 'eval_data.csv')
```

### Step 3: 应用筛选逻辑

```python
from filter_eval import filter_evaluations, format_output

# 筛选未来7天内到期评估
results = filter_evaluations('eval_data.csv')

# 格式化输出
message = format_output(results)
print(message)
```

## 常见错误处理

### 错误1：授权失败（851014）

**现象：**
```json
{"error": {"code": 851014, "message": "授权已过期"}}
```

**解决方案：**
1. 在 WorkBuddy 中重新连接腾讯文档服务
2. 确保账号有访问该文档的权限
3. 检查文档是否已被删除或移动

### 错误2：字段名不匹配

**现象：** 记录中找不到预期的字段名

**原因：** 腾讯文档的字段名可能与表头显示不一致

**解决方案：**
1. 使用 `mcp__tencent-docs__smartsheet_get_fields` 获取实际字段名
2. 建立字段名映射表

```python
# 获取字段信息
fields = call_api(
    "mcp__tencent-docs__smartsheet_get_fields",
    docid="DVmp5RkRXSk9ZWkVY",
    sheet_id="000001"
)

# 建立映射
field_map = {field['field_name']: field['field_id'] for field in fields}
```

### 错误3：日期格式异常

**现象：** 日期解析失败

**解决方案：**
1. 增加更多日期格式支持
2. 添加错误处理和日志
3. 对无法解析的日期记录警告信息

```python
def safe_parse_date(date_str):
    """安全解析日期，失败返回None并记录"""
    result = parse_date(date_str)
    if result is None and date_str and date_str.strip():
        print(f"警告：无法解析日期 - {date_str}", file=sys.stderr)
    return result
```

## API 限流和性能优化

### 批量操作

如果需要处理大量数据：
1. 使用搜索接口而非获取全部
2. 添加筛选条件减少返回数据量
3. 分批处理，避免超时

### 缓存策略

对于不频繁变化的数据：
1. 本地缓存 CSV 文件
2. 设置缓存有效期（如1小时）
3. 定时刷新缓存

```python
import os
import time

def get_cached_data(cache_file, max_age_seconds=3600):
    """获取缓存数据，如果过期则重新获取"""
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < max_age_seconds:
            return cache_file

    # 重新获取数据
    records = fetch_from_api()
    records_to_csv(records, cache_file)
    return cache_file
```

## 相关链接

- 腾讯文档 API 官方文档：https://docs.qq.com/open/document/
- WorkBuddy MCP 工具文档：参见 WorkBuddy 内置帮助
