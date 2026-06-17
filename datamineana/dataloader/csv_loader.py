from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, Optional

import pandas as pd

from datamineana.dataobject import TabularData
from datamineana.dataobject import ColumnSelector, FileType, PathLike, RowSelector
from datamineana.dataloader.base import BaseDataLoader


class CSVLoader(BaseDataLoader):
    """
    CSV 文件读取类。
    """

    file_type = FileType.CSV

    def load(
        self,
        path: PathLike,
        columns: ColumnSelector = None,
        rows: RowSelector = None,
        dtype: Optional[Dict[str, Any]] = None,
        lazy: bool = False,
        chunksize: Optional[int] = None,
        encoding: Optional[str] = None,
        **kwargs: Any,
    ) -> TabularData:
        path = Path(path)

        usecols = TabularData._normalize_columns(columns)

        if lazy:
            if chunksize is None:
                chunksize = 10000

            def factory() -> Iterator[pd.DataFrame]:
                return pd.read_csv(
                    path,
                    usecols=usecols,
                    dtype=dtype,
                    encoding=encoding,
                    chunksize=chunksize,
                    **kwargs,
                )

            return TabularData(
                data=None,
                chunk_factory=factory,
                source_path=path,
                file_type=self.file_type,
            )

        df = pd.read_csv(
            path,
            usecols=usecols,
            dtype=dtype,
            encoding=encoding,
            **kwargs,
        )

        if rows is not None:
            df = TabularData._select_dataframe(df, rows=rows)

        return TabularData(
            data=df,
            source_path=path,
            file_type=self.file_type,
        )