"""
数据查询模块
提供简单的查询功能
"""
from typing import List, Dict, Any


def query_by_field(
    connector,
    table_name: str,
    field_name: str,
    field_value: Any
) -> List[Dict[str, Any]]:
    """
    根据表名、字段名和字段值进行查询

    Args:
        connector: 数据库连接器实例
        table_name: 表名
        field_name: 字段名
        field_value: 字段值

    Returns:
        查询结果列表
    """
    sql = f"SELECT * FROM {table_name} WHERE {field_name} = ?"
    params = (field_value,)
    result = connector.execute(sql, params)
    return result
