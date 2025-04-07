"""
配置文件管理模块
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Optional, Tuple


class Config:

    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.getenv('GITBI_CONFIG_PATH')
        if not self.config_path:
            raise ValueError("未指定配置文件路径，请通过参数或环境变量GITBI_CONFIG_PATH指定")
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_db_config(self, db_name: str) -> Tuple[str, str]:
        """获取数据库配置"""
        db_config = self.config.get('databases', {}).get(db_name)
        if not db_config:
            raise ValueError(f"数据库 {db_name} 未配置")

        db_type = db_config.get('type')
        if not db_type:
            raise ValueError(f"数据库 {db_name} 未指定类型")

        conn_str = db_config.get('connection_string')
        if not conn_str:
            raise ValueError(f"数据库 {db_name} 未指定连接字符串")

        return db_type, conn_str

    def get_email_config(self) -> Optional[dict]:
        """获取邮件配置"""
        return self.config.get('email')

    def get_auth_config(self) -> Optional[list]:
        """获取认证配置"""
        return self.config.get('auth', {}).get('users')

    def get_repo_dir(self) -> str:
        """获取仓库目录"""
        repo_dir = self.config.get('repo', {}).get('dir')
        if not repo_dir:
            raise ValueError("未配置仓库目录")
        return repo_dir


# 全局配置实例
config = Config()
