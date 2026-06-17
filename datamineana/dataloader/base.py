from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from datamineana.dataobject import TabularData
from datamineana.dataobject import ColumnSelector, FileType, PathLike, RowSelector


class BaseDataLoader(ABC):
    """
    数据读取抽象父类。

    所有文件读取类都继承它。

    注意：
    读取类只负责读取，不负责数据清洗、不负责数据预处理。
    """

    file_type: FileType = FileType.UNKNOWN

    @abstractmethod
    def load(
            self,
            path: PathLike,
            columns: ColumnSelector = None,
            rows: RowSelector = None,
            dtype: Optional[Dict[str, Any]] = None,
            lazy: bool = False,
            chunksize: Optional[int] = None,
            **kwargs: Any,
    ) -> TabularData:
        """
        读取数据并返回 TabularData。
        """

        raise NotImplementedError
