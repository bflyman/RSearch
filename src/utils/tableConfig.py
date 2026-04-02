"""
表格配置模块
用于加载和查询 table_display.yml 配置
"""

import os
from typing import List, Dict, Any, Optional

try:
    import yaml
except ImportError:
    raise ImportError("请先安装 PyYAML: pip install pyyaml")


class TableConfig:
    """表格配置加载和查询类"""
    
    def __init__(self, config_path: str = None):
        """
        初始化表格配置
        
        Args:
            config_path: 配置文件路径，默认为项目根目录下的 config/table_display.yml
        """
        if config_path is None:
            # 获取项目根目录
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(base, "config","table" )
        
        self.config_path = config_path
        self.config_data = self._load_config()
    def get_yaml_files(self,dir_path):
        """
        列出目录下所有 .yaml / .yml 文件（不递归子目录）
        返回文件路径列表
        """
        yaml_files = []
        if not os.path.isdir(dir_path):
            return yaml_files

        for filename in os.listdir(dir_path):
            # 匹配后缀
            if filename.lower().endswith(('.yaml', '.yml'))  :
                yaml_files.append(os.path.join(dir_path, filename))
        
        # 排序（保证加载顺序稳定）
        yaml_files.sort()
        return yaml_files
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            配置数据字典
        """
        files=self.get_yaml_files(self.config_path)
        config_data={}
        for file in files:
            with open(file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                config_data.update(data)
        return config_data
    
    def get_table_display_name(self, table_name: str) -> Optional[str]:
        """
        获取表的显示名称
        
        Args:
            table_name: 表名
            
        Returns:
            表的显示名称，如果不存在则返回 None
        """
        table_config = self.config_data.get(str.lowertable_name)
        if table_config:
            return table_config.get("display_name")
        return None
    
    def get_search_menu(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取指定表的搜索菜单配置
        
        Args:
            table_name: 表名（顶级配置项）
            
        Returns:
            搜索菜单配置列表，每个配置项包含：
                - display_name: 显示名称
                - search_fields: 搜索字段（字符串或列表）
            如果表不存在或没有配置 search_menu，返回空列表
        """
        table_config = self.config_data.get(table_name)
        if not table_config:
            return []
        
        search_menu = table_config.get("search_menu", [])
        return search_menu
    def get_Relation_tables(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取指定表的关联表配置
        
        Args:
            table_name: 表名（顶级配置项）
            
        Returns:
            关联表配置列表，每个配置项包含：
                - display_name: 显示名称
                - relation_fields: 关联字段（字符串或列表）
            如果表不存在或没有配置 relation_tables，返回空列表
        """
        table_config = self.config_data.get(table_name)
        if not table_config:
            return []
        
        relation_tables = table_config.get("relation_tables", [])
        return relation_tables

    def get_scenarios(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取指定表的所有检查场景
        
        Args:
            table_name: 表名
            
        Returns:
            检查场景列表，每个场景包含：
                - name: 场景名称
                - description: 场景说明
                - fields: 字段列表
            如果表不存在或没有配置 scenarios，返回空列表
        """
        table_config = self.config_data.get(table_name)
        if not table_config:
            return []
        
        scenarios = table_config.get("scenarios", [])
        return scenarios
    
    def get_scenario_fields(self, table_name: str, scenario_index: int) -> List[str]:
        """
        获取指定场景的字段列表
        
        Args:
            table_name: 表名
            scenario_index: 场景索引（从 0 开始）
            
        Returns:
            字段列表，如果表或场景不存在则返回空列表
        """
        scenarios = self.get_scenarios(table_name)
        
        if 0 <= scenario_index < len(scenarios):
            scenario = scenarios[scenario_index]
            return scenario.get("fields", [])
        
        return []
    
    def get_all_tables(self) -> List[str]:
        """
        获取所有配置的表名
        
        Returns:
            表名列表
        """
        return list(self.config_data.keys())


if __name__ == "__main__":
    # 测试代码
    try:
        config = TableConfig()
        
        # 测试获取所有表名
        print("=== 所有表名 ===")
        tables = config.get_all_tables()
        for table in tables:
            print(f"  - {table}")
        
        # 测试获取表显示名称
        print("\n=== 表显示名称 ===")
        table_name = "voucher"
        display_name = config.get_table_display_name(table_name)
        print(f"  {table_name}: {display_name}")
        
        # 测试获取搜索菜单
        print(f"\n=== {table_name} 的搜索菜单 ===")
        search_menu = config.get_search_menu(table_name)
        for idx, item in enumerate(search_menu, start=1):
            print(f"  {idx}. {item['display_name']}")
            print(f"     搜索字段: {item.get('search_fields')}")
        
        # 测试获取检查场景
        print(f"\n=== {table_name} 的检查场景 ===")
        scenarios = config.get_scenarios(table_name)
        for idx, scenario in enumerate(scenarios, start=1):
            print(f"  {idx}. {scenario['name']}")
            print(f"     说明: {scenario['description']}")
            print(f"     字段: {scenario['fields'][:3]}... (共{len(scenario['fields'])}个)")
        
        # 测试获取指定场景的字段
        print(f"\n=== 获取第一个场景的字段 ===")
        fields = config.get_scenario_fields(table_name, 0)
        print(f"  字段列表: {fields}")
        
    except FileNotFoundError as e:
        print(f"错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")
