import requests
from lxml import etree
import execjs
import json
import re
import time
from selenium import webdriver
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.chrome.options import Options

def logIn(username,password):
    res = requests.Session()
    url = 'https://authserver.ecupl.edu.cn/authserver/login?service=http%3A%2F%2Fyqrb.ecupl.edu.cn%2Fportal%2Findex.jsp'
    dailyurl = ''
    headers = {
        "User-Agent":"Mozilla/5.0 (Linux; Android 10; HLK-AL00 Build/HONORHLK-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.108 Mobile Safari/537.36  cpdaily/8.2.10 wisedu/8.2.10",
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "X-Requested-With":"XMLHttpRequest",
        'Content-Type': 'application/x-www-form-urlencoded'

        }
    res_resp = res.get(url=url, headers=headers)
    start_html = etree.HTML(res_resp.text, parser=etree.HTMLParser())
    lt = start_html.xpath('//*[@id="casLoginForm"]/input[1]/@value')[0]
    dllt = start_html.xpath('//*[@id="casLoginForm"]/input[2]/@value')[0]
    execution = start_html.xpath('//*[@id="casLoginForm"]/input[3]/@value')[0]
    _eventId = start_html.xpath('//*[@id="casLoginForm"]/input[4]/@value')[0]
    rmShown = start_html.xpath('//*[@id="casLoginForm"]/input[5]/@value')[0]
    pwdDefaultEncryptSalt = re.search('var pwdDefaultEncryptSalt = (.+?);',res_resp.text).group().split('=',1)[1].split('"',3)[1]
    with open('encrypt.js', 'r', encoding = 'utf-8') as f:
        js = f.read()
    ctx = execjs.compile(js)
    password = ctx.call('encryptAES', password, pwdDefaultEncryptSalt)
    print("[OK]Encrypted Password for:"+username+"\n   -Content:"+password)
    data = {
        'username': username,
        'password': password,
        'lt': lt,
        'dllt': dllt,
        'execution': execution,
        '_eventId': _eventId,
        'rmShown': rmShown,
        'rememberMe':'on'
        }
    res_resp = res.post(url=url, headers=headers, data=data)
    #print(res_resp.text)
    data2 = {
        'userid':username,
        'cmd':'CLIENT_USER_LOGIN',
        'deviceType':'pc',
        'sid':None,
        'lang':'cn'
        }
    res_resp = res.post(url='https://yqrb.ecupl.edu.cn/portal/r/jd', headers=headers, data=data2)
    sidd = json.loads(res_resp.text)['data']['sid']
    url3 = 'https://yqrb.ecupl.edu.cn/portal/r/w?cmd=com.awspaas.user.apps.datamanager_html&appId=com.awspaas.user.apps.onlineoffice&html=mobileIndex_lixin.html&sid='+sidd
    url4 = 'https://yqrb.ecupl.edu.cn/portal/r/w?cmd=CLIENT_DW_PORTAL&processGroupName=%E7%96%AB%E6%83%85%E6%97%A5%E6%8A%A5&processGroupId=obj_4ceb6be945c0425aa337b606cdbb0298&dwViewId=obj_39fc5ec612334f0dbe5c4d711f384995&sid='+sidd
    res_resp = res.post(url=url4, headers=headers)
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('blink-settings=imagesEnabled=false')
    chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    
    driver.get(url4) 
    driver.delete_all_cookies() 
    for k,v in res.cookies.items(): 
        driver.add_cookie({'name':k,'value':v})
    time.sleep(5)
    driver.switch_to.frame('pageFrame')
    processInstId = driver.find_element_by_xpath('//*[@id="processInstId"]').get_attribute('value')
    formDefId = driver.find_element_by_xpath('//*[@id="formDefId"]').get_attribute('value')
    
    oldFormData = json.loads(driver.find_element_by_xpath('//*[@id="oldFormData"]').get_attribute('value'))
    isCreate = driver.find_element_by_xpath('//*[@id="isCreate"]').get_attribute('value')
    processDefId = driver.find_element_by_xpath('//*[@id="processDefId"]').get_attribute('value')
    boId = driver.find_element_by_xpath('//*[@id="boId"]').get_attribute('value')
    boDefId = driver.find_element_by_xpath('//*[@id="boDefId"]').get_attribute('value')
    driver.quit()
    commentInfo = {"isSelected":'false',"isValidateForm":'true',"commentOption":"","commentId":"","isCommentCreate":'false',"hasFiles":'false',"setComments":'false'}
    commentInfo['processDefId']=processDefId
    formData = oldFormData
    formData['CNSM'] = '确认已认真查看，且填写信息无误'
    formData['TJZGFXQ'] = '无'
    data3 = {
        'sid':sidd,
        'cmd':'CLIENT_BPM_FORM_PAGE_P_SAVE_DATA',
        'processInstId':processInstId,
        'taskInstId':None,
        'openState':1,
        'currentPage':1,
        'formDefId':formDefId,
        'formData':json.dumps(formData),
        'boId':boId,
        'boDefId':boDefId,
        'oldFormData':oldFormData,
        'isCreate':'false',
        'commentInfo':json.dumps(commentInfo),
        'isTransact':'false',
        'isValidateForm':'true'
        }
    url_post = 'https://yqrb.ecupl.edu.cn/portal/r/jd'
    res_resp = res.post(url=url_post, headers=headers, data=data3)
    if(json.loads(res_resp.text)['result']=='ok'):
        return [username,password,True]
    else:
        return [username,password,False]

def callBack(future):
    result = future.result()
    if(result[2]==False):
        print("[FAIL]Failure:",result[0])
        future = threadPool.submit(logIn,result[0],result[1])
        print("[INFO]Resubmitted to threadpool:",result[0])
        future.add_done_callback(callBack)
    else:
        print("[OK]Success:",result[0])
        pass
    
if __name__ == '__main__':
    print("Powered by Muruan @ ZhaZiDong\n\n(C)Copyright 2020-2021 Muruan's Lazy&Easy ECUPL Toolset\n\nTime:",time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())),"\n")
    threadPool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="test_")
    f=open("userdata.txt","r",encoding='utf-8')
    acclist = json.loads(f.read())
    for account in acclist['data']:
        print("[INFO]Submitted to threadpool:",account['username'])
        future = threadPool.submit(logIn,account['username'],account['pwd'])
        future.add_done_callback(callBack)
    threadPool.shutdown(wait=True)
