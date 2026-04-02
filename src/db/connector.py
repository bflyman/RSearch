"""
MSSQL 数据库连接器（支持强制加密）
"""

import pyodbc
from typing import List, Dict, Any, Optional


# 按优先级尝试的 ODBC 驱动列表
_ODBC_DRIVERS = [
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 13 for SQL Server",
    "SQL Server Native Client 11.0",
    "SQL Server",
]


def _find_driver() -> Optional[str]:
    """自动探测本机已安装的 SQL Server ODBC 驱动"""
    installed = [d for d in pyodbc.drivers() if "SQL Server" in d]
    for preferred in _ODBC_DRIVERS:
        if preferred in installed:
            return preferred
    return installed[0] if installed else None


class MSSQLConnector:
    """MSSQL 连接器，封装连接、查询、元数据操作"""

    def __init__(self):
        self.conn: Optional[pyodbc.Connection] = None
        self.cursor: Optional[pyodbc.Cursor] = None
        self._db_info: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # 连接 / 断开
    # ------------------------------------------------------------------
    def connect(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        timeout: int = 10,
        encrypt: bool = False,  # 默认不加密
        trust_server_certificate: bool = False,  # 默认不信任服务器证书
    ) -> bool:
        """
        建立连接，成功返回 True，失败返回 False 并打印原因。

        参数:
            encrypt: 是否强制加密连接（默认 False）
            trust_server_certificate: 是否信任服务器证书（默认 False）
        """
        driver = _find_driver()
        if not driver:
            raise EnvironmentError(
                "未找到任何 SQL Server ODBC 驱动，请先安装：\n"
                "  https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server"
            )

        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={host};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Connection Timeout={timeout};"
            f"Encrypt={'yes' if encrypt else 'no'};"
            f"TrustServerCertificate={'yes' if trust_server_certificate else 'no'};"
        )
        try:
            self.conn = pyodbc.connect(conn_str, autocommit=True)
            self.cursor = self.conn.cursor()
            self._db_info = {
                "host": host, "port": str(port),
                "database": database, "username": username,
                "driver": driver,
                "encrypt": str(encrypt),
                "trust_cert": str(trust_server_certificate),
            }
            return True
        except pyodbc.Error as e:
            self.conn = None
            self.cursor = None
            raise ConnectionError(f"MSSQL 连接失败: {e}") from e

    def close(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
        except Exception:
            pass
        finally:
            self.conn = None
            self.cursor = None

    def is_connected(self) -> bool:
        return self.conn is not None

    def get_db_info(self) -> Dict[str, str]:
        return self._db_info.copy()

    # ------------------------------------------------------------------
    # SQL 执行
    # ------------------------------------------------------------------
    def execute(self, sql: str, params=None) -> List[Dict[str, Any]]:
        """
        执行 SQL，返回 List[dict]。
        SELECT → 返回结果集；非 SELECT → 返回空列表。
        """
        if not self.cursor:
            raise RuntimeError("数据库未连接")
        self.cursor.execute(sql, params or ())
        if self.cursor.description:
            cols = [col[0] for col in self.cursor.description]
            return [dict(zip(cols, row)) for row in self.cursor.fetchall()]
        return []

    def execute_many(self, sql: str, param_list: list) -> int:
        """批量执行，返回影响行数"""
        if not self.cursor:
            raise RuntimeError("数据库未连接")
        self.cursor.executemany(sql, param_list)
        return self.cursor.rowcount

    def get_columns(self) -> Optional[List[str]]:
        """获取上次 SELECT 的列名列表"""
        if self.cursor and self.cursor.description:
            return [col[0] for col in self.cursor.description]
        return None

    # ------------------------------------------------------------------
    # 元数据
    # ------------------------------------------------------------------
    def list_tables(self, schema: str = "dbo") -> List[str]:
        """列出指定 schema 下的所有用户表"""
        sql = """
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
              AND TABLE_SCHEMA = ?
            ORDER BY TABLE_NAME
        """
        rows = self.execute(sql, (schema,))
        return [r["TABLE_NAME"] for r in rows]

    def list_schemas(self) -> List[str]:
        """列出所有 schema"""
        rows = self.execute(
            "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA ORDER BY SCHEMA_NAME"
        )
        return [r["SCHEMA_NAME"] for r in rows]

    def describe_table(self, table: str, schema: str = "dbo") -> List[Dict]:
        """查看表结构（列名、类型、可空、默认值）"""
        sql = """
            SELECT
                c.COLUMN_NAME        AS 列名,
                c.DATA_TYPE          AS 类型,
                CASE c.CHARACTER_MAXIMUM_LENGTH
                    WHEN -1 THEN 'MAX'
                    WHEN NULL THEN CAST(c.NUMERIC_PRECISION AS VARCHAR)
                    ELSE CAST(c.CHARACTER_MAXIMUM_LENGTH AS VARCHAR)
                END                  AS 长度,
                c.IS_NULLABLE        AS 可空,
                c.COLUMN_DEFAULT     AS 默认值
            FROM INFORMATION_SCHEMA.COLUMNS c
            WHERE c.TABLE_NAME   = ?
              AND c.TABLE_SCHEMA  = ?
            ORDER BY c.ORDINAL_POSITION
        """
        return self.execute(sql, (table, schema))

    def get_row_count(self, table: str, schema: str = "dbo") -> int:
        """快速获取表行数（走系统统计，大表极快）"""
        sql = """
            SELECT SUM(p.rows) AS row_count
            FROM sys.tables t
            JOIN sys.schemas s ON t.schema_id = s.schema_id
            JOIN sys.partitions p ON t.object_id = p.object_id
            WHERE s.name = ? AND t.name = ? AND p.index_id IN (0, 1)
        """
        rows = self.execute(sql, (schema, table))
        val = rows[0]["row_count"] if rows else None
        return int(val) if val is not None else 0

    def test_connection(self) -> bool:
        """发送轻量 ping 测试连接是否仍然存活"""
        try:
            self.execute("SELECT 1 AS ping")
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # context manager
    # ------------------------------------------------------------------
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
