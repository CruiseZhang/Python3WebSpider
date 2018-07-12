# 抓取猫眼电影排名前100部


import requests  # 抓取要用
import re        # 正则解析
import json      # 提取的结果写入文件要用
import time      # 延时等待，针对网页的反爬虫
from requests.exceptions import RequestException  # 以防万一请求失败


# 1.1 抓取第一页代码
def get_one_page(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) '
                          + 'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
        }
        response = requests.get(url, headers=headers)  # 获取HTTP请求
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        return None


# 1.2. 主函数里传入URL和offset参数，后者可以获取剩下页面
def main(offset):
    url = 'http://maoyan.com/board/4?offset=' + str(offset)
    html = get_one_page(url)
    for item in parse_one_page(html):
        print(item)
        write_to_file(item)


# 2. 解析获取代码，正则表提取7个关键信息
def parse_one_page(html):
    pattern = re.compile( '<dd>.*?board-index.*?>(\d+)</i>.*?data-src="(.*?)".*?name"><a'
        + '.*?>(.*?)</a>.*?star">(.*?)</p>.*?releasetime">(.*?)</p>'
        + '.*?integer">(.*?)</i>.*?fraction">(.*?)</i>.*?</dd>', re.S)  # 正则字符串编译成正则表达式对象，便于后面匹配复用
    items = re.findall(pattern, html)
    for item in items:
        yield {
            'index': item[0],
            'image': item[1],
            'title': item[2].strip(),
            'actor': item[3].strip()[3:],
            'time':  item[4].strip()[5:],
            'score': item[5].strip() + item[6].strip()
        }


# 3 提取的结果写入文件
def write_to_file(content):
    with open('result.txt', 'a', encoding='utf-8') as f:  # 写入文件
        f.write(json.dumps(content, ensure_ascii=False) + '\n')  # dumps对数据进行编码，false保证是Unicode编码
                                                                   # 有中文时候使用

if __name__ == '__main__':
    for i in range(10):
        main(offset=i * 10)
        time.sleep(1)   # 延时等待，防止反爬虫
