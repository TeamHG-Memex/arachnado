import logging
import time

import lxml.html
import scrapy
from scrapy.http.request.form import _get_inputs, _get_form_url
from scrapy.exceptions import NotConfigured
from formasaurus import FormExtractor


logger = logging.getLogger(__name__)

# Scrapy signals
test_login_credentials = object()


class LoginFormRequest(scrapy.FormRequest):

    @classmethod
    def from_response(cls, response, formname=None, formnumber=0,
                      formdata=None, clickdata=None, dont_click=False,
                      formxpath=None, form=None, **kwargs):
        kwargs.setdefault('encoding', response.encoding)
        formdata = _get_inputs(form, formdata, dont_click, clickdata, response)
        url = _get_form_url(form, kwargs.pop('url', None))
        method = kwargs.pop('method', form.method)
        return cls(url=url, method=method, formdata=formdata, **kwargs)


class Login(object):

    LOGIN_FLAGS = set(['login_pending', 'login_required', 'login_failed',
                       'login_success'])
    TEST_LOGIN_FLAGS = set(['test_login_success', 'test_login_failed'])

    def __init__(self, crawler):
        self.crawler = crawler
        if not crawler.settings.getbool('LOGIN_ENABLED'):
            raise NotConfigured
        crawler.signals.connect(self.test_login_credentials,
                                signal=test_login_credentials)
        self.ex = FormExtractor.load("./myextractor.joblib")

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_start_requests(self, start_requests, spider):
        self.start_requests = list(start_requests)
        self.spider = spider
        self.username = getattr(spider, 'login_username', None)
        self.password = getattr(spider, 'login_password', None)
        login_url = getattr(spider, 'login_url', None)
        if all([self.username, self.password, login_url]):
            self._set_login_flag('login_pending')
            logger.info('Logging in: {}/{}'.format(self.username,
                                                   self.password))
            yield scrapy.Request(login_url, self.parse_login_form)
        else:
            for request in self.start_requests:
                yield request

    def process_spider_output(self, response, result, spider):
        if 'login_failed' in spider.flags or 'login_success' in spider.flags:
            return result
        if self._find_login_form(response):
            logger.info('Login form found')
            self._set_login_flag('login_required')
            spider.login_form_response = response
        return result

    def parse_login_form(self, response):
        login_request = self._get_login_request(
            response, self.crawler.spider, self.username, self.password
        )
        if login_request is not None:
            login_request.callback = self.parse_logged_in_page
            yield login_request
        else:
            logger.warning('No login request generated, aborting login')
            self._set_login_flag('login_failed')
            for request in self.start_requests:
                yield request

    def parse_logged_in_page(self, response):
        if self._find_login_form(response):
            from scrapy.utils.response import open_in_browser
            open_in_browser(response)
            logger.info('Login failed')
            self._set_login_flag('login_failed')
        else:
            logger.info('Login successful')
            self._set_login_flag('login_success')
        for request in self.start_requests:
            yield request

    def test_login_credentials(self, spider, username, password):
        self._set_test_login_flag()
        if spider.login_form_response is None:
            return
        login_request = self._get_login_request(
            spider.login_form_response, spider, username, password
        )
        login_request.meta['cookiejar'] = 'test_login' + str(time.time())
        login_request.callback = self.parse_test_login_credentials
        self.crawler.engine.schedule(login_request, spider)

    def parse_test_login_credentials(self, response):
        if self._find_login_form(response):
            from scrapy.utils.response import open_in_browser
            open_in_browser(response)
            logger.info('Test login failed')
            self._set_test_login_flag('test_login_failed')
        else:
            logger.info('Test login successful')
            self._set_test_login_flag('test_login_success')

    def _set_login_flag(self, flag=None):
        self.spider.flags -= self.LOGIN_FLAGS
        if flag is not None:
            self.spider.flags.add(flag)

    def _set_test_login_flag(self, flag=None):
        self.spider.flags -= self.TEST_LOGIN_FLAGS
        if flag is not None:
            self.spider.flags.add(flag)

    def _find_login_form(self, response):
        tree = lxml.html.fromstring(response.body, base_url=response.url)
        for form_element, form_type in self.ex.extract_forms(tree):
            if form_type == 'l':  # Login form
                return form_element

    def _get_login_request(self, response, spider, username, password):
        form_element = self._find_login_form(response)
        if form_element is None:
            logger.debug('No form element was found')
            return
        text_inputs = form_element.xpath(
            './/input[not(@type) or @type="" or @type="text" '
            'or @type="password"]'
        )
        if len(text_inputs) < 2:
            logger.debug('Too few number of inputs: {}'
                         .format(len(text_inputs)))
            return
        formdata = {}
        username_field = text_inputs[0].attrib.get('name')
        password_field = text_inputs[1].attrib.get('name')
        if not username_field or not password_field:
            logger.debug('No form element was found')
            return
        formdata[username_field] = username
        formdata[password_field] = password
        checkboxes = form_element.xpath(
            './/input[@type="checkbox"]'
        )
        for checkbox in checkboxes:
            checkbox_name = checkbox.attrib.get('name')
            if checkbox_name:
                formdata[checkbox_name] = 'on'
        return LoginFormRequest.from_response(
            response,
            formdata=formdata,
            form=form_element,
            priority=10 ** 9
        )
