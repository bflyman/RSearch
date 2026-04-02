
import os
from tracemalloc import start
from typing import List, Dict, Any, Optional
from src.utils.tableConfig import TableConfig
import subprocess
from src.utils.interactive_helper import InteractiveHelper
from src.utils.formatter import print_custom_fields
from src.utils.formatter import print_table
from src.utils.logger import get_logger
logger=get_logger(__name__)
class TableChecker:
    def __init__(self, db_connector,parent=None):
        self.db = db_connector
        self.rows=[]
        self.config=TableConfig()
        self.ihelper=InteractiveHelper()
        self.tableName=""
        self.parent=parent

    def Interactive(self, table_name: str) -> Optional[List[Dict[str, Any]]]:
        self.tableName=table_name
        while True: 
            self.rows=None
            self.InteractiveBySearchMenu()
            if self.rows is None:
                return None
            self.displayFirstScenario()
            option=self.showHasDataMenu()

    def InteractiveNonSelfSearch(self, table_name: str) -> Optional[List[Dict[str, Any]]]:
        self.tableName=table_name
                  

    def showHasDataMenu(self)-> Optional[int]:
        hasDataMenu = ["显示数据","查找子表数据","查询所有子表数据","更换条件查询","打印数据的JSON格式"]
        while True:
            idx,_=self.ihelper.select_from_list(f"{self.tableName}  更多操作", hasDataMenu, "輸入数字选择操作")
            if idx ==0:
                self.InteractiveByscenarios()
            elif idx ==1:
                 self.InteractiveByRelationTable()
            elif idx ==2:
                self.SearhRelationTable(self.tableName,None, None, self.rows)
            elif idx ==4:
                import json
                print(json.dumps(self.rows, indent=2, ensure_ascii=False,default=str))
                outFile=input("输出文件名 (空白跳过): ").strip()
                if outFile:
                    with open(outFile, "w", encoding="utf-8") as f:
                        json.dump(self.rows, f, indent=2, ensure_ascii=False,default=str)
                        subprocess.run(['explorer', '/select,', os.path.normpath(outFile)])
            elif idx ==5:
                resultList=[]
                searchPath=self.SearchPath(resultList)
                for path in resultList:
                    print(path)
            else:
                return None        
    def SearchPath(self, result: List[str]):
         
        search_menu=self.config.get_search_menu(self.tableName) 
        filtered_menu = [menu for menu in search_menu if not menu["search_fields"].endswith('key')]
        if len(filtered_menu)>0:
            for menu in filtered_menu:
                print(f'\t{menu["search_fields"]}:\n\t\t{self._get_parent_path("")}')  
        tables=self.config.get_Relation_tables(self.tableName)         
        if not tables:
            return 
        for table in tables:
            if self.CheckParentSearch(table["table_name"]):
                continue
           
            relationTableChecker=TableChecker(self.db,self)
            relationTableChecker.tableName=table["table_name"]
            relationTableChecker.SearchPath(result)
             
    def _get_parent_path(self,path)->str    :
        if self.parent:
           
            parent_path=self.parent._get_parent_path(path)
            return self.tableName+ " -> "  + parent_path 
        else:
            return self.tableName
    def InteractiveByParent(self,table_name:str,query_field:str,field:str,rows:List[Dict[str, Any]]):
        self.tableName=table_name

        self.rows=[]
        for row in rows:
            temp= self.query_by_field(self.tableName, query_field, row[field])
            if temp:
                row[table_name]=temp
                self.rows.extend(temp)
        print(f'InteractiveByParent-查询结果: {len(self.rows)} 条记录')        
        self.displayFirstScenario()     
        while True: 
            option=self.showHasDataMenu()
            if option is None:
                break
        
        
         
    def InteractiveByRelationTable(self):
        relation_tables = self.config.get_Relation_tables(self.tableName)
        if not relation_tables:
            logger.warning(f"{self.tableName}: 没有配置关联表")
            return
        
        idx,selected = self.ihelper.select_from_list(f"{self.tableName} 关联表选择", [item["table_name"] for item in relation_tables], "请选择关联表")
        if idx is not None:
            relation_table = relation_tables[idx]
            relationTableChecker=TableChecker(self.db)
            
            relationTableChecker.InteractiveByParent(relation_table["table_name"],relation_table.get("query_field", relation_table["field"]),relation_table["field"],self.rows)
    def SearhRelationTable(self,table_name:str,query_filed:str,field:str,rows:List[Dict[str, Any]]):
        if table_name!=self.tableName:
            self.tableName=table_name

            self.rows=[]
            for row in rows:
                if field not in row:
                    print(f"当前行数据中缺少字段 {field}，无法查询关联表 {table_name}")
                    continue
                temp= self.query_by_field(self.tableName, query_filed, row[field])
                if temp:
                    row[table_name]=temp
                    self.rows.extend(temp)
            print(f'{table_name} -查询结果: {len(self.rows)} 条记录')        
        relation_tables = self.config.get_Relation_tables(self.tableName)
  
        if not relation_tables:
            logger.warning(f"{table_name}没有配置关联表")
            return
        for relation_table in relation_tables:
            if( self.CheckParentSearch(relation_table["table_name"])):
                print(f"已查询过关联表 {relation_table['table_name']}，跳过避免循环查询")
                continue    
            relationTableChecker=TableChecker(self.db,self)
            relationTableChecker.SearhRelationTable(relation_table["table_name"],relation_table.get("query_field", relation_table["field"]), relation_table["field"],self.rows)
    def CheckParentSearch(self,table_name:str)->bool:
        logger.debug(f"检查 {self.tableName} 的父级 {table_name}")
        parent=self.parent
        if parent :
            logger.debug(f"当前父级 {parent.tableName}")
            if parent.rows and len([row for row in parent.rows if  table_name in row]):
                return True
            if parent.tableName==table_name:
                return True
            else:
                return parent.CheckParentSearch(table_name)
        else:
            return False

    def InteractiveByscenarios(self):
        scenarios = self.config.get_scenarios(self.tableName)
        if not scenarios:
            # print("没有配置检查场景")
            print_table(self.rows)
            return
        
        idx,selected = self.ihelper.select_from_list(f"{self.tableName} 场景选择", [item["name"] for item in scenarios], "请选择检查场景")
        if idx is not None:
            scenario_fields = self.config.get_scenario_fields(self.tableName, idx)
            print_custom_fields(self.rows, scenario_fields)
    def displayFirstScenario(self ):
         
        
        # 获取第一个场景的字段配置1

        scenarios = self.config.get_scenarios(self.tableName)
        if not scenarios:
            print("没有配置默认场景")
            return
        
        first_scenario = scenarios[0]
        fields_to_display = first_scenario.get("fields", [])
        
        # 打印表头
        print_custom_fields(self.rows,fields_to_display)
         
    def InteractiveBySearchMenu(self  ) -> bool:
        search_menu = self.config.get_search_menu(self.tableName)
        menu=search_menu.copy()
        menu.insert(0, {"display_name": "查询全部数据", "search_fields": None})    
        menu.insert(1,{"display_name": "关联查询路径", "search_fields": None})    
        while True:
            idx,selected = self.ihelper.select_from_list(f"{self.tableName} 查询", [item["display_name"] for item in menu], "请輸入数字选择查询条件")
            if idx is not None:
                if idx ==0:
                    self.rows = self.query_by_field(self.tableName, "1", "1")
                    print(f'查询结果: {len(self.rows)} 条记录')
                    return True
                if idx ==1:
                    result=[]
                    self.SearchPath(result)
                    for path in result:
                        print(path)
                    return True
                field_name = search_menu[idx-2]['search_fields']
                
                field_value = input(f"请输入 {field_name} 的值: ").strip()
                if field_value:
                    self.rows = self.query_by_field(self.tableName, field_name, field_value)
                    print(f'查询结果: {len(self.rows)} 条记录')
                    return True
            else:
                return False
    
                 
              
            

    def query_by_field(
        self,
        table_name: str,
        field_name: str,
        field_value: Any,
   
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
        result = self.db.execute(sql, params)
        return result    
        