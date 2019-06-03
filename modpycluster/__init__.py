import requests
import urllib.parse
import time
from threading import Thread
import signal
import os
import sys


class modpycluster:
    AdvertiseUrl = ""
    host = ""
    port = None
    uuid = ""
    StickySessionForce = ""
    Type = ""
    contexts = []
    _runFlag = True

    def __init__(self, AdvertiseUrl, host, port, uuid, StickySessionForce=False, Type="http"):
        self.AdvertiseUrl = AdvertiseUrl
        self.host = host
        self.port = port
        self.uuid = uuid
        self.StickySessionForce = "Yes" if StickySessionForce else "No"
        self.Type = Type
        self._sigint = signal.getsignal(signal.SIGINT)
        self._sigterm = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def config(self):
        params = {"JVMRoute": self.uuid,
                  "Host": self.host,
                  "Port": self.port,
                  "StickySessionForce": self.StickySessionForce,
                  "Type": self.Type
                  }

        data = urllib.parse.urlencode(params)

        r = requests.request('CONFIG', self.AdvertiseUrl, data=data)

        if r.status_code == 200:
            return True
        else:
            raise Exception(
                'Error while modcluster %s: %i, %s' % (sys._getframe().f_code.co_name, r.status_code, r.text))

    def _do_app(self, method, alias=None, context=None):
        params = {"JVMRoute": self.uuid
                  }
        if alias is not None: params["Alias"] = alias
        if context is not None: 
            params["Context"] = context
        else:
            self.AdvertiseUrl = self.AdvertiseUrl + "/*"

        data = urllib.parse.urlencode(params)

        r = requests.request(method, self.AdvertiseUrl, data=data)

        if r.status_code == 200:
            return True
        else:
            raise Exception(
                'Error while modcluster %s ,%s: %i, %s' % (sys._getframe().f_code.co_name, method, r.status_code, r.text))

    def enable_app(self, alias, context):
        return self._do_app(method="ENABLE-APP", alias=alias, context=context)

    def disable_app(self, alias, context):
        return self._do_app(method="DISABLE-APP", alias=alias, context=context)

    def stop_app(self, alias, context):
        return self._do_app(method="STOP-APP", alias=alias, context=context)

    def remove_app(self, alias, context):
        return self._do_app(method="REMOVE-APP", alias=alias, context=context)

    def status(self):
        params = {"JVMRoute": self.uuid,
                  "Load": 100,
                  }

        data = urllib.parse.urlencode(params)

        r = requests.request('STATUS', self.AdvertiseUrl,
                             data=data)

        if r.status_code == 200:
            return True
        else:
            raise Exception(
                'Error while modcluster %s: %i, %s' % (sys._getframe().f_code.co_name, r.status_code, r.text))

    def _loop(self):
        while self._runFlag:
            try:
                if self.config():
                    print("configured modculster, uuid:%s, apache addr: %s, my addr: %s:%s." % (
                        self.uuid, self.AdvertiseUrl, self.host, self.port))
                self._enablecontexts()
                while self._runFlag:
                    time.sleep(1)
                    self.status()
            except Exception as e:
                print(e)
                pass

    def _enablecontexts(self):
        for context in self.contexts:
            if self.enable_app(alias="localhost", context=context):
                print("enabled context %s" % context)

    def _shutdowncontexts(self):
        for context in self.contexts:
            self.disable_app(alias="localhost", context=context)
            self.stop_app(alias="localhost", context=context)
            self.remove_app(alias="localhost", context=context)
            print("shutdown context %s" % context)
        self._do_app(method="REMOVE-APP")

    def run(self):
        self.t = Thread(target=self._loop)
        self.t.start()

    def bindFlaskApp(self, flaskapp):
        for rule in flaskapp.url_map.iter_rules():
            # hack?
            context = rule._trace[1][1]
            if context.endswith("/"):
                context = context[:-1]
            self.contexts.append(context)

    def _signal_handler(self, sig, frame):
        self._runFlag = False
        self.t.join()
        self._shutdowncontexts()
        #reset signals and throw origial signal
        signal.signal(signal.SIGTERM, self._sigterm)
        signal.signal(signal.SIGINT, self._sigint)
        os.kill(os.getpid(), sig)