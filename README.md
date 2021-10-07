# Bing_Crawler
Crawling Bing pictures by keyword and number of pictures and storing them in the specified path. (Using Python language)

## Guide

1. Search the keyword that you require on Bing. Copy the link of the image page.

2. Change the parameters, an example is like this:

   ```python
   url = 'https://cn.bing.com/images/search?q=ipad&form=HDRSC2&first=1&tsc=ImageBasicHover'
   BingImageCrawler('ipad', 20, url, '\home\wxn\images').run()
   ```

3. Run the program

