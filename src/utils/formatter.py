"""
结果格式化输出工具
"""

from typing import List, Dict, Any


def print_table(rows: List[Dict[str, Any]], max_col_width: int = 40) -> None:
    """以表格形式打印查询结果"""
    if not rows:
        print("  (无数据)")
        return

    cols = list(rows[0].keys())
    # 计算每列宽度
    widths = {c: min(max(len(str(c)), max(len(str(r.get(c, ""))) for r in rows)), max_col_width) for c in cols}

    sep = "+" + "+".join("-" * (w + 2) for w in widths.values()) + "+"
    header = "|" + "|".join(f" {str(c).ljust(widths[c])} " for c in cols) + "|"

    print(sep)
    print(header)
    print(sep)
    for row in rows:
        line = "|"
        for c in cols:
            val = str(row.get(c, "NULL"))
            if len(val) > max_col_width:
                val = val[:max_col_width - 3] + "..."
            line += f" {val.ljust(widths[c])} |"
        print(line)
    print(sep)
    print(f"  共 {len(rows)} 行")


def print_kv(data: Dict[str, Any], title: str = "") -> None:
    """以键值对形式打印信息"""
    if title:
        print(f"\n{'='*40}")
        print(f"  {title}")
        print(f"{'='*40}")
    for k, v in data.items():
        print(f"  {str(k):<25} : {v}")


def print_kv_table(rows: List[Dict[str, Any]], max_col_width: int = 40) -> None:
    """
    以"字段: 值"格式显示查询结果

    Args:
        rows: 行字典列表
        max_col_width: 列最大宽度
    """
    if not rows:
        print("  （无数据）")
        return

    print("\n  ┌─ 查询结果 ───────────────────────────────┐")

    # 只打印第一行的所有字段和值
    for row in rows:
        for key, value in row.items():
            val_str = str(value)
            # 截断过长的值
            if len(val_str) > max_col_width:
                val_str = val_str[:max_col_width - 3] + "..."
            print(f"  │  {key}: {val_str}")

    print("  └─────────────────────────────────────────────┘")

    if len(rows) > 1:
        print(f"  [提示] 共 {len(rows)} 条记录，只显示第一条的详情。")


def print_custom_fields(rows: List[Dict[str, Any]], field_list: List[str]) -> None:
    """
    打印指定字段的值

    Args:
        row: 字典，包含所有字段
        field_list: 需要打印的字段列表

    Returns:
        None
    """
    for row in rows:
        print("--------------------------------")
        for field in field_list:
            value = row.get(field, "")
            
            print(f"  {field}: {value}")
        print("")
