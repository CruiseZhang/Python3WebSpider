# 爬取头条新闻搜索结果——再次熟悉Ajax请求

import requests
from urllib.parse import urlencode
import os
from hashlib import md5  # hashlib是涉及安全散列和消息摘要，提供多个不同的加密算法接口，如SHA1、SHA224、SHA256、SHA384、SHA512、MD5等。
from multiprocessing.pool import Pool


GROUP_START = 1
GROUP_END = 5


def get_page(offset):  # 步骤一，获取单个Ajax请求
    params = {
        'offset': offset,
        'format': 'json',
        'keyword': '火影忍者',
        'autoload': 'true',
        'count': 20,
        'cur_tab': 1,  # 实际网页端的request url并没有结束，所以保留一个逗号
        'from': 'gallery',
    }
    url = 'https://www.toutiao.com/search_content/?' + urlencode(params)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()   # json()将结果
    except requests.ConnectionError:   # 和爬取微博那个作业不同的意外捕捉方式
        return None
    # except requests.ConnectionError as e:
    #     print('Error', e.args)


def get_images(json):  # 步骤一，提取每条数据的image_detail字段中的每一张图片链接，将图片链接和图片所属的标题一并返回
    data = json.get('data')
    if data:
        for item in data:
            image_list = item.get('image_list')  # 和书上image_detail冲突，因为源网页已没有该字段
            title = item.get('title')
            if image_list:
                for image in image_list:
                    yield {
                        'image': image.get('url'),
                        'title': title
                    }


def save_image(item):  # 步骤二，保存图片
    if not os.path.exists(item.get('title')):
        os.mkdir(item.get('title'))       # mkdir创建一个目录
    try:
        local_image_url = item.get('image')
        new_image_url = local_image_url.replace('list', 'large')
        response = requests.get('http:' + new_image_url)
        if response.status_code == 200:
                                    # hash.hexdigest() 返回摘要，作为十六进制数据字符串值
            file_path = '{0}/{1}.{2}'.format(item.get('title'), md5(response.content).hexdigest(), 'jpg')
                                    # 012那里依次代表文件夹名，文件名，文件后缀
            if not os.path.exists(file_path):
                with open(file_path, 'wb') as f:
                    f.write(response.content)
            else:
                print('Already Downloaded', file_path)
    except requests.ConnectionError:
        print('Failed to Save Image')


def main(offset):
    json = get_page(offset)
    for item in get_images(json):
        print(item)
        save_image(item)

if __name__ == '__main__':
    pool = Pool()
    groups = ([x * 20 for x in range(GROUP_START, GROUP_END + 1)])
    pool.map(main, groups)  # 实现多线程下载,pool类的map方法和以前的map用法一样，使进程阻塞直到结果返回
    pool.close()            # 关闭进程池（pool），使其不再接受新的任务。
    pool.join()             # 主进程阻塞等待子进程的退出， join方法要在close或terminate之后使用
