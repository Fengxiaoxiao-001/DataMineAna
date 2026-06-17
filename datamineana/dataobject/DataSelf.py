from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Union,
)

import numpy as np
import pandas as pd

from .Dtypes import (
    ColumnSelector,
    FileType,
    PathLike,
    RowSelector,
    StoreMode,
)


@dataclass
class ColumnInfo:
    """
    单列信息。
    """

    name: str
    dtype: str


@dataclass
class DataViewInfo:
    """
    数据视图信息。

    用于：
    1. 后续 HTML 展示
    2. 数据预处理前后结构查看
    3. 数据分析前的数据概览
    """

    row_count: Optional[int]
    column_count: Optional[int]

    columns: List[ColumnInfo] = field(default_factory=list)

    added_columns: List[ColumnInfo] = field(default_factory=list)
    dropped_columns: List[str] = field(default_factory=list)

    source_path: Optional[str] = None
    file_type: FileType = FileType.UNKNOWN

    is_lazy: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns": [
                {
                    "name": col.name,
                    "dtype": col.dtype,
                }
                for col in self.columns
            ],
            "added_columns": [
                {
                    "name": col.name,
                    "dtype": col.dtype,
                }
                for col in self.added_columns
            ],
            "dropped_columns": self.dropped_columns,
            "source_path": self.source_path,
            "file_type": self.file_type.value,
            "is_lazy": self.is_lazy,
        }

    def to_json(self, ensure_ascii: bool = False, indent: int = 2) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=ensure_ascii,
            indent=indent,
        )


@dataclass
class TabularData:
    """
    通用表格数据容器。

    这个类是后续所有模块之间的数据中转对象。

    读取模块读取文件后，返回 TabularData。
    数据预处理模块接收 TabularData，返回新的 TabularData。
    数据分析模块接收 TabularData。
    数据可视化模块接收 TabularData。
    数据保存模块接收 TabularData。

    本类只负责：
    1. 存放数据
    2. 读取数据
    3. 转 pandas / numpy
    4. 分块迭代
    5. 提供数据视图信息
    """

    data: Optional[pd.DataFrame] = None

    chunk_factory: Optional[Callable[[], Iterator[pd.DataFrame]]] = None

    source_path: Optional[PathLike] = None
    file_type: FileType = FileType.UNKNOWN

    added_columns: Dict[str, str] = field(default_factory=dict)
    dropped_columns: List[str] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_lazy(self) -> bool:
        return self.data is None and self.chunk_factory is not None

    @property
    def is_empty(self) -> bool:
        return self.data is None and self.chunk_factory is None

    def store(
            self,
            data: Union[
                pd.DataFrame,
                np.ndarray,
                Dict[str, Sequence[Any]],
                List[Dict[str, Any]],
            ],
            mode: StoreMode = StoreMode.REPLACE,
            columns: Optional[List[str]] = None,
    ) -> None:
        """
        存放数据。

        支持：
        - pandas.DataFrame
        - numpy.ndarray
        - dict
        - list[dict]
        """

        new_df = self._to_dataframe(data, columns=columns)

        if mode == StoreMode.REPLACE or self.data is None:
            self.data = new_df
            self.chunk_factory = None

        elif mode == StoreMode.APPEND_ROWS:
            self.data = pd.concat(
                [self.data, new_df],
                axis=0,
                ignore_index=True,
            )

        elif mode == StoreMode.APPEND_COLUMNS:
            self.data = pd.concat(
                [
                    self.data.reset_index(drop=True),
                    new_df.reset_index(drop=True),
                ],
                axis=1,
            )

        else:
            raise ValueError(f"Unsupported store mode: {mode}")

    def read(
            self,
            columns: ColumnSelector = None,
            rows: RowSelector = None,
            as_numpy: bool = False,
            materialize: bool = True,
    ) -> Union[pd.DataFrame, np.ndarray, Iterator[pd.DataFrame]]:
        """
        读取数据。

        columns:
            读取指定列。

        rows:
            读取指定行。

        as_numpy:
            是否转成 numpy.ndarray。

        materialize:
            懒加载数据是否立刻合并成 DataFrame。
        """

        if self.data is not None:
            result = self._select_dataframe(
                self.data,
                columns=columns,
                rows=rows,
            )
            return result.to_numpy() if as_numpy else result

        if self.chunk_factory is not None:
            if not materialize:
                return self.iter_chunks(columns=columns)

            chunks: List[pd.DataFrame] = []
            global_start = 0

            for chunk in self.iter_chunks(columns=columns):
                selected = self._select_chunk_by_global_rows(
                    chunk=chunk,
                    rows=rows,
                    global_start=global_start,
                )

                if selected is not None and not selected.empty:
                    chunks.append(selected)

                global_start += len(chunk)

            if chunks:
                result = pd.concat(
                    chunks,
                    axis=0,
                    ignore_index=True,
                )
            else:
                result = pd.DataFrame()

            return result.to_numpy() if as_numpy else result

        raise ValueError("当前 TabularData 为空，没有可读取的数据。")

    def iter_chunks(
            self,
            columns: ColumnSelector = None,
    ) -> Iterator[pd.DataFrame]:
        """
        分块读取数据。

        适用于超大文件。
        """

        if self.data is not None:
            yield self._select_dataframe(
                self.data,
                columns=columns,
                rows=None,
            )
            return

        if self.chunk_factory is None:
            raise ValueError("当前数据不是懒加载数据，无法分块读取。")

        for chunk in self.chunk_factory():
            yield self._select_dataframe(
                chunk,
                columns=columns,
                rows=None,
            )

    def view(self) -> DataViewInfo:
        """
        获取当前数据结构视图。

        包括：
        - 当前行数
        - 当前列数
        - 每列名称
        - 每列数据类型
        - 新增列
        - 删除列
        """

        if self.data is not None:
            row_count, column_count = self.data.shape
            columns = [
                ColumnInfo(name=str(col), dtype=str(dtype))
                for col, dtype in self.data.dtypes.items()
            ]

        elif self.chunk_factory is not None:
            row_count = None
            column_count = None
            columns = []

            try:
                first_chunk = next(self.chunk_factory())
                column_count = first_chunk.shape[1]
                columns = [
                    ColumnInfo(name=str(col), dtype=str(dtype))
                    for col, dtype in first_chunk.dtypes.items()
                ]
            except StopIteration:
                pass

        else:
            row_count = 0
            column_count = 0
            columns = []

        added_columns = [
            ColumnInfo(name=name, dtype=dtype)
            for name, dtype in self.added_columns.items()
        ]

        return DataViewInfo(
            row_count=row_count,
            column_count=column_count,
            columns=columns,
            added_columns=added_columns,
            dropped_columns=self.dropped_columns,
            source_path=str(self.source_path)
            if self.source_path is not None
            else None,
            file_type=self.file_type,
            is_lazy=self.is_lazy,
        )

    def preview(self, rows: int = 5) -> pd.DataFrame:
        """
        预览前几行。
        """

        return self.read(rows=slice(0, rows), materialize=True)

    def to_pandas(self) -> pd.DataFrame:
        """
        转 pandas.DataFrame。
        """

        return self.read(materialize=True)

    def to_numpy(self) -> np.ndarray:
        """
        转 numpy.ndarray。
        """

        return self.read(as_numpy=True, materialize=True)

    def register_added_column(self, name: str, dtype: str) -> None:
        """
        记录预处理后新增的列。
        """

        self.added_columns[name] = dtype

    def register_dropped_column(self, name: str) -> None:
        """
        记录预处理后删除的列。
        """

        if name not in self.dropped_columns:
            self.dropped_columns.append(name)

    @staticmethod
    def _to_dataframe(
            data: Union[
                pd.DataFrame,
                np.ndarray,
                Dict[str, Sequence[Any]],
                List[Dict[str, Any]],
            ],
            columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        if isinstance(data, pd.DataFrame):
            return data

        if isinstance(data, np.ndarray):
            return pd.DataFrame(data, columns=columns)

        if isinstance(data, dict):
            return pd.DataFrame(data)

        if isinstance(data, list):
            return pd.DataFrame(data)

        raise TypeError(f"Unsupported data type: {type(data)}")

    @staticmethod
    def _normalize_columns(columns: ColumnSelector) -> Optional[List[str]]:
        if columns is None:
            return None

        if isinstance(columns, str):
            return [columns]

        return list(columns)

    @classmethod
    def _select_dataframe(
            cls,
            df: pd.DataFrame,
            columns: ColumnSelector = None,
            rows: RowSelector = None,
    ) -> pd.DataFrame:
        selected = df

        normalized_columns = cls._normalize_columns(columns)
        if normalized_columns is not None:
            selected = selected.loc[:, normalized_columns]

        if rows is not None:
            if isinstance(rows, int):
                selected = selected.iloc[[rows]]

            elif isinstance(rows, slice):
                selected = selected.iloc[rows]

            elif isinstance(rows, range):
                selected = selected.iloc[list(rows)]

            elif isinstance(rows, (list, tuple)):
                selected = selected.iloc[list(rows)]

            else:
                raise TypeError(f"Unsupported rows selector: {type(rows)}")

        return selected

    @staticmethod
    def _select_chunk_by_global_rows(
            chunk: pd.DataFrame,
            rows: RowSelector,
            global_start: int,
    ) -> Optional[pd.DataFrame]:
        if rows is None:
            return chunk

        chunk_len = len(chunk)
        global_end = global_start + chunk_len

        if isinstance(rows, int):
            if global_start <= rows < global_end:
                local_index = rows - global_start
                return chunk.iloc[[local_index]]

            return None

        if isinstance(rows, slice):
            start = 0 if rows.start is None else rows.start
            stop = global_end if rows.stop is None else rows.stop
            step = 1 if rows.step is None else rows.step

            wanted = range(start, stop, step)

            local_positions = [
                i - global_start
                for i in wanted
                if global_start <= i < global_end
            ]

            if not local_positions:
                return None

            return chunk.iloc[local_positions]

        if isinstance(rows, range):
            local_positions = [
                i - global_start
                for i in rows
                if global_start <= i < global_end
            ]

            if not local_positions:
                return None

            return chunk.iloc[local_positions]

        if isinstance(rows, (list, tuple)):
            local_positions = [
                i - global_start
                for i in rows
                if global_start <= i < global_end
            ]

            if not local_positions:
                return None

            return chunk.iloc[local_positions]

        raise TypeError(f"Unsupported rows selector: {type(rows)}")
