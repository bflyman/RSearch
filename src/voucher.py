"""
Voucher 子模块
用于检查 voucher 表数据
"""

from typing import List, Dict, Any, Optional


class VoucherChecker:
    """Voucher 检查器"""

    def __init__(self, connector):
        self.db = connector

    # ------------------------------------------------------------------
    # 按 vo_no 查询 Voucher 记录
    # ------------------------------------------------------------------
    def query_by_vo_no(self, vo_no: str) -> Optional[List[Dict[str, Any]]]:
        """
        根据 vo_no 查询 Voucher 记录

        Args:
            vo_no: Voucher 编号

        Returns:
            查询结果列表（List[dict]），未找到返回 None
        """
        # 构建查询 SQL
        sql = f"SELECT * FROM voucher WHERE vo_no = @vo_no"

        try:
            rows = self.db.execute(sql)
            return rows
        except Exception as e:
            print(f"  [错误] 查询 Voucher 失败: {e}")
            return None

    # ------------------------------------------------------------------
    # 交互式输入 vo_no 并查询
    # ------------------------------------------------------------------
    def interactive_query(self):
        """交互式查询：让用户输入 vo_no，然后执行查询"""
        while True:
            try:
                vo_no = input("  请输入 vo_no (q 退出): ").strip()
                if not vo_no:
                    print("  [提示] vo_no 不能为空\n")
                    continue
                if vo_no.lower() in ("q", "quit", "exit"):
                    print("  退出查询")
                    return
            except (EOFError, KeyboardInterrupt):
                print("\n  退出查询")
                return

            # 查询
            rows = self.query_by_vo_no(vo_no)
            if rows is None:
                print("  [错误] 查询失败\n")
                continue
            if not rows:
                print(f"  [提示] 未找到 vo_no = {vo_no} 的记录\n")
                continue

            # 显示结果
            print(f"\n  查询结果: vo_no = {vo_no}\n")
            from src.utils.formatter import print_table
            print_table(rows)
