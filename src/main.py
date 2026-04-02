"""
数据查询运维工具 — CLI 主程序
启动流程:
  1. 读取 config/databases.yml，列出所有数据库配置
  2. 用户输入编号选择目标数据库（未选择则不进入下一步）
  3. 尝试建立连接，失败则允许重新选择
  4. 连接成功后进入主菜单（后续功能扩展点）
"""
import sys
import os

# 将项目根目录加入 sys.path，确保 src.* 可正常导入
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.checks.table_check import TableChecker
from src.db.config_loader import load_db_configs, DBConfig
from src.db.connector import MSSQLConnector
from src.utils.logger import get_logger
from src.checks.voucher_checker import VoucherChecker

# 导入 YAML 模块
try:
    import yaml
except ImportError:
    print("错误: 需要安装 PyYAML，请运行: pip install pyyaml")
    sys.exit(1)

logger = get_logger("db_query")

# ======================================================================
# 工具函数
# ======================================================================

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


def _select_database(configs: list) -> DBConfig:
    """
    交互式让用户选择数据库。
    未做出有效选择时持续提示，不返回 None。
    """
    while True:
        try:
            raw = input("  请输入编号选择数据库（q 退出）: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  已取消，程序退出。")
            sys.exit(0)

        if raw.lower() in ("q", "quit", "exit"):
            print("  程序退出。")
            sys.exit(0)

        if not raw:
            print("  [提示] 未输入编号，请重新选择。\n")
            continue

        if not raw.isdigit():
            print("  [提示] 请输入有效数字编号。\n")
            continue

        idx = int(raw)
        if 1 <= idx <= len(configs):
            chosen = configs[idx - 1]
            print(f"\n  已选择: {chosen}\n")
            return chosen
        else:
            print(f"  [提示] 编号超出范围，请输入 1 ~ {len(configs)} 之间的数字。\n")


def _connect_with_retry(configs: list) -> tuple:
    """
    让用户选择并连接数据库，连接失败时提示重新选择。
    返回 (MSSQLConnector, DBConfig)。
    """
    while True:
        cfg = _select_database(configs)
        connector = MSSQLConnector()
        print(f"  正在连接 {cfg.host}:{cfg.port} …", end=" ", flush=True)
        try:
            connector.connect(
                host=cfg.host,
                port=cfg.port,
                database=cfg.database,
                username=cfg.username,
                password=cfg.password,
                encrypt=True,  # 强制加密连接
                trust_server_certificate=True,
            )
            print("连接成功 ✓")
            logger.info(f"已连接: [{cfg.env}] {cfg.name} ({cfg.host}/{cfg.database})")
            return connector, cfg
        except Exception as e:
            print(f"\n  [错误] {e}")
            logger.error(f"连接失败 [{cfg.section}]: {e}")
            print("  请重新选择数据库。\n")
            _print_db_list(configs)


# ======================================================================
# 主菜单（后续扩展点）
# ======================================================================

def _load_menu_config():
    """加载菜单配置"""
    menu_path = os.path.join(_ROOT, "config", "menu.yml")
    if not os.path.exists(menu_path):
        print(f"  [警告] 菜单配置文件不存在: {menu_path}")
        return []
    
    with open(menu_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    if config and 'menu' in config:
        return config['menu']
    return []

def _main_menu(connector: MSSQLConnector, cfg: DBConfig):
    """主操作菜单 — 连接成功后进入"""
    print(f"\n  当前连接: [{cfg.env}] {cfg.name}")
    print(f"  数据库:   {cfg.host}:{cfg.port} / {cfg.database}\n")

    # 加载菜单配置
    menu_items = _load_menu_config()
    
    # 如果没有配置菜单,使用默认菜单
    if not menu_items:
        menu_items = [
            {'display_name': '列出所有表', 'table_name': '', 'remark': '查看数据库中的所有表列表'},
            {'display_name': '查看表结构', 'table_name': '', 'remark': '查看指定表的字段信息'},
            {'display_name': '执行自定义 SQL', 'table_name': '', 'remark': '执行自定义 SQL 查询语句'},
            {'display_name': 'Voucher 查询', 'table_name': 'voucher', 'remark': '根据 Voucher 编号查询相关信息'},
            {'display_name': '切换数据库', 'table_name': '', 'remark': '重新选择数据库连接'},
            {'display_name': '退出', 'table_name': '', 'remark': '退出程序'},
        ]
    else:
        menu_items.append({'display_name': '輸入表名查询', 'table_name': '', 'remark': '重新选择数据库连接'})
    # 初始化 Voucher Checker - 使用已建立的连接
 

    while True:
        tableChecker = TableChecker(connector)
        # 打印菜单
        print("  ┌─ 主菜单 " + "─" * 38)
        for idx, item in enumerate(menu_items, start=1):
            print(f"  │  {idx}. {item['display_name']}")
        print(f"  │  0. 退出")
        print("  └" + "─" * 47)

        try:
            choice = input("  请选择操作: ").strip()
            if(choice=="0"):
                print("  程序退出。")
                return False
            item=menu_items[int(choice) - 1]
            print(f'您选择的是: {item["display_name"]}')
            if(item["display_name"]=='輸入表名查询'):
                table = input("请输入表名: ").strip()
                tableChecker.Interactive(table)
                continue
            else:
                tableChecker.Interactive(item['table_name'])
        except (EOFError, KeyboardInterrupt):
            print("\n  程序退出。")
            break

        if choice == "0":
            print("  程序退出。")
            break
        
        

    return False  # 退出程序

def _execute_menu_action(connector: MSSQLConnector, menu_item: dict, voucher_checker: VoucherChecker):
    """执行菜单操作"""
    display_name = menu_item['display_name']
    
    if display_name == "列出所有表":
        _action_list_tables(connector)
    elif display_name == "查看表结构":
        _action_describe_table(connector)
    elif display_name == "执行自定义 SQL":
        _action_exec_sql(connector)
    elif display_name == "Voucher 查询":
        voucher_checker.interactive()
    elif display_name == "切换数据库":
        connector.close()
        raise SwitchDatabaseException()  # 通知外层重新选择数据库
    else:
        print(f"  [提示] 功能 '{display_name}' 尚未实现。\n")

class SwitchDatabaseException(Exception):
    """切换数据库异常"""
    pass


# ──────────────────────────────────────────
# 菜单动作
# ──────────────────────────────────────────

def _action_list_tables(connector: MSSQLConnector):
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


def _action_describe_table(connector: MSSQLConnector):
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
        # 行数
        cnt = connector.get_row_count(table, schema)
        print(f"  当前行数: {cnt:,}\n")
    except Exception as e:
        print(f"  [错误] {e}\n")
        logger.error(f"describe_table: {e}")


def _action_exec_sql(connector: MSSQLConnector):
    print("  输入 SQL（单行，回车执行；输入 'back' 返回）：")
    try:
        sql = input("  SQL> ").strip()
    except (EOFError, KeyboardInterrupt):
        return
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


def _action_voucher_query(voucher_checker: VoucherChecker):
    """Voucher 查询操作"""
    print("\n  ┌─ Voucher 查询 ────────────────────────────────┐")
    try:

        vo_no = input("\n  请输入 Voucher 编号（留空返回）: ").strip()
        if not vo_no:
            return
        result = voucher_checker.query_by_vo_no(vo_no)
        if result:
            print(f"\n  查询到 {len(result)} 条记录：")
            from src.utils.formatter import print_table
            print_table(result)
            
            # 显示子菜单
            while True:
                print("\n  ┌─ Voucher 子菜单 " + "─" * 33)
                print("  │  1. 查询 vo_service")
                print("  │  2. 查询 vo_procedure")
                print("  │  0. 返回主菜单")
                print("  └" + "─" * 47)
                
                try:
                    sub_choice = input("  请选择操作: ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                
                if sub_choice == "1":
                    _query_vo_service(voucher_checker, vo_no)
                elif sub_choice == "2":
                    _query_vo_procedure(voucher_checker, vo_no)
                elif sub_choice == "0":
                    break
                else:
                    print("  [提示] 无效选项，请重新输入。\n")
        else:
            print(f"\n  未找到 vo_no = '{vo_no}' 的记录")
    except Exception as e:
        print(f"\n  [错误] Voucher 查询失败: {e}")
        logger.error(f"voucher_query error: {e}")
    finally:
        print()


def _query_vo_service(voucher_checker: VoucherChecker, vo_no: str):
    """查询 Voucher 的服务信息"""
    try:
        result = voucher_checker.query_vo_service(vo_no)
        if result:
            print(f"\n  Voucher 编号: {vo_no}")
            print("  ┌─ Service 信息 ─────────────────────────────┐")
            from src.utils.formatter import print_table
            print_table(result)
        else:
            print(f"\n  未找到 vo_no = '{vo_no}' 的 service 信息")
    except Exception as e:
        print(f"\n  [错误] 查询 service 失败: {e}")
        logger.error(f"query_vo_service error: {e}")
    finally:
        print()


def _query_vo_procedure(voucher_checker: VoucherChecker, vo_no: str):
    """查询 Voucher 的流程信息"""
    try:
        result = voucher_checker.query_vo_procedure(vo_no)
        if result:
            print(f"\n  Voucher 编号: {vo_no}")
            print("  ┌─ Procedure 信息 ───────────────────────────┐")
            from src.utils.formatter import print_table
            print_table(result)
        else:
            print(f"\n  未找到 vo_no = '{vo_no}' 的 procedure 信息")
    except Exception as e:
        print(f"\n  [错误] 查询 procedure 失败: {e}")
        logger.error(f"query_vo_procedure error: {e}")
    finally:
        print()


# ======================================================================
# 程序入口
# ======================================================================

def main():
    _banner()

    # 1. 加载配置
    try:
        configs = load_db_configs()
    except FileNotFoundError as e:
        print(f"\n  [错误] {e}")
        sys.exit(1)

    if not configs:
        print("\n  [错误] 配置文件中没有任何数据库配置，请检查 config/databases.yml")
        sys.exit(1)

    # 2. 展示数据库列表
    _print_db_list(configs)

    # 3. 选择 → 连接 → 主菜单（支持切换数据库）
    while True:
        connector, cfg = _connect_with_retry(configs)
        try:
            switch = _main_menu(connector, cfg)
        finally:
            connector.close()

        if not switch:
            break
        # switch=True 时重新展示列表，让用户切换数据库
        print("\n  重新选择数据库：")
        _print_db_list(configs)


if __name__ == "__main__":
    main()
