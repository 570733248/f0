# coding=utf-8
import datetime
import json
import math
import time

import requests

import WrSignal
# import getCookies
import utils
from computThread import myThread
# from jdbc import jdbc
from decimal import *
# from aliyunsdkcore.client import AcsClient
# from aliyunsdkcore.request import CommonRequest
from jdbc1 import MySqLHelper
from rizhi import log_jilu
from rizhi import content_jilu


class bfGetUrlListTennis():
    def __init__(self):
        self.session = requests.session()
        # 从模拟浏览器中获取cookie
        # cookies = getCookies.getCookies().get_bf_cookies()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Connection": "keep-alive",
            # "Cookie":cookies,
            "Cookie": "Cookie: vid=a857326b-532f-48f6-b510-20bb096daed7; bfsd=ts=1626061967954|st=rp; storageSSC=lsSSC%3D1%3Bcookie-policy%3D1; betexPtk=betexLocale%3Den%7EbetexRegion%3DIRL; language=en; exp=ex; __cf_bm=2a341cb1429bd265ce3bb8bb2132f513c524f0c7-1626061972-1800-ASM7JfsRuQzmW/nsouu4GDyOkwF9oWunvpCvXAG1/VC5Dy1etmJeB4LjGKdfTX/LeQ9BaQfeTgh2PLKSXMQwu4g=; exp=ex",
        }

        self.select_value =[]
        pass
    '''
        @summary: 请求所有的比赛id
    '''
    def getMarketIdList(self):
        # nzIFcwyWhrlwYMrh    这个参数目前不确定是否固定
        WrSignal.write()
        targetURL = "https://scan-inbf.betfair.com.au/www/sports/navigation/facet/v1/search?_ak=nzIFcwyWhrlwYMrh&alt=json"


        req_json = {"filter":{"marketBettingTypes":["ASIAN_HANDICAP_SINGLE_LINE","ASIAN_HANDICAP_DOUBLE_LINE","ODDS"],"productTypes":["EXCHANGE"],"marketTypeCodes":["MATCH_ODDS","MATCH_ODDS_UNMANAGED","MONEYLINE","MONEY_LINE"],"selectBy":"RANK","contentGroup":{"language":"en","regionCode":"NZAUS"},"turnInPlayEnabled":"true","maxResults":0,"eventTypeIds":[2]},"facets":[{"type":"EVENT_TYPE","skipValues":0,"maxValues":10,"next":{"type":"COMPETITION","skipValues":0,"maxValues":5,"next":{"type":"EVENT","skipValues":0,"maxValues":10,"next":{"type":"MARKET","maxValues":1,"next":{"type":"COMPETITION","maxValues":1}}}}}],"currencyCode":"AUD","locale":"en"}
        # req_json = {
        #     "filter": {"marketBettingTypes": ["ASIAN_HANDICAP_SINGLE_LINE", "ASIAN_HANDICAP_DOUBLE_LINE", "ODDS"],
        #                "productTypes": ["EXCHANGE"],
        #                "marketTypeCodes": ["MATCH_ODDS", "MATCH_ODDS_UNMANAGED", "MONEYLINE", "MONEY_LINE"],
        #                "selectBy": "FIRST_TO_START_AZ", "contentGroup": {"language": "en", "regionCode": "ASIA"},
        #                "turnInPlayEnabled": "true", "maxResults": 0, "marketStartingBefore": "{}"
        #             .format((datetime.datetime.now()+datetime.timedelta(hours=-1)).strftime("%Y-%m-%dT%H:00:00.000Z")), "eventTypeIds": [7522]},
        #     "facets": [{"type": "EVENT_TYPE", "skipValues": 0, "maxValues": 10,
        #                 "next": {"type": "EVENT", "skipValues": 0, "maxValues": 50,
        #                          "next": {"type": "MARKET", "maxValues": 1,
        #                                   "next": {"type": "COMPETITION", "maxValues": 1}}}}], "currencyCode": "GBP",
        #     "locale": "en_GB"}
        try:
            resp = self.session.post(url=targetURL,json=req_json,timeout=8)
        except Exception as e:
            print("getMarketIdList超时")
            return self.getMarketIdList()
        print('Market状态码: ',resp.status_code)
        resp.encoding = 'utf-8'
        req_data = json.loads(resp.content.decode())
        # print(req_data)
        MarketIdList = self.jsonMarketIdList(req_data)


        try:
            self.getMatchInformation(MarketIdList, 0)
        except Exception as e:
            log_jilu("getMatchInformation"+e.__str__())
            content_jilu("getMatchInformation--- @@@@"+resp.text)
            print("异常处",e.__str__())
        return

    '''
        @summary: 请求比赛id的结果解析 查看是否是已开赛的和当天的比赛
        @return: id的字典
    '''
    def jsonMarketIdList(self,data):
        market_lists = data["attachments"]["markets"]
        eventId_list = {}
        for market in market_lists:
            # 状态 是否已经开赛
            status = market_lists[market]['inplay']
            if not status:
                # 比赛的id
                eventId = market_lists[market]['eventId']
                # 以前的老id
                marketId = market_lists[market]['marketId']
                marketTime = market_lists[market]['marketTime']
                openTime = datetime.datetime.strptime(marketTime, '%Y-%m-%dT%H:%M:%S.000Z') + datetime.timedelta(
                    hours=8)  # 开赛时间
                isToday = self.is_today(str(openTime))
                openTimeStamp = int(time.mktime(openTime.timetuple()))
                localTimeStamp = int(time.time())
                Diff = openTimeStamp - localTimeStamp
                if isToday == False and Diff > 900:
                    pass
                else:
                    eventId_list[marketId] = eventId
                #时间暂时先不在这里获取
        return eventId_list


    '''
    @summary: 获取比赛的信息和赔率。。。
    '''
    def getMatchInformation(self,eventIdList,indexs):
        db = MySqLHelper()
        select_v_sql = "SELECT a.id FROM `m_testing` AS a INNER JOIN m_list AS b WHERE a.m_list_id = b.id AND b.m_type_id =  2"
        cursors = db.selectall(select_v_sql)
        self.select_value = list(cursors)  # 查询出来数据库中的所有实时的比赛
        print('数据库中的实时比赛:', self.select_value)
        biduiindex = 0
        print('网球数据长度',len(eventIdList))
        for key in eventIdList:
            if indexs == biduiindex:
                WrSignal.write()
                informationUrl = "https://ips.betfair.com/inplayservice/v1/eventDetails?_ak=nzIFcwyWhrlwYMrh&alt=json&eventIds={}&locale=en_GB&productType=EXCHANGE&regionCode=ASIA".format(
                    eventIdList[key])
                oddDataUrl = "https://ero.betfair.com/www/sports/exchange/readonly/v1/bymarket?_ak=nzIFcwyWhrlwYMrh&alt=json&currencyCode=GBP&locale=en_GB&marketIds={}&rollupLimit=10&rollupModel=STAKE&types=MARKET_STATE,RUNNER_STATE,RUNNER_EXCHANGE_PRICES_BEST".format(
                    key
                )
                print(informationUrl)
                try:
                    informationResp = self.session.get(informationUrl,timeout=8)
                except Exception as e:
                    print("informationResp超时")
                    log_jilu("informationResp超时")
                    return self.getMatchInformation(eventIdList,indexs)
                print('informationUrl状态码: ', informationResp.status_code)
                informationResp.encoding = 'utf-8'
                reps_information = json.loads(informationResp.content.decode())
                print(reps_information)
                valid_competitions=    valid_competitions = ['ATP', 'WTA', 'Roland Garros']  # 需要爬取的比赛类型
                print('比赛是否开始：',reps_information[0]['inPlayBettingStatus'])
                print('赛事名称：',reps_information[0]['competitionName'])
                if len(reps_information)!=0 and reps_information[0]['inPlayBettingStatus'] != 'InPlay' and any(competition in reps_information[0]['competitionName'] for competition in valid_competitions):
                    competitionName = reps_information[0]['competitionName']  # 联赛名
                    eventTypeId = reps_information[0]['eventTypeId']    # 类型  篮球？足球
                    eventName = reps_information[0]['eventName']  # 比赛 name v name
                    startTime = reps_information[0]['startTime']  # 开赛时间  需要进行处理
                    homeName = reps_information[0]['homeName']  # 主队
                    awayName = reps_information[0]['awayName']  # 客队
                    # TlengueID = reps_information[0]['topLevelEventId']  # 联赛id  不在这一级
                    # 判断联赛 是否是 法网
                    # if TlengueID!=30553158:
                    # if competitionName !="French Open 2021" :
                    if False :
                    #     print("打印信息")
                    #     print(competitionName)
                    #     print(eventTypeId)
                        pass
                    #     print("这个不是法网")
                    else:
                        # print("这个是法网")
                        openTime = datetime.datetime.strptime(startTime, '%Y-%m-%dT%H:%M:%S.000Z') + datetime.timedelta(
                            hours=8)  # 开赛时间 经过了转化后的北京时区
                        localtime_t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # 本地时间
                        data_list = [eventTypeId, informationUrl, openTime, indexs]
                        req_mListId = self.mListSelect(data_list)  # 计算是否可以爬取 和mlistId

                        if  req_mListId[1]==1:
                            #   获取赔率信息
                            try:
                                oddDataResp = self.session.get(oddDataUrl,timeout=10)
                            except Exception as e:
                                print("oddDataResp超时")
                                log_jilu("oddDataResp超时")
                                return self.getMatchInformation(eventIdList, indexs)
                            print('oddDataResp状态码: ', oddDataResp.status_code)
                            oddDataResp.encoding = 'utf-8'
                            print(oddDataResp.text)
                            reps_oddData = json.loads(oddDataResp.content.decode())
                            usd = Decimal(float(reps_oddData['eventTypes'][0]['eventNodes'][0]['marketNodes'][0]['state']['totalMatched'])).quantize(Decimal('0'))   # 成交量
                            try:
                                oneBack = reps_oddData['eventTypes'][0]['eventNodes'][0]['marketNodes'][0]['runners'][0]['exchange'][
                                    'availableToBack']  # 第一行的 back
                            except Exception:
                                oneBack = []
                                log_jilu("oneBack空")
                                content_jilu("oneBack--- @@@@" + oddDataResp.text)
                            try:
                                oneLay = reps_oddData['eventTypes'][0]['eventNodes'][0]['marketNodes'][0]['runners'][0]['exchange']['availableToLay']   # 第一行的 lay
                            except Exception:
                                oneLay = []
                                log_jilu("oneLay空")
                                content_jilu("oneLay--- @@@@" + oddDataResp.text)
                            try:
                                towBack = reps_oddData['eventTypes'][0]['eventNodes'][0]['marketNodes'][0]['runners'][1]['exchange']['availableToBack'] # 第二行的 back
                            except Exception:
                                towBack = []
                                log_jilu("towBack空")
                                content_jilu("towBack--- @@@@" + oddDataResp.text)
                            try:
                                towLay = reps_oddData['eventTypes'][0]['eventNodes'][0]['marketNodes'][0]['runners'][1]['exchange']['availableToLay'] # 第二行的 lay
                            except Exception:
                                towLay = []
                                log_jilu("towLay空")
                                content_jilu("towLay --- @@@@" + oddDataResp.text)

                            try:
                                price_b1 = oneBack[2]['price']
                                size_b1 = math.floor(float(oneBack[2]['size']))
                            except IndexError:
                                price_b1 = 0
                                size_b1=0
                            try:
                                price_b2 = oneBack[1]['price']
                                size_b2 = math.floor(float(oneBack[1]['size']))
                            except IndexError:
                                price_b2 = 0
                                size_b2 = 0
                            try:
                                price_b3 = oneBack[0]['price']
                                size_b3 = math.floor(float(oneBack[0]['size']))
                            except IndexError:
                                price_b3 = 0
                                size_b3 = 0
                            try:
                                price_r1 = oneLay[0]['price']
                                size_r1 = math.floor(float(oneLay[0]['size']))
                            except IndexError:
                                price_r1 = 0
                                size_r1 = 0
                            try:
                                price_r2 = oneLay[1]['price']
                                size_r2 = math.floor(float(oneLay[1]['size']))
                            except IndexError:
                                price_r2 = 0
                                size_r2 = 0
                                pass
                            try:
                                price_r3 = oneLay[2]['price']
                                size_r3 = math.floor(float(oneLay[2]['size']))
                            except IndexError:
                                price_r3 = 0
                                size_r3 = 0
                                pass
                            try:
                                price_cb1 = towBack[2]['price']
                                size_cb1 = math.floor(float(towBack[2]['size']))
                            except IndexError:
                                price_cb1=0
                                size_cb1=0
                                pass
                            try:
                                price_cb2 = towBack[1]['price']
                                size_cb2 = math.floor(float(towBack[1]['size']))
                            except IndexError:
                                price_cb2 = 0
                                size_cb2 = 0
                                pass
                            try:
                                price_cb3 = towBack[0]['price']
                                size_cb3 = math.floor(float(towBack[0]['size']))
                            except IndexError:
                                price_cb3 = 0
                                size_cb3 = 0
                                pass
                            try:
                                price_cr1 = towLay[0]['price']
                                size_cr1 = math.floor(float(towLay[0]['size']))
                            except IndexError:
                                price_cr1 = 0
                                size_cr1 = 0
                            try:
                                price_cr2 = towLay[1]['price']
                                size_cr2 = math.floor(float(towLay[1]['size']))
                            except IndexError:
                                price_cr2 = 0
                                size_cr2 = 0
                            try:
                                price_cr3 = towLay[2]['price']
                                size_cr3 = math.floor(float(towLay[2]['size']))
                            except IndexError:
                                price_cr3 = 0
                                size_cr3 = 0
                            # 处理组合时间
                            localTimeStamp = int(time.time())   #本地的时间戳
                            openTimeStamp = int(time.mktime(openTime.timetuple()))  #开赛时间戳
                            otherStyleTime = time.strftime("%H:%M", time.localtime(openTimeStamp))
                            otherStyleTi = time.strftime("%a %b %d, %H:%M", time.localtime(openTimeStamp))
                            openDiff = openTimeStamp - localTimeStamp
                            if openDiff>3600:
                                playtime = "Today {}".format(otherStyleTime)
                            elif openDiff <180:
                                playtime = "Starting soon"
                            else:
                                playtime = "Starting in {}".format(math.floor(openDiff/60))
                            if req_mListId[1]==1:
                                lists = [0, req_mListId[0], competitionName, homeName,
                                         awayName, usd, price_b1, price_b2, price_b3, price_r1, price_r2, price_r3, price_cb1, price_cb2, price_cb3, price_cr1, price_cr2, price_cr3, size_b1,
                                         size_b2,
                                         size_b3, size_r1, size_r2, size_r3, size_cb1, size_cb2, size_cb3,
                                         size_cr1, size_cr2, size_cr3, playtime, localtime_t]
                                ut = utils.utils(lists)
                                valuess = ut.p()
                                list_coluor = ut.z()
                                new_h = list_coluor[0]
                                new_v = list_coluor[1]
                                # 查询最新的一条
                                up_coluor = ut.z1(usd)
                                if up_coluor != None:
                                    old_h = up_coluor[0]
                                    old_v = up_coluor[1]

                                    value_h = new_h - old_h
                                    value_v = new_v - old_v

                                    # odd_chan
                                    if value_h == value_v:
                                        value_change = 0
                                        odd_chan = 0
                                    else:
                                        if value_h > 0 and value_h > value_v:
                                            value_change = 1
                                        elif value_h < 0 and value_h < value_v:
                                            value_change = -1
                                        elif value_h > 0 and value_h < value_v:
                                            value_change = -1
                                        elif value_h < 0 and value_h > value_v:
                                            value_change = 1
                                        elif value_h == 0 and value_v < 0:
                                            value_change = 1
                                        elif value_h == 0 and value_v > 0:
                                            value_change = -1
                                        else:
                                            value_change = 0

                                        if value_v > 0 and value_v > value_h:
                                            odd_chan = 1
                                        elif value_v < 0 and value_v < value_h:
                                            odd_chan = -1
                                        elif value_v > 0 and value_v < value_h:
                                            odd_chan = -1
                                        elif value_v < 0 and value_v > value_h:
                                            odd_chan = 1
                                        elif value_v == 0 and value_h < 0:
                                            odd_chan = 1
                                        elif value_v == 0 and value_h > 0:
                                            odd_chan = -1
                                        else:
                                            odd_chan = 0
                                else:
                                    value_change = 0
                                    odd_chan = 0
                                # cc的判断
                                if (new_v - new_h) > 2 or (new_h == 0 and new_v == 2):
                                    if value_change == -1 or value_change == 0:
                                        # -1蓝色 深色 大箭头
                                        cc = -1
                                    else:
                                        # -2蓝色 浅色 大箭头
                                        cc = -2
                                elif new_v > new_h:
                                    if value_change == -1 or value_change == 0:
                                        # -3蓝色 深色 小箭头
                                        cc = -3
                                    else:
                                        # -4蓝色 浅色 小箭头
                                        cc = -4
                                elif (new_h - new_v) > 2 or (new_v == 0 and new_h == 2):
                                    if odd_chan == -1 or odd_chan == 0:
                                        # 1红色 深色 大箭头
                                        cc = 1
                                    else:
                                        # 2红色 浅色 大箭头
                                        cc = 2
                                elif new_h > new_v:
                                    if odd_chan == -1 or odd_chan == 0:
                                        # 3红色 深色 小箭头
                                        cc = 3
                                    else:
                                        # 4红色 浅色 小箭头
                                        cc = 4
                                else:
                                    cc = 0
                                # 去点特殊字符
                                league = competitionName.replace('\'', '')
                                h_name = homeName.replace('\'', '')
                                v_name = awayName.replace('\'', '')
                                # 查询m_list中的lengid是否存在 绑定
                                select_lengue = "SELECT id FROM m_league WHERE league = '{}'".format(league)
                                lengue_ids = db.selectone(select_lengue)
                                if lengue_ids == None:
                                    insert_lengue = "INSERT INTO m_league(league,m_type_id) VALUES ('{}',{})".format(league,
                                                                                                                     req_mListId[2])
                                    lengue_id = db.zhix(insert_lengue)
                                else:
                                    lengue_id = lengue_ids[0]
                                # select_m_list = "SELECT m_list.m_league_id FROM m_list WHERE id = {}".format(req_mListId[0])
                                instal_data = "INSERT INTO m_match(m_list_id,league,h_name,v_name,volume,h_odds_b_1,h_odds_b_2," \
                                            "h_odds_b_3,h_odds_r_1,h_odds_r_2,h_odds_r_3,v_odds_b_1,v_odds_b_2,v_odds_b_3,v_odds_r_1,v_odds_r_2," \
                                            "v_odds_r_3,h_value_b_1,h_value_b_2,h_value_b_3,h_value_r_1,h_value_r_2,h_value_r_3,v_value_b_1,v_value_b_2,v_value_" \
                                            "b_3,v_value_r_1,v_value_r_2,v_value_r_3,opentime,getdatatime,points,is_start,h_coluor,v_coluor,value_chan,odd_chan,cc) VALUES({},'{}','{}','{}','{}','{}','{}','{}','{}','{}'," \
                                            "'{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}',{},{},{},{},{})".format(
                                    req_mListId[0], league, h_name,
                                    v_name, usd, price_b1, price_b2, price_b3, price_r1, price_r2, price_r3, price_cb1, price_cb2,
                                    price_cb3, price_cr1, price_cr2, price_cr3, size_b1,
                                    size_b2,
                                    size_b3, size_r1, size_r2, size_r3, size_cb1, size_cb2, size_cb3,
                                    size_cr1, size_cr2, size_cr3, otherStyleTi, localtime_t, valuess[0], playtime, list_coluor[0], list_coluor[1],
                                    value_change, odd_chan, cc)
                                print(instal_data)
                                db.zhix(instal_data)
                                updata_m_list = "UPDATE m_list SET m_league_id={},updatatime ='{}' WHERE id ={} ".format(
                                    lengue_id, localtime_t, req_mListId[0])
                                db.zhix(updata_m_list)
                                th = myThread(mlistid=req_mListId[0])
                                th.start()
                                # 短信推送
                                if openDiff <=900:
                                        isSendnum = 1
                                else:
                                        isSendnum = 0

                                if valuess[0] >= 60 and isSendnum == 1:
                                    select_isno_sql = "select * from m_abnormal where m_list_id={}".format(req_mListId[0])
                                    select_value = db.selectone(select_isno_sql)
                                    if select_value == None:
                                        insert_sql = "INSERT INTO m_abnormal(m_list_id) VALUES ({})".format(req_mListId[0])
                                        localtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                                        text = "打印时间：" + localtime + "联赛：" + valuess[2] + "队伍：" + valuess[1] + "开赛时间：" + valuess[
                                            3] + "计算分数：{}".format(valuess[0]) + "赔率：{}\n".format(valuess[4])
                                        print(text)

                                        f = open('match.txt', 'a+', encoding='UTF-8')
                                        f.write(text)
                                        f.close()

                                        phonelist = ["18883523572"]
                                        # 只推送给自己
                                        # self.sms(phonelist, valuess[2], valuess[1], valuess[0], openTime)
                                        # 限制推送联赛
                                        # if lengue_id == 73:
                                        #     add_phonelist = ["15347024666"]
                                        #     self.sms(add_phonelist, valuess[2], valuess[1], valuess[0], openTime)

                                        db.zhix(insert_sql)
                        select_m_v_sql = "SELECT id FROM m_testing WHERE m_list_id ={}".format(req_mListId[0])
                        select_m_v_lsit = db.selectall(select_m_v_sql)
                        if len(select_m_v_lsit) == 0:  # 如果实时的里面没有 则添加
                            add_v_sql = "INSERT INTO m_testing (m_list_id,is_exist,gettime,opentime)  VALUES ({},{},'{}','{}')".format(
                                req_mListId[0],
                                data_list[3],
                                localtime_t, openTime)
                            db.zhix(add_v_sql)
                        else:
                            print("打印m_list_id：")
                            print(select_m_v_lsit[0][0], )
                            try:
                                print("=====================================",(select_m_v_lsit[0][0],))
                                self.select_value.remove((select_m_v_lsit[0][0],))
                            except Exception as e:
                                print(e)
                                print("删除list异常")
                                pass
                else:
                    print("警告----：没有数据")
                indexs+=1
            biduiindex+=1
        print("剩下的要删除")
        print(self.select_value)
        print("select_value" + "======================================================")
        if self.select_value != None:
            for i in self.select_value:
                del_v_sql = "DELETE FROM m_testing WHERE id = {}".format(i[0])
                db.zhix(del_v_sql)
        return
    '''
    @summary: 得到mListId 和是否可以爬取的控制
    @return: mListId,zhix,type_id
    '''
    def mListSelect(self,data_list):
        db = MySqLHelper()
        localtime_t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        localTimeStamp = int(time.time())
        if data_list[0]==7522:  #判断是属于什么比赛
            type_id = 5
        else:
            type_id = 2
        openTime = data_list[2]    # 开赛时间 经过了转化后的北京时区
        print('openTime',openTime)
        openTimeStamp = int(time.mktime(openTime.timetuple()))
        selectSql = "SELECT * FROM `m_list` WHERE m_type_id = {} AND url ='{}' ".format(type_id, data_list[1])
        select_m_list = db.selectone(selectSql)
        # =====
        if select_m_list == None:  # 如果实时比赛表中没有 则添加 有则更新 index     判断是否是新添加的数据
            install_m_list = "INSERT INTO m_list(m_type_id,url,getdatatime,updatatime) VALUES({},'{}','{}','{}')".format(
                type_id, data_list[1], localtime_t, localtime_t)
            m_list_id = db.zhix(install_m_list)
            zhix = 1
        else:
            m_list_id = int(select_m_list[0])
            updata_v_sql = "UPDATE m_testing SET is_exist={},opentime = '{}' WHERE m_list_id = {}".format(
                data_list[3], openTime, m_list_id)
            db.zhix(updata_v_sql)
            otime = str(select_m_list[6])
            d1 = datetime.datetime.strptime(otime, '%Y-%m-%d %H:%M:%S')
            d2 = datetime.datetime.strptime(localtime_t, '%Y-%m-%d %H:%M:%S')
            print(localtime_t)
            print(otime)
            delta = (d2 - d1).seconds
            openDiff = openTimeStamp - localTimeStamp
            zhix = 0
            if openDiff > 3600:
                if delta >= 600:
                    zhix = 1
            if openDiff <= 3600:
                if delta > 200:
                    zhix = 1
            if openDiff <= 1800:
                if delta > 100:
                    # print('100秒')
                    zhix = 1
            if openDiff <= 1200:
                if delta > 50:
                    # print('50秒')
                    zhix = 1
            if openDiff <= 360:
                if delta > 30:
                    # print('30秒')
                    zhix = 1
            if openDiff <= 180:
                if delta > 20:
                    # print('0.4分钟')
                    zhix = 1
        return m_list_id, zhix, type_id
    '''
        @summary: 短信服务
    '''
    # def sms(self,phonenumbers,sleague,name,pp,opentime):
    #     sleague = sleague[:20]
    #     name = name[:20]
    #     for i in phonenumbers:
    #         client = AcsClient('LTAIR3o0S5ADRi2m', 'IniJx4NX3QDZLCZmQ7aD0f3t5JR32Q', 'default')
    #         request = CommonRequest()
    #         request.set_accept_format('json')
    #         request.set_domain('dysmsapi.aliyuncs.com')
    #         request.set_method('POST')
    #         request.set_protocol_type('https')  # https | http
    #         request.set_version('2017-05-25')
    #         request.set_action_name('SendSms')
    #
    #         request.add_query_param('PhoneNumbers', "{}".format(i))
    #         request.add_query_param('SignName', "长灵")
    #         request.add_query_param('TemplateCode', "SMS_169642558")
    #         pr = "'sleague':\"{}\",'name':\"{}\",'pp':\"{}\",'opentime':\"{}\"".format(sleague,name,pp,opentime)
    #         jsons = '{%s}'%pr
    #         request.add_query_param('TemplateParam',"{}".format(jsons))
    #
    #         response = client.do_action(request)
    #         fe = open('login.txt', 'a+', encoding='UTF-8')
    #         fe.write(str(response, encoding='utf-8'))
    #         fe.write("\n")
    #         fe.close()
    #         print(str(response, encoding='utf-8'))

    """
            @summary:   判断时间是否是当天的
    """
    def is_today(self,target_date):
        c_year = datetime.datetime.now().year
        c_month = datetime.datetime.now().month
        c_day = datetime.datetime.now().day
        date_list = target_date.split(" ")[0].split("-")
        t_year = int(date_list[0])
        t_month = int(date_list[1])
        t_day = int(date_list[2])
        final = False
        if c_year == t_year and c_month == t_month and c_day == t_day:
            final = True

        return final
if __name__ == '__main__':
    bf = bfGetUrlListTennis()
    # bf.getMarketIdList()
    # bf.ttt()
    while True:
        start = time.clock()
        # write()
        bf.getMarketIdList()
        elapsed = (time.clock() - start)
        print("Time used(运行一次所用时间):", elapsed)
        if elapsed < 9:
            time.sleep(10 - int(elapsed))
