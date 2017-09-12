from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
# from selenium.webdriver import FirefoxProfile, Firefox
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import Select

from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.common.by import By

import calendar
import argparse
import logging
from logging import handlers

class ReservationChecker(object):
    '''to scrape the Ontario parks webpages to check campsite availablility
    '''

    # TODO remove POSSIBLE_x -- generate
    POSSIBLE_CAMPSITES = ['Campsite', 'Roofed Accommodation', 'Cottage', 'Backcountry', 'Group']

    POSSIBLE_MONTHS = map(lambda x: x[:3], calendar.month_name)
    POSSIBLE_DAYS = range(1, 32)

    POSSIBLE_PARKS_CAMPSITE = ['Algonquin - Achray', 'Algonquin - Brent', 'Algonquin - Canisbay Lake', 'Algonquin - Kiosk', 'Algonquin - Lake Of Two Rivers', 'Algonquin - Mew Lake', 'Algonquin - Pog and Kearney Lakes', 'Algonquin - Rock and Coon Lakes', 'Algonquin - Tea Lake', 'Aaron', 'Arrowhead', 'Awenda', 'Balsam Lake', 'Bass Lake', 'Blue Lake', 'Bon Echo', 'Bonnechere', 'Bronte Creek', 'Caliper Lake', 'Charleston Lake', 'Chutes', 'Craigleith', 'Darlington', 'Driftwood', 'Earl Rowe', 'Emily', 'Esker Lakes', 'Fairbank', 'Ferris', 'Finlayson Point', 'Fushimi Lake', 'Fitzroy', 'Grundy Lake', 'Halfway Lake', 'Inverhuron', 'Ivanhoe Lake', 'Kakabeka Falls', 'Kettle Lakes', 'Killarney', 'Killbear', 'Lake Superior - Agawa Bay', 'Lake Superior - Rabbit Blanket', 'Lake St. Peter', 'Long Point', 'MacGregor Point', 'Mara', 'Marten River', 'McRae Point', 'Mikisew', 'Mississagi', 'Murphys Point', 'Nagagamisis', 'Neys', 'Oastler Lake', 'Pancake Bay', 'Pinery', 'Point Farms', 'Port Burwell', 'Presquile', 'Quetico', 'Rainbow Falls - Rossport', 'Rainbow Falls - Whitesand', 'Rene Brunelle', 'Restoule', 'Rideau River', 'Rock Point', 'Rondeau', 'Rushing River', 'Samuel de Champlain', 'Sandbanks', 'Sandbar Lake', 'Sauble Falls', 'Selkirk', 'Sharbot Lake', 'Sioux Narrows', 'Sibbald Point', 'Silent Lake', 'Silver Lake', 'Six Mile Lake', 'Sleeping Giant', 'Sturgeon Bay ', 'Turkey Point', 'Voyageur', 'Wakami Lake', 'Wheatley', 'White Lake', 'Windy Lake']
    POSSIBLE_PARKS_BACKCOUNTRY = ['Algonquin Interior', 'Bon Echo', 'Charleston Lake', 'Fushimi Lake', 'Frontenac', 'Grundy Lake', 'Kawartha Highlands', 'Killarney', 'Massasauga', 'Murphys Point', 'Quetico']
    POSSIBLE_PARKS = POSSIBLE_PARKS_BACKCOUNTRY + POSSIBLE_PARKS_CAMPSITE

    HOMEPAGE = 'https://reservations.ontarioparks.com/'

    LOGGER_PATH = '/tmp/ont_resv.log' #assume this path exists
    LOGGER_LEVEL = logging.INFO

    SCREENSHOT_FOLDER = '/tmp/reservations_screenshots/' # assume folder exists

    def __init__(self):
        self.log = self._create_logger()
        self.start()

    def start(self):
        """Opens an instance of the browser_type
        """
        self.log.info("START SESSION ----------------")

        # self.firefox_profile = FirefoxProfile()
        # self.dr_tmp = self.firefox_profile.profile_dir
        # self.chrome_profile = ChromeProfile()
        # self.dr_tmp = self.chrome_profile.profile_dir

        # self.browser = Firefox(firefox_profile=self.firefox_profile)
        # self.log.info("opened the Firefox browser")
        self.log.info("opened the Chrome browser")
        self.browser = Chrome(executable_path='/usr/local/bin/chromedriver')

    def _create_logger(self):
        """create logger
        TODO: Might be issues with multiple initializations of this obj
        """

        logger = logging.getLogger()
        logger.setLevel(self.LOGGER_LEVEL) # set to lowest severity

        rotating_handle = handlers.RotatingFileHandler(filename=self.LOGGER_PATH,
            mode='a', backupCount=2)
        formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
        rotating_handle.setFormatter(formatter)
        # rotating_handle.setLevel(self.LOGGER_LEVEL)
        logger.addHandler(rotating_handle)

        # always display on std out
        console = logging.StreamHandler()
        formatter.datefmt = '%H:%M:%S'
        console.setFormatter(formatter)
        # console.setLevel(self.LOGGER_LEVEL)
        logger.addHandler(console)

        return logger

    def end(self):
        """Closes an instance of the browser_type
        """
        if self.browser:
            self.browser.close()
            self.browser.quit()
            self.log.info("closed the browser")
        else:
            self.log.debug("no browser to close")
        self.log.info("CLOSE SESSION ----------------")

    def get_availability(self, campsite, month, day, park, n):
        """Gets the available locations. 
        TODO Get screenshot of map
        Returns:
            list of names of available campsites
        """
        self.browser.get(self.HOMEPAGE)
        # might have to choose language
        try:
            l = self.browser.find_element_by_id('ChooseLanguage')
            e = self.browser.find_element_by_xpath("//div[@id='language1']/a")
            if e:
                e.click()
            else:
                raise ValueError("Not sure what's going on...")
        except NoSuchElementException, e:
            self.log.info('Did not need to select language')
        
        self._select('selResType', campsite)
        self._select('selArrMth', self.POSSIBLE_MONTHS[month])
        self._select('selArrDay', "%d%s" % (day,"tsnrhtdd"[(day/10%10!=1)*(day%10<4)*day%10::4]))
        #https://stackoverflow.com/questions/9647202/ordinal-numbers-replacement
        self._select('selLocation', park)
        self._select('selPartySize', str(n))

        # click find by list
        self.browser.find_element_by_id('linkButtonList').click() # alt: trigger 'href' directly
        xpath = "//div[@id='viewPort']/table[@class='list_new']/tbody/tr"
        try:
            lst_elemt = self.browser.find_elements_by_xpath(xpath)
        except NoSuchElementException, e:
            self.log.error('Could not find list of availability\n'
                'expecting xpath: %s' % xpath)
        l = self._check_for_avail(lst_elemt)

        self.screenshot('after.png')

        return l

    def _select(self, html_id, select_value):
        """select the indicated value, if possible
        Args:
            html_id: id of the <select> obj
            select_value: VISIBLE text to select from select
        """

        try:
            html_obj = self.browser.find_element_by_id(html_id)
            Select(html_obj).select_by_visible_text(select_value)
            self.log.info("Selected %s" % select_value)
        except NoSuchElementException, e:
            self.log.error("Cannot find id '%s', or selector for value %s" % (html_id,
                select_value))
        WebDriverWait(self.browser, 10).until(EC.invisibility_of_element_located((By.ID, 'viewPortStatus')))

    def _check_for_avail(self, lst_of_tr):
        """Interpret <tr> to be available or not
        Returns:
            list of names of sites that are available
        """
        lst_of_avail_sites = []
        for i in lst_of_tr:
            try:
                # TODO save thumbnail of all available sites
                xpath = "./td[1]/a/img[@title='Available']"
                t = i.find_elements_by_xpath(xpath)
                lst_of_avail_sites.append(i.find_element_by_xpath('./td[2]').text)
            except NoSuchElementException: # Unavailable / Unreservable
                break
        return lst_of_avail_sites

    def screenshot(self, fn):
        self.browser.save_screenshot(self.SCREENSHOT_FOLDER + fn)

if __name__ == '__main__':
    r = ReservationChecker()

    parser = argparse.ArgumentParser(description='Check site for availability')
    parser.add_argument('-c', '--campsite', type=str,
        choices=ReservationChecker.POSSIBLE_CAMPSITES, required=True,
        help='type of the campsite')
    parser.add_argument('-m', '--month', type=int, choices=range(1,13), required=True,
        help='number representation of month')
    parser.add_argument('-d', '--day', type=int, choices=range(1,32), required=True,
        help='number representation of day')
    parser.add_argument('-p', '--park', type=str,
        choices=ReservationChecker.POSSIBLE_PARKS, required=True,
        help='The name of the park')
    parser.add_argument('-n', type=int,
        choices=range(1, 10), required=True,
        help='Party number')

    args = parser.parse_args()
    try:
        print r.get_availability(args.campsite, args.month, args.day, args.park, args.n)
    finally:
        r.end()
