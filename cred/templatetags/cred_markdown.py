from django import template
import markdown

register = template.Library()


@register.simple_tag
def markdown_cred(description):
    out = markdown.markdown(
        text=description,
        extensions=[
            'fenced_code',
            'nl2br',
        ],
        safe_mode='escape',
    )

    return out
