from loguru import logger
from termcolor import cprint
import tldextract
import simplejson
import fire
import dns
import traceback
import time
import tempfile
from urllib.parse import urlsplit
import sys
import base64
import csv
import inspect
import json
import os
import re
import shutil
import subprocess
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def create_logfile():
    if os.path.exists(f'{os.getcwd()}/log') is False:
        os.makedirs(f'{os.getcwd()}/log')
    logger.add(sink='log/runtime.log', level='INFO', encoding='utf-8')
    logger.add(sink='log/error.log', level='ERROR', encoding='utf-8')


def get_system():
    # global suffix
    platform = sys.platform
    if platform == 'win32':
        suffix = ".exe"
        return suffix
    elif "linux" in platform:
        return ""
    else:
        print("get system type error")
        exit(1)


def makedir0(path):
    if os.path.exists(path) is False:
        os.makedirs(path)
        logger.info(f'[+] Create {path} success.')


def additional(func1):
    def init2():
        logger.info(f'[+] start {func1.__qualname__}')
        func1()
        logger.info(f'[+] finish {func1.__qualname__}')

    return init2


def to_file(filename, data: list, mmode='a'):
    # 将links记录到 result/{date}/{domain}.links.csv中
    with open(filename, mmode, encoding="utf-8") as f1:
        for i in data:
            f1.write(i + "\n")


def to_csv(filename, data: list, mmode='a'):
    # with open(f"{root}/result/{date}/{domain}.links.csv", "a", encoding="utf-8") as f1:
    with open(filename, mmode, encoding="utf-8", newline='') as f1:
        writer = csv.writer(f1)
        for row in data:
            writer.writerow(row)


# @logger.catch
def checkport(port):
    if port < 1024 or 65535 < port:
        return False
    if 'win32' == sys.platform:
        cmd = 'netstat -aon|findstr ":%s "' % port
    elif 'linux' == sys.platform:
        cmd = 'netstat -aon|grep ":%s "' % port
    else:
        logger.error('Unsupported system type %s' % sys.platform)
        return False
    with os.popen(cmd, 'r') as f:
        if '' != f.read():
            return True
        else:
            logger.error('Port %s is not open' % port)
            return False


# @logger.catch


def request0(req_json):
    proxies = {
        'http': 'http://127.0.0.1:7777',
        'https': 'http://127.0.0.1:7777',
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"}
    method0 = req_json['method']
    urls0 = req_json['url']
    headers0 = json.loads(req_json['headers']) if str(req_json['headers']).strip(
    ) != "" else headers if "headers" in req_json.keys() else ""
    data0 = req_json['data'] if "data" in req_json.keys() else ""
    try:
        if (method0 == 'GET'):
            a = requests.get(urls0, headers=headers0,
                             proxies=proxies, timeout=30, verify=False)
            # opt2File(urls0)
        elif (method0 == 'POST'):
            a = requests.post(urls0, headers=headers0, data=data0,
                              proxies=proxies, timeout=30, verify=False)
            # opt2File(urls0)
    except:
        pass


def __subprocess(cmd):
    try:
        out_temp = tempfile.TemporaryFile(mode='w+b')
        fileno = out_temp.fileno()
        p = subprocess.Popen(cmd, shell=True, stdout=fileno, stderr=fileno)
        p.wait()
        out_temp.seek(0)
        rt = out_temp.read()
        rt_list = rt.strip().split('\n')
    except Exception as e:
        logger.error(traceback.format_exc())
    finally:
        if out_temp:
            out_temp.close()

    return rt_list


@logger.catch
def __subprocess1(cmd, timeout=None, path=None):
    '''
    rad 不支持结果输出到管道所以stdout=None才可以，即默认不设置
    :param cmd:
    :param timeout:
    :param path:
    :return:
    '''
    if isinstance(cmd, str):
        cmd = cmd.split(' ')
    elif isinstance(cmd, list):
        cmd = cmd
    else:
        logger.error(
            f'[-] cmd type error,cmd should be a string or list: {cmd}')
        return
    try:
        p = subprocess.Popen(cmd, shell=True, cwd=path)
        # p = subprocess.Popen(cmd, shell=True,cwd=path,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if timeout:
            p.wait(timeout=timeout)
        else:
            p.wait()
    except Exception as e:
        logger.error(traceback.format_exc())
        # logger.error(f'{sys._getframe().f_code.co_name} Reach Set Time and exit')
    finally:
        f_name = inspect.getframeinfo(inspect.currentframe().f_back)[2]
        logger.info(f'{f_name} finished.')


# @logger.catch
def __subprocess2(cmd):
    if isinstance(cmd, str):
        cmd = cmd.split(' ')
    elif isinstance(cmd, list):
        cmd = cmd
    else:
        logger.error(
            f'[-] cmd type error,cmd should be a string or list: {cmd}')
        return
    lines = []
    try:
        out_temp = tempfile.SpooledTemporaryFile(
            max_size=10 * 1000, mode='w+b')
        fileno = out_temp.fileno()
        obj = subprocess.Popen(cmd, stdout=fileno, stderr=fileno, shell=True)
        obj.wait()
        out_temp.seek(0)
        lines = out_temp.readlines()
        # print(lines)
    except Exception as e:
        logger.error(traceback.format_exc())
    finally:
        if out_temp:
            out_temp.close()
    return lines


@logger.catch
def to_xray(urls, attackflag=None):
    if attackflag:
        if checkport(7777):
            for url in urls:
                # if url not in links_set:
                request0({"method": "GET", "url": url,
                          "headers": "", "data": ""})
                # links_set.add(url)
        else:
            logger.error("xray not running on 7777! skip to xray attack!")


@logger.catch
def manager(domain=None, url=None, urlsfile=None, attackflag=False, date="2022-09-02-00-01-39"):
    '''
    获取敏感信息
    crawlergo rad,URLFinder 爬取url，attackflag标志位设定是否传给xray进行攻击
    两种模式
        1 每个模块顺序调用到sensitiveinfo_main模块，只需传入domain即可
        2 单独使用该模块，只需传入urlsfile或url即可
    :param domain:
    :param urlsfile:
    :param attackflag: 标志位设定是否传给xray进行攻击，如果为true，记得开启xray监听127.0.0.1:7777
    :param date:
    :return:
    '''
    logger.info('-' * 10 + f'start {__file__}' + '-' * 10)
    isdomain = False
    # 两种模式,三种情况
    if domain and urlsfile is None and url is None:
        isdomain = True
        urlsfile = f"result/{date}/{domain}.subdomains.with.http.txt"
        # output_filename_prefix = domain
    elif urlsfile and domain is None and url is None:
        domain = date
        urlsfile = urlsfile
        # output_filename_prefix = domain
    elif url and domain is None and urlsfile is None:
        domain = '.'.join(part for part in tldextract.extract(url) if part)
        urlsfile = f"temp.sensitiveinfo_main.txt"
        # output_filename_prefix = domain
        with open(urlsfile, "w", encoding="utf-8") as f:
            f.write(url)

    suffix = get_system()
    root = os.getcwd()
    pwd_and_file = os.path.abspath(__file__)
    # E:\ccode\python\006_lunzi\core\tools\domain
    pwd = os.path.dirname(pwd_and_file)

    # 获取当前目录的前三级目录，即到domain目录下，来寻找exe domain目录下
    grader_father = os.path.abspath(
        os.path.dirname(pwd_and_file) + os.path.sep + "../..")
    # print(grader_father) # E:\ccode\python\006_lunzi\core
    # 存储爬取到的links，不在其中的links.csv 存储该结果
    links_set = set()

    # 创建存储工具扫描结果的文件夹
    sensitiveinfo_log_folder = f"{root}/result/{date}/sensitiveinfo_log"
    makedir0(sensitiveinfo_log_folder)

    # 初始话往result/{date}/{domain}.links.csv  写入 title
    to_csv(f"result/{date}/{domain}.links.csv",
           [["method", "url", "header", "body"]], mmode='a')

    # 爬取url的link  result/{date}/sensitiveinfo_log/{domain}.{sys._getframe().f_code.co_name}.json

    @logger.catch
    def crawlergo(data1, attackflag=attackflag):
        '''
        只能单个url,爬取网站的url,保存完整请求到json文件，并存储一份"method url"的txt
        crawlergo 0.4.3
        存储的在：{sensitiveinfo_log_folder}/{subdomain}.{sys._getframe().f_code.co_name}.json
        :return:
        '''
        logger.info(
            '-' * 10 + f'start {sys._getframe().f_code.co_name}' + '-' * 10)
        # 创建多个子域名结果输出文件夹
        output_folder = f'{sensitiveinfo_log_folder}/{sys._getframe().f_code.co_name}_log'
        makedir0(output_folder)

        target = data1
        # ExtractResult(subdomain='www', domain='worldbank', suffix='org.kg')
        subdomain_tuple = tldextract.extract(data1)
        output_filename_prefix = '.'.join(
            part for part in subdomain_tuple if part)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
        }
        # cmd = ["./crawlergo", "-c", "/usr/bin/google-chrome","-t", "10","-f","smart","--fuzz-path", "--output-mode", "json","--ignore-url-keywords", "quit,exit,logout",  "--custom-headers", simplejson.dumps(headers),"--robots-path","--log-level","debug","--push-to-proxy","http://xray_username:xray_password@xray_ip:xray_port",target]
        # cmdstr = f"crawlergo_windows_amd64_0.4.3.exe -c chrome-win/chrome.exe -t 8 -f smart --fuzz-path --robots-path --custom-headers {simplejson.dumps(headers)} --output-mode json --output-json crawlergo.json --push-to-proxy http://xray_username:xray_password@xray_ip:xray_port {target}"
        if attackflag:
            # 端口没开则直接结束
            if checkport(7777) is False:
                logger.error("Exit!!!")
                exit(1)
            proxy = "http://127.0.0.1:7777"
            cmdstr = f"{pwd}/crawlergo/crawlergo{suffix} -c {pwd}/chrome-win/chrome.exe -t 8 -f smart --fuzz-path --robots-path --output-mode json --output-json {output_folder}/{output_filename_prefix}.{sys._getframe().f_code.co_name}.json --push-to-proxy {proxy} {target}"
        else:
            cmdstr = f"{pwd}/crawlergo/crawlergo{suffix} -c {pwd}/chrome-win/chrome.exe -t 8 -f smart --fuzz-path --robots-path --output-mode json --output-json {output_folder}/{output_filename_prefix}.{sys._getframe().f_code.co_name}.json {target}"

        logger.info(f"[+] command:{cmdstr}")
        cmd = cmdstr.split(' ')
        rsp = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = rsp.communicate()
        try:
            result = simplejson.loads(
                output.decode().split("--[Mission Complete]--")[1])
        except:
            logger.error(f'[-] crawlergo get output failed: {target}')
            return

        req_list = result["req_list"]
        sub_domain_list = result["sub_domain_list"]

        with open(f"result/{date}/{domain}.links.csv", "a", encoding="utf-8", newline='') as f1:
            writer = csv.writer(f1)
            for req in req_list:
                if req['url'] not in links_set:
                    del req["headers"]["Spider-Name"]
                    writer.writerow([str(sys._getframe().f_code.co_name), req['method'],
                                     req['url'], json.dumps(req['headers']), req['data']])
                    links_set.add(req['url'])
        logger.info(f'[+] From url {target} found {len(req_list)} links')
        logger.info(
            f'[+] Links file exist:{root}/result/{date}/{domain}.links.csv')

        if sub_domain_list is not None:
            with open(f"{sensitiveinfo_log_folder}/{domain}.subdomains.{sys._getframe().f_code.co_name}.txt", "a",
                      encoding="utf-8") as f2:
                for i in sub_domain_list:
                    f2.write(i + "\n")
        logger.info(f"[+] {sys._getframe().f_code.co_name} finished: {target}")

    @logger.catch
    def rad(data1, attackflag=attackflag):
        '''
        只能单个url,爬取网站的url,保存完整请求到json文件，并存储一份"method url"的txt
        rad 0.4
        :return:
        '''
        logger.info(
            '-' * 10 + f'start {sys._getframe().f_code.co_name}' + '-' * 10)
        output_folder = f'{sensitiveinfo_log_folder}/{sys._getframe().f_code.co_name}_log'
        makedir0(output_folder)

        target = data1
        subdomain_tuple = tldextract.extract(data1)
        output_filename_prefix = '.'.join(
            part for part in subdomain_tuple if part)

        # cmd = ["rad.exe", "--http-proxy", "http://127.0.0.1:7777", "--target", target]
        # 提前删除结果文件，否则rad报错，结果文件已存在
        print(
            f"{output_folder}/{output_filename_prefix}.{sys._getframe().f_code.co_name}.json")
        if os.path.exists(f"{output_folder}/{output_filename_prefix}.{sys._getframe().f_code.co_name}.json"):
            os.remove(
                f"{output_folder}/{output_filename_prefix}.{sys._getframe().f_code.co_name}.json")
            logger.info(
                f"{output_folder}/{output_filename_prefix}.{sys._getframe().f_code.co_name}.json delete success!")
        time.sleep(2)

        proxy = "http://127.0.0.1:7777"
        if attackflag:
            # 端口没开则直接结束
            if checkport(7777) is False:
                logger.error("Exit!!!")
                exit(1)
            cmdstr = f"{pwd}/rad/rad{suffix} --target {target} --json-output {output_folder}/{output_filename_prefix}.{sys._getframe().f_code.co_name}.json --http-proxy {proxy}"
        else:
            cmdstr = f"{pwd}/rad/rad{suffix} --target {target} --json-output {output_folder}/{output_filename_prefix}.{sys._getframe().f_code.co_name}.json"
        logger.info(f"[+] command:{cmdstr}")
        # os.system(cmdstr)
        __subprocess1(cmdstr, timeout=None,
                      path=f"{pwd}/{sys._getframe().f_code.co_name}")

        urls_data_tmp_to_csv = []  # 存储urldata四个字段的列表
        # 从rad结果中获取url,不存在url的则写入csv和links_set
        with open(f"{output_folder}/{output_filename_prefix}.{sys._getframe().f_code.co_name}.json", "r",
                  encoding="utf-8", errors='ignore') as f2:
            result = json.loads(f2.read())
            for row in result:
                if row["URL"] not in links_set:
                    if row["Method"] == "GET":
                        data = [str(sys._getframe().f_code.co_name), row["Method"],
                                row["URL"], json.dumps(row["Header"]), ""]
                    elif row["Method"] == "POST":
                        # print(base64.b64decode(row["b64_body"]))
                        if 'b64_body' in row.keys():
                            data = [str(sys._getframe().f_code.co_name), row["Method"], row["URL"], json.dumps(
                                row["Header"]), base64.b64decode(row["b64_body"]).decode()]
                        else:
                            data = [str(sys._getframe().f_code.co_name), row["Method"], row["URL"], json.dumps(
                                row["Header"]), ""]
                        # data = row["Method"] + "," + row["URL"] + "," + str(row["Header"]) + "," + base64.b64decode(row["b64_body"])
                    urls_data_tmp_to_csv.append(data)
                    links_set.add(row["URL"])

        # 存储rad 爬取到的url method headers body
        # with open(f"{root}/result/{date}/{domain}.links.csv", "a", encoding="utf-8") as f1:
        to_csv(f"result/{date}/{domain}.links.csv",
               urls_data_tmp_to_csv, mmode='a')
        logger.info(f"[+] {sys._getframe().f_code.co_name} finished: {target}")

    # URLFinder爬取

    @logger.catch
    def URLFinder(data1, attackflag=attackflag):
        '''
        URLFinder v
        urlfinder 的输出结果是domain:port.csv ip:port.csv 如果有port的话
        可以单个url,爬取网站的url,保存完整请求到json文件，并存储一份"method url"的txt
        可以多个url，一个url一个csv 格式子域名.csv
        :return: jieguowenjian:new.xxx.com.cn：443.csv 中文冒号
        '''
        logger.info(
            '-' * 10 + f'start {sys._getframe().f_code.co_name}' + '-' * 10)

        # 创建多个子域名结果输出文件夹
        output_folder = f'{sensitiveinfo_log_folder}/{sys._getframe().f_code.co_name}_log'
        makedir0(output_folder)

        target = data1
        urls_data_tmp_to_csv = []
        urls_set_tmp = set()

        # 结果文件名 {subdomain}.csv {sensitiveinfo_log_folder}/URLFinder_log/{domain}.{sys._getframe().f_code.co_name}.csv
        cmdstr = f'{pwd}/URLFinder/URLFinder{suffix} -u {target} -s all -m 2 -o {output_folder}'
        logger.info(f"[+] command:{cmdstr}")
        # os.system(cmdstr)
        __subprocess1(cmdstr, timeout=None,
                      path=f"{pwd}/{sys._getframe().f_code.co_name}")
        # print(f"[+] {sys._getframe().f_code.co_name} finished: {target}")
        logger.info(f"[+] {sys._getframe().f_code.co_name} finished: {target}")

        # 对结果处理，不在links_set的就存储到link.csv中
        groups_tmp = urlsplit(target)
        output_filename = groups_tmp[1].replace(':', '：')
        if os.path.exists(f'{output_folder}/{output_filename}.csv'):
            with open(f'{output_folder}/{output_filename}.csv', 'r', encoding="utf-8", errors='ignore') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) != 0:
                        if f"URL to {groups_tmp[1].split(':')[0]}" in row[0]:
                            # num = reader.line_num
                            break
                for row in reader:
                    if len(row) != 0:
                        if row[1] == "200" and row[0] not in links_set:
                            # data = f'GET,{row[0]},,'
                            data = [str(sys._getframe().f_code.co_name),
                                    "GET", row[0], "", ""]
                            urls_data_tmp_to_csv.append(data)
                            urls_set_tmp.add(row[0])
                            links_set.add(row[0])  # links_set 增加新的
                    else:
                        break  # 在读到空行则说明结果中的子域部分解释，终止
        else:
            logger.error(
                f'URLFinder not found {output_folder}/{output_filename}.csv')

        # 差集发送给xray,攻击模式端口没,则只收集跳过发送给xray的攻击扫描
        to_xray(urls_set_tmp, attackflag=attackflag)

        # 存储rad 爬取到的url method headers body
        to_csv(f"result/{date}/{domain}.links.csv",
               urls_data_tmp_to_csv, mmode='a')

    @logger.catch
    def gospider(data1, attackflag=attackflag):
        '''
        gospider 1.7.1
        gospider.exe -S 1.txt --depth 0 --js --subs --sitemap --robots --other-source --include-subs --include-other-source  --quiet --output 1
        gospider的输出是 xx_xx_xx ip xx_xx_xx_xx 都不带端口 无后缀
        :param data1: gospider 要求url必须以http/https开头
        :param attackflag:
        :return:
        '''
        logger.info(
            '-' * 10 + f'start {sys._getframe().f_code.co_name}' + '-' * 10)
        output_folder = f'{sensitiveinfo_log_folder}/{sys._getframe().f_code.co_name}_log'
        makedir0(output_folder)

        target = data1
        if 'http://' not in target and 'https://' not in target:
            logger.error(
                f"{sys._getframe().f_code.co_name} can't run: {target} Exclude http or https")
            return
        subdomain_tuple = tldextract.extract(target)
        output_filename = '.'.join(part for part in subdomain_tuple if part).replace(
            '.', '_')  # www_baidu_com 127_0_0_1
        urls_data_tmp_to_csv = []
        urls_set_tmp = set()
        # 结果文件名 xx_xx_xx 结果是指定文件夹 --include-other-source Also include other-source's urls (still crawl and request)
        cmdstr = f'{pwd}/gospider/gospider{suffix} -s {target} --threads 10 --depth 2 --js --subs --sitemap --robots --other-source --include-subs --quiet --output {output_folder}'
        logger.info(f"[+] command:{cmdstr}")
        __subprocess1(cmdstr, timeout=60 * 15,
                      path=f"{pwd}/{sys._getframe().f_code.co_name}")

        logger.info(f"[+] {sys._getframe().f_code.co_name} finished: {target}")

        # 对结果处理，不在links_set的就存储到link.csv中
        if os.path.exists(f'{output_folder}/{output_filename}'):
            with open(f'{output_folder}/{output_filename}', 'r', encoding="utf-8", errors='ignore') as f:
                for line in f.readlines():
                    line = line.strip()
                    url = re.sub('.*? - ', '', line)
                    if url not in links_set:
                        # data = f'GET,{url},,'
                        data = [str(sys._getframe().f_code.co_name),
                                "GET", url, "", ""]
                        urls_data_tmp_to_csv.append(data)
                        urls_set_tmp.add(url)
                        links_set.add(url)

        else:
            logger.error(
                f'[-] gospider not found {output_folder}/{output_filename}')

        # 差集发送给xray,攻击模式端口没,则只收集跳过发送给xray的攻击扫描
        to_xray(urls_set_tmp, attackflag=attackflag)

        # 存储gospider 爬取到的url method headers body
        # with open(f"{root}/result/{date}/{domain}.links.csv", "a", encoding="utf-8") as f1:
        to_csv(f"result/{date}/{domain}.links.csv",
               urls_data_tmp_to_csv, mmode='a')

    @logger.catch
    def hakrawler(data1, attackflag=attackflag):
        '''
        hakrawler v 2.1 exe路径要为\反斜杠
        hakrawler.exe -u http://testphp.vulnweb.com/
        :param data1: 需要带http
        :param attackflag:
        :return:
        '''

        logger.info(
            '-' * 10 + f'start {sys._getframe().f_code.co_name}' + '-' * 10)
        output_folder = f'{sensitiveinfo_log_folder}/{sys._getframe().f_code.co_name}_log'
        makedir0(output_folder)

        target = data1
        subdomain_tuple = tldextract.extract(target)
        subdomain = '.'.join(
            part for part in subdomain_tuple if part)  # www_baidu_com
        urls_data_tmp_to_csv = []
        urls_set_tmp = set()
        # 结果文件名 xx_xx_xx 结果是指定文件夹
        cmdstr = f'{pwd}\\hakrawler\\hakrawler{suffix} -u {target} -d 4 -subs -timeout 10 -unique'
        logger.info(f"[+] command:{cmdstr}")
        # cmd = cmdstr.split(' ')
        resultlist = __subprocess2(cmdstr)
        logger.info(f"[+] {sys._getframe().f_code.co_name} finished: {target}")
        # 二进制读取结果，没有生成文件,后面将结果存储起来
        # 对结果处理，不在links_set的就存储到link.csv中
        for i in resultlist:
            url = i.decode().strip()
            if url not in links_set:
                # data = f'GET,{url},,'
                data = [str(sys._getframe().f_code.co_name),
                        "GET", url, "", ""]
                urls_data_tmp_to_csv.append(data)
                urls_set_tmp.add(url)
                links_set.add(url)

        # 差集发送给xray,攻击模式端口没,则只收集跳过发送给xray的攻击扫描
        to_xray(urls_set_tmp, attackflag=attackflag)

        # 对结果处理,新增的,不是扫描的全部结果,是剔除links_set之后的url,将结果存储到txt中
        with open(f'{output_folder}/{subdomain}.{sys._getframe().f_code.co_name}.txt', 'w', encoding='utf-8',
                  errors='ignore') as f:
            for i in urls_set_tmp:
                f.write(i + '\n')

        # 存储gospider 爬取到的url method headers body
        # with open(f"{root}/result/{date}/{domain}.links.csv", "a", encoding="utf-8") as f1:
        to_csv(f"result/{date}/{domain}.links.csv",
               urls_data_tmp_to_csv, mmode='a')

    #

    @logger.catch
    def gau(data1, attackflag=attackflag):
        '''
        gau v 2.1 2.1.2  exe路径要为\反斜杠
        gau.exe --subs --retries 2  --timeout 65 --fc 404,302 testphp.vulnweb.com --verbose --o  2.txt
        :param data1: 带不带http,都行
        :param attackflag:
        :return:
        '''

        logger.info(
            '-' * 10 + f'start {sys._getframe().f_code.co_name}' + '-' * 10)

        # 创建多个子域名结果输出文件夹
        output_folder = f'{sensitiveinfo_log_folder}/{sys._getframe().f_code.co_name}_log'
        makedir0(output_folder)

        target = urlsplit(data1)[1]
        # subdomain_tuple = tldextract.extract(target)
        # subdomain = '.'.join(part for part in subdomain_tuple if part)  # www_baidu_com

        urls_data_tmp_to_csv = []
        urls_set_tmp = set()
        # 结果文件名 xx_xx_xx 结果是指定文件夹
        cmdstr = f'{pwd}/gau/gau{suffix} --subs --retries 2 --fc 404,302 --verbose --o {output_folder}/{target}.{sys._getframe().f_code.co_name}.txt {target}'
        logger.info(f"[+] command:{cmdstr}")
        # cmd = cmdstr.split(' ')
        __subprocess1(cmdstr, timeout=None,
                      path=f"{pwd}/{sys._getframe().f_code.co_name}")
        logger.info(f"[+] {sys._getframe().f_code.co_name} finished: {target}")
        if os.path.exists(f'{output_folder}/{target}.txt'):
            with open(f'{output_folder}/{target}.txt', 'r', encoding='utf-8') as f:
                for line in f.readlines():
                    line = line.strip()
                    if line not in links_set:
                        data = [str(sys._getframe().f_code.co_name),
                                "GET", line, "", ""]
                        urls_data_tmp_to_csv.append(data)
                        urls_set_tmp.add(line)
                        links_set.add(line)  # links_set 增加新的

        # 差集发送给xray,攻击模式端口没,则只收集跳过发送给xray的攻击扫描
        to_xray(urls_set_tmp, attackflag=attackflag)

        # 存储gospider 爬取到的url method headers body
        # with open(f"{root}/result/{date}/{domain}.links.csv", "a", encoding="utf-8") as f1:
        to_csv(f"result/{date}/{domain}.links.csv",
               urls_data_tmp_to_csv, mmode='a')

    @logger.catch
    def urlcollector(data1):
        '''
        url-collector 20220908  exe路径
        :param data1: 需要带http
        :param attackflag:
        :return:
        '''
        logger.info(
            '-' * 10 + f'start {sys._getframe().f_code.co_name}' + '-' * 10)
        # 代理端口没开跳过
        if checkport(10809) is False:
            logger.error("proxy port 10809 not open!")
            return

        # 创建多个子域名结果输出文件夹
        output_folder = f'{sensitiveinfo_log_folder}/{sys._getframe().f_code.co_name}_log'
        makedir0(output_folder)

        target = data1
        subdomain_tuple = tldextract.extract(data1)
        subdomain = '.'.join(
            part for part in subdomain_tuple if part)  # www_baidu_com
        urls_data_tmp = []
        urls_set_tmp = set()

        dorkfile = f'{pwd}/dorks.txt'
        cmdstr = f'{pwd}/urlcollector/urlcollector{suffix} -i {dorkfile} -o {output_folder}/{domain}.txt --routine-count 5 --proxy "http://127.0.0.1:10809"'
        logger.info(f"[+] command:{cmdstr}")
        resultlist = __subprocess2(cmdstr)
        logger.info(f"[+] {sys._getframe().f_code.co_name} finished: {target}")
        # 二进制读取结果，没有生成文件
        # 对结果处理，不在links_set的就存储到link.csv中
        for i in resultlist:
            url = i.decode().strip()
            urls_set_tmp.add(url)
            if url not in links_set:
                data = f'GET,{url},,'
                urls_data_tmp.append(data)
                links_set.add(url)

                if attackflag:
                    if checkport(7777):
                        request0({"method": "GET", "url": url,
                                  "headers": "", "data": ""})
                    else:
                        logger.error(
                            "xray not running on 7777! skip to xray attack!")
        # 对结果处理,将结果存储到txt中
        with open(f'{output_folder}/{subdomain}.txt', 'w', encoding='utf-8', errors='ignore') as f:
            for i in urls_set_tmp:
                f.write(i + '\n')

        # 存储gospider 爬取到的url method headers body
        # with open(f"{root}/result/{date}/{domain}.links.csv", "a", encoding="utf-8") as f1:
        with open(f"result/{date}/{domain}.links.csv", "a", encoding="utf-8") as f1:
            for i in urls_data_tmp:
                f1.write(i + "\n")

    @logger.catch
    def emailall(data1):
        '''
        emailall 20220908  exe路径
        :param data1:
        :return:
        '''
        logger.info(
            '-' * 10 + f'start {sys._getframe().f_code.co_name}' + '-' * 10)
        output_folder = f'{sensitiveinfo_log_folder}/{sys._getframe().f_code.co_name}_log'
        makedir0(output_folder)

        subdomain_tuple = tldextract.extract(data1)
        output_filename_prefix = subdomain_tuple.domain + '.' + subdomain_tuple.suffix
        cmdstr = f'python3 {pwd}/emailall/emailall.py --domain {data1} run'
        logger.info(f"[+] command:{cmdstr}")
        # os.system(cmdstr)
        __subprocess1(cmdstr, timeout=None,
                      path=f"{pwd}/{sys._getframe().f_code.co_name}")

        # 移动结果文件 \sensitiveinfo\emailall\result\vulweb_com\vulweb.com_All.json
        output_filename_tmp = f"{pwd}/{sys._getframe().f_code.co_name}/result/{output_filename_prefix.replace('.', '_')}/{output_filename_prefix}_All.json"
        if os.path.exists(output_filename_tmp):
            try:
                shutil.copy(output_filename_tmp, output_folder)
            except Exception as e:
                logger.error(traceback.format_exc())
        else:
            logger.error(
                f'[-] {sys._getframe().f_code.co_name} not found {output_filename_tmp} ')

    # if domain and url is None and urlsfile is None:
    if isdomain:
        emailall(domain)
    with open(urlsfile, "r", encoding="utf-8") as f:
        for url in f.readlines():
            url = url.strip()
            print(url)
            crawlergo(url, attackflag=attackflag)
            rad(url, attackflag=attackflag)
            hakrawler(url, attackflag=attackflag)
            gospider(url, attackflag=attackflag)
            gau(url, attackflag=attackflag)
            URLFinder(url, attackflag=attackflag)
            # urlcollector('未完成')
            links_set.clear()
            # dirsearch(url.strip())
            # dirsearch(url.strip())


@logger.catch
def run(url=None, urlfile=None, attack=False, date=None):
    '''
    usage:

        python main.py --url xxx.com
        python main.py --urlfile urls.txt
        python main.py --url xxx.com --attack True  记得开xray监听

    :param str  url:     One url
    :param str  urlfile:    File path of urlsfile per line
    :return:
    '''
    create_logfile()
    import datetime
    date1 = str(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
    date = date if date else date1
    if url and urlfile is None:
        manager(domain=None, url=url, urlsfile=None,
                attackflag=attack, date=date)
    elif urlfile and url is None:
        if os.path.exists(urlfile):
            manager(domain=None, url=None, urlsfile=urlfile,
                    attackflag=attack, date=date)
        else:
            logger.error(f'{urlfile} not found!')
    else:
        logger.error(
            "Please check --url or --urlfile\nCheck that the parameters are correct.")


if __name__ == '__main__':
    fire.Fire(run)