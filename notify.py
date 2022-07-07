import os

from settings import log, req


class Notify(object):
    """
    Push all in one
        :param TG_BOT_API: Telegram Bot's api address, used to reverse the proxy Telegram API address.
        :param TG_BOT_TOKEN: Telegram Bot token. Generated when applying for bot from bot father.
        :param TG_USER_ID: The user ID of the Telegram push object.
    """
    # For GitHub Actions: Use the variable in the settings -> secrets of the REPO, and the variable name must be completely consistent with the above parameter variable name, otherwise it will be invalid!!!
    # Name = <Variable Name>, value = <Get Value>
    # Telegram Bot
    TG_BOT_API = 'api.telegram.org'
    TG_BOT_TOKEN = ''
    TG_USER_ID = ''

    def pushTemplate(self, method, url, params=None, data=None, json=None, headers=None, **kwargs):
        name = kwargs.get('name')
        # needs = kwargs.get('needs')
        token = kwargs.get('token')
        text = kwargs.get('text')
        code = kwargs.get('code')
        if not token:
            log.info(f'{name} 🚫')
            return
        try:
            response = req.to_python(req.request(
                method, url, 2, params, data, json, headers).text)
            rspcode = response[text]
        except Exception as e:
            # 🚫:disabled; 🥳:success; 😳:fail;
            log.error(f'{name} 😳\n{e}')
        else:
            if rspcode == code:
                log.info(f'{name} 🥳')
            # Telegram Bot
            elif name == 'Telegram Bot' and rspcode:
                log.info(f'{name} 🥳')
            elif name == 'Telegram Bot' and response[code] == 400:
                log.error(f'{name} 😳\n Please take the initiative bot, send a message and check if the TG_USER_ID is right or not')
            elif name == 'Telegram Bot' and response[code] == 401:
                log.error(f'{name} 😳\nTG_BOT_TOKEN error')
            else:
                log.error(f'{name} 😳\n{response}')

    def tgBot(self, text, status, desp):
        TG_BOT_TOKEN = self.TG_BOT_TOKEN
        if 'TG_BOT_TOKEN' in os.environ:
            TG_BOT_TOKEN = os.environ['TG_BOT_TOKEN']

        TG_USER_ID = self.TG_USER_ID
        if 'TG_USER_ID' in os.environ:
            TG_USER_ID = os.environ['TG_USER_ID']

        token = ''
        if TG_BOT_TOKEN and TG_USER_ID:
            token = 'token'

        TG_BOT_API = self.TG_BOT_API
        if 'TG_BOT_API' in os.environ:
            TG_BOT_API = os.environ['TG_BOT_API']

        url = f'https://{TG_BOT_API}/bot{TG_BOT_TOKEN}/sendMessage'
        data = {
            'chat_id': TG_USER_ID,
            'text': f'*{text}*\n_{status}_\n\n{desp}',
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        conf = ['Telegram Bot', 'TG_BOT_TOKEN and TG_USER_ID', token, 'ok', 'error_code']
        name, needs, token, text, code  = conf

        return self.pushTemplate('post', url, data=data, name=name, needs=needs, token=token, text=text, code=code)

    def send(self, **kwargs):
        app = 'Genshin Impact Helper'
        status = kwargs.get('status', '')
        msg = kwargs.get('msg', '')
        hide = kwargs.get('hide', '')
        if isinstance(msg, list) or isinstance(msg, dict):
            msg = '\n\n'.join(msg)
        if not hide:
            log.info(f'Sign-in: {status}\n\n{msg}')
        log.info('Ready to send notification(s)...')

        self.tgBot(app, status, msg)


if __name__ == '__main__':
    Notify().send(app='Genshin Impact Helper', status='Sign-in', msg='Details')
