# -*- coding : utf-8 -*-
# coding: utf-8

import requests
from lxml import etree
import os
from multiprocessing.dummy import Pool
import json
from time import time
import re


# A Bing Crawler: Crawling Bing pictures by keyword and number of pictures and storing them in the specified path.
# Guide: Just run the command -- for example: bingImageCrawler ('ipad', 20,'/home/wxn/images'). Run()


class BingImageCrawler:
    thread_amount = 1000  # Number of thread pools
    per_page_images = 30  # Number of requested pictures per page
    count = 0
    success_count = 0

    # Ignore some characters...
    ignore_chars = ['|', '.', ',', '', '/', '@', ':', ';', '[', ']', '+']
    # Image format
    image_types = ['bmp', 'jpg', 'png', 'tif', 'gif', 'pcx', 'tga', 'exif', 'fpx', 'svg', 'psd', 'cdr', 'pcd', 'dxf',
                   'ufo', 'eps', 'ai', 'raw', 'WMF', 'webp']
    # Request headers
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/85.0.4183.83 Safari/537.36'}

    def __init__(self, keyword, amount, bing_image_url_pattern, path='./'):
        # keyword: keyword of the crawler
        # amount: number of images needed
        # path: where the images will be stored
        self.keyword = keyword
        self.amount = amount
        self.path = path
        self.thread_pool = Pool(self.thread_amount)
        self.bing_image_url_pattern = bing_image_url_pattern

    def __del__(self):
        self.thread_pool.close()
        self.thread_pool.join()

    def request_homepage(self, url):
        return requests.get(url, headers=self.headers)

    # Parse the Bing web page, convert the info into a list and return

    # The information of the image is stored in a dictionary,
    # and the keys of the dictionary includes image_title, image_type, image_md5, image_url
    def parse_homepage_response(self, response):
        # response: response of the page

        # Get the JSON-formatted string of each image
        tree = etree.HTML(response.text)
        m_list = tree.xpath('//*[@class="imgpt"]/a/@m')

        # Process the image
        info_list = []
        for m in m_list:
            dic = json.loads(m)

            # Remove characters that are not allowed in file names
            image_title = dic['t']
            for char in self.ignore_chars:
                image_title = image_title.replace(char, '')
                image_title = image_title.replace(" ", "")
                re.sub('[^A-Za-z0-9.]', '', image_title)
                image_title = ''.join(filter(str.isalnum, image_title))
            image_title = image_title.strip()

            # The information of some images does not contain the format.
            # In this case, the image is set to JPG format:
            image_type = dic['murl'].split('.')[-1]
            if image_type not in self.image_types:
                image_type = 'jpg'

            # Store the info into a list
            info = dict()
            info['image_title'] = image_title
            info['image_type'] = image_type
            info['image_md5'] = dic['md5']
            info['image_url'] = dic['murl']

            info_list.append(info)
        return info_list

    def request_and_save_image(self, info):
        # info: image_title, image_type, image_md5, image_url
        filename = '{}.{}'.format(info['image_title'], info['image_type'])
        filepath = os.path.join(self.path, filename)

        try:
            response = requests.get(info['image_url'], headers=self.headers, timeout=5)

            with open(filepath, 'wb') as fp:
                fp.write(response.content)

            self.count += 1
            self.success_count += 1
            print('{}: saving {} done.'.format(self.count, filepath))

        except requests.exceptions.RequestException as e:
            self.count += 1
            print('{}: saving {}failed. url: {}'.format(self.count, filepath, info['image_url']))
            print('\t tip:', e)

    # Remove duplicates
    def deduplication(self, info_list):
        result = []

        # Use MD5 as the unique identifier
        md5_set = set()
        for info in info_list:
            if info['image_md5'] not in md5_set:
                result.append(info)
                md5_set.add(info['image_md5'])
        return result

    def run(self):
        if not os.path.exists(self.path):
            os.mkdir(self.path)

        homepage_urls = []
        for i in range(int(self.amount / self.per_page_images * 1.5) + 1):  # In case of repeated images
            url = self.bing_image_url_pattern.format(self.keyword, i * self.per_page_images, self.per_page_images)
            homepage_urls.append(url)
        print('homepage_urls len {}'.format(len(homepage_urls)))

        # Request all Bing image web pages through the thread pool
        homepage_responses = self.thread_pool.map(self.request_homepage, homepage_urls)

        # Parse the information of all images from Bing's web page.
        # Each picture includes image_title, image_type, image_md5, image_url...
        info_list = []
        for response in homepage_responses:
            result = self.parse_homepage_response(response)
            info_list += result
        print('info amount before deduplication', len(info_list))

        # Remove duplicates
        info_list = self.deduplication(info_list)
        print('info amount after deduplication', len(info_list))
        info_list = info_list[: self.amount]
        print('info amount after split', len(info_list))

        # Download
        self.thread_pool.map(self.request_and_save_image, info_list)
        print('all done. {} successfully downloaded, {} failed.'.format(self.success_count,
                                                                        self.count - self.success_count))


if __name__ == '__main__':
    # keyword: ipad
    # Number of images need：100
    # File path: '\home\wxn\images'
    start = time()
    # URL: the url of the search page(with specific keywords included)
    url = 'https://cn.bing.com/images/search?q=ipad&form=HDRSC2&first=1&tsc=ImageBasicHover'
    BingImageCrawler('ipad', 20, url, '/home/wxn/images').run()
    print(time() - start)
