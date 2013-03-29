from django import template
import markdown

register = template.Library()

@register.simple_tag
def markdown_file(filename):
    with open(filename) as f:
        out = markdown.markdown(f.read())

    return out

