from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from datamineana.dataobject import TabularData


class BaseDatabaseSaver(ABC):
    """
    数据库存储抽象接口。

    这里只定义接口，不实现具体数据库逻辑。

    后续可以实现：
    - MySQLSaver
    - PostgreSQLSaver
    - SQLiteSaver
    - MongoDBSaver
    - ClickHouseSaver
    """

    @abstractmethod
    def connect(self, **kwargs: Any) -> Any:
        """
        连接数据库。
        """

        raise NotImplementedError

    @abstractmethod
    def save_table(
        self,
        data: TabularData,
        table_name: str,
        if_exists: str = "replace",
        **kwargs: Any,
    ) -> Any:
        """
        保存为数据库表。
        """

        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """
        关闭数据库连接。
        """

        raise NotImplementedError