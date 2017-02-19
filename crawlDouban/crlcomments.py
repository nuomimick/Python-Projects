import requests
from lxml import etree
import re
from base64 import b64decode
import pandas as pd
import asyncio
from functools import partial
from multiprocessing.dummy import Pool


class CrlComments:
    def __init__(self):
        self.loop = asyncio.get_event_loop()

        login_url = 'https://accounts.douban.com/login'
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch, br",
            "Accept-Language": "zh-CN, zh; q=0.8, en; q=0.6",
        }
        #模拟登录
        # data = {'form_email':b64decode(b'MzUwNDc4MDY0QHFxLmNvbQ=='),'form_password':b64decode(b'emhvdTkzMDcyMQ=='),\
        # 'source':'movie','login':'登录','redir':'https://movie.douban.com'}
        # r = self.session.post(login_url,data=data)
        # print(r.status_code,'login successfully!')
        # self.session.cookies.update(r.cookies)

    def get_comments(self, response):
        url = response.url
        html = etree.HTML(response.text)
        divs = html.xpath('//div[@class="comment-item"]')
        if len(divs) > 1:
            for div in divs:
                user_name = div.xpath('.//span[@class="comment-info"]/a/text()')[0]
                user_url = div.xpath('.//span[@class="comment-info"]/a/@href')[0]
                saw = div.xpath('.//span[@class="comment-info"]/child::span[1]/text()')
                saw = saw[0] if saw else None
                rating = div.xpath('.//span[@class="comment-info"]/child::span[2]/@class')
                rating = rating[0] if rating else None
                time = div.xpath('.//span[@class="comment-info"]/span[@class="comment-time "]/text()')[0].strip()
                content = div.xpath('.//p/text()')[0].strip()
                df = pd.DataFrame([(url,user_name,user_url,saw,rating,time,content)],columns=\
                    ['url','user_name','user_url','saw','rating','time','content'])
                df.to_csv('comments.csv',mode='a',index=False,encoding='utf-8',header=False)

    # async def download(self,url,*args,**kwargs):
    #     future = self.loop.run_in_executor(None,partial(self.session.get,url,*args,**kwargs))
    #     response = await future
    #     print(response.status_code,url)
    #     self.get_comments(response)

    def download(self,url,*args,**kwargs):
        response = self.session.get(url,*args,**kwargs)
        print(response.status_code,url)
        self.get_comments(response)

    def download_one(self,url):
        r = self.session.get(url)
        # tasks = [asyncio.ensure_future(self.download(url+\
        #         '?start={}&limit=20&sort=new_score&status=P'.format(i*20))) \
        #         for i in range(10)]
        # self.loop.run_until_complete(asyncio.gather(*tasks))
        urls = [url+'?start={}&limit=20&sort=new_score&status=P'.format(i*20) for i in range(10)]
        pool = Pool(10)
        pool.map(self.download,urls)



    def crawls(self):
        df = pd.read_csv('moviedata.csv')
        urls = df['url'].apply(lambda url:url+'comments')
        pool = Pool(10)
        pool.map(self.download_one,urls)
        
        self.loop.close()

if __name__ == '__main__':
    cc = CrlComments()
    cc.crawls()


