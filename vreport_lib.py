import warnings
import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from matplotlib.dates import date2num, WeekdayLocator, DayLocator, DateFormatter, MONDAY
import matplotlib.ticker as ticker
from matplotlib.ticker import FuncFormatter
from matplotlib import colors
import matplotlib.patches as patches
from cycler import cycler
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import seaborn as sns
from IPython.display import display
import datetime
from datetime import timedelta
from wordcloud import WordCloud
from collections import OrderedDict

from fetch_data_odps import run_sql, pt

%config InlineBackend.figure_format = 'svg'
%matplotlib inline

warnings.filterwarnings('ignore')
matplotlib.rcParams['font.family'] = 'SimSun'
clrs = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
       '#800000', '#f032e6', '#fabebe', '#008080', '#e6beff', '#fffac8', '#ffe119', '#aaffc3', '#808000', '#ffd8b1',
       '#000080', '#808080']
plt.rc('axes', prop_cycle=(cycler('color', clrs)))

UP_COLOR = '#C45C54'
DOWN_COLOR = '#79AA8F'
WC_DPI = 360

def str2date(s):
    return datetime.datetime.strptime(s, '%Y-%m-%d')

def background_gradient(s, m, M, cmap='Oranges', low=0, high=0):
    rng = M - m
    norm = colors.Normalize(m - (rng * low),
                            M + (rng * high))
    normed = norm(s.values)
    c = [colors.rgb2hex(x) for x in plt.cm.get_cmap(cmap)(normed)]
    return ['background-color: %s' % color for color in c]

def percent(x, digits=1, sign_labels=['', '', '-']):
    if x == 0:
        sign_label = sign_labels[0]
    elif x > 0:
        sign_label = sign_labels[1]
    else:
        sign_label = sign_labels[2]
    return '{}{}%'.format(sign_label, round(abs(x) * 100, digits))

def percent_ticks(x, pos):
    return percent(x)

def word_cloud_show(df):
    wc = WordCloud(width=3000, height=1500, margin=0, font_path='~/Library/Fonts/SimSun.ttf')
    wc.generate_from_frequencies({a: b for _, a, b in df.itertuples()})
    plt.figure(figsize=(10,5), facecolor='k', dpi=WC_DPI)
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.margins(x=0, y=0)
    plt.tight_layout(pad=0)
    plt.show()

def dict2excel(data_dict, filename):
    with pd.ExcelWriter(filename, engine='xlsxwriter', options={'strings_to_urls': False}) as writer:
        for df_name, df in data_dict.items():
            df.to_excel(writer, sheet_name=df_name, index=False)

def write_pt(pt):
    with open('current.pt', 'w') as f:
        f.write(pt)