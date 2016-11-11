import errno
import select
import socket
import re
import time
import sys
from HTMLParser import HTMLParser
sys.setrecursionlimit(10000000)

USER_HOMEPAGE_REGEX = re.compile('/fakebook/\d+')

USERNAME = '001947001'
PASSWORD = 'UGLJ1MLC'

cookie = {}

SOCKET = None

searched_friends = [] #/fakebook/131231231, /fakebook/32131231/friends/1

flags = []

counter = 0



def setup_socket():
    print 'starting server'
    global SOCKET
    SOCKET = socket.socket()
    SOCKET.connect(('fring.ccs.neu.edu', 80))
    SOCKET.setblocking(0)


setup_socket()


def parse_friend(attributes):
    for attribute in attributes:
        tag = attribute[0]
        value = attribute[1]
        if tag == 'href' and USER_HOMEPAGE_REGEX.match(value) and value not in searched_friends:
            GET(value)


# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            parse_friend(attrs)

    def handle_data(self, data):
        if 'FLAG' in data:
            if data not in flags:
                print data
                flags.append(data)
            if len(flags) == 5:
                print 'DONE'
                print flags
                sys.exit(0)

parser = MyHTMLParser()


def handle_moved_response(response_array):
    global cookie
    for response_line in response_array:
        if 'Location:' in response_line:
            location = response_line.split('Location:')[1]
            path = location.split('http://fring.ccs.neu.edu')[1]
            GET(path)


def handle_response(path, response):
    global cookie, SOCKET, counter
    response_array = response.rstrip().split('\n')
    move_request = False
    for response_line in response_array:
        if 'HTTP/1.1 200 OK' in response_line:
            searched_friends.append(path)
            counter += 1
            #print 'completed requests ' + str(counter)
            print 'searched friends ' + str(len(searched_friends))
            print "OK"
        elif 'HTTP/1.1 302 FOUND' in response_line or 'HTTP/1.1 301 MOVED PERMANENTLY' in response_line:
            print "MOVED"
            move_request = True
        elif 'HTTP/1.1 500 INTERNAL SERVER ERROR' in response_line:
            print "INTERNAL SERVER ERROR"
            setup_socket()
            GET(path)
        elif 'Set-Cookie: ' in response_line:
            cookie_string = response_line.split('Set-Cookie: ')[1].split(';')[0]
            cookie_array = cookie_string.split('=')
            print 'updating cookie %s to %s' % (cookie_array[0], cookie_array[1])
            cookie[cookie_array[0]] = cookie_array[1]
    if move_request:
        handle_moved_response(response_array)
    else:
        search_friends(response)


def GET(path):
    #print 'GET ' + path
    global cookie
    cookie_string = ''
    for name, value in cookie.items():
        cookie_string += name + '=' + value + '; '

    if cookie_string != '':
        cookie_string = cookie_string[:-2]
    request = 'GET '+path+' HTTP/1.1 \nHost: fring.ccs.neu.edu\nAccept: text/html,application/xhtml+xml,application/xml\nAccept-Language: en-US'
    if cookie_string:
        request += '\nCookie: ' + cookie_string
    CRLF = "\r\n\r\n"
    request += CRLF
    while True:
        try:
            SOCKET.send(request)
            response = SOCKET.recv(4096)
            if len(response) == 0:
                setup_socket()
                GET(path)
            else:
                handle_response(path, response)
            break
        except socket.error, e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                time.sleep(.1)
            else:
                print e
                sys.exit(1)


def POST(path, form):
    global cookie
    cookie_string = ''
    for name, value in cookie.items():
        cookie_string += name + '=' + value + ';'
    if cookie_string != '':
        cookie_string = cookie_string[:-2]

    form_string = ''
    for key, value in form.items():
        form_string += key + '=' + value + '&'
    form_string = form_string[:-1]

    request_header = \
        "POST " + path + " HTTP/1.1\r\n" \
        "Host: {hostname}\r\n" \
        "Connection: keep-alive\r\n" \
        "Content-Type: application/x-www-form-urlencoded\r\n" \
        "Content-Length: {len}\r\n" \
        "Cookie: {cookies}\r\n\r\n"\
            .format(hostname='fring.ccs.neu.edu', len=len(form_string), cookies=cookie_string)

    request = request_header + form_string
    while True:
        try:
            SOCKET.send(request)
            response = SOCKET.recv(4096)
            handle_response(path, response)
            break
        except socket.error, e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                time.sleep(.1)
            else:
                print e
                sys.exit(1)


def search_friends(response):
    parser.feed(response)


def login():
    GET('/accounts/login/?next=/fakebook/\r')
    csrftoken = cookie['csrftoken']
    POST('/accounts/login/', {"username": USERNAME, "password": PASSWORD, "csrfmiddlewaretoken": csrftoken,
                             "next": "%2Ffakebook%2F"})
    GET('/fakebook/')

login()


# while True:
#     try:
#         response = SOCKET.recv(4096)
#     except socket.error, e:
#         err = e.args[0]
#         if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
#             time.sleep(.1)
#             print 'Waiting...'
#             continue
#         else:
#             print e
#             print err
#             sys.exit(1)
#     else:
#         if len(response) == 0:
#             GET(path)
#         elif "sessionid" not in cookie:
#             handle_response(response)
#             csrftoken = cookie['csrftoken']
#             POST('/accounts/login/', {"username": USERNAME, "password": PASSWORD, "csrfmiddlewaretoken": csrftoken,
#                                       "next": "%2Ffakebook%2F"})
#         else:
#             # for path in in_flight:
#             #     if path in response:
#             #         in_flight.remove(path)
#             #         searched_friends.append(path)
#             #     else:
#             #         GET(path)
#             handle_response(response)

