import re

def default_style(s):
    return ['' for _ in s]

def highlight_unequal(s):
    return ['background-color: red' if re.search('%$', str(v)) and not re.search('^100.00%$', str(v)) else '' for v in s]

STYLE_FUNC_MAP = {
    'highlight_unequal': highlight_unequal,
    'default_style': default_style
}
