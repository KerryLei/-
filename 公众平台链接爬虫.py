#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 18 21:22:35 2022

@author: 1d_lyx
"""
import time
import random
import traceback
import requests
import pandas as pd
from selenium import webdriver
import re
from datetime import datetime, timedelta

class Spider(object): 
    
    # 微信公众号文章爬虫

    def __init__(self):
        global token
        global cookies
        
        # 每天更新
        date = datetime.now().date()-timedelta(1)
        self.epoch = int(date.strftime('%s'))
        self.fakeids = ['MzUyMDk5NTc2MQ==','MjM5MzEwMzIxMA==','MzA3NzAwNjcyMg==','MzI4MDIzMjk5Mw==','MzUyMTQ0MTMwMQ==','MzI3MjU2NTEwMg==','MzUyNzE4MDM2MA==']
        self.link_list = []


    def create_driver(self):  
        options = webdriver.ChromeOptions()
        # 禁用gpu加速，防止出一些未知bug
        options.add_argument('--disable-gpu')

        self.driver = webdriver.Chrome(executable_path='/Users/geed/Desktop/DF/Weixin/chromedriver', options=options)
        # 设置一个隐性等待 5s
        self.driver.implicitly_wait(5)


    def login(self):        
        try:
            self.create_driver()
            # 访问微信公众平台
            self.driver.get('https://mp.weixin.qq.com/')
            print("请拿手机扫码二维码登录公众号")
            
            # 等待手机扫描
            time.sleep(20)
            print("登录成功")
            
            # 获取个人token
            self.token = self.driver.current_url.split('=')[-1]
            # 获取cookies
            self.cookies = dict([[x['name'], x['value']] for x in self.driver.get_cookies()])
        
        except Exception as e:
            traceback.print_exc()
        finally:
            self.driver.quit()
            
            
    def get_article(self, query=''):
        try:
            # 设置headers
            headers = {
                "HOST": "mp.weixin.qq.com",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36"
            }

            # 微信公众号文章接口地址
            search_url = 'https://mp.weixin.qq.com/cgi-bin/appmsg?'
            
            for fakeid in self.fakeids:
                page = 0
                while True:
                    # 搜索文章需要传入几个参数：登录的公众号token、要爬取文章的公众号fakeid、随机数random
                    params = {
                        'action': 'list_ex',
                        'token': self.token,
                        'random': random.random(),
                        'fakeid': fakeid,
                        'lang': 'zh_CN',
                        'f': 'json',
                        'ajax': '1',
                        'begin': page,  # 不同页，此参数变化，变化规则为每页加5
                        'count': '5',
                        'query': '',
                        'type': '9'
                    }
                    
                    response = requests.get(search_url, headers=headers, params=params, cookies=self.cookies)
                    time.sleep(2)
                    
                    #保证不超过最大页数
                    if page + 5 > int(response.json().get('app_msg_cnt')) and page != 0:
                        break
                    
                    #仅爬取指定时间内文章
                    i = 0
                    for per in response.json().get('app_msg_list', []):
                        if per.get('create_time') < self.epoch:
                            i += 1
                            continue
                        
                        if per.get('link') not in self.link_list:
                            self.link_list.append(per.get('link'))
                    
                    #链接输出成数据表
                    pd.DataFrame(self.link_list,columns=['link']).to_csv('links.csv',index=False)
                    page += 5
                    print('%s links get' %len(self.link_list))
                    
                    if i >= 5:
                        break

        except Exception as e:
            traceback.print_exc()
            pd.DataFrame(self.link_list,columns=['link']).to_csv('links.csv',index=False)
            
                
    def get_html_content(self):
        
        # 带图片及格式，存html
        
        self.create_driver()
        df = pd.read_csv('/Users/geed/Desktop/DF/Weixin/links.csv',index_col=False)
        self.link_list = list(df['link'])
        
        for link in self.link_list:
            self.driver.get(link)
            try:
                #页面信息采集
                title_element = self.driver.find_element_by_id('activity-name')
                content_element = self.driver.find_element_by_id('js_content')
                date_element = self.driver.find_element_by_id('publish_time')
                author = self.driver.find_element_by_id('js_name').text
            except Exception as e:
                continue
            
            #拿到包含格式的所有html内容
            content = content_element.get_attribute('outerHTML')
            
            #搜索文章中的图片
            pattern = re.compile('src=".*?"')
            all_img = re.findall(r'<img.*?>', content)
            
            for i in range(len(all_img)-1):
                try:
                    img = all_img[i]
                    l = re.findall(pattern, img)
                    
                    #重置图片链接
                    l[0] = re.sub(r'&amp;wxfrom=5&amp;wx_lazy=1&amp;wx_co=1','',l[0])
                    img_name = l[0].split('/')[-2]
                    ext = l[0].split('/')[-1][:-1]
                    ext = re.sub(r'640\?wx_fmt=','.',ext)
                    
                    #去除特殊格式图片
                    if ext not in ['.png','.gif','.jpeg','.jpg']:
                        ext = '.jpeg'
                        print('---Picture access failed---\n',link)
                        
                    #保存图片到本地
                    img_name = img_name + ext
                    
                    img_name_new = 'src="http://digifinexff.com/wp-content/uploads/2022/08/' + img_name + '"'
                    img_filename = '/Users/geed/Desktop/DF/Weixin/微信图片/' + img_name
                    
                    if img_name not in ['1VO2FSicRGVSHBCp5btm8sMLu6vlBm5Bicf9UZrDjoktMNL7YicAjrgIwcKoovC0zHLUibeJ5wbuhAURlsjM3RS1uw.gif','1VO2FSicRGVSrn8Vm1380mGC715T5ImefvEAlV45Tk7ibPavsFJ2Tz8qpMfW5fOibQeRPJDnqibXMYSz5F3Ws1F56g.jpeg','1VO2FSicRGVTS31Q3F86c10OEMG1vyn4mX3lhMLDEeWWdLKEzMmNnVdGK3CiaM7OqKQgvGpgrZODn8oRGqbWsulg.gif']:
                        f = open(img_filename,'wb')
                        f.write(requests.get(l[0][5:-1]).content)
                        f.close()
                    
                    #更新原html中的图片链接
                    if len(l) >= 2:
                        img_new = img.replace(l[-1],img_name_new)
                    elif len(l) == 1:
                        img_new = img[:-1] + ' ' + img_name_new + img[-1]
                    else:
                        img_new = img
                        print(img)                    
                    img_new = re.sub(r'max-width','width',img_new)
                    content = content.replace(img,img_new)
                except Exception as e:
                    continue
                    
            #写入html文档
            title = title_element.text
            title = re.sub('\W','',title)
            filepath = '/Users/geed/Desktop/DF/Weixin/微信文章/' + author + '/'
            filename = filepath + title + '.html'
            
            f = open(filename,'w')
            f.write(title_element.get_attribute('outerHTML'))
            f.write(date_element.get_attribute('outerHTML'))
            f.write(content)
            f.close()
                                
        self.driver.quit()

            
if __name__ == '__main__':
    spider = Spider()
    spider.login()
    spider.get_article()
    spider.get_html_content()


  
'''
    def get_content(self):
        # 纯文本，存进csv
        self.create_driver()
        
        df = pd.DataFrame(columns=['post_title','post_author','post_date','post_content'])

        for link in self.link_list:
            self.driver.get(link)
            content = self.driver.find_element_by_id('js_content').text
            title = self.driver.find_element_by_class_name('rich_media_title').text
            author = self.driver.find_element_by_id('profileBt').text
            date = self.driver.find_element_by_id('publish_time').text
            self.df.loc[len(self.df.index)] = [title,author,date,content]
            time.sleep(2)
        
        df.to_csv('/Users/geed/Desktop/DF/Weixin/Articles.csv',index=False)
        self.driver.quit()
'''
    
    
