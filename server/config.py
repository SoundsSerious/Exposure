#Define EXP_PATH
import os
from sqlalchemy_imageattach.stores.fs import FileSystemStore

import sys
sys.path.append('../')

#CUR_URL = '127.0.0.1'
SOCIAL_PORT = 17776
WEB_PORT = 8888

dropboxpath = os.path.join('Dropbox','workspace','Exposure')
if os.name == 'posix':
    HOME_URL = 'localhost'
    EXP_PATH = os.path.join(os.path.expanduser('~'),dropboxpath)
    ENG_STR = 'postgresql://Cabin@localhost:5432/postgis_test'
    USR_IMG = os.path.join(EXP_PATH,'user_images')
elif os.name == 'nt':
    usr = r'C:\Users\Sup'
    EXP_PATH = os.path.join(usr,dropboxpath)
    HOME_URL = 'localhost'
    ENG_STR = 'postgresql://exposureguy:Keavin#1123@localhost:5433/gistest'
    USR_IMG = os.path.join(EXP_PATH,r'user_images')
else:
    #Default to unix config
    HOME_URL = 'http://exposureapp.io'
    EXP_PATH = os.path.join(os.path.expanduser('~'),dropboxpath)
    ENG_STR = 'postgresql://Cabin@localhost:5432/postgis_test'
    USR_IMG = os.path.join(EXP_PATH,'user_images')

STORE_URL = 'http://{}:{}'.format(HOME_URL,WEB_PORT)
STORE = FileSystemStore(USR_IMG,STORE_URL)
print STORE_URL, STORE.base_url, STORE.path
APP_PATH = os.path.join(EXP_PATH,'app')
SRV_PATH = os.path.join(EXP_PATH,'server')
LOCAL_IMAGE = os.path.join(EXP_PATH,'app','Login_Image.jpg')
