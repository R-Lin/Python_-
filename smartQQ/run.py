# coding:utf8
import re
import sys
import time
import json
import ini


class SmartQQ():
    """
    A simple robot! For Fun!
    """
    def __init__(self):
        self.qtwebqq = None
        self.clientid = 53999199
        self.psessionid = ''
        self.vfwebqq = None
        self.para_dic = {}
        self.url_request = ini.get_req()
        self.log = ini.log()
        self.groupName ={}
        self.groupMember = {}
        self.url_dic = {
            'qrcode': 'https://ssl.ptlogin2.qq.com/ptqrshow?appid={0}&e=0&l=L&s=8&d=72&v=4',
            'groupNameList': 'http://s.web2.qq.com/api/get_group_name_list_mask2',
            'groupInfo': 'http://s.web2.qq.com/api/get_group_info_ext2?gcode={0}&vfwebqq={1}&t={2}',
            'pollMessage': 'http://d1.web2.qq.com/channel/poll2',
            'para': "".join((
                'https://ui.ptlogin2.qq.com/cgi-bin/login?daid=164&target=self&style=16&mibao_css=m_webqq',
                '&appid=501004106&enable_qlogin=0&no_verifyimg=1&s_url=http%3A%2F%2Fw.qq.com%2Fproxy.html&',
                'f_url=loginerroralert&strong_login=1&login_state=10&t=20131024001')),
            'check_scan': ''.join((
                'https://ssl.ptlogin2.qq.com/ptqrlogin?webqq_type=10&remember_uin=1&login2qq=1&aid={0[appid]}',
                '&u1=http%3A%2F%2Fw.qq.com%2Fproxy.html%3Flogin2qq%3D1%26webqq_type%3D10&ptredirect=0&ptlang=',
                '2052&daid=164&from_ui=1&pttype=1&dumy=&fp=loginerroralert&action=0-0-0&mibao_css={0[mibao_css]}',
                '&t=undefined&g=1&js_type=0&js_ver={0[js_ver]}&login_sig={0[sign]}&pt_randsalt=0'))}

    def downQrcode(self):
        """
         Download the Qrcode png
        """
        try:
            url = self.url_dic['qrcode'].format(
                self.para_dic['appid']
            )
            with open('qrcode.png', 'wb') as f:
                f.write(self.url_request.get(url, verify=True).content)
                self.log.info('Qrcode file is qrcode.png ! Please scan qrcode immediatety')
        except Exception as messages:
            self.log.error(messages)
            self.log.error('Webbrowser open or down failed! Please retry')
            sys.exit()

    def getPara(self):
        """
        Return a dict that contains appid, sign, js_ver, mibao_cass
        """
        html = self.url_request.get(self.url_dic['para'])
        self.para_dic['appid'] = re.findall(r'<input type="hidden" name="aid" value="(\d+)" />', html.text)[0]
        self.para_dic['sign'] = re.findall(r'g_login_sig=encodeURIComponent\("(.*?)"\)', html.text)[0]
        self.para_dic['js_ver'] = re.findall(r'g_pt_version=encodeURIComponent\("(\d+)"\)', html.text)[0]
        self.para_dic['mibao_css'] = re.findall(r'g_mibao_css=encodeURIComponent\("(.+?)"\)', html.text)[0]

    def checkLogin(self):
        """
        Loop to check the QRcode status
        """
        url = self.url_dic['check_scan'].format(self.para_dic)
        while 1:
            result = eval(self.url_request.get(url, verify=True).text[6:-3])
            self.log.info(result[4])
            if result[0] == '0':
                redirect_url = result[2]
                self.url_request.get(redirect_url)  # visit redirect_url to modify the session cookies
                break
            time.sleep(4)

        self.qtwebqq = self.url_request.cookies['ptwebqq']
        r_data = {
            'r': '{{"ptwebqq":"{0}","clientid":{1},"psessionid":"{2}","status":"online"}}'.format(
                        self.qtwebqq,
                        self.clientid,
                        self.psessionid,
                    )
        }
        self.url_request.headers['Referer'] = 'http://d1.web2.qq.com/proxy.html?v=20151105001&callback=1&id=2'
        result = json.loads(self.url_request.post( 'http://d1.web2.qq.com/channel/login2', data=r_data).text)
        self.psessionid = result['result']['psessionid']
        vfwebqq_url = "http://s.web2.qq.com/api/getvfwebqq?ptwebqq={0}&clientid={1}&psessionid={2}&t={3}".format(
                        self.qtwebqq,
                        self.clientid,
                        self.psessionid,
                        str(int(time.time()*1000))
                    )
        result2 = json.loads(self.url_request.get(vfwebqq_url).text)
        self.vfwebqq = result2['result']['vfwebqq']

    def poll(self):
        """
        Poll the messages
        """
        if not self.vfwebqq or not self.psessionid:
            self.log("Please login")
            self.login()
        else:
            data = {'r':json.dumps(
                {"ptwebqq": self.qtwebqq,
                 "clientid": self.clientid,
                 'psessionid': self.psessionid,
                 "key": ""
                 })}
            # print self.url_request.post('https://httpbin.org/post', data=data).text
            # sys.exit()
            while 1:
                try:
                    mess = json.loads(
                        self.url_request.post(self.url_dic['pollMessage'], data=data).text
                    )
                    # print mess
                    messages = mess['result'][0]['value']
                    # print messages
                    words = messages['content'][1]
                    groupid = str(messages['group_code'])
                    if groupid not in self.groupMember:
                        self.log.info('GroupId : %s is not in dict GroupName'%groupid)
                        self.groupInfo(groupid)
                    send_uid = str(messages['send_uin'])
                    print self.groupName[groupid]['name'], self.groupMember[groupid][send_uid] + ":" + words
                except KeyError as m:
                    self.log.error('KeyError: 131 lines')
                    self.log.error(m)
                    print 133,self.groupName
                    print 134, groupid, send_uid, self.groupMember
                    print mess
                except TypeError:
                    self.log.error('TypeError: 136 lines')
                    print self.groupMember[groupid][send_uid]
                except ValueError:
                    print mess, 139
                    self.log.error('TypeError: 140 lines')
                    print self.url_request.post(self.url_dic['pollMessage'], data=data).text, 141

    def groupInfo(self, groupid ):
        self.log.info("Enter function groupInfo")
        def _hash_digest(uin, ptwebqq):
            """
            提取自http://pub.idqqimg.com/smartqq/js/mq.js
            """
            N = [0, 0, 0, 0]
            for t in range(len(ptwebqq)):
                N[t % 4] ^= ord(ptwebqq[t])
            U = ["EC", "OK"]
            V = [0, 0, 0, 0]
            V[0] = int(uin) >> 24 & 255 ^ ord(U[0][0])
            V[1] = int(uin) >> 16 & 255 ^ ord(U[0][1])
            V[2] = int(uin) >> 8 & 255 ^ ord(U[1][0])
            V[3] = int(uin) & 255 ^ ord(U[1][1])
            U = [0, 0, 0, 0, 0, 0, 0, 0]
            for T in range(8):
                if T % 2 == 0:
                    U[T] = N[T >> 1]
                else:
                    U[T] = V[T >> 1]
            N = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F"]
            V = ""
            for T in range(len(U)):
                V += N[U[T] >> 4 & 15]
                V += N[U[T] & 15]
            return V

        response = self.url_request.post(
            'http://s.web2.qq.com/api/get_group_name_list_mask2',
            {
                'r': json.dumps(
                    {
                        "vfwebqq": self.vfwebqq,
                        "hash": _hash_digest('0659030105', self.qtwebqq),
                    }
                )
            },
        )
        result = json.loads(response.text)
        if result['retcode'] == 0:
            for group in result['result']['gnamelist']:
                self.groupName[str(group['gid'])] = group
                #self.groupName[group['code']] = group
                # if 'linux /shell/awk/sed' in group['name']:
                #     group_info_list = [group['code'], group['gid'], group['name']]
                #     targer_code = group['code']
                #     targer_gid = group['gid']
            # print groupid
            # print self.groupName[groupid]['gid'], self.groupName[groupid]['code'],
            self.log.info('Get groupList success!')
            stamp = time.time() * 1000
            group_id = self.groupName[groupid]['code']     # qqqun code
            tmp_dic = {}
            url = self.url_dic['groupInfo'].format(group_id, self.vfwebqq, stamp)
            try:
                member_list = json.loads(self.url_request.get(url).text)['result']['minfo']
                # print json.loads(self.url_request.get(url).text)['result']
                # print member_list
                for member in member_list:
                    tmp_dic[str(member['uin'])] = member['nick']
                self.groupMember[str(self.groupName[groupid]['gid'])] = tmp_dic
            except KeyError:
                print "KeyError The line is 187"
                print json.loads(self.url_request.get(url).text)

    def login(self):
        self.getPara()
        self.downQrcode()
        self.checkLogin()


a = SmartQQ()
a.login()
a.poll()
