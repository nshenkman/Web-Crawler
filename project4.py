import socket
from urlparse import urlparse



USERNAME = '001947001'
PASSWORD = 'UGLJ1MLC'

cookie = {}
DATA_SIZE = 4096

def handle_moved_response(response_array):
    global cookie
    for response_line in response_array:
        if 'Location:' in response_line:
            location = response_line.split('Location:')[1]
            path = location.split('http://fring.ccs.neu.edu')[1]
            return GET(path)
    return None


def handle_response(response):
    global cookie
    response_array = response.rstrip().split('\n')
    move_request = False
    for response_line in response_array:
        if 'HTTP/1.1 200 OK' in response_line:
            print "OK"
        elif 'HTTP/1.1 302 FOUND' in response_line or 'HTTP/1.1 301 MOVED PERMANENTLY' in response_line:
            print "MOVED"
            move_request = True
        elif 'Set-Cookie: ' in response_line:
            cookie_string = response_line.split('Set-Cookie: ')[1].split(';')[0]
            cookie_array = cookie_string.split('=')
            print 'updating cookie %s to %s' % (cookie_array[0], cookie_array[1])
            cookie[cookie_array[0]] = cookie_array[1]
    if move_request:
        return handle_moved_response(response_array)
    else:
        return response_array


def GET(path):
    print 'GET ' + path

    global cookie
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('fring.ccs.neu.edu', 80))
    cookie_string = ''
    for name, value in cookie.items():
        cookie_string += name + '=' + value + ';'

    if cookie_string != '':
        cookie_string = cookie_string[:-1]
    request = 'GET '+path+' HTTP/1.1 \nHost: fring.ccs.neu.edu\nAccept: text/html,application/xhtml+xml,application/xml\nAccept-Language: en-US'
    if cookie_string:
        request += '\nCookie: ' + cookie_string
    CRLF = "\r\n\r\n"


    print request

    s.send(request + CRLF)
    data = s.recv(4096)
    response = ''
    while len(data):
        response += data
        data = s.recv(4096)
    s.shutdown(1)
    s.close()
    return handle_response(response)


def POST(path, form):
    print 'POST ' + path

    global cookie
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('fring.ccs.neu.edu', 80))
    cookie_string = ''
    for name, value in cookie.items():
        cookie_string += name + '=' + value + '; '
    if cookie_string != '':
        cookie_string = cookie_string[:-2]

    form_string = ''
    for key, value in form.items():
        form_string += key + '=' + value + '&'
    form_string = form_string[:-1]

    request = 'POST '+path+' HTTP/1.1 \r\nHost: fring.ccs.neu.edu\r\nAccept: text/html,application/xhtml+xml,application/xml\r\nAccept-Language: en-US\r\nCookie: '+cookie_string+'\r\n' + 'Content-Length: ' + str(len(form_string)) +'\r\nContent-Type: application/x-www-form-urlencoded'
    CRLF = "\r\n\r\n"
    form_string += '\r\n'

    print 'FORM: ' + form_string


    request += CRLF
    request += form_string
    print request
    s.send(request)
    data = s.recv(4096)
    response = ''
    while len(data):
        response += data
        data = s.recv(4096)
    handle_response(response)
    #GET('/fakebook/')
    s.shutdown(1)
    s.close()



# def login():
#     response_array = GET('/fakebook/')
#     for response_line in response_array:
#         if 'csrfmiddlewaretoken' in response_line:
#             token = response_line.split('value=\'')[1].split('\'')[0]
#             POST('/accounts/login', {"username": USERNAME, "password": PASSWORD, "csrfmiddlewaretoken": token, "next": "/fakebook/"})
# login()
