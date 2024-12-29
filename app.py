import streamlit as st
import urllib.request, urllib.error  # 制定URL，获取网页数据
from bs4 import BeautifulSoup  # 网页解析，获取数据
import re
import jieba
from collections import Counter
import string
from pyecharts.charts import WordCloud, Bar, Line, Pie, Scatter, Radar, TreeMap
from pyecharts import options as opts
from pyecharts.globals import SymbolType
from streamlit.components.v1 import html

# 初始化 session_state
if 'url' not in st.session_state:
    st.session_state.url = ''
if 'data' not in st.session_state:
    st.session_state.data = None
if 'chart_type' not in st.session_state:
    st.session_state.chart_type = 'WordCloud'


# 爬取网页并获取body内容
def getData(baseurl):
    html = askURL(baseurl)  # 保存获取到的网页源码
    soup = BeautifulSoup(html, "html.parser")
    item = soup.find('body')  # 查找符合要求的字符串
    return item.prettify()


# 得到指定一个URL的网页内容
def askURL(url):
    head = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36"
    }
    request = urllib.request.Request(url, headers=head)
    html = ""
    try:
        response = urllib.request.urlopen(request)
        html = response.read().decode("utf-8")
    except urllib.error.URLError as e:
        if hasattr(e, "code"):
            print(e.code)
        if hasattr(e, "reason"):
            print(e.reason)
    return html


# 清洗文本并统计词频
def remv(text):
    clean = re.compile('<.*?>')
    temp = re.sub(clean, '', text)
    # 移除所有空白字符（包括空格、制表符、换行符等）
    temp = re.sub(r'\s+', '', temp)  # \s 匹配任何空白字符，+ 表示匹配一个或多个
    punctuations = set(string.punctuation)  # 英文标点符号
    chinese_punctuations = set('！？｡。＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟📐｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏.')
    all_punctuations = punctuations.union(chinese_punctuations)
    middle = ''.join([char for char in temp if char not in all_punctuations])
    words = jieba.lcut(middle)
    word_counts = Counter(words)
    word_counts = Counter({word: count for word, count in word_counts.items() if len(word) > 1})
    top_20 = word_counts.most_common(20)
    return top_20


# 创建词云图
def create_wordcloud(data):
    wordcloud = WordCloud()
    wordcloud.add("", data, word_size_range=[20, 100], shape=SymbolType.DIAMOND)
    return wordcloud


# 创建其他图表类型
def create_chart(chart_type, data):
    if chart_type == 'Bar':
        chart = Bar()
        chart.add_xaxis([item[0] for item in data])
        chart.add_yaxis("频率", [item[1] for item in data])
    elif chart_type == 'Line':
        chart = Line()
        chart.add_xaxis([item[0] for item in data])
        chart.add_yaxis("频率", [item[1] for item in data])
    elif chart_type == 'Pie':
        chart = Pie()
        chart.add("", data)
    elif chart_type == 'Scatter':
        chart = Scatter()
        chart.add_xaxis([item[0] for item in data])
        chart.add_yaxis("频率", [item[1] for item in data])
    elif chart_type == 'Radar':
        chart = Radar()
        schema = [{"name": item[0], "max": max([d[1] for d in data])} for item in data]
        chart.add_schema(schema)
        chart.add("频率", [[item[1] for item in data]])
    elif chart_type == 'Treemap':
        chart = TreeMap()
        # 构造适合 Treemap 的数据结构
        treemap_data = [
            {"name": item[0], "value": item[1]} for item in data
        ]
        chart.add(
            series_name="频率",
            data=treemap_data,
            label_opts=opts.LabelOpts(is_show=True),  # 直接在这里设置标签选项
        )
        chart.set_global_opts(title_opts=opts.TitleOpts(title="Treemap 图"))
    else:
        raise ValueError("Unsupported chart type")

    chart.set_global_opts(title_opts=opts.TitleOpts(title=f"{chart_type} 图"))
    return chart


# 渲染 pyecharts 图表
def render_pyecharts(chart):
    chart_html = chart.render_embed()
    components_html = f"""
    <html>
        <head><script src="https://cdn.jsdelivr.net/npm/echarts@latest/dist/echarts.min.js"></script></head>
        <body>
            {chart_html}
        </body>
    </html>
    """
    html(components_html, width=800, height=600)


# Streamlit 应用程序
st.title("网页内容分析与可视化")

# 用户输入
url = st.text_input('请输入文章的URL:', value=st.session_state.url, key='url_input')
submit_button = st.button('提交')

# 当用户提交新URL时，更新 session_state 并获取新数据
if submit_button and url != st.session_state.url:
    st.session_state.url = url
    with st.spinner('正在爬取和处理数据...'):
        text = getData(url)
        st.session_state.data = remv(text)

# 如果有数据，根据用户选择的图表类型显示图表
if st.session_state.data:
    selected_chart = st.sidebar.selectbox('选择图表类型',
                                          ['词云', '柱状图', '折线图', '饼图', '散点图', '雷达图', '树状图'],
                                          key='chart_select')  # 更新图表选项
    st.session_state.chart_type = selected_chart

    # 将中文选项映射回原始的英文选项
    chart_type_mapping = {
        '词云': 'WordCloud',
        '柱状图': 'Bar',
        '折线图': 'Line',
        '饼图': 'Pie',
        '散点图': 'Scatter',
        '雷达图': 'Radar',
        '树状图': 'Treemap'
    }

    if selected_chart == '词云':
        wc = create_wordcloud(st.session_state.data)
        render_pyecharts(wc)
    else:
        chart = create_chart(chart_type_mapping[selected_chart], st.session_state.data)
        render_pyecharts(chart)
else:
    st.write("请提供一个有效的URL并点击提交以开始分析。")