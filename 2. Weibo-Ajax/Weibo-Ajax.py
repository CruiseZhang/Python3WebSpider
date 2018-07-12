# 爬取微博——熟悉Ajax数据爬取


from urllib.parse import urlencode
from pyquery import PyQuery as pq
from pymongo import MongoClient
import requests

base_url = 'https://m.weibo.cn/api/container/getIndex?'
headers = {
    'Host': 'm.weibo.cn',
    'Referer': 'https://m.weibo.cn/u/3910838102',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
}
client = MongoClient()
db = client['weibo']        # 指定数据库——weibo
collection = db['weibo']    # 指定集合——声明一个collection对象
max_page = 10


def get_page(page):   # 步骤一，获取每次请求的结果
    params = {         # 参数字典
        'type': 'uid',
        'value': '3910838102',
        'containerid': '1076033910838102',  # 这里很关键，几次出错，应该用第二个Ajax请求的值，1076开头那个
        'page': page    # 这四个参数只有page对应微博第几页，是变化的，其他都是不变的
    }
    url = base_url + urlencode(params)  #  urlencode将参数转化为URL的GET请求参数
    try:
        response = requests.get(url, headers=headers)  # 利用requests获得get请求，返回请求头、URL、IP等信息
        if response.status_code == 200:
            return response.json(), page              # 调用json方法，将返回结果是JSON格式的字符串转化为字典
    except requests.ConnectionError as e:
        print('Error', e.args)


def parse_page(json, page: int):  # 步骤2，定义一个解析方法
    if json:
        items = json.get('data').get('cards')
        for index, item in enumerate(items):
            if page == 1 and index == 1:
                continue
            else:
                item = item.get('mblog')
                weibo = {}                     # 赋值为一个新的字典
                weibo['微博id'] = item.get('id')
                weibo['正文'] = pq(item.get('text')).text()
                weibo['点赞数'] = item.get('attitudes_count')
                weibo['评论数'] = item.get('comments_count')
                weibo['转发数'] = item.get('reposts_count')
                yield weibo


def save_to_mongo(result):
    if collection.insert(result):
        print('Save to Mongo')


def save_to_txt(content):
    with open('MyWeibo.txt', 'a', encoding='utf-8') as f:
        f.write(str(content) + '\n')
        print('Save to txt')

if __name__ == '__main__':
    for page in range(1, 10):
        json = get_page(page)
        results = parse_page(*json)  # 用了*可以不用再写page
        for result in results:
            print(result)
            save_to_mongo(result)
            save_to_txt(result)
