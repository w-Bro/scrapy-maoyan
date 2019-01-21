import requests
from bs4 import BeautifulSoup
import pymongo
from fontTools.ttLib import TTFont
import re

# 连接数据库
client = pymongo.MongoClient(host='localhost', port=27017)
db = client.maoyan
collection = db.movies
print('connect mongodb successfully')


# 访问页面
def get_page(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text


# 获得每个电源详细页链接
def get_film_url(html):
    soup = BeautifulSoup(html, 'html.parser')
    film_href = soup.find_all(class_='channel-detail movie-item-title')
    film_url = []
    for href in film_href:
        film_url.append('https://maoyan.com' + href.select('a')[0]['href'])
    return film_url


def to_mongodb(data):
    # 存储数据
    try:
        collection.insert(data)
        print('Insert data Successfully')
    except:
        print('Insert Data Failed')


def get_numbers(u):
    """
    对猫眼的文字反爬进行破解
    """
    cmp = re.compile(",\n           url\('(//.*.woff)'\) format\('woff'\)")
    rst = cmp.findall(u)
    ttf = requests.get("http:" + rst[0], stream=True)
    with open("maoyan.woff", "wb") as pdf:
        for chunk in ttf.iter_content(chunk_size=1024):
            if chunk:
                pdf.write(chunk)
    base_font = TTFont('base.woff')
    maoyan_font = TTFont('maoyan.woff')
    maoyan_unicode_list = maoyan_font['cmap'].tables[0].ttFont.getGlyphOrder()
    maoyan_num_list = []
    base_num_list = ['.', '5', '1', '8', '7', '0', '4', '9', '2', '6', '3']
    base_unicode_list = ['x', 'uniF294', 'uniEEC3', 'uniE393', 'uniF800', 'uniE676', 'uniF194', 'uniE285', 'uniF1BD',
                         'uniEB09', 'uniE8E8']
    for i in range(1, 12):
        maoyan_glyph = maoyan_font['glyf'][maoyan_unicode_list[i]]
        for j in range(11):
            base_glyph = base_font['glyf'][base_unicode_list[j]]
            if maoyan_glyph == base_glyph:
                maoyan_num_list.append(base_num_list[j])
                break
    maoyan_unicode_list[1] = 'uni0078'
    utf8List = [eval(r"'\u" + uni[3:] + "'").encode("utf-8") for uni in maoyan_unicode_list[1:]]
    utf8last = []
    for i in range(len(utf8List)):
        utf8List[i] = str(utf8List[i], encoding='utf-8')
        utf8last.append(utf8List[i])
    return maoyan_num_list, utf8last


# 解析电源详细页面，获得影片名称，票房等
def get_data(film_url, headers):
    for url in film_url:
        data = {}
        response = get_page(url, headers)
        soup = BeautifulSoup(response, 'html.parser')
        data['_id'] = url[len('https://maoyan.com/films/'):]
        data["name"] = soup.find_all('h3', class_='name')[0].get_text()
        data["type"] = soup.find_all('li', class_='ellipsis')[0].get_text()
        data["country"] = soup.find_all('li', class_='ellipsis')[1].get_text().split('/')[0].strip()
        data['time'] = soup.find_all('li', class_='ellipsis')[1].get_text().split('/')[1].strip()

        # 获取被编码的数字
        score_code = soup.find_all('span', class_='stonefont')[0].get_text().strip().encode('utf-8')
        data['score'] = str(score_code, encoding='utf-8')
        score_num_code = soup.find_all('span', class_='stonefont')[1].get_text().strip().encode('utf-8')
        data['score_num'] = str(score_num_code, encoding='utf-8')
        booking_office_code = soup.find_all('span', class_='stonefont')[2].get_text().strip().encode('utf-8')
        data['booking_office'] = str(booking_office_code, encoding='utf-8')

        # 票房单位
        unit = soup.find_all('span', class_='unit')[0].get_text().strip()

        # 破解
        maoyan_num_list, utf8last = get_numbers(response)
        # print(maoyan_num_list, utf8last)

        # 进行替换得到正确的结果
        for i in range(len(utf8last)):
            data['score'] = data['score'].replace(utf8last[i], maoyan_num_list[i])
            data['score_num'] = data['score_num'].replace(utf8last[i], maoyan_num_list[i])
            data['booking_office'] = data['booking_office'].replace(utf8last[i], maoyan_num_list[i])

        # 对单位进行换算
        if '万' in data['score_num']:
            data['score_num'] = int(float(data['score_num'][:len(data['score_num'])-1]) * 10000)
        if '万' == unit:
            data['booking_office'] = int(float(data['booking_office']) * 10000)
        elif '亿' == unit:
            data['booking_office'] = int(float(data['booking_office']) * 100000000)
        # print(data)
        to_mongodb(data)


def main():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/71.0.3578.98 Safari/537.36'}
    for offset in range(0, 120, 30):
        url = 'https://maoyan.com/films?showType=3&yearId=13&sortId=3&offset={}'.format(offset)
        response_html = get_page(url, headers)
        film_url = get_film_url(response_html)
        get_data(film_url, headers)


if __name__ == '__main__':
    main()
