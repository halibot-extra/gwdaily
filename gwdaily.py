import json
import urllib.request
import asyncio
import time
from threading import Thread
from halibot import HalModule, Message

class GwApi:

    @staticmethod
    def _get(url):
        resp = urllib.request.urlopen(url)
        return json.loads(resp.readall().decode('utf-8'))

    @staticmethod
    def dailies():
        return GwApi._get('https://api.guildwars2.com/v2/achievements/daily')

    @staticmethod
    def achievement(num):
        return GwApi._get('https://api.guildwars2.com/v2/achievements/' + str(num))

class GwDaily(HalModule):

    options = {
        'show_pve': {
            'type'    : 'bool',
            'prompt'  : 'Show PvE dailies',
            'default' : 'true',
        },
        'show_pvp': {
            'type'    : 'bool',
            'prompt'  : 'Show PvP dailies',
            'default' : 'true',
        },
        'show_wvw': {
            'type'    : 'bool',
            'prompt'  : 'Show WvW dailies',
            'default' : 'true',
        },
        'show_special': {
            'type'    : 'bool',
            'prompt'  : 'Show special dailies',
            'default' : 'true',
        },
        'rate_limit': {
            'type'    : 'int',
            'prompt'  : 'Rate limit in seconds',
            'default' : 1,
        },
        'dest': {
            'type'    : 'string',
            'prompt'  : 'Output destination',
        },
        'format': {
            'type'    : 'string',
            'prompt'  : 'Output format',
            'default' : 'Guild wars {name}',
        },
    }

    SECONDS_IN_DAY = 24 * 60 * 60

    def init(self):
        self.loop = asyncio.SelectorEventLoop()
        self.thread = Thread(target=self.loop.run_forever)
        self.thread.start()
        self.schedule_next()

    def shutdown(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()

    def schedule_next(self):
        self.loop.call_soon_threadsafe(self.loop.call_later, self.SECONDS_IN_DAY, self.get_dailies)

    def get_dailies(self):
        dailies = GwApi.dailies()

        for k in dailies:
            if self.config.get('show_' + k, True):
                for obj in dailies[k]:
                    self.show_achievement(obj['id'], k)

        self.schedule_next()

    def show_achievement(self, num, kind):
        details = GwApi.achievement(num)
        details['kind'] = kind
        s = self.config['format'].format(**details)

        print("Sending: "+s)
        self.send_to(Message(body=s), [ self.config['dest'] ])

        time.sleep(self.config.get('rate_limit', 0))

