import random
import re
import smtplib
import time
from email.header import Header
from email.mime.text import MIMEText
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from bs4 import BeautifulSoup


class WJX_TJ:
    def __init__(self, Username, Password, IP = '111.187.78.214', Address = None):
        """
        :param Username: 用户名。
        :param Password: 登陆密码。
        :param IP: 本地公网IP, 用于伪装代理。
        :param Address: 定位地址, 请手动从历史问卷复制, 程序自动随机经纬坐标的最后两位数。
        """
        self.Username = Username
        self.Password = Password
        self.IP = IP
        self.Mon, self.Day = time.strftime("%b %d", time.localtime()).split()
        if Address:
            Addr = Address.split(',')
            self.Address = Addr[0][:-2]+str(random.randint(10, 90)) +','+ Addr[1][:-3]+str(random.randint(10, 90))+']'
        self.headers = {'X-Forwarded-For': IP, 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
        self.ifSuccess = False

    def run(self):
        self.CheckFeedback(self.Submit(self.Select(self.Login())))
        return self.ifSuccess

    def LOG(self, msg):
        with open('WJX_TJ.log','a') as LOG:
            t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            LOG.write(t+'  '+msg+'\n')
            print(t+'  '+msg+'\n')

    def Login(self):
        LoginUrl = 'https://tongjistudent.wjx.cn/user/loginForm.aspx?user_token=RzCs8KPQb4VEfycFVJ8OMztE5FTgJGXpdBEja3vmhfACDox2Pt121vdCYeWNHrTmWnSH0CuCghDhy8bMnMKd9BD9VyTN%2fNYk%2fyYsUxVH2acEXm9rN0f5hA%3d%3d&returnUrl=%2fuser%2fqlist.aspx%3fu%3d%25e6%2589%258b%25e6%259c%25ba%25e7%2594%25a8%25e6%2588%25b7g0xtoyb1buuqdrqsc9egsw%26userSystem%3d1%26systemId%3d55926111'
        try:
            LoginRequ = requests.get(url = LoginUrl, headers = self.headers)
        except Exception as Error:
            self.Error('无法打开登录界面！\n' + str(Error))
        LoginSoup = BeautifulSoup(LoginRequ.text, 'lxml')
        SubmitUrl = 'https://tongjistudent.wjx.cn/user'+LoginSoup.select('#form1')[0].get('action').lstrip('.')
        VIEWSTATE = LoginSoup.select('#__VIEWSTATE')[0].get('value')
        VIEWSTATEGENERATOR = LoginSoup.select('#__VIEWSTATEGENERATOR')[0].get('value')
        EVENTTARGET = LoginSoup.select('#__EVENTVALIDATION')[0].get('value')
        formdata = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': VIEWSTATE,
            '__VIEWSTATEGENERATOR': VIEWSTATEGENERATOR,
            '__EVENTVALIDATION': EVENTTARGET,
            'hfQuery': '10000|'+self.Username+'〒30000|'+self.Password,
            'hfPwd': '2',
            'hideIsPhone': '',
            'btnSubmit': '登录',
            'phoneVal': '',
            'txtVerifyCode_1': '',
            'title': '',
            'hidPhone': '',
            'password': '',
        }
        self.HomeRequ = requests.post(url = SubmitUrl, headers = self.headers, data = formdata)
        self.cookies = self.HomeRequ.cookies
        return self.HomeRequ.text

    def Select(self, HomeText = None):
        if not HomeText:
            try:
                HomeText = self.HomeRequ.text
            except Exception as Error:
                self.Error('登录失败！\n' + str(Error))
        HomeSoup = BeautifulSoup(HomeText, 'lxml')
        self.relrealname = HomeSoup.select('#body-wrapper > ul > li:nth-child(1) > div > span')[0].contents[0].strip()
        Papers = HomeSoup.select('#ctl00_ContentPlaceHolder1_ulQs > li > a')
        for Paper in Papers[::-1]:
            PaperTitle = Paper.get_text()
            if '每日信息上报' in PaperTitle and self.Mon in PaperTitle and self.Day in PaperTitle:
                self.TodayUrl = Paper.get('href')
                return self.TodayUrl

    def Submit(self, TodayUrl = None):
        def get_jqsign(ktimes, jqnonce):
            r = []
            b = ktimes % 10 if ktimes % 10 else 1
            for char in jqnonce[0]:
                f = ord(char) ^ b
                r.append(chr(f))
            jqsign =  ''.join(r)
            return jqsign

        if not TodayUrl:
            try:
                TodayUrl = self.TodayUrl
            except Exception as Error:
                self.Error('无法获取今日问卷链接！\n' + str(Error))
        self.TodayRequ = requests.get(url = TodayUrl, headers = self.headers, cookies = self.cookies)
        Params =  parse_qs(urlparse(TodayUrl).query)
        ktimes = random.randint(15, 50)
        jqnonce = re.search(r'.{8}-.{4}-.{4}-.{4}-.{12}', self.TodayRequ.text).group()
        self.SubmitParams = {
            'submittype': 1,
            'curID': re.search(r'\d{8}', self.TodayRequ.text).group(),
            't': '{}{}'.format(int(time.time()), random.randint(100, 200)),
            'starttime': re.search(r'\d+?/\d+?/\d+?\s\d+?:\d{2}', self.TodayRequ.text).group(),
            'ktimes': ktimes,
            'rn': re.search(r'\d{9,10}\.\d{8}', self.TodayRequ.text).group(),
            'relts': Params['relts'][0],
            'relusername': Params['relusername'][0],
            'relsign': Params['relsign'][0],
            'relrealname': self.relrealname,
            'reldept': Params['relDept'][0],
            'relext': Params['relExt'][0],
            'hlv': 1,
            'sd': 'http://tongjistudent.wjx.cn/',
            'jqnonce': jqnonce,
            'jqsign': get_jqsign(ktimes, jqnonce)
        }

        SubmitUrl = 'https://www.wjx.cn/joinnew/processjq.ashx?'+urlencode(self.SubmitParams)
        formdata = {'submitdata': '1$1}2$1}3$'+self.Address+'}4$(跳过)}5$(跳过)}6$(跳过)}7$-3}8$-3}9$(跳过)}10$-3}11$-3}12$(跳过)^(跳过)^(跳过)^(跳过)}13$-3}14$-3}15$(跳过)^(跳过)}16$-3'}
        self.FeedbackRequ = requests.post(url = SubmitUrl, headers = self.headers, data = formdata, cookies = self.cookies)
        return self.FeedbackRequ.text

    def CheckFeedback(self, FeedbackText = None):
        if not FeedbackText:
            FeedbackText = self.FeedbackRequ.text
        try:
            FeedbackDict = {i.split('=')[0]: i.split('=')[1] for i in FeedbackText.split('?')[1].split('&')}
            self.SerialNumber = FeedbackDict.get('jidx')
            self.Certificate = FeedbackDict.get('JoinID')
            self.PaperID = FeedbackDict.get('q')
            self.CheckHistory(self.History())
        except Exception as Error:
            self.Error('上报失败！\n' + str(Error))

    def History(self, HomeText = None):
        if not HomeText:
            HomeText = self.HomeRequ.text
        HomeSoup = BeautifulSoup(HomeText, 'lxml')
        HistoryUrl = 'https://tongjistudent.wjx.cn/user/'+HomeSoup.select('#ctl00_ContentPlaceHolder1_hrefHasJoin')[0].get('href')
        HistoryRequ = requests.get(url = HistoryUrl, headers = self.headers, cookies = self.cookies)
        HistorySoup = BeautifulSoup(HistoryRequ.text, 'lxml')
        HistoryTitles =  [i.get_text() for i in HistorySoup.select('#ctl00_ContentPlaceHolder1_ulQs > li > div.pull-left > div.clearfix > div')]
        HistoryUrls = ['https://tongjistudent.wjx.cn'+i.get('href')  for i in HistorySoup.select('#ctl00_ContentPlaceHolder1_ulQs > li > div.pull-right > a.details-box')]
        self.Historys = dict(zip(HistoryTitles, HistoryUrls))
        return self.Historys

    def CheckHistory(self, Historys = None):
        if not Historys:
            Historys = self.Historys
        for HistoryTitle, HistoryUrl in Historys.items():
            if self.Mon in HistoryTitle and self.Day in HistoryTitle:
                self.HistoryRequ = requests.get(url = HistoryUrl, headers = self.headers, cookies = self.cookies)
                HistorySoup = BeautifulSoup(self.HistoryRequ.text, 'lxml')
                self.SerialNumber = HistorySoup.select('#divattrsign > div.query__data-details > dl.jindex > dd > strong')[0].get_text()
                self.Answer = [i.get_text() for i in HistorySoup.select('#divattrsign > div.query__data-result > div > div.data__key > div')]
                self.Success()
                break

    def Success(self):
        self.ifSuccess = True
        Title = '{}{:\u3000<4}  序号: {:<5}'.format(self.Username, self.relrealname, self.SerialNumber)
        Content = '  凭证: {}  详情: '.format(self.Certificate) + ' '.join(self.Answer)
        self.SendEmail(Title, Content)
        self.LOG(Title + Content)

    def Error(self, Error):
        Title = 'Fail: {}{:\u3000<4}  '.format(self.Username, self.relrealname)
        Content = Error
        self.SendEmail(Title, Content)
        self.LOG(Title + Content)

    def SendEmail(self, title, content):
        mail_host = "smtp.163.com"
        mail_user = ""      #发送邮箱用户名
        mail_pass = ""      #发送邮箱密码
        if not mail_pass:
            return
        sender = ''         #发送邮箱用户名
        receivers = ['']    #接收邮箱用户名

        message = MIMEText(content, 'plain', 'utf-8')
        message['From'] = "{}".format(sender)
        message['To'] = ",".join(receivers)
        message['Subject'] = title

        try:
            smtpObj = smtplib.SMTP_SSL(mail_host, 465)
            smtpObj.login(mail_user, mail_pass)
            smtpObj.sendmail(sender, receivers, message.as_string())
        except smtplib.SMTPException as Error:
            Title = 'Fail to Send Email: {}{:\u3000<4}'.format(self.Username, self.relrealname)
            self.LOG(Title)

WJX = WJX_TJ('学号', '密码', '本地公网IP', '定位地址，例如：上海市杨浦区同济大学[121.499225,31.283236]')

WJX.run()

