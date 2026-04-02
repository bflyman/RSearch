"""
检查场景交互模块
用于加载表显示配置并提供交互式场景选择
"""

import yaml
import os
from typing import List, Dict, Optional


class ScenarioInteractor:
    """检查场景交互器"""

    def __init__(self, config_path: str = None):
        """
        初始化场景交互器

        Args:
            config_path: 配置文件路径，默认为 config/table_display.yml
        """
        if config_path is None:
            # 获取项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(project_root, 'config', 'table_display.yml')

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"  [错误] 配置文件不存在: {self.config_path}")
            return {}
        except yaml.YAMLError as e:
            print(f"  [错误] 配置文件格式错误: {e}")
            return {}

    def list_tables(self) -> List[str]:
        """
        获取所有可用的表名

        Returns:
            表名列表
        """
        return list(self.config.keys())

    def get_table_display_name(self, table_name: str) -> str:
        """
        获取表的显示名称

        Args:
            table_name: 表名（小写）

        Returns:
            表显示名称，如果表不存在则返回表名
        """
        table_config = self.config.get(table_name, {})
        return table_config.get('display_name', table_name)

    def list_scenarios(self, table_name: str) -> List[Dict]:
        """
        获取指定表的所有检查场景

        Args:
            table_name: 表名（小写）

        Returns:
            场景列表，每个场景包含 name 和 description
        """
        table_config = self.config.get(table_name, {})
        scenarios = table_config.get('scenarios', [])

        # 返回场景列表（只包含名称和说明）
        return [
            {
                'name': scenario.get('name', ''),
                'description': scenario.get('description', '')
            }
            for scenario in scenarios
        ]

    def select_scenario(self, table_name: str) -> Optional[List[str]]:
        """
        交互式选择检查场景

        Args:
            table_name: 表名（小写）

        Returns:
            选中的字段列表，如果用户取消则返回 None
        """
        # 获取场景列表
        scenarios = self.list_scenarios(table_name)

        if not scenarios:
            print(f"  [提示] 表 '{table_name}' 没有配置检查场景")
            return None

        # 获取表显示名称
        table_display_name = self.get_table_display_name(table_name)

        # 显示场景列表
        print(f"\n  ┌─ {table_display_name} 检查场景 ────────────────┐")
        for idx, scenario in enumerate(scenarios, 1):
            name = scenario['name']
            desc = scenario['description']
            print(f"  │  {idx}. {name}")
            if desc:
                # 简化显示，截断过长的说明
                short_desc = desc[:50] + "..." if len(desc) > 50 else desc
                print(f"  │     {short_desc}")
        print("  │  0. 返回")
        print("  └──────────────────────────────────────────────────┘")

        # 用户选择
        while True:
            try:
                choice = input("  请选择场景编号: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n  已取消")
                return None

            if choice == "0":
                return None

            if not choice.isdigit():
                print("  [提示] 请输入有效数字编号")
                continue

            idx = int(choice) - 1
            if 0 <= idx < len(scenarios):
                # 获取选中的场景配置
                table_config = self.config.get(table_name, {})
                scenarios_full = table_config.get('scenarios', [])
                selected_scenario = scenarios_full[idx]

                # 返回字段列表
                fields = selected_scenario.get('fields', [])

                # 显示选中的场景信息
                print(f"\n  已选择: {selected_scenario.get('name', '')}")
                print(f"  说明: {selected_scenario.get('description', '')}")
                print(f"  字段 ({len(fields)} 个): {', '.join(fields)}")

                return fields
            else:
                print(f"  [提示] 编号超出范围，请输入 0 ~ {len(scenarios)}")

    def get_scenario_fields(self, table_name: str, scenario_index: int) -> Optional[List[str]]:
        """
        直接获取指定场景的字段列表（非交互式）

        Args:
            table_name: 表名（小写）
            scenario_index: 场景索引（从0开始）

        Returns:
            字段列表，如果索引无效则返回 None
        """
        table_config = self.config.get(table_name, {})
        scenarios = table_config.get('scenarios', [])

        if 0 <= scenario_index < len(scenarios):
            return scenarios[scenario_index].get('fields', [])
        else:
            return None

    def show_available_tables(self) -> None:
        """显示所有可用的表"""
        tables = self.list_tables()

        print("\n  ┌─ 可用表 ───────────────────────────────┐")
        for idx, table_name in enumerate(tables, 1):
            display_name = self.get_table_display_name(table_name)
            print(f"  │  {idx}. {table_name} ({display_name})")
        print("  └──────────────────────────────────────────────┘")


# ========================================
# 测试代码
# ========================================
if __name__ == "__main__":
    # 创建场景交互器
    interactor = ScenarioInteractor()

    print("=" * 60)
    print("   检查场景配置测试工具")
    print("=" * 60)

    # 显示所有表
    interactor.show_available_tables()

    # 用户输入表名
    table_name = input("\n  请输入表名: ").strip().lower()

    if not table_name:
        print("  [提示] 未输入表名")
    else:
        # 获取表配置
        table_display_name = interactor.get_table_display_name(table_name)

        # 检查表是否存在
        if table_name not in interactor.list_tables():
            print(f"  [错误] 表 '{table_name}' 不存在")
        else:
            print(f"\n  表名: {table_name}")
            print(f"  显示名称: {table_display_name}")

            # 显示所有场景
            scenarios = interactor.list_scenarios(table_name)

            if not scenarios:
                print(f"  [提示] 表 '{table_name}' 没有配置检查场景")
            else:
                print(f"\n  ┌─ {table_display_name} 的检查场景 ────────────────┐")
                for idx, scenario in enumerate(scenarios, 1):
                    name = scenario['name']
                    desc = scenario['description']

                    print(f"  │  {idx}. {name}")
                    # 显示说明（截断过长的）
                    if desc:
                        short_desc = desc[:55] + "..." if len(desc) > 55 else desc
                        print(f"  │     {short_desc}")

                    # 显示字段
                    fields = interactor.get_scenario_fields(table_name, idx - 1)
                    if fields:
                        field_str = ", ".join(fields)
                        # 截断过长的字段串
                        if len(field_str) > 50:
                            field_str = field_str[:47] + "..."
                        print(f"  │     字段: {field_str}")

                print("  └───────────────────────────────────────────────────┘")

                # 交互式选择场景
                print(f"\n  提示: 您可以选择场景编号来进一步查询，或按 Ctrl+C 退出")
                selected_fields = interactor.select_scenario(table_name)

                if selected_fields:
                    print(f"\n  ✅ 成功获取字段列表 ({len(selected_fields)} 个):")
                    for field in selected_fields:
                        print(f"     - {field}")

                    # 显示使用示例
                    print("\n  SQL 查询示例：")
                    field_list_str = ", ".join(selected_fields)
                    print(f"     SELECT {field_list_str}")
                    print(f"     FROM {table_name}")
                    print(f"     WHERE [条件]")
                else:
                    print("  已取消选择")
    print("\n" + "=" * 60)
