from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import pandas as pd

from datamineana.dataobject import TabularData
from datamineana.dataobject import PathLike, SaveMode
from datamineana.savers.base import BaseDataSaver


class PandasDataSaver(BaseDataSaver):
    """
    基于 pandas 的文件保存实现。

    支持：
    - csv
    - xlsx
    - xls

    不实现数据库保存。
    """

    def save(
        self,
        data: TabularData,
        path: Optional[PathLike] = None,
        mode: SaveMode = SaveMode.NEW_FILE,
        **kwargs: Any,
    ) -> Path:
        if mode == SaveMode.DATABASE:
            raise NotImplementedError(
                "数据库保存请使用 BaseDatabaseSaver 的子类实现。"
            )

        if mode == SaveMode.MODIFY_ORIGINAL:
            if data.source_path is None:
                raise ValueError("MODIFY_ORIGINAL 模式需要 data.source_path。")

            save_path = Path(data.source_path)

        elif mode in {SaveMode.NEW_FILE, SaveMode.PATCH_FILE}:
            if path is None:
                raise ValueError(f"{mode.value} 模式需要指定 path。")

            save_path = Path(path)

        else:
            raise ValueError(f"Unsupported save mode: {mode}")

        df = data.to_pandas()

        self._save_dataframe(
            df=df,
            path=save_path,
            **kwargs,
        )

        return save_path

    def _save_dataframe(
        self,
        df: pd.DataFrame,
        path: PathLike,
        **kwargs: Any,
    ) -> None:
        path = Path(path)
        suffix = path.suffix.lower()

        if suffix == ".csv":
            df.to_csv(
                path,
                index=False,
                **kwargs,
            )

        elif suffix == ".xlsx":
            df.to_excel(
                path,
                index=False,
                engine="openpyxl",
                **kwargs,
            )

        elif suffix == ".xls":
            df.to_excel(
                path,
                index=False,
                **kwargs,
            )

        else:
            raise ValueError(f"不支持的保存文件类型: {suffix}")