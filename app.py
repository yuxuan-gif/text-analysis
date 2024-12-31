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
import matplotlib.pyplot as plt
from io import BytesIO
import altair as alt
import pandas as pd
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用黑体显示中文
plt.rcParams['axes.unicode_minus'] = False    # 正常显示负号

# 初始化 session_state
if 'url' not in st.session_state:
    st.session_state.url = ''
if 'data' not in st.session_state:
    st.session_state.data = None
if 'chart_type' not in st.session_state:
    st.session_state.chart_type = 'WordCloud'
if 'chart_library' not in st.session_state:
    st.session_state.chart_library = 'Pyecharts'

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
def create_chart(chart_type, chart_library, data):
    df = pd.DataFrame(data, columns=['word', 'frequency'])

    # 检查是否选择了不支持的图表类型
    if chart_library != 'Pyecharts' and chart_type in ['Radar', 'Treemap']:
        st.warning(f"{chart_library} 不支持 {chart_type} 图，将自动使用 Pyecharts 生成该图表。")
        chart_library = 'Pyecharts'

    if chart_library == 'Matplotlib':
        fig, ax = plt.subplots(figsize=(10, 6))
        if chart_type == 'Bar':
            df.plot(kind='bar', x='word', y='frequency', ax=ax, legend=False)
            ax.set_xlabel('词语')
            ax.set_ylabel('频率')
            ax.set_title('柱状图')
        elif chart_type == 'Line':
            df.plot(kind='line', x='word', y='frequency', ax=ax, legend=False)
            ax.set_xlabel('词语')
            ax.set_ylabel('频率')
            ax.set_title('折线图')
        elif chart_type == 'Pie':
            df.plot(kind='pie', y='frequency', labels=df['word'], ax=ax, autopct='%1.1f%%')
            ax.set_title('饼图')
        elif chart_type == 'Scatter':
            df.plot(kind='scatter', x='word', y='frequency', ax=ax)
            ax.set_xlabel('词语')
            ax.set_ylabel('频率')
            ax.set_title('散点图')
        else:
            raise ValueError("Unsupported chart type for Matplotlib")

        buf = BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        return chart_library,buf

    elif chart_library == 'Altair':
        if chart_type == 'Bar':
            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X('word:N', title='词语'),
                y=alt.Y('frequency:Q', title='频率'),
                tooltip=['word', 'frequency']
            ).properties(title="柱状图")
        elif chart_type == 'Line':
            chart = alt.Chart(df).mark_line().encode(
                x=alt.X('word:N', title='词语'),
                y=alt.Y('frequency:Q', title='频率'),
                tooltip=['word', 'frequency']
            ).properties(title="折线图")
        elif chart_type == 'Pie':
            chart = alt.Chart(df).mark_arc().encode(
                theta=alt.Theta(field="frequency", type="quantitative"),
                color=alt.Color(field="word", type="nominal"),
                tooltip=['word', 'frequency']
            ).properties(title="饼图")
        elif chart_type == 'Scatter':
            chart = alt.Chart(df).mark_point().encode(
                x=alt.X('word:N', title='词语'),
                y=alt.Y('frequency:Q', title='频率'),
                tooltip=['word', 'frequency']
            ).properties(title="散点图")
        else:
            raise ValueError("Unsupported chart type for Altair")

        return chart_library,chart

    elif chart_library == 'Pyecharts':
        if chart_type == 'Bar':
            chart = Bar()
            chart.add_xaxis(df['word'].tolist())
            chart.add_yaxis("频率", df['frequency'].tolist())
        elif chart_type == 'Line':
            chart = Line()
            chart.add_xaxis(df['word'].tolist())
            chart.add_yaxis("频率", df['frequency'].tolist())
        elif chart_type == 'Pie':
            chart = Pie()
            chart.add("", [list(z) for z in zip(df['word'], df['frequency'])])
        elif chart_type == 'Scatter':
            chart = Scatter()
            chart.add_xaxis(df['word'].tolist())
            chart.add_yaxis("频率", df['frequency'].tolist())
        elif chart_type == 'Radar':
            chart = Radar()
            schema = [{"name": item[0], "max": max([d[1] for d in data])} for item in data]
            chart.add_schema(schema)
            chart.add("频率", [[item[1] for item in data]])
        elif chart_type == 'Treemap':
            chart = TreeMap()
            treemap_data = [
                {"name": word, "value": freq} for word, freq in zip(df['word'], df['frequency'])
            ]
            chart.add(
                series_name="频率",
                data=treemap_data,
                label_opts=opts.LabelOpts(is_show=True),  # 直接在这里设置标签选项
            )
            chart.set_global_opts(title_opts=opts.TitleOpts(title="树状图"))
        else:
            raise ValueError("Unsupported chart type for Pyecharts")

        chart.set_global_opts(title_opts=opts.TitleOpts(title=f"{chart_type} 图"))
        return chart_library,chart
    else:
        raise ValueError("Unsupported chart library")

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

# 渲染 matplotlib 图表
def render_matplotlib(fig_buffer):
    st.image(fig_buffer)

# 渲染 altair 图表
def render_altair(chart):
    st.altair_chart(chart, use_container_width=True)

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
    selected_library = st.sidebar.selectbox('选择图表库',
                                            ['Pyecharts', 'Matplotlib', 'Altair'],
                                            key='library_select')  # 添加图表库选项
    st.session_state.chart_type = selected_chart
    st.session_state.chart_library = selected_library

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
        selected_library,chart = create_chart(chart_type_mapping[selected_chart], selected_library, st.session_state.data)
        if selected_library == 'Matplotlib':
            render_matplotlib(chart)
        elif selected_library == 'Altair':
            render_altair(chart)
        else:
            render_pyecharts(chart)
else:
    st.write("请提供一个有效的URL并点击提交以开始分析。")