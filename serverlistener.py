import socket
import threading
import os
import email.utils
import mimetypes

# keep track of where all files are stored
baseDirectory = os.path.abspath('public')

# class to handle HTTP requests
# Request.validate() returns 1 if request is valid, or appropriate error code if not
# Requst.checksIfModified() returns True if the request contains an 'If-Modified-Since' clause
# Request.generateLog() returns a formatted string containing the request's address, timestamp, HTTP type and file requested
# Request.wantsImage() returns True if MIMEtypes predicts an image-type request
class Request():

    def __init__(self, httpType, file, version, connection, keepAliveFlag, fullPath, lastModifiedTime, address, fileType):

        self.httpType = httpType
        self.file = file
        self.version = version
        self.connection = connection
        self.lastModifiedTime = lastModifiedTime
        self.keepAliveFlag = keepAliveFlag
        self.fullPath = fullPath
        self.address = address
        self.fileType = fileType

    def validate(self):
        if (self.httpType != 'GET') and (self.httpType != 'HEAD'):
            return 400 # 400 Bad Request; invalid request
        
        if not self.fullPath.startswith(baseDirectory):
            return 403 # 403 Forbidden; attempts to access different directories
        
        if not os.path.exists(self.fullPath):
            return 404 # 404 File Not Found
        
        # if valid request,
        return 1
    
    def checksIfModified(self):
        if self.lastModifiedTime == -1: return False
        else: return True

    # returns a log line, missing the return code
    def generateLog(self): 
        currentTime = email.utils.formatdate(timeval=None, localtime=False, usegmt=True)
        return f"{self.address} --- {currentTime} --- '{self.httpType} {self.file}'"
    
    def wantsImage(self):
        if self.fileType.startswith("image"): return True
        else: return False

# get raw data string from request, then split into different variables
# returns new Request object from derived variables
def parseData(data,address):

    # get headers
    httpType, file, version = data[0].split() 
    connection = 'close' # default
    lastModifiedTimeStr = None

    # find connection type and if-modified-since clause
    for line in data[1:]:

        if line.startswith('Connection:'):
            connection = line.split(": ")[1].strip()

        elif line.startswith('If-Modified-Since:'):
            lastModifiedTimeStr = line.split(": ", 1)[1].strip()

    # if there is a last modified time clause, turn it into a standard timestamp, else = -1
    if lastModifiedTimeStr:
        datetimeHeader = email.utils.parsedate_to_datetime(lastModifiedTimeStr)
        lastModifiedTime = int(datetimeHeader.timestamp())

    else:
        lastModifiedTime = -1


    # loop repeat flag
    keepAliveFlag = 1 if connection == 'keep-alive' else 0

    # get full path
    fullPath = os.path.abspath(os.path.join(baseDirectory,file.lstrip('/')))

    # get filetype
    fileType, _= mimetypes.guess_type(fullPath)
    if fileType is None: fileType = 'application/octet-stream' # default

    return Request(httpType, file, version, connection, keepAliveFlag, fullPath, lastModifiedTime, address, fileType)

# extension of main program
# receives data, decodes it and sends to parseData
# determines appropriate HTTP response for received request
# returns appropriate HTTP responses back to client and logs all received requests
def handleClient(connectionSocket, address):

    try: 
        while True:


            # receive 4KB of data. decode it, then split it by arguments. 
            data = connectionSocket.recv(4096)
            if not data: break # client disconnected
            data = data.decode('utf-8').split('\r\n')


            request = parseData(data,address)
            # print(f'total data: {data} \n request: {Type} \n connection: {connection} \n since: {lastModified}')

            # GET/HEAD flag used to determine whether bytes should be sent
            sendData = 1 if request.httpType != 'HEAD' else 0
            
            # check for errors
            valid = request.validate()

            if valid != 1: # if there is an error, 
                errorCode = valid 
                
                # return appropriate response
                if errorCode == 400: connectionSocket.sendall(return400(sendData))
                if errorCode == 403: connectionSocket.sendall(return403(sendData))
                if errorCode == 404: connectionSocket.sendall(return404(sendData)) 

                publishLog(request, errorCode, getMessage(errorCode))
                break

            # at this point it's an okay request, can either be close or keep-alive

            fileModifiedTime = int(os.path.getmtime(request.fullPath))
            
            # catch 304 file not modified
            if request.checksIfModified(): # if the request wants us to check,

                if fileModifiedTime <= request.lastModifiedTime: # if the file was not modified since the request's timestamp
                    connectionSocket.sendall(return304(request.connection)) # return 304 File Not Modified
                    publishLog(request, 304, getMessage(304)) 
                    if request.keepAliveFlag: continue # if keep-alive, continue
                    break

            # now to send data...
            size = os.path.getsize(request.fullPath)
            formattedModifiedTime = email.utils.formatdate(fileModifiedTime, usegmt=True)
            currentTime = email.utils.formatdate(timeval=None, localtime=False, usegmt=True)

            # boilerplate 200 OK response
            response = f"HTTP/1.1 200 OK\r\nDate: {currentTime}\r\nLast-Modified: {formattedModifiedTime}\r\nContent-Type: {request.fileType}\r\nContent-Length: {size}\r\nConnection: {request.connection}\r\n\r\n".encode('utf-8')
            
            # if it's a GET request, attach bytes
            if sendData: response += getFile(request)

            # SEND IT
            connectionSocket.sendall(response)

            publishLog(request, 200, getMessage(200))

            # if connection type is close, break
            if not request.keepAliveFlag: break
    except socket.timeout:
        pass
        
    connectionSocket.close()
  
# fetches file data
def getFile(request):

    if request.wantsImage(): 
        with open(request.fullPath, 'rb') as file:
            return file.read()
    else: 
        with open(request.fullPath, 'r') as file:
            return file.read().encode('utf-8')
    

    file.close()

    return data

# publishes a log line to logs.txt. derives message from Request class and appends attributes
def publishLog(request, returnCode, message):
    f = open("logs.txt", 'a')
    log = f'{request.generateLog()} --- {str(returnCode)} {message} \n'
    f.write(log)
    f.close()

def return404(sendData):
    msg ="HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\nContent-Length: 48\r\nConnection: close\r\n\r\n"
    if sendData: msg += "<html><body><h1>404 Not Found</h1></body></html>"
    return msg.encode('utf-8')

def return400(sendData):
    msg ="HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\nContent-Length: 50\r\nConnection: close\r\n\r\n"
    if sendData: msg += "<html><body><h1>400 Bad Request</h1></body></html>"
    return msg.encode('utf-8')

def return403(sendData):
    msg ="HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\nContent-Length: 48\r\nConnection: close\r\n\r\n"
    if sendData: msg += "<html><body><h1>403 Forbidden</h1></body></html>"
    return msg.encode('utf-8')

def return304(connection):
    timestamp = email.utils.formatdate(timeval=None, localtime=False, usegmt=True)
    return f"HTTP/1.1 304 Not Modified\r\nDate: {timestamp}\r\nConnection: {connection}\r\n\r\n".encode('utf-8')

# matches error code to message
def getMessage(code): 
    if code == 404: return "File Not Found"
    if code == 403: return "Forbidden"
    if code == 400: return "Bad Request"
    if code == 304: return "File Not Modified"
    if code == 200: return "OK"





# =================================
#           MAIN PROGRAM
# =================================


# creates tcp socket
# bind listener to 127.0.0.1:9999
# endless listening loop
# in loop, waits for connections
# when connection received, create new thread and send it to handler
# repeat loop


# create TCP socket
listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# set SO_REUSEADDR option to 1 so that we can reuse the same address and port if needed.
listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# bind listener to ip 127.0.0.1, port 9999
listener.bind(('127.0.0.1', 9999))

# listen for incoming connections
listener.listen(5)

while True:
    print("connection pending...")
    # accept incoming connection and get client socket and address
    client_socket, client_address = listener.accept()
    print(f"connection accepted from {client_address}")
    
    # create new thread for each request
    client_thread =  threading.Thread(target=handleClient, args=(client_socket, client_address))
    client_thread.start()

    # loop goes back to beginning
