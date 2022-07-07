import hashlib
import json
import time
import os

from settings import log, CONFIG, req
from notify import Notify


def hexdigest(text):
    md5 = hashlib.md5()
    md5.update(text.encode())
    return md5.hexdigest()


class Base(object):
    def __init__(self, cookies: str = None):
        if not isinstance(cookies, str):
            raise TypeError('%s want a %s but got %s' %
                            (self.__class__, type(__name__), type(cookies)))
        self._cookie = cookies

    def get_header(self):
        header = {
            'User-Agent': CONFIG.USER_AGENT,
            'Referer': CONFIG.REFERER_URL,
            'Accept-Encoding': 'gzip, deflate, br',
            'Cookie': self._cookie
        }
        return header


class Roles(Base):
    def get_awards(self):
        response = {}
        try:
            response = req.to_python(req.request(
                'get', CONFIG.REWARD_URL, headers=self.get_header()).text)
        except json.JSONDecodeError as e:
            raise Exception(e)

        return response


class Sign(Base):
    def __init__(self, cookies: str = None):
        super(Sign, self).__init__(cookies)
        self.uid = uid

    def get_header(self):
        header = super(Sign, self).get_header()
        return header

    def get_info(self):
        log.info('Ready to get check-in information...')
        info_url = CONFIG.INFO_URL
        try:
            response = req.request(
                'get', info_url, headers=self.get_header()).text
        except Exception as e:
            raise Exception(e)

        log.info('The sign-in information has been successfully acquired')
        return req.to_python(response)

    def run(self):
        info_list = self.get_info()
        message_list = []
        if info_list:
            today = info_list.get('data',{}).get('today')
            total_sign_day = info_list.get('data',{}).get('total_sign_day')
            awards = Roles(self._cookie).get_awards().get('data',{}).get('awards')
            uid = str(self.uid).replace(
                str(self.uid)[1:7], '******', 1)

            log.info(f'Preparing for traveler {uid}s sign in...')
            time.sleep(10)
            message = {
                'today': today,
                'region_name': 'EU',
                'uid': uid,
                'total_sign_day': total_sign_day,
                'end': '',
            }
            if info_list.get('data',{}).get('is_sign') is True:
                message['award_name'] = awards[total_sign_day - 1]['name']
                message['award_cnt'] = awards[total_sign_day - 1]['cnt']
                message['status'] = f"👀 Traveler! You've already checked in today"
                message_list.append(self.message.format(**message))
                return ''.join(message_list)
            else:
                message['award_name'] = awards[total_sign_day]['name']
                message['award_cnt'] = awards[total_sign_day]['cnt']
            if info_list.get('data',{}).get('first_bind') is True:
                message['status'] = f'💪 Please check in manually once'
                message_list.append(self.message.format(**message))
                return ''.join(message_list)

            data = {
                'act_id': CONFIG.ACT_ID
            }

            try:
                response = req.to_python(req.request(
                    'post', CONFIG.SIGN_URL, headers=self.get_header(),
                    data=json.dumps(data, ensure_ascii=False)).text)
            except Exception as e:
                raise Exception(e)
            code = response.get('retcode', 99999)
            # 0:      success
            # -5003:  already checked in
            if code != 0:
                message_list.append(response)
                return ''.join(message_list)
            message['total_sign_day'] = total_sign_day + 1
            message['status'] = response['message']
            message_list.append(self.message.format(**message))
        log.info('Check in')

        return ''.join(message_list)

    @property
    def message(self):
        return CONFIG.MESSAGE_TEMPLATE


if __name__ == '__main__':
    log.info(f'🌀 Genshin Impact Helper')
    log.info('If you fail to check in, please try to update and check the logs!')
    log.info('Workflow starting...')
    notify = Notify()
    msg_list = []
    ret = success_num = fail_num = 0
    # GitHub Actions Users Please go to the settings-> secrets of the REPO to set the variable, the variable name must be completely consistent with the above parameter variable name, otherwise it will be invalid !!!
    # Name = <Variable Name>, value = <Get Value>
    COOKIE = ''

    if os.environ.get('COOKIE', '') != '':
        COOKIE = os.environ['COOKIE']

    cookie_list = COOKIE.split('#')
    log.info(f'Configured Account(s) {len(cookie_list)}')
    for i in range(len(cookie_list)):
        log.info(f'Ready for Account NO.{i + 1} check in...')
        try:
            ltoken = cookie_list[i].split('ltoken=')[1].split(';')[0]
            uid = cookie_list[i].split('ltuid=')[1].split(';')[0]
            msg = f'Account NO.{i + 1} {Sign(cookie_list[i]).run()}'
            msg_list.append(msg)
            success_num = success_num + 1
        except Exception as e:
            msg = f'Account NO.{i + 1}\n    {e}'
            msg_list.append(msg)
            fail_num = fail_num + 1
            log.error(msg)
            ret = -1
        continue
    notify.send(status=f'Success: {success_num} | Failure: {fail_num}', msg=msg_list)
    if ret != 0:
        log.error('Error: Abnormal exit. Please check the logs.')
        exit(ret)
    log.info('Workflow ended successfully! 🎉')

