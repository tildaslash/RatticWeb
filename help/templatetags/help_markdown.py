from django import template
import markdown

register = template.Library()

@register.simple_tag
def markdown_file(filename):
    with open(filename) as f:
        out = markdown.markdown(
                text=f.read(),
                extensions=[
                    'fenced_code',
                    'nl2br',
                    'wikilinks(base_url=/help/)'
                    ],
                safe_mode='escape',
                )

    return out

