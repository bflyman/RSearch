"""
Voucher 表检查/查询模块
"""

import select
from typing import List, Dict, Any, Optional
from src.utils.formatter import print_custom_fields, print_kv_table
from src.utils.interactive_helper import InteractiveHelper
from src.utils.scenario_interactor import ScenarioInteractor
class VoucherChecker:
    """Voucher 检查器"""

    def __init__(self, connector):
        """初始化，传入 MSSQLConnector 实例"""
        self.db = connector
        
    def query_by_vo_no(self, vo_no: str) -> Optional[List[Dict[str, Any]]]:
        """
        根据 vo_no 查询 Voucher 记录

        Args:
            vo_no: Voucher 单号

        Returns:
            查询结果列表，未找到返回 None
        """
        # SQL: SELECT * FROM voucher WHERE vo_no = @vo_no
        # 在 pyodbc 中使用 ? 作为占位符
        sql = "SELECT * FROM voucher WHERE vo_no = ?"

        try:
            rows = self.db.execute(sql, (vo_no,))  # 确保返回的记录中包含 vo_no 字段
            return rows if rows else None
        except Exception as e:
            print(f"  [错误] 查询失败: {e}")
            return None

    def get_vo_no_list(self, limit: int = 20) -> Optional[List[Dict]]:
        """
        列出最近的 vo_no 列表（用于辅助输入）

        Args:
            limit: 返回的最大行数

        Returns:
            vo_no 列表
        """
        sql = """
            SELECT TOP (?) vo_no
            FROM voucher
            ORDER BY vo_no DESC
        """
        try:
            rows = self.db.execute(sql, (limit,))
            return rows
        except Exception as e:
            print(f"  [错误] 获取 vo_no 列表失败: {e}")
            return None

    def query_vo_service(self, voucher_key: int) -> Optional[List[Dict[str, Any]]]:
        """
        根据 voucher_key 查询 vo_service 记录

        Args:
            voucher_key: Voucher Key（从 Voucher 表中查询到的字段）

        Returns:
            查询结果列表，未找到返回 None
        """
        # SQL: SELECT * FROM vo_service WHERE voucher_key = @voucher_key
        sql = "SELECT * FROM vo_service WHERE voucher_key = ?"
        try:
            rows = self.db.execute(sql, (voucher_key,))
            return rows if rows else None
        except Exception as e:
            print(f"  [错误] 查询 vo_service 失败: {e}")
            return None
    def interactive(self):
        interactor = ScenarioInteractor()
        iHelper=InteractiveHelper()
        """Voucher 查询操作"""
        print("\n  ┌─ Voucher 查询 ────────────────────────────────┐")
        try:

           
            while True:
                vo_no = input("\n  请输入 Voucher 编号（留空返回）: ").strip()
                if not vo_no:
                    return
                result = self.query_by_vo_no(vo_no)
                if result:
                    print(f"\n  查询到 {len(result)} 条记录：")
                    
                    print_kv_table(result)
                    fileds= interactor.select_scenario("voucher" )
                   
                    if fileds:
                        print_custom_fields(result, fileds)
                    

                    
                else:
                    print(f"\n  未找到 vo_no = '{vo_no}' 的记录")
          
        except Exception as e:
            print(f"\n  [错误] Voucher 查询失败: {e}")
            print(f"voucher_query error: {e}")
        finally:
            print()
    def interactive2(self,voucher_key: int):
        """Voucher 查询操作"""
        print("\n  ┌─ Voucher 查询 ────────────────────────────────┐")
        try:

             
            while True:
                print("  │  1. 查询 vo_service")
                print("  │  0. 返回主菜单")
                
                try:
                    sub_choice = input("  请选择操作: ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                
                if sub_choice == "1":
                    self.query_vo_service(voucher_key)
                elif sub_choice == "2":
                    _query_vo_procedure(voucher_key)
                elif sub_choice == "0":
                    break
                else:
                    print("  [提示] 无效选项，请重新输入。\n")
        except Exception as e:
            print(f"\n  [错误] Voucher 查询失败: {e}")
            logger.error(f"voucher_query error: {e}")
        finally:
            print()