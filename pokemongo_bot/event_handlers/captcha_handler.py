# -*- coding: utf-8 -*-
from __future__ import print_function
import time

import requests

from pokemongo_bot.event_manager import EventHandler


SITE_KEY = '6LeeTScTAAAAADqvhqVMhPpr_vB9D364Ia-1dSgK'


class CaptchaHandler(EventHandler):
    def __init__(self, bot):
        super(CaptchaHandler, self).__init__()
        self.bot = bot

    def handle_event(self, event, sender, level, formatted_msg, data):
        if event in ('pokestop_searching_too_often', 'login_successful'):
            self.bot.logger.info('Checking for captcha challenge.')

            response_dict = self.bot.api.check_challenge()
            challenge = response_dict['responses']['CHECK_CHALLENGE']
            if not challenge.get('show_challenge'):
                return
            url = challenge['challenge_url']

            if not self.bot.config.twocaptcha_token:
                self.bot.logger.warn('No 2captcha token set, not solving captcha.')
                return

            self.bot.logger.info('Creating 2captcha session for {}.'.format(url))
            response = requests.get('http://2captcha.com/in.php', params={
                'key': self.bot.config.twocaptcha_token,
                'method': 'userrecaptcha',
                'googlekey': SITE_KEY,
                'pageurl': url,
            })
            result = response.text.split('|', 1)
            if result[0] != 'OK':
                self.bot.logger.error('Failed to send captcha to 2captcha: {}'.format('|'.join(result)))
                return
            captcha_id = result[1]

            while True:
                time.sleep(10)
                response = requests.get('http://2captcha.com/res.php', params={
                    'key': self.bot.config.twocaptcha_token,
                    'action': 'get',
                    'id': captcha_id
                })
                result = response.text.split('|', 1)
                if result[0] == 'CAPCHA_NOT_READY':
                    self.bot.logger.info('2captcha reports captcha has not been solved yet.')
                    continue

                if result[0] == 'OK':
                    self.bot.logger.info('2captcha reports captcha has been solved.')
                    self.bot.api.verify_challenge(token=result[1])
                else:
                    self.bot.logger.error('Could not solve captcha: {}'.format('|'.join(result)))

                break
