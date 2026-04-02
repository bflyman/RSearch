"""
交互帮助类
提供各种交互式输入辅助函数
"""

from typing import List, Tuple, Optional, Any


class InteractiveHelper:
    """交互帮助类"""

    @staticmethod
    def select_from_list(title: str, items: List[Any], prompt: str = "请选择") -> Tuple[Optional[int], Optional[Any]]:
        """
        从列表中交互式选择一个项目

        Args:
            title: 显示的标题
            items: 可选项目列表
            prompt: 输入提示文字

        Returns:
            Tuple[int, Any]: (索引, 选中的项目)
            如果用户取消则返回 (None, None)
        """
        if not items:
            print(f"  [提示] 没有可选项目")
            return None, None

        print(f"\n  ┌─ {title} ────────────────────────────────┐")

        # 显示列表项
        for idx, item in enumerate(items, 1):
            item_str = str(item)
            # 截断过长的显示
            display_item = item_str[:45] + "..." if len(item_str) > 45 else item_str
            print(f"  │  {idx:>3}. {display_item}")

        print("  │    0. 返回/取消")
        print("  └──────────────────────────────────────────────┘")

        # 用户输入
        while True:
            try:
                choice = input(f"  {prompt}: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n  已取消")
                return None, None

            if choice == "0":
                return None, None

            if not choice.isdigit():
                print("  [提示] 请输入有效的数字编号")
                continue

            idx = int(choice) - 1
            if 0 <= idx < len(items):
                selected_item = items[idx]
                # 显示选择结果
                item_str = str(selected_item)
                display_item = item_str[:40] + "..." if len(item_str) > 40 else item_str
                print(f"\n  ✅ 已选择: {display_item}")
                return idx, selected_item
            else:
                print(f"  [提示] 编号超出范围，请输入 0 ~ {len(items)}")


    @staticmethod
    def select_from_dict(title: str, items: dict, display_key: str, prompt: str = "请选择") -> Tuple[Optional[int], Optional[Any]]:
        """
        从字典中交互式选择一个项目

        Args:
            title: 显示的标题
            items: 字典 {key: value}
            display_key: 用于显示的字段名（如果字典的值是字典）
            prompt: 输入提示文字

        Returns:
            Tuple[int, Any]: (索引, 选中的项目)
            如果用户取消则返回 (None, None)
        """
        if not items:
            print(f"  [提示] 没有可选项目")
            return None, None

        print(f"\n  ┌─ {title} ────────────────────────────────┐")

        # 显示列表项
        keys = list(items.keys())
        for idx, key in enumerate(keys, 1):
            item = items[key]
            # 如果值是字典，使用 display_key 来显示
            if isinstance(item, dict) and display_key in item:
                display_text = f"{key}: {item[display_key]}"
            else:
                display_text = f"{key}: {str(item)}"

            # 截断过长的显示
            display_item = display_text[:45] + "..." if len(display_text) > 45 else display_text
            print(f"  │  {idx:>3}. {display_item}")

        print("  │    0. 返回/取消")
        print("  └──────────────────────────────────────────────┘")

        # 用户输入
        while True:
            try:
                choice = input(f"  {prompt}: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n  已取消")
                return None, None

            if choice == "0":
                return None, None

            if not choice.isdigit():
                print("  [提示] 请输入有效的数字编号")
                continue

            idx = int(choice) - 1
            if 0 <= idx < len(keys):
                selected_key = keys[idx]
                selected_item = items[selected_key]
                # 显示选择结果
                if isinstance(selected_item, dict) and display_key in selected_item:
                    display_item = f"{selected_key}: {selected_item[display_key]}"
                else:
                    display_item = f"{selected_key}: {str(selected_item)}"
                print(f"\n  ✅ 已选择: {display_item}")
                return idx, selected_item
            else:
                print(f"  [提示] 编号超出范围，请输入 0 ~ {len(items)}")


# ========================================
# 测试代码
# ========================================
if __name__ == "__main__":
    print("=" * 60)
    print("   交互帮助类测试")
    print("=" * 60)

    helper = InteractiveHelper()

    # 测试1: 从列表中选择
    print("\n【测试1】从列表中选择")
    fields = ['voucher_key', 'vo_no', 'create_time', 'create_user', 'status']
    idx, selected_field = helper.select_from_list(
        title="可选字段",
        items=fields,
        prompt="请选择字段编号"
    )
    if selected_field is not None:
        print(f"  返回值: 索引={idx}, 选择={selected_field}")

    # 测试2: 从字符串列表中选择
    print("\n【测试2】从场景列表中选择")
    scenarios = [
        "创建数据检查",
        "状态检查",
        "基本信息检查",
        "完整信息检查"
    ]
    idx, selected_scenario = helper.select_from_list(
        title="检查场景",
        items=scenarios,
        prompt="请选择场景编号"
    )
    if selected_scenario is not None:
        print(f"  返回值: 索引={idx}, 选择={selected_scenario}")

    # 测试3: 从字典中选择
    print("\n【测试3】从字典中选择")
    table_dict = {
        'voucher': {'display_name': '凭证表', 'row_count': 1000},
        'vo_service': {'display_name': '服务表', 'row_count': 500},
        'vo_procedure': {'display_name': '流程表', 'row_count': 200}
    }
    idx, selected_table = helper.select_from_dict(
        title="可选表",
        items=table_dict,
        display_key='display_name',
        prompt="请选择表编号"
    )
    if selected_table is not None:
        print(f"  返回值: 索引={idx}, 选择={selected_table}")

    print("\n" + "=" * 60)
