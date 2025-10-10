
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.html import format_html
from django.utils.safestring import mark_safe


class AdminImagePreviewWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        input_html = super().render(name, value, attrs, renderer)
        img_html = ""
        if value and hasattr(value, "url"):
            img_html = format_html(
                '<img src="{}" style="height:64px;width:64px;'
                'object-fit:cover;border-radius:8px;margin-left:8px;'
                'vertical-align:middle;" />',
                value.url,
            )
        return mark_safe(
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'{input_html}{img_html}</div>')
