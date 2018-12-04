#!/usr/bin/env python
# encoding=utf-8
#codeby     道长且阻
#email      @ydhcui/QQ664284092
#https://github.com/ydhcui/Scanver

class SessionManager(object):
    def __init__(self, secret, store_options, session_timeout):
        self.secret = secret
        self.session_timeout = session_timeout
        try:
            if store_options['redis_pass']:
                self.redis = redis.StrictRedis(host=store_options['redis_host'], port=store_options['redis_port'], password=store_options['redis_pass'])
            else:
                self.redis = redis.StrictRedis(host=store_options['redis_host'], port=store_options['redis_port'])
        except Exception as e:
            print(e)


    def _fetch(self, session_id):
        try:
            session_data = raw_data = self.redis.get(session_id)
            if raw_data != None:
                self.redis.setex(session_id, self.session_timeout, raw_data)
                session_data = ujson.loads(raw_data)
            if type(session_data) == type({}):
                return session_data
            else:
                return {}
        except IOError:
            return {}
    def get(self, request_handler = None):
        if (request_handler == None):
            session_id = None
            hmac_key = None
        else:
            session_id = request_handler.get_secure_cookie("session_id")
            hmac_key = request_handler.get_secure_cookie("verification")
        if session_id == None:
            session_exists = False
            session_id = self._generate_id()
            hmac_key = self._generate_hmac(session_id)
        else:
            session_exists = True
        check_hmac = self._generate_hmac(session_id)
        if hmac_key != check_hmac:
            raise InvalidSessionException()
        session = SessionData(session_id, hmac_key)
        if session_exists:
            session_data = self._fetch(session_id)
            for key, data in session_data.iteritems():
                session[key] = data
        return session

    def set(self, request_handler, session):
        request_handler.set_secure_cookie("session_id", session.session_id)
        request_handler.set_secure_cookie("verification", session.hmac_key)
        session_data = ujson.dumps(dict(session.items()))
        self.redis.setex(session.session_id, self.session_timeout, session_data)
    def _generate_id(self):
        new_id = hashlib.sha256(self.secret + str(uuid.uuid4()))
        return new_id.hexdigest()
    def _generate_hmac(self, session_id):
        return hmac.new(session_id, self.secret, hashlib.sha256).hexdigest()






