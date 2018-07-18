# 使用selenium爬取淘宝商品
import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By       # 这几行不用死记硬背，直接搜selenium官方文档复制粘贴
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from urllib.parse import quote
from pyquery import PyQuery as pq
import pymongo


MONGO_URL = 'localhost'  # 连接MONGODB标准写法
MONGO_DB = 'taobao'      # 数据库名称
MONGO_TABLE = 'product'  # 表
client = pymongo.MongoClient()  # 创建一个对象
db = client[MONGO_DB]           # 传入数据库

# browser = webdriver.Chrome()  # 如果要弹出chrome，用该行
chrome_options = webdriver.ChromeOptions()   # 不弹出chrome,用下面三行
chrome_options.add_argument('--headless')    # 但是爬取方法里加上print输出提示“正在爬取”
browser = webdriver.Chrome(chrome_options=chrome_options)

wait = WebDriverWait(browser, 10)
# KEYWORD = '火影忍者'


def search():  # 步骤一，获取商品列表
    '''
    抓取索引页
    :param page: 页码
    '''
    # print('正在搜索')
    try:
        # url = 'https://s.taobao.com/search?q=' + quote(KEYWORD)
        url = 'https://www.taobao.com'
        browser.get(url)
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q')))
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button')))
        input.clear()
        input.send_keys('火影忍者')
        submit.click()
        total = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total')))
        get_products()  # 在第一页刷出来之后就开始调用产品解析方法
        return total.text
    except TimeoutException:
        return search()


def next_page(page_number): # 步骤二，翻页
    # print('正在翻页:')
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input')))
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'),
            str(page_number)) # 传入当前要判断的页码数
        )
        get_products()  # 翻页也是要等到页面加载完毕之后再解析网页
    except TimeoutException:
        return next_page(page_number)  # 如果出错则递归继续调用，单页出错不影响下一步


def get_products():  # 步骤三，解析产品
    # print('正在解析:')
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
    html = browser.page_source  # 获取网页源代码
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()  # items()可以得到所有的item
    for item in items:
        product = {
            'image': item.find('.pic .img').attr('src'),  # 注意选取两层css的class名
            'price': item.find('.price').text(),
            'deal': item.find('.deal-cnt').text()[:-3],  # [:-3]为去掉后三个字
            'title': item.find('.title').text(),   # 如果源网页前端代码里没有其他多余文字信息，可以用text直接获取
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text(),
        }
        print(product)
        save_to_mongo(product)


def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('存储到MONGODB成功', result)
    except Exception:
        print('存储到MONGODB失败', result)


def main():
    try:
        total = search()  # search方法本身带有return，所以此处用递归
        total = int(re.compile('(\d+)').search(total).group(1))  # 正则表达式提取出数字，即100页，也可直接定义一个
        for i in range(2, total - 89):                            # MAX_SIZE为100页, 这里只要10页
            next_page(i)
    except Exception:
        print('出错')
    finally:             # 无论是否出现异常，最终仍要关闭网页
        browser.close()
        
if __name__ == '__main__':
    main()
