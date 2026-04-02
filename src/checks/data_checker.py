"""
数据检查模块 — 运维常用的数据质量检测工具
"""

from typing import List, Dict, Any
from src.db.connector import DBConnector
from src.utils.formatter import print_table, print_warn, print_success, print_info


class DataChecker:
    """数据检查器"""

    def __init__(self, connector: DBConnector):
        self.db = connector

    # ------------------------------------------------------------------
    # 行数统计
    # ------------------------------------------------------------------
    def count_rows(self, table: str, where: str = None) -> int:
        """统计表行数，可附加 WHERE 条件"""
        sql = f"SELECT COUNT(*) AS cnt FROM {table}"
        if where:
            sql += f" WHERE {where}"
        rows = self.db.execute(sql)
        return int(list(rows[0].values())[0]) if rows else 0

    # ------------------------------------------------------------------
    # 空值检测
    # ------------------------------------------------------------------
    def check_nulls(self, table: str) -> List[Dict[str, Any]]:
        """
        检测表中每列的 NULL 数量及占比，
        返回存在 NULL 的列的汇总列表。
        """
        # 先获取列名
        struct = self.db.describe_table(table)
        if not struct:
            print_warn(f"无法获取表 {table} 的结构")
            return []

        # 兼容不同数据库返回的字段名
        col_key = None
        for key in ("Field", "column_name", "COLUMN_NAME"):
            if key in struct[0]:
                col_key = key
                break
        if not col_key:
            col_key = list(struct[0].keys())[0]

        columns = [row[col_key] for row in struct]
        total = self.count_rows(table)
        results = []

        for col in columns:
            null_sql = f"SELECT COUNT(*) AS cnt FROM {table} WHERE `{col}` IS NULL" \
                if self.db.db_type == "mysql" \
                else f'SELECT COUNT(*) AS cnt FROM {table} WHERE "{col}" IS NULL'
            rows = self.db.execute(null_sql)
            null_cnt = int(list(rows[0].values())[0]) if rows else 0
            if null_cnt > 0:
                pct = round(null_cnt / total * 100, 2) if total else 0
                results.append({"列名": col, "NULL数量": null_cnt, "总行数": total, "NULL占比(%)": pct})

        return results

    # ------------------------------------------------------------------
    # 重复值检测
    # ------------------------------------------------------------------
    def check_duplicates(self, table: str, key_columns: List[str]) -> int:
        """
        检测指定字段组合是否存在重复行。
        返回重复的行数（重复组合出现次数 > 1 的总行数）。
        """
        if self.db.db_type == "mysql":
            cols = ", ".join(f"`{c}`" for c in key_columns)
        else:
            cols = ", ".join(f'"{c}"' for c in key_columns)

        sql = f"""
            SELECT {cols}, COUNT(*) AS dup_count
            FROM {table}
            GROUP BY {cols}
            HAVING COUNT(*) > 1
        """
        rows = self.db.execute(sql)
        total_dups = sum(int(r["dup_count"]) for r in rows) if rows else 0
        return total_dups

    # ------------------------------------------------------------------
    # 数据范围检测
    # ------------------------------------------------------------------
    def check_range(self, table: str, column: str) -> Dict[str, Any]:
        """检测数值/日期列的最大、最小、平均值"""
        if self.db.db_type == "mysql":
            col_expr = f"`{column}`"
        else:
            col_expr = f'"{column}"'

        sql = f"""
            SELECT
                MIN({col_expr})  AS min_val,
                MAX({col_expr})  AS max_val,
                AVG({col_expr})  AS avg_val,
                COUNT({col_expr}) AS non_null_cnt
            FROM {table}
        """
        rows = self.db.execute(sql)
        return rows[0] if rows else {}

    # ------------------------------------------------------------------
    # 枚举值检测
    # ------------------------------------------------------------------
    def check_distinct_values(self, table: str, column: str, limit: int = 20) -> List[Dict]:
        """列出某列的所有不同值及出现次数"""
        if self.db.db_type == "mysql":
            col_expr = f"`{column}`"
        else:
            col_expr = f'"{column}"'

        sql = f"""
            SELECT {col_expr} AS value, COUNT(*) AS cnt
            FROM {table}
            GROUP BY {col_expr}
            ORDER BY cnt DESC
            LIMIT {limit}
        """
        return self.db.execute(sql)

    # ------------------------------------------------------------------
    # 综合检查报告（快速巡检）
    # ------------------------------------------------------------------
    def quick_check(self, table: str) -> None:
        """对指定表执行一键快速巡检，打印报告"""
        print(f"\n{'='*50}")
        print(f"  快速巡检: {table}")
        print(f"{'='*50}")

        # 1. 行数
        total = self.count_rows(table)
        print_info(f"总行数: {total}")

        # 2. 表结构
        struct = self.db.describe_table(table)
        print_info(f"列数: {len(struct)}")

        # 3. NULL 检查
        nulls = self.check_nulls(table)
        if nulls:
            print_warn(f"发现 {len(nulls)} 列存在 NULL 值:")
            print_table(nulls)
        else:
            print_success("所有列均无 NULL 值")

        print(f"{'='*50}\n")
