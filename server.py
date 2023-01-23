import os
import socket
from jinja2 import Environment,select_autoescape,FileSystemLoader
import _thread
import datetime
import logging
file_log = logging.FileHandler('server.log',mode='w')
console_out = logging.StreamHandler()
logging.basicConfig(handlers=(file_log, console_out),format='%(asctime)s - %(message)s',level=logging.INFO)
logging.info("Server started")


ip = socket.gethostbyname(socket.gethostname())
with open('settings.ini','r') as settings:
    s = settings.read().split('\n')
    port = int(s[0].split('=')[1])
    maxRecv = int(s[1].split('=')[1])
    workDirectory = s[2].split('=')[1]


env = Environment(
    loader=FileSystemLoader('.'),
    autoescape=select_autoescape(['html', 'xml'])
)
template = env.get_template('temp.html')

def client_handler(client,addr):
    data = client.recv(maxRecv).decode('utf-8')
    content = get_request_handler(data,client,addr)
    client.send(content)

def server_start():
    try:
        server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        server.bind((ip,port))
        server.listen(4)
        while True:
            client,address = server.accept()
            _thread.start_new_thread(client_handler,(client,address))
    except KeyboardInterrupt:
        server.close()
        logging.info("Server stopped")

def get_request_handler(request_data,client,addr):
    cur_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%Z")
    HDRS_403 = f'HTTP/1.1 403 OK\r\nDate: {cur_date}\r\nContent-Type: text/html; charset=utf-8\r\nServer: Python 3.11\r\nContent-Length: {len("<h1>403 forbidden</h1>".encode("utf-8"))}\r\n\r\n'
    HDRS_404 = f'HTTP/1.1 404 OK\r\nDate: {cur_date}\r\nContent-Type: text/html; charset=utf-8\r\nServer: Python 3.11\r\nContent-Length: {len("<h1>404 not found</h1>".encode("utf-8"))}\r\nConnection: close\r\n\r\n'

    mime = ''
    response = ''
    path = request_data.split(' ')[1]


    if path == "/":
        ospath = os.getcwd()
        all_files = os.listdir(ospath  + f"/{workDirectory}")
        files_list = []
        for file in all_files:
            files_list.append({"url": f"http://{ip}:{port}/{file}", "name": file})
        rendered_page = template.render(
            files=files_list
        )
        with open('index.html', 'w', encoding="utf8") as file:
            file.write(rendered_page)
        with open('index.html','rb') as file:
            response = file.read()
        HDRS_200 = f'HTTP/1.1 200 OK\r\nDate: {cur_date}\r\nContent-Type: text/html; charset=utf-8\r\nServer: Python 3.11\r\nContent-Length: {len(response)}\r\nConnection: close\r\n\r\n'
        logging.info(f"{addr[0]} get index.html with code 200")
        return HDRS_200.encode('utf-8') + response

    match path.split('.')[-1]:
        case 'png':
            mime = 'image/png'
        case 'html':
            mime  = 'text/html'
        case 'mp3':
            mime = 'audio/mpeg'
        case 'mp4':
            mime = 'video/mp4'
        case _:
            logging.info(f"{addr[0]} get {path} with code 403")
            return HDRS_403.encode('utf-8') + '<h1>403 forbidden</h1>'.encode('utf-8')


    try:
        with open(workDirectory+path,'rb') as file:
            response = file.read()
            HDRS_200 = f'HTTP/1.1 200 OK\r\nDate: {cur_date}\r\nContent-Type: {mime}; charset=utf-8\r\nServer: Python 3.11\r\nContent-Length: {len(response)}\r\nConnection: close\r\n\r\n'
            logging.info(f"{addr[0]} get {path} with code 200")
        return HDRS_200.encode('utf-8') + response
    except FileNotFoundError:
        logging.info(f"{addr[0]} get {path} with code 404")
        return HDRS_404.encode('utf-8') + '<h1>404 not found</h1>'.encode('utf-8')


if __name__ == '__main__':
    server_start()