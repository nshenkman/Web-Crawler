import errno
import socket
import re
import time
import sys
from HTMLParser import HTMLParser

USER_HOMEPAGE_REGEX = re.compile('/fakebook/\d+')
USERNAME = sys.argv[1]
PASSWORD = sys.argv[2]
BUFFER = 10

cookie = {}
searched_friends = []  # /fakebook/131231231, /fakebook/32131231/friends/1
flags = []
sockets = {}
to_send = []


def parse_friend(attributes):
    for attribute in attributes:
        tag = attribute[0]
        value = attribute[1]
        if tag == 'href' and USER_HOMEPAGE_REGEX.match(value) and value not in searched_friends:
            def get(): GET(value)

            to_send.append(get)


# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            parse_friend(attrs)

    def handle_data(self, data):
        if 'FLAG' in data:
            flag = data.split('FLAG: ')[1]

            if flag not in flags:
                flags.append(flag)
            if len(flags) == 5:
                print("\n".join(flags))
                sys.exit(0)


def handle_moved_response(response_array):
    global cookie
    for response_line in response_array:
        if 'Location:' in response_line:
            location = response_line.split('Location:')[1]
            path = location.split('http://fring.ccs.neu.edu')[1]
            GET(path)


def handle_response(path, response):
    global cookie
    response_array = response.rstrip().split('\n')
    move_request = False
    for response_line in response_array:
        if 'HTTP/1.1 200 OK' in response_line:
            searched_friends.append(path)
            print len(searched_friends)
        elif 'HTTP/1.1 302 FOUND' in response_line or 'HTTP/1.1 301 MOVED PERMANENTLY' in response_line:
            move_request = True
        elif 'HTTP/1.1 500 INTERNAL SERVER ERROR' in response_line:
            GET(path)
        elif 'Set-Cookie: ' in response_line:
            cookie_string = response_line.split('Set-Cookie: ')[1].split(';')[0]
            cookie_array = cookie_string.split('=')
            cookie[cookie_array[0]] = cookie_array[1]
    if move_request:
        handle_moved_response(response_array)
    else:
        search_friends(response)


def GET(path):
    global cookie

    s = socket.socket()
    s.connect(('fring.ccs.neu.edu', 80))
    s.setblocking(0)

    cookie_string = ''
    for name, value in cookie.items():
        cookie_string += name + '=' + value + '; '

    if cookie_string != '':
        cookie_string = cookie_string[:-2]
    request = 'GET ' + path + ' HTTP/1.1 \nHost: fring.ccs.neu.edu\nAccept: text/html,application/xhtml+xml,application/xml\nAccept-Language: en-US'
    if cookie_string:
        request += '\nCookie: ' + cookie_string
    CRLF = "\r\n\r\n"
    request += CRLF
    s.send(request)
    sockets[path] = s


def POST(path, form):
    global cookie

    s = socket.socket()
    s.connect(('fring.ccs.neu.edu', 80))
    s.setblocking(0)

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
                         "Cookie: {cookies}\r\n\r\n" \
            .format(hostname='fring.ccs.neu.edu', len=len(form_string), cookies=cookie_string)

    request = request_header + form_string
    s.send(request)
    sockets[path] = s



def search_friends(response):
    parser.feed(response)

GET('/accounts/login/?next=/fakebook/\r')
parser = MyHTMLParser()


while True:
    if len(sockets) < BUFFER and len(to_send) > BUFFER - len(sockets):
        for i in range(0, BUFFER - len(sockets)):
            get = to_send[i]
            get()
            del to_send[i]
    elif len(to_send) <= BUFFER - len(sockets):
        for get in to_send:
            get()

    for path, s in sockets.items():
        try:
            response = s.recv(4096)
        except socket.error, e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                time.sleep(.1)
                continue
            else:
                print e
                sys.exit(1)
        else:
            s.close()
            del sockets[path]
            if len(response) == 0:
                GET(path)
            elif "sessionid" not in cookie:
                handle_response(path, response)
                csrftoken = cookie['csrftoken']
                POST('/accounts/login/', {"username": USERNAME, "password": PASSWORD, "csrfmiddlewaretoken": csrftoken,
                                          "next": "%2Ffakebook%2F"})
            else:
                handle_response(path, response)