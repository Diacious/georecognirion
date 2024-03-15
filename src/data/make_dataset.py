# -*- coding: utf-8 -*-
import click
import logging
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
from seleniumwire import webdriver
#from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
from bs4 import BeautifulSoup
import pathlib
import concurrent.futures
import re
import urllib.request
import os

MAIN_URL = "https://yandex.ru/images/search"
PARENT_PATH = pathlib.Path('./moscow_images')
TIMEOUT = 30
reg = re.compile(r'.jpg|.jpeg|.png|.gif|.bmp')

def _download_image(url, title, path):
        #img_extensions = (".jpg", ".jpeg", ".gif", ".png", ".bmp")
        exten = reg.search(url.lower())
        #exten = [img_ex  for img_ex in img_extensions if url.lower().endswith(img_ex)]
        
        if exten:
            path = pathlib.PurePath(path, title + exten[0])
            try:
                response = urllib.request.urlopen(url, timeout=300).read()

                with open(path, 'wb') as f:
                    f.write(response)
            except:
                print('failed to download')
        else:
            print('fail to define img extension', url)
        return 0

class YandexImagesDownloader():
    MAIN_URL = "https://yandex.ru/images/search"
    PARENT_PATH = pathlib.Path('./moscow_images')

    def __init__(self, driver):
        self.driver = driver
        self.action = ActionChains(driver)


    def check_captcha(self, url):
        self.soup = BeautifulSoup(self.driver.page_source, "lxml")
        if self.soup.find('script', {'src': "/captchapgrd"}):
            #del self.driver.requests
            #del self.driver.page_source
            reply = input()
            #self.driver.get(url)
            #time.sleep(4)
            self.check_captcha(url)


    def get_images_ids(self, url):
        self.driver.get(url)

        self.check_captcha(url)

        time.sleep(4)
        self.soup = BeautifulSoup(self.driver.page_source, "lxml")
        items_place = self.soup.find_all('div', {"class": "SerpItem"})

        ids = []

        for item in items_place:
            id = item.get('id')

            ids.append(id)
        del self.driver.requests

        return ids
    

    def scroll_shim(self, object):
        x = object.location['x']
        y = object.location['y']
        scroll_by_coord = 'window.scrollTo(%s,%s);' % (
            x,
            y
        )
        scroll_nav_out_of_way = 'window.scrollBy(0, -120);'
        self.driver.execute_script(scroll_by_coord)
        self.driver.execute_script(scroll_nav_out_of_way)
        

    def download_image(self, id, title):
        is_clicked = False
        n_tries = 1
        while not is_clicked and n_tries < 10:
            try:
                n_tries += 1
                self.check_captcha(self.driver.current_url)
                img = self.driver.find_element(By.ID, id)
                self.scroll_shim(img)
                self.action.move_to_element(img).click().perform()
                time.sleep(4)
                self.check_captcha(self.driver.current_url)
                is_clicked = True
            except:
                print(f'something wrong when clicking, image: {title}')
                self.driver.get(self.url)
                time.sleep(4)

        self.soup = BeautifulSoup(self.driver.page_source, "lxml")

        items_place = self.soup.find_all('div', {"class": "MMViewerButtons"})

        if items_place:
            dw_url = items_place[0].find('a').get('href')
        else:
            dw_url = None

        if dw_url:
            _download_image(dw_url, title, self.class_path)           
        else:           
            print(f'failed to find link for image {title} with id: {id}') 
        try:
            close_button = self.driver.find_element(By.CLASS_NAME, "MMViewerModal-Close")
            self.action.move_to_element(close_button).click().perform()
        except:
            print(f'failed ot close windows for image {title}')

        

    def get_images_by_keyword(self, word, page):
        
        self.url = f'{YandexImagesDownloader.MAIN_URL}?text={word}&p={page}'
        'https://yandex.ru/images/search?text=Zaikonospassky monastery&p=8'
        img_ids = self.get_images_ids(self.url)
        n_tries = 1
        while len(img_ids) == 0 and n_tries != 10:
            time.sleep(10)
            img_ids = self.get_images_ids(self.url)
            n_tries += 1
        print(len(img_ids))
        for i, id in enumerate(img_ids):
            title = word + '_' + str(i) + '_' + str(page)
            try:
                print(f'trying to download image for {word} with id {id} {i + 1}/{len(img_ids)}')
                res = self.download_image(id, title)
            except TimeoutException as e:
                print('Selenium tiemout', word)
                self.check_captcha(self.url)
            except WebDriverException as e:
                print("Webdriver Exception")
            except:
                print('Unexpected error when trying to download')
                #self.driver.get(url)
                self.check_captcha(self.url)
        

    def quit_driver(self):
        self.driver.quit()


    def set_class_path(self, path):
        self.class_path = path


def download(items):
    place, pages = items
    if pages:
        print(f'working on {place} with page {pages[0]}')
        dirname = os.path.dirname(__file__).split('\\')
        filename = '/'.join(dirname[:-2]) + '/data/raw'
        #print(filename)
        class_path = pathlib.Path(f"{filename}/{YandexImagesDownloader.PARENT_PATH}")

        if not class_path.exists():
            class_path.mkdir()

        class_path = pathlib.Path(f"{class_path}/{place}")

        if not class_path.exists():
            class_path.mkdir()

        try:
            y_downloader = YandexImagesDownloader(webdriver.Firefox())
            y_downloader.set_class_path(class_path)
            y_downloader.get_images_by_keyword(place, pages[0])
        except TimeoutException as e:
            print('selenium wire timeout in parents prcocess') 
        finally:
            y_downloader.quit_driver()
        
        return (place, pages[1:])
    else:
        return place, []


@click.command()
@click.argument('input_filepath', type=click.Path(exists=True))
@click.argument('output_filepath', type=click.Path())
def main(input_filepath, output_filepath):
    """ Maeking dataset by using selenium 
        in some moment there will be captcha and it is necessary
        to solve it to continue gathering data
    """
    landmark_pages = {}
    result_dict = {}
    with open(input_filepath, encoding='utf-8') as f:
        for line in f:
            place, pages = line.strip().split(';')
            pages = [int(p) for p in pages.split(',') if p]
            landmark_pages[place] = pages

    result_dict = {}
    #n_puls = int(input())
    n_puls = 2

    with concurrent.futures.ThreadPoolExecutor(max_workers=n_puls) as executor:
        res = executor.map(download, landmark_pages.items())

    for el in res:
        result_dict[el[0]] = el[1]
    #print(result_dict)

    with open(input_filepath, 'w', encoding='utf-8') as f:
        for place, pages in result_dict.items():
            f.write(place + ';' + ','.join([str(el) for el in pages]) + '\n')

    logger = logging.getLogger(__name__)
    logger.info('making final data set from raw data')


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
