"""
模拟运行版本 — 自动选择第一个数据库并展示主菜单
用于演示界面效果，无需交互输入
"""

import sys
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.db.config_loader import load_db_configs
from src.db.connector import MSSQLConnector
from src.utils.logger import get_logger

logger = get_logger("db_query")


def _banner():
    print("=" * 58)
    print("   数据库运维查询工具  v1.0")
    print("=" * 58)


def _print_db_list(configs: list):
    """打印数据库选择列表，按环境分组显示"""
    print("\n  可用数据库连接：\n")

    current_env = None
    for idx, cfg in enumerate(configs, start=1):
        if cfg.env != current_env:
            current_env = cfg.env
            tag = f"[ {current_env} ]"
            print(f"  {'─'*10} {tag} {'─'*(30-len(tag))}")
        print(f"    {idx:>2}.  {cfg.name}")
        print(f"          {cfg.host}:{cfg.port}  /  {cfg.database}")
    print()


def _main_menu(connector: MSSQLConnector, cfg):
    """主操作菜单"""
    print(f"\n  当前连接: [{cfg.env}] {cfg.name}")
    print(f"  数据库:   {cfg.host}:{cfg.port} / {cfg.database}\n")

    while True:
        print("  ┌─ 主菜单 " + "─" * 38)
        print("  │  1. 列出所有表")
        print("  │  2. 查看表结构")
        print("  │  3. 执行自定义 SQL")
        print("  │  4. 切换数据库")
        print("  │  0. 退出")
        print("  └" + "─" * 47)

        choice = input("  请选择操作: ").strip()

        if choice == "1":
            _action_list_tables(connector)
        elif choice == "2":
            _action_describe_table(connector)
        elif choice == "3":
            _action_exec_sql(connector)
        elif choice == "4":
            return True   # 切换数据库
        elif choice == "0":
            print("  程序退出。")
            return False  # 退出程序
        else:
            print("  [提示] 无效选项，请重新输入。\n")


def _action_list_tables(connector):
    try:
        schema = input("  Schema 名称（直接回车默认 dbo）: ").strip() or "dbo"
        tables = connector.list_tables(schema)
        if not tables:
            print(f"  [{schema}] 下暂无表\n")
            return
        print(f"\n  [{schema}] 共 {len(tables)} 张表：")
        for i, t in enumerate(tables, 1):
            print(f"    {i:>3}. {t}")
        print()
    except Exception as e:
        print(f"  [错误] {e}\n")
        logger.error(f"list_tables: {e}")


def _action_describe_table(connector):
    try:
        table  = input("  表名: ").strip()
        schema = input("  Schema（直接回车默认 dbo）: ").strip() or "dbo"
        if not table:
            print("  [提示] 表名不能为空\n")
            return
        rows = connector.describe_table(table, schema)
        if not rows:
            print(f"  未找到表 [{schema}].[{table}]\n")
            return
        from src.utils.formatter import print_table
        print(f"\n  表结构: [{schema}].[{table}]")
        print_table(rows)
        cnt = connector.get_row_count(table, schema)
        print(f"  当前行数: {cnt:,}\n")
    except Exception as e:
        print(f"  [错误] {e}\n")
        logger.error(f"describe_table: {e}")


def _action_exec_sql(connector):
    print("  输入 SQL（单行，回车执行；输入 'back' 返回）：")
    sql = input("  SQL> ").strip()
    if not sql or sql.lower() == "back":
        return
    try:
        rows = connector.execute(sql)
        if rows:
            from src.utils.formatter import print_table
            print_table(rows)
        else:
            print("  执行成功（无返回结果）\n")
        logger.info(f"执行SQL: {sql[:120]}")
    except Exception as e:
        print(f"  [错误] {e}\n")
        logger.error(f"exec_sql error: {e} | SQL: {sql}")


def main():
    _banner()

    try:
        configs = load_db_configs()
    except FileNotFoundError as e:
        print(f"\n  [错误] {e}")
        sys.exit(1)

    if not configs:
        print("\n  [错误] 配置文件中没有任何数据库配置，请检查 config/databases.yml")
        sys.exit(1)

    _print_db_list(configs)

    # 自动选择第一个配置进行演示
    print("  [演示模式] 自动选择第一个数据库：")
    cfg = configs[0]
    print(f"\n  已选择: {cfg}\n")

    print(f"  正在连接 {cfg.host}:{cfg.port} …", end=" ", flush=True)
    try:
        connector = MSSQLConnector()
        connector.connect(
            host=cfg.host,
            port=cfg.port,
            database=cfg.database,
            username=cfg.username,
            password=cfg.password,
        )
        print("连接成功 ✓")
        logger.info(f"已连接: [{cfg.env}] {cfg.name} ({cfg.host}/{cfg.database})")

        # 进入主菜单
        _main_menu(connector, cfg)

        connector.close()
    except Exception as e:
        print(f"\n  [错误] {e}")
        logger.error(f"连接失败 [{cfg.section}]: {e}")
        print("\n  请检查：")
        print("    1. 数据库地址、端口是否正确")
        print("    2. 用户名、密码是否正确")
        print("    3. 服务器是否可访问")
        print("    4. 是否已安装 ODBC Driver for SQL Server")


if __name__ == "__main__":
    main()
