import re

def default_style(s):
    return ['' for _ in s]

def highlight_unequal(s):
    return ['background-color: red' if re.search('%$', str(v)) and not re.search('^100.00%$', str(v)) else '' for v in s]

def highlight_rank(s, css='color: red', ascending=True, size=1):

    if isinstance(size, float) and size >= 0 and size <= 1:
        size = int(round(s.size * size))

    hilight_s = s.isin(s.sort_values(ascending=ascending)[:size])

    return [css if v else '' for v in hilight_s]
