from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from datamineana.dataobject  import TabularData
from datamineana.dataobject  import PathLike, SaveMode


class BaseDataSaver(ABC):
    """
    数据保存抽象父类。

    设计支持四种模式：

    1. 新文件保存
    2. 原文件修改保存
    3. 新增补丁文件保存
    4. 数据库存储
    """

    @abstractmethod
    def save(
        self,
        data: TabularData,
        path: Optional[PathLike] = None,
        mode: SaveMode = SaveMode.NEW_FILE,
        **kwargs: Any,
    ) -> Any:
        raise NotImplementedError