import pymongo
import pandas as pd
import numpy as np
from pyecharts import Bar, Pie

client = pymongo.MongoClient('localhost', 27017)
db = client.maoyan
table = db.movies
print('connect mongodb successfully')

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
df = pd.DataFrame(list(table.find()))

# 默认已经是按评分从高到低
top10_movie_name = np.array(df.head(10)['name'])
top10_movie_score = np.array(df.head(10)['score'])
bar = Bar("2018猫眼电影评分排行TOP10", title_pos='center', title_top=18, width=1200, height=500)
bar.add("电影名称", top10_movie_name, top10_movie_score, is_convert=True, is_label_show=True,
        label_pos='right', xaxis_label_textsize=5, yaxis_label_textsize=15, is_legend_show=False)
bar.render("2018猫眼电影评分排行TOP10.html")

# 按票房排序
top10_movie_name = np.array(df.sort_values(by='booking_office', ascending=False).head(10)['name'])
top10_movie_booking_office = np.array(df.sort_values(by='booking_office', ascending=False).head(10)['booking_office'])
# print(top10_movie_name, top10_movie_booking_office)
bar = Bar("2018猫眼电影票房排行TOP10(单位：元)", title_pos='center', title_top=18, width=1500, height=500)
bar.add("电影名称", top10_movie_name, top10_movie_booking_office, is_convert=False, is_label_show=True,
        label_pos='top', xaxis_label_textsize=30, yaxis_label_textsize=15, is_legend_show=False)
bar.render("2018猫眼电影票房排行TOP10.html")


movie_country = list(df['country'])
country_value = [0, 0, 0, 0]
for country in movie_country:
        if'中国大陆' in country:
                country_value[0] += 1
        if '中国香港' in country:
                country_value[1] += 1
        if '美国' in country:
                country_value[2] += 1
country_value[3] = len(movie_country)-country_value[0]-country_value[1]-country_value[2]

pie = Pie("2018猫眼电影产地状况饼状图", background_color='white', title_text_size=25, title_pos='center')
attr = ['中国大陆', '中国香港', '美国', '其他']
pie.add("地区", attr, country_value, is_label_show=True, is_legend_show=False)
pie.render("2018猫眼电影产地状况饼状图.html")
