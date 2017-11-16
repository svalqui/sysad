# notes
#
# looking for emails.
# ldapsearch -x -h domain.org -D "user@domain.org" -W -b "ou=an-ou,dc=domain, dc=org" -s sub "(cn=*)" cn mail sn

import sys
import getpass
# import gssapi
import configparser
import pathlib
from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES, SASL

# Removing configuration from Project, configuration file 'ldapq.ini' moved 2 directories up
file_conf_dir = pathlib.Path(__file__).absolute().parents[2]
print('file_conf_dir', file_conf_dir)
file_conf_name = pathlib.Path(file_conf_dir) / 'ldapq.ini'
print('file_conf_name', file_conf_name)

# Reading configuration
config = configparser.ConfigParser()

try:
    config.read(str(file_conf_name))
    user_name = config['Settings']['default_user']
    URI = config['Settings']['uri']
    BASE = config['Settings']['default_base']
    show_fields = config['Filters']['show_attributes'].split(',')
    proceed = True

except BaseException as e:
    print('--FileError: ', e)
    print('--Exception Name :', type(e))
    proceed = False

# Query
look_for = input("Search AD for :")
# QUERY = '(|(cn=*' + look_for + '*)(&(objectcategory=computer)(name=*' + look_for + '*))(&(objectclass=group)(name=*' + look_for +'*)))'
# QUERY = '(givenName=val*)'

user_password = getpass.getpass()


def show_detail(detail):  # List or Value
    if isinstance(detail, list):
        print(detail)
        for element in detail:
            print("   ", element)
    else:
        print(" -> ", detail)


def show_attributes(one_response, fields=[]):  # Attributes is a Dict
    attributes = one_response['attributes']

    if len(fields) == 0:
        for key in sorted(attributes.keys()):
            if isinstance(attributes[key], list):
                print(key)
                for element in attributes[key]:
                    print("   ", element)
            else:
                print(key, " -> ", attributes[key])

        print("-----End of above response")
        print()

    else:

        for field in fields:
            if field in attributes.keys():
                if isinstance(attributes[field], list):
                    print(field)
                    for element in attributes[field]:
                        print("   ", element)
                else:
                    print(field, " : ", attributes[field])


def ldap_search(uri, base, query, fields=[]):
    '''
    ldap search
    :param uri:
    :param base:
    :param query:
    :param fields:
    :return:
    '''

    search_response = []

    print()
    print('URI :', uri)
    print('BASE :', base)
    print('QUERY :', query)

    try:
        server = Server(uri, use_ssl=True, get_info=ALL)
        conn = Connection(server, user=user_name, password=user_password, auto_bind=True)
        # conn = Connection(server, auto_bind=True, authentication=SASL, sasl_mechanism='GSSAPI')
        # print(conn)
        conn.search(base, query, attributes=ALL_ATTRIBUTES)
        # print(" RESPONSE LENGTH ", len(conn.response), " ENTRIES LENGTH ", len(conn.entries))
        # print()
        search_response = conn.response

        for index, one_response in enumerate(conn.response):
            # print("---Response---", index)
            if 'attributes' in one_response.keys():
                show_attributes(one_response, fields)
            # print("---End response---",index)

    except BaseException as e:
        print('LDAPError: ', e)
        print('Exception Name :', type(e))
        search_response = []

    # print('---End LDAP SEARCH')
    # print()

    return search_response


def find_domains(uri, base):  # for main domains with sub-domains
    domains = []  # List of Domains and sub-domains
    query = '(&(objectclass=domain)(dc=*))'
    q_response = ldap_search(uri, base, query, ['dc', 'distinguishedName', 'subRefs'])
    if len(q_response) > 0:
        for one_response in q_response:
            if 'attributes' in one_response.keys():

                if one_response['attributes']['distinguishedName'].find('DomainDnsZones') < 0 and \
                                one_response['attributes']['distinguishedName'].find('ForestDnsZones') < 0:
                    if one_response['attributes']['distinguishedName'] not in domains:

                        domains.append(one_response['attributes']['distinguishedName'])
                        # print('+++ Adding Domain :', one_response['attributes']['distinguishedName'])
                    if 'subRefs' in one_response['attributes'].keys():
                        if len(one_response['attributes']['subRefs']) > 0:
                            for ref in one_response['attributes']['subRefs']:
                                # print("ref -> ", ref)
                                find_domains(uri, ref)
    return domains


def find_users(uri, base):
    query = '(&(objectClass=user)(objectCategory=person)(|(cn=*' + look_for + '*)(displayName=*' + look_for + '*)))'
    q_response = ldap_search(uri, base, query)


def find_computers(uri, base):
    query = '(&(objectcategory=computer)(|(description=*' + look_for + '*)(name=*' + look_for + '*)))'
    q_response = ldap_search(uri, base, query)


def find_groups(uri, base):
    query = '(&(objectclass=group)(name=*' + look_for + '*))'
    q_response = ldap_search(uri, base, query)


def main():
    # ldap_search(URI, BASE, QUERY)
    print()
    for base in find_domains(URI, BASE):
        print(">>>-------------->DOMAIN BASE : ", base)
        find_users(URI, base)


if __name__ == '__main__':
    sys.exit(main())

# Credits Disclaimer
# The below sites/articles/code has been used totally, partially or as reference
#
#
# http://everythingisgray.com/2014/06/01/complex-ldap-queries-with-ldapsearch-and-python-ldap/
# https://stackoverflow.com/questions/13410540/how-to-read-the-contents-of-active-directory-using-python-ldap
# https://stackoverflow.com/questions/2193362/how-to-connect-to-a-ldap-server-using-a-p12-certificate
# https://stackoverflow.com/questions/4990718/python-about-catching-any-exception
# https://stackoverflow.com/questions/27844088/python-get-directory-two-levels-up
# https://wiki.python.org/moin/HandlingExceptions
# https://docs.python.org/3/library/pathlib.html
# https://docs.python.org/3/library/configparser.html
# http://ldap3.readthedocs.io/tutorial_intro.html
# https://social.technet.microsoft.com/Forums/scriptcenter/en-US/191a7f47-d4a7-4e06-af78-e9d2699a464a/get-all-sub-domains?forum=ITCG
# https://stackoverflow.com/questions/1400933/active-directory-search-for-only-user-objects