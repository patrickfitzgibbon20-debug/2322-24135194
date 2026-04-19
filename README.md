# 2322-24135194

### Multithreaded Web Server

This is a multithreaded webserver implemented in Python without using HTTPServer, as requested by the project description. All the functionalities required for the project are included in this submission. 

**Student ID 24135194D**

(all instructions below for Windows 11 machines only)






## Prerequisites

**You must have Python installed on system PATH** or other OS' equivalent before running this program. To do so, go to https://www.python.org/downloads/ and during installation confirm that Python is added to PATH.

To confirm that Python is installed correctly, enter `python --version` in a command terminal and check if `'Python 3.X.X'` (where X can be any number) is printed.





## Instructions

1. **Clone entire repository and extract** into a freely accessible directory

2. **Upload all test files** (image, text) into the `/public/` folder. There are 3 files already installed here for convenience, `egypt.gif` , `emoji.png` and `index.html` . 

3. Open the command terminal/PowerShell and **navigate to the directory** where this project is stored. This can be done through the command `cd C:\path\to\repository\2322-24135194`

4. **Run the server** through the terminal command `python serverlistener.py` . If running correctly, the terminal should print `'connection pending...'`

After this point, the socket will be listening on address 127.0.0.1:9999 . You may test the functionality of the web server by using Google Chrome, curl, NatCat, or any other HTTP client. All transactions are logged in the included `logs.txt` file of the repository. 






## Example Commands


### Google Chrome

- `http://127.0.0.1:9999/egypt.gif` sends a GIF image of a seemingly Egyptian man, with response headers `200 OK` and a `keep-alive` connection. Refresh this result to receive a `304 File Not Modified` response code.


- `http://127.0.0.1:9999/emoji.png` sends an image of an emoji challenging you to find where the errors in this project are. The response headers and behaviour is the same as above, and taking the emoji up on this challenge would be futile, as there are no errors here. 


- `http://127.0.0.1:9999/index.html` sends HTML bytes which display `'Hello World!'` onscreen. Behaviour is the same as the two listed above. 


- `http://127.0.0.1:9999/THISFILEDOESNOTEXIST.png` returns a `404 File Not Found` error, as the file requested does not exist.



### Command Terminal (curl)

- `curl.exe -v -X POST http://127.0.0.1:9999/index.html` returns a `400 Bad Request` error as the request type is not `GET` or `HEAD`.


- `curl.exe -v -H "Connection: close" http://127.0.0.1:9999/index.html` returns the same HTML bytes as shown earlier but with a `connection: close` type response.


- `curl.exe -v --path-as-is http://127.0.0.1:9999/../serverlistener.py` returns a `403 Forbidden` error as it attempts to access files outside of the public folder.


- `curl.exe -I http://127.0.0.1:9999/notes.txt` returns headers only as this is a `HEAD`-type request






