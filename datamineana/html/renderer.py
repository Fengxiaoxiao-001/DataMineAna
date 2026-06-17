from __future__ import annotations

from abc import ABC, abstractmethod

from datamineana.dataobject import TabularData


class BaseHTMLRenderer(ABC):
    """
    HTML 展示抽象类。

    未来可以对接：
    - Flask
    - FastAPI
    - Django
    - Streamlit
    - Vue / React 前端
    """

    @abstractmethod
    def render_view(self, data: TabularData) -> str:
        """
        渲染数据结构视图。
        """

        raise NotImplementedError

    @abstractmethod
    def render_preview(
        self,
        data: TabularData,
        rows: int = 20,
    ) -> str:
        """
        渲染数据预览。
        """

        raise NotImplementedError

    @abstractmethod
    def render_full(
        self,
        data: TabularData,
        rows: int = 20,
    ) -> str:
        """
        渲染完整 HTML 页面。
        """

        raise NotImplementedError


class SimpleHTMLRenderer(BaseHTMLRenderer):
    """
    简单 HTML 渲染实现。

    后续可以换成模板引擎，比如：
    - Jinja2
    - React
    - Vue
    """

    def render_view(self, data: TabularData) -> str:
        info = data.view().to_dict()

        html = []

        html.append("<section>")
        html.append("<h2>数据视图信息</h2>")

        html.append("<ul>")
        html.append(f"<li>行数: {info['row_count']}</li>")
        html.append(f"<li>列数: {info['column_count']}</li>")
        html.append(f"<li>文件路径: {info['source_path']}</li>")
        html.append(f"<li>文件类型: {info['file_type']}</li>")
        html.append(f"<li>是否懒加载: {info['is_lazy']}</li>")
        html.append("</ul>")

        html.append("<h3>当前列</h3>")
        html.append("<table border='1'>")
        html.append("<tr><th>列名</th><th>数据类型</th></tr>")

        for col in info["columns"]:
            html.append(
                f"<tr><td>{col['name']}</td><td>{col['dtype']}</td></tr>"
            )

        html.append("</table>")

        html.append("<h3>预处理新增列</h3>")
        html.append("<table border='1'>")
        html.append("<tr><th>列名</th><th>数据类型</th></tr>")

        for col in info["added_columns"]:
            html.append(
                f"<tr><td>{col['name']}</td><td>{col['dtype']}</td></tr>"
            )

        html.append("</table>")

        html.append("<h3>预处理删除列</h3>")
        html.append("<ul>")

        for col in info["dropped_columns"]:
            html.append(f"<li>{col}</li>")

        html.append("</ul>")
        html.append("</section>")

        return "\n".join(html)

    def render_preview(
        self,
        data: TabularData,
        rows: int = 20,
    ) -> str:
        preview_df = data.preview(rows=rows)
        return preview_df.to_html(index=False, border=1)

    def render_full(
        self,
        data: TabularData,
        rows: int = 20,
    ) -> str:
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>数据展示</title>
</head>
<body>
    <h1>数据展示页面</h1>

    {self.render_view(data)}

    <h2>数据预览</h2>

    {self.render_preview(data, rows=rows)}
</body>
</html>
"""