class LDAP_API(object):

    _ldap_path = ldap_config['ldap_path']
    _base_dn = ldap_config['base_dn']
    _ldap_user = ldap_config['ldap_user']
    _ldap_pass = ldap_config['ldap_pass']
    _original_pass = ldap_config['original_pass']

    # 连接ldap服务器
    def __init__(self):

        try:
            self.ldapconn = ldap.initialize(self._ldap_path)
            self.ldapconn.protocal_version = ldap.VERSION3
            self.ldapconn.simple_bind(self._ldap_user, self._ldap_pass)

        except ldap.LDAPError, e:
            print e

    # 验证用户登录
    def ldap_check_login(self, username, password):

        obj = self.ldapconn
        searchScope = ldap.SCOPE_SUBTREE
        # searchFilter = '(&(cn='+username+')(userPassword='+password+'))'
        searchFilter = 'uid=' + username

        try:
            obj.search(self._base_dn, searchScope, searchFilter, None)  # id--2
            # 将上一步计算的id在下面运算
            result_type, result_data = obj.result(2, 0)
            if result_type != ldap.RES_SEARCH_ENTRY:
                return {'status': ldap_message[1], 'data': ''}
            dic = result_data[0][1]
            l_realname = dic['sn'][0]
            l_password = dic['userPassword'][0]
            md_password = LDAP_API.hash_md5(password)
            if l_password in (password, md_password):
                return {'status': ldap_message[0], 'data': l_realname}
            else:
                return {'status': ldap_message[1], 'data': ''}
        except ldap.LDAPError, e:
            return {'status': ldap_message[2], 'data': ''}

    @staticmethod
    def hash_md5(data):
        md = hashlib.md5()
        md.update(str(data))
        a = md.digest()
        b = '{MD5}' + base64.b64encode(a)
        return b