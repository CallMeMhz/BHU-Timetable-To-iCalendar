# coding: utf-8
import re
import random
import requests
from datetime import datetime, timedelta
from icalendar import Calendar, Event
from pprint import pprint
from bs4 import BeautifulSoup as BS

def login(usr, pwd):
    s = requests.Session()
    vcode_url = 'http://jw.bhu.edu.cn/validateCodeAction.do?random=' + str(random.random())[:-1]
    login_url = 'http://jw.bhu.edu.cn/loginAction.do'
    img = s.get(vcode_url)
    with open('vcode.jpg', 'wb') as f:
        f.write(img.content)
    print('请查看当前路径下 vcode.jpg 验证码图像，输入验证码按回车继续...\n')
    code = input()
    login_data = dict(zjh=USR, mm=PWD, v_yzm=code)
    res = s.post(login_url, data=login_data)
    if 'top.jsp' in res.text:
        return s
    else:
        print("Login Fialed")

def grasp_courses(s):
    courses = dict()
    courses_url = 'http://jw.bhu.edu.cn/xkAction.do?actionType=6'
    soup = BS(s.get(courses_url).text.replace('&nbsp;', '')\
              .replace('\r\n  \r\n\t', ''), 'html.parser')
    tr_list = soup.find_all(id='user')[1].find_all('tr')[1:] # del table header
    cid = ''
    for tr in tr_list:
        td = [ td.text.strip() for td in tr.find_all('td')]
        if len(td) != 7: # new course
            cid = td[1]
            courses[cid] = {'summary': td[2],
                            'teacher': td[7][:-1], # del char '* '
                            'timetable': list()}
            courses[cid]['timetable'].append({
                'weeks': td[12][:-1].replace('周', '').replace('上', ''),
                'week': int(td[13]),
                'section': int(td[14]),
                'repeat': int(td[15]),
                'loc': td[16] + td[17] + td[18]
            })
        else:
            courses[cid]['timetable'].append({
                'weeks': td[0][:-1].replace('周', '').replace('上', ''),
                'week': int(td[1]),
                'section': int(td[2]),
                'repeat': int(td[3]),
                'loc': td[4] + td[5] + td[6]
            })
    return courses

def format_weeks(weeks, model='normal'):
    res = list()
    flag = ''
    if weeks.find(',') >= 0:
        flag = ','
    elif weeks.find('.') >= 0:
        flag = '.'
    if flag:
        for week in weeks.split(flag):
            if '-' in week:
                start, end = week.split('-')
                for i in range(int(start), int(end)+1):
                    if ((model == 'odd' and i % 2 == 1)
                       or (model == 'even' and i % 2 == 0)
                       or model == 'normal'):
                        res.append(i)
            else:
                res.append(int(week))
    return res

def generate_calendar(courses):
    ical = Calendar()
    for cid in courses:
        for tt in courses[cid]['timetable']:
            if '单' in tt['weeks']:
                weeks = format_weeks(tt['weeks'][:-3], 'odd')
            elif '双' in tt['weeks']:
                weeks = format_weeks(tt['weeks'][:-3], 'even')
            else:
                weeks = format_weeks(tt['weeks'])
            
            for week in weeks:
                today = TERM_START + timedelta(days=7*(week-1)+(tt['week']-1))
                dtstart = today
                dtstart +=  timedelta(hours=TIMETABLE_SCHEMA[tt['section']][0][0])
                dtstart +=  timedelta(minutes=TIMETABLE_SCHEMA[tt['section']][0][1])
                dtend = today
                dtend += timedelta(hours=TIMETABLE_SCHEMA[tt['section']+tt['repeat']-1][1][0])
                dtend += timedelta(minutes=TIMETABLE_SCHEMA[tt['section']+tt['repeat']-1][1][1])
                e = Event()
                e.add('summary', courses[cid]['summary'])
                e.add('teacher', courses[cid]['teacher'])
                e.add('location', tt['loc'])
                e.add('dtstart', dtstart)
                e.add('dtend', dtend)
                ical.add_component(e)
    return ical
                            

if __name__ == '__main__':
    cnt = 0
    print('请输入学号')
    USR = input()
    print('请输入密码')
    PWD = input()
    print('请输入开学日期，如 2018-9-27 然后按回车继续')
    y, m, d = input().split('-')
    TERM_START = datetime(int(y), int(m), int(d))
    TIMETABLE_SCHEMA = [
        None,
        ((8, 20), (9, 10)),
        ((9, 20), (10, 10)),
        ((10, 20), (11, 10)),
        ((11, 20), (12, 10)),
        ((13, 20), (14, 10)),
        ((14, 20), (15, 10)),
        ((15, 20), (16, 10)),
        ((16, 20), (17, 10))
    ]
    CLASS_STARTAT = timedelta(hours=8, minutes=20)
    CLASS_PERIOD = timedelta(hours=1)
    with login(USR, PWD) as s:
        courses = grasp_courses(s)
    pprint(courses)
    ical = generate_calendar(courses)
    with open('timetable.ics', 'wb') as f:
        f.write(ical.to_ical())
