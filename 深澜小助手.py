#update 2023年3月23日15:56:54
import socket
import logging
import configparser
import time
import os

dataSource='DataSource.txt' #数据源
setting_path = "my_setting.ini" #数据列表

def generate_config():  # 从数据源生成全部数据列表
    config = configparser.ConfigParser()
    f = open(dataSource, 'r', encoding='utf-8')
    awsl=1 #行总数
    for i in f.readlines():
        namemima = i.strip().split()
        
        config['the%d' % awsl] = {'username': namemima[0],
                               'passwd': namemima[1], 
                               'srun_ip': '10.5.0.100',
                               }
        awsl=awsl+1
    f.close()
    config['Description']={'totalNumber':awsl-1,
                            'defaultStart':int(awsl/2),
                            'randomStart':True
                            }
    config['DEFAULT']=config['the1']

    print('wit...')
    with open('my_setting.ini', 'w') as configfile:
        config.write(configfile)
    print('my_setting create success!')


if bytes is str:
    input = raw_input

try:
    import requests

    def get_func(url, *args, **kwargs):
        resp = requests.get(url, *args, **kwargs)
        return resp.text

    def post_func(url, data, *args, **kwargs):
        resp = requests.post(url, data=data, *args, **kwargs)
        return resp.text

except ImportError:
    import urllib.request

    def get_func(url, *args, **kwargs):
        req = urllib.request.Request(url, *args, **kwargs)
        resp = urllib.request.urlopen(req)
        return resp.read().decode("utf-8")

    def post_func(url, data, *args, **kwargs):
        data_bytes = bytes(urllib.parse.urlencode(data), encoding='utf-8')
        req = urllib.request.Request(url, data=data_bytes, *args, **kwargs)
        resp = urllib.request.urlopen(req)
        return resp.read().decode("utf-8")


def time2date(timestamp):
    time_arry = time.localtime(int(timestamp))
    return time.strftime('%Y-%m-%d %H:%M:%S', time_arry)


def humanable_bytes(num_byte):
    num_byte = float(num_byte)
    num_GB, num_MB, num_KB = 0, 0, 0
    if num_byte >= 1024**3:
        num_GB = num_byte // (1024**3)
        num_byte -= num_GB * (1024**3)
    if num_byte >= 1024**2:
        num_MB = num_byte // (1024**2)
        num_byte -= num_MB * (1024**2)
    if num_byte >= 1024:
        num_KB = num_byte // 1024
        num_byte -= num_KB * 1024
    return '{} GB {} MB {} KB {} B'.format(num_GB, num_MB, num_KB, num_byte)


def humanable_bytes2(num_byte):
    num_byte = float(num_byte)
    if num_byte >= 1024**3:
        return '{:.2f} GB'.format(num_byte/(1024**3))
    elif num_byte >= 1024**2:
        return '{:.2f} MB'.format(num_byte/(1024**2))
    elif num_byte >= 1024**1:
        return '{:.2f} KB'.format(num_byte/(1024**1))



logging.basicConfig(
    format='%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] %(message)s',
    datefmt='## %Y-%m-%d %H:%M:%S'
)
logging.getLogger("heartbeat").setLevel(logging.INFO)
logger = logging.getLogger("heartbeat")


class SrunClient:

    name = 'UCAS'
    srun_ip = ''

    def __init__(self, username=None, passwd=None, print_log=True):
        # setting_path = "setting.ini"
        self.username = ""
        self.passwd = ""
        if os.path.exists(setting_path):
            config = configparser.ConfigParser()
            config.read(setting_path)
            self.username = config['DEFAULT']['username']
            self.passwd = config['DEFAULT']['passwd']
            self.srun_ip = config['DEFAULT']['srun_ip']
        self.login_url = 'http://{}/cgi-bin/srun_portal'.format(self.srun_ip)
        #login_url = 'http://{}/srun_portal_pc'.format(srun_ip)
        self.online_url = 'http://{}/cgi-bin/rad_user_info'.format(
            self.srun_ip)
        # headers = {'User-Agent': 'SrunClient {}'.format(name)}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.56'}
        self.print_log = print_log
        self.online_info = dict()
        self.check_online()

    # 不明觉厉的加密！！！
    def _encrypt(self, passwd):
        column_key = [0, 0, 'd', 'c', 'j', 'i', 'h', 'g']
        row_key = [
            ['6', '7', '8', '9', ':', ';', '<', '=',
                '>', '?', '@', 'A', 'B', 'C', 'D', 'E'],
            ['?', '>', 'A', '@', 'C', 'B', 'E', 'D',
                '7', '6', '9', '8', ';', ':', '=', '<'],
            ['>', '?', '@', 'A', 'B', 'C', 'D', 'E',
                '6', '7', '8', '9', ':', ';', '<', '='],
            ['=', '<', ';', ':', '9', '8', '7', '6',
                'E', 'D', 'C', 'B', 'A', '@', '?', '>'],
            ['<', '=', ':', ';', '8', '9', '6', '7',
                'D', 'E', 'B', 'C', '@', 'A', '>', '?'],
            [';', ':', '=', '<', '7', '6', '9', '8',
                'C', 'B', 'E', 'D', '?', '>', 'A', '@'],
            [':', ';', '<', '=', '6', '7', '8', '9',
                'B', 'C', 'D', 'E', '>', '?', '@', 'A'],
            ['9', '8', '7', '6', '=', '<', ';', ':',
                'A', '@', '?', '>', 'E', 'D', 'B', 'C'],
            ['8', '9', '6', '7', '<', '=', ':', ';',
                '@', 'A', '>', '?', 'D', 'E', 'B', 'C'],
            ['7', '6', '8', '9', ';', ':', '=', '<',
                '?', '>', 'A', '@', 'C', 'B', 'D', 'E'],
        ]
        encrypt_passwd = ''
        for idx, c in enumerate(passwd):
            char_c = column_key[ord(c) >> 4]
            char_r = row_key[idx % 10][ord(c) & 0xf]
            if idx % 2:
                encrypt_passwd += char_c + char_r
            else:
                encrypt_passwd += char_r + char_c
        return encrypt_passwd

    def _log(self, msg):
        if self.print_log:
            print('[SrunClient {}] {}'.format(self.name, msg))

    def check_online(self):
        resp_text = get_func(self.online_url, headers=self.headers)
        if 'not_online' in resp_text:
            self._log('###*** NOT ONLINE! ***###')
            return False
        try:
            items = resp_text.split(',')
            self.online_info = {
                'online': True, 'username': items[0],
                'login_time': items[1], 'now_time': items[2],
                'used_bytes': items[6], 'used_second': items[7],
                'ip': items[8], 'balance': items[11],
                'auth_server_version': items[21]
            }
            return True
        except Exception as e:
            print(resp_text)
            print('Catch `Status Internal Server Error`? The request is frequent!')
            print(e)

    def show_online(self):
        if not self.check_online():
            return
        self._log('###*** ONLINE INFORMATION! ***###')
        header = '================== ONLIN INFORMATION =================='
        print(header)
        print('Username: {}'.format(self.online_info['username']))
        print('Login time: {}'.format(
            time2date(self.online_info['login_time'])))
        print('Now time: {}'.format(time2date(self.online_info['now_time'])))
        print('Used data: {}'.format(
            humanable_bytes(self.online_info['used_bytes'])))
        print('Ip: {}'.format(self.online_info['ip']))
        print('Balance: {}'.format(self.online_info['balance']))
        print('=' * len(header))

    def login(self):
        if self.check_online():
            self._log('###*** ALREADY ONLINE! ***###')
            return True
        if not self.username or not self.passwd:
            self._log('###*** LOGIN FAILED! (username or passwd is None) ***###')
            self._log(
                'username and passwd are required! (check username and passwd)')
            return False
        encrypt_passwd = self._encrypt(self.passwd)
        payload = {
            'action': 'login',
            'username': self.username,
            'password': encrypt_passwd,
            'type': 2, 'n': 117,
            'drop': 0, 'pop': 0,
            'mbytes': 0, 'minutes': 0,
            'ac_id': 1
        }
        resp_text = post_func(
            self.login_url, data=payload, headers=self.headers)
        if 'login_ok' in resp_text:
            self._log('###*** LOGIN SUCCESS! ***###')
            self._log(resp_text)
            self.show_online()
            return True
        elif 'login_error' in resp_text:
            self._log('###*** LOGIN FAILED! (login error)***###')
            self._log(resp_text)
            return False
        else:
            self._log('###*** LOGIN FAILED! (unknown error) ***###')
            self._log(resp_text)
            return False

    def logout(self):
        if not self.check_online():
            return True
        payload = {
            'action': 'logout',
            'ac_id': 1,
            'username': self.online_info['username'],
            'type': 2
        }
        resp_text = post_func(
            self.login_url, data=payload, headers=self.headers)
        if 'logout_ok' in resp_text:
            self._log('###*** LOGOUT SUCCESS! ***###')
            return True
        elif 'login_error' in resp_text:
            self._log('###*** LOGOUT FAILED! (login error) ***###')
            self._log(resp_text)
            return False
        else:
            self._log('###*** LOGOUT FAILED! (unknown error) ***###')
            self._log(resp_text)
            return False

class HeartBeat:
    USERNAME = ''
    PASSWD = ''

    CHECK_SERVER = 'www.baidu.com'

    def read_config(self, a):  # 读取the[a]下的账号信息

        if os.path.exists(setting_path):

            config = configparser.ConfigParser()

            config.read(setting_path)  # 配置文件
            
            try:
                 theX=config['the%d'%a]
            except:
                 print('尝试从1开始...')
                 theX=config['the1']
            self.USERNAME = theX['username']
            self.PASSWD = theX['passwd']

            # self.USERNAME = config['the%d' % a]['username']
            # #PASSWD = config['DEFAULT']['passwd']
            # self.PASSWD = str(base64.b64decode(config['the%d' % a]['passwd']), 'utf-8')
        else:
            print('file my_setting.ini is not exists !')




    def check_connect(self):  # 连接成功时返回 0 ，连接失败时候返回编码，例如：10061
        with socket.socket() as s:
            s.settimeout(3)
            try:
                status = s.connect_ex((self.CHECK_SERVER, 443))
                return status == 0
            except Exception as e:
                print(e)
                return False

    def login(self):
        srun_client = SrunClient(print_log=False)  # 这是什么函数???
        # Use this method frequently to check online is not suggested!
        # if srun_client.check_online(): return
        logger.info('NOT ONLINE, TRY TO LOGIN!')
        srun_client.username = self.USERNAME  # 给登录对象赋值账号信息
        srun_client.passwd = self.PASSWD
        srun_client.login()  # 开始登陆函数

    def check_online(self):  # 程序起点
        
        # 异常点：无判断存在

        if os.path.exists(setting_path)==False:
            generate_config()

        config = configparser.ConfigParser()
        config.read(setting_path)  # 配置文件

        totalNumber=int(config['Description']['totalNumber'].strip())#读取总数
        randomStart=bool(config['Description']['randomStart'].strip())#读取“是否从随机处开始”
        
        # 起始点随机
        if randomStart:
            import random
            randomIndex=random.randint(1,totalNumber)
            startIndex=randomIndex
        
        # 起点处默认
        else:
            startIndex=int(config['Description']['defaultStart'].strip()) 


                
        self.read_config(startIndex)
        while not self.check_connect():  # check连接,若失败
            print('正在连接第'+str(startIndex)+'...')
            self.read_config(startIndex)
            self.login()  # 则重新login
            if(startIndex <= totalNumber):  
                startIndex = startIndex+1
            else:
                print("已到最后,现在从头开始循环...")
                startIndex = 1

        print('OVER!')
        print('Create By 夕颜.')
        input('请按任意键继续. . .')

if __name__ == "__main__":
    HeartBeat().check_online()
