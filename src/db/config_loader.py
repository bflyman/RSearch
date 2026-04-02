"""
数据库配置加载器（YAML 版）
读取 config/databases.yml，返回结构化的连接配置列表
"""

import os
from dataclasses import dataclass
from typing import List, Optional

try:
    import yaml
except ImportError:
    raise ImportError("请先安装 PyYAML: pip install pyyaml")


@dataclass
class DBConfig:
    """单个数据库连接配置"""
    section: str       # 内部唯一 key（name + env 拼接）
    name: str          # 显示名称
    env: str           # 环境（UAT / PROD / DEV …）
    host: str
    port: int
    database: str
    username: str
    password: str

    def __str__(self):
        return f"[{self.env}] {self.name}  ({self.host}:{self.port}/{self.database})"


def load_db_configs(config_path: str = None) -> List[DBConfig]:
    """
    从 YAML 文件加载所有数据库配置，按 env 排序后返回。
    config_path 默认为项目根目录下的 config/databases.yml。
    """
    if config_path is None:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(base, "config", "databases.yml")

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"找不到配置文件: {config_path}\n"
            f"请先创建 config/databases.yml 并填写连接信息。"
        )

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if "connections" not in data:
        raise ValueError("配置文件缺少顶级 'connections' 字段")

    configs: List[DBConfig] = []
    for idx, item in enumerate(data["connections"]):
        name = item.get("name", f"未命名连接_{idx}")
        env  = item.get("env", "").upper()

        configs.append(DBConfig(
            section  = f"{env}_{name}",  # 作为唯一 key
            name     = name,
            env      = env,
            host     = item.get("host", ""),
            port     = item.get("port", 1433),
            database = item.get("database", ""),
            username = item.get("username", ""),
            password = item.get("password", ""),
        ))

    # 按环境排序：DEV → UAT → PROD（其余按字母）
    env_order = {"DEV": 0, "UAT": 1, "PROD": 2}
    configs.sort(key=lambda c: (env_order.get(c.env, 99), c.env, c.name))
    return configs


def get_config_by_section(section: str, config_path: str = None) -> Optional[DBConfig]:
    """按 section 名查找单条配置"""
    for cfg in load_db_configs(config_path):
        if cfg.section == section:
            return cfg
    return None
