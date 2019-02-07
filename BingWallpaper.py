#!/usr/bin/python3
# -*- coding:utf-8 -*-

from datetime import datetime
import requests,time,os,argparse,imghdr,random

class Logger(object):

    @staticmethod
    def error(content,**kwargs):
        time = datetime.now().strftime("[%Y-%m-%d %H:%M:%S.%f]")
        path = "%s/BingWallpaper/.oneclickbingwallpaper.log" % os.path.expanduser('~')

        if "path" in kwargs:
            path = kwargs["path"]

        str = "%s#error : %s\n" % ( time, content )
        print(str,end="")

        with open(path,"a+") as file:
            file.write(str)

    @staticmethod
    def info(content,**kwargs):
        time = datetime.now().strftime("[%Y-%m-%d %H:%M:%S.%f]")
        path = "%s/BingWallpaper/.oneclickbingwallpaper.log" % os.path.expanduser('~')
        if "path" in kwargs:
            path = kwargs["path"]
        
        str = "%s#info : %s\n" % ( time, content )
        print(str,end="")

        with open(path,"a+") as file:
            file.write(str)

class Downloader(object):

    @staticmethod
    def get(url,fileName):
        try:
            downloadReponse = requests.get(url)
        except:
            Logger.error("exception throw when getting %s" % fileName )

        if downloadReponse.status_code != 200:
            Logger.error("network error: %s" % str(downloadReponse.status_code) )

        lastIndex = fileName.rfind("/")
        if lastIndex:
            if not os.path.exists(fileName[:lastIndex]):
                os.mkdir(fileName[:lastIndex])
                Logger.info("%s not exist,repairing ..." % fileName[:lastIndex] )

        with open(fileName,"wb") as file:
            file.write(downloadReponse.content)

class BingWallpaper(object):

    def __init__(self,de="",command=""):

        self.de = de
        self.command = command
        self.random = False
        self.path = "/HPImageArchive.aspx?format=js&idx=0&n=1"
        self.json = dict()
        self.imgFolder = "%s/BingWallpaper" % os.path.expanduser('~')
        self.notifyIconPath = "/usr/share/icons/hicolor/64x64/apps/OneClickBingWallpaper.png"
    
    def setBaseUrl(self,baseURL):
        url = "%s%s" % ( baseURL, self.path )
        Logger.info(url)
        try:
            rsp = requests.get(url)
        except requests.exceptions.InvalidURL:
            Logger.error("InvaildURL")
            return -1
        except requests.exceptions.ConnectionError:
            Logger.error("ConnectionError")
            return -1
        
        if rsp.status_code == 200:
            try:
                self.json = rsp.json() # This *call* raises an exception if JSON decoding fails
            except ValueError:
                Logger.error("ValueError")
                return -1

            Logger.info(baseURL)
        else:
            Logger.error("StatusCodeNot200:"+str(rsp.status_code))
            return -1

        try:
            imgLocation = self.json['images'][0]['url']
            self.imgUrl = "%s%s" % ( baseURL, imgLocation )
            lastIndex = imgLocation.rfind(".")
            imgSuffix = imgLocation[lastIndex+1:] # if lastIndex=-1, imgSuffix=imgLocation
            self.imgName = "BingWallpaper-%s.%s" % ( time.strftime("%Y-%m-%d",time.localtime()), imgSuffix )
            self.imgPath = "%s/%s" % ( self.imgFolder, self.imgName)
        except Exception as e:
            Logger.error(e)
            return -1

    def setWallpaper(self):
        Logger.info("setting begin")
        
        if (not os.path.exists(self.imgPath) ) and (not self.random):
            Logger.info("%s not exist,downloading..." % self.imgName)
            Downloader.get(self.imgUrl,self.imgPath)
        
        Logger.info("de: %s, command: %s" % (self.de, self.command))

        if self.de == "cinnamon":
            self.command = "gsettings set org.cinnamon.desktop.background picture-uri \"file:///%s\"" % self.imgPath
            Logger.info("cinnamon command status:%s" % str(os.system(self.command)))
        
        elif self.de == "deepin":
            self.command = "gsettings set com.deepin.wrap.gnome.desktop.background picture-uri \"file:///%s\"" % self.imgPath
            Logger.info("deepin command status:%s" % str(os.system(self.command)))
        
        elif self.de == "gnome":
            shell = '''
                gsettings set org.gnome.desktop.background draw-background false && 
                gsettings set org.gnome.desktop.background picture-uri file://# && 
                gsettings set org.gnome.desktop.background draw-background true
            '''
            self.command = shell.replace("#",self.imgPath)
            Logger.info("gnome command status:%s" % str(os.system(self.command)))
        
        elif self.de == "kde":
            plasmashell = '''
                var Desktops = desktops();
                d = Desktops[0];
                d.wallpaperPlugin= "org.kde.image";
                d.currentConfigGroup = Array("Wallpaper","org.kde.image","General");
                d.writeConfig("Image","#");
            '''.replace("#",self.imgPath)
            self.command = "qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript \'#\'".replace("#",plasmashell)
            Logger.info("kde command status:%s" % str(os.system(self.command)))
            # if 'sh: 1: notify-send: not found' in kde , please install libnotify-bin
            # sudo apt install libnotify-bin

        elif self.de == "mate":
            self.command = "gsettings set org.mate.background picture-filename #".replace("#",self.imgPath)
            Logger.info("mate command status:%s" % str(os.system(self.command)))
            
        elif self.de == "wm":
            self.command = "feh --bg-fill %s" % self.imgPath
            Logger.info("feh command status:%s" % str(os.system(self.command)))

        elif self.de == "xfce":
            self.command = "xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitor0/workspace0/last-image -s %s" % self.imgPath
            Logger.info("xfce command status:%s" % str(os.system(self.command)))

        elif self.command:
            command = self.command.replace("{{}}",self.imgPath)
            Logger.info("%s command status: %s" % ( self.command, str(os.system(command)) ) )

        else:
            Logger.info("not support desktop environment:%s" % str(self.de))
        
        if self.de or self.command:
            self.notify()
        Logger.info("setting finish")

    def notify(self):
        content = ""
        if not self.random:
            try:
                content = self.json['images'][0]['copyright']
                lastIndex = content.rfind("(")
                content = content[:lastIndex]
            except Exception:
                pass
        else:
            content = self.imgName
        if os.path.exists(self.notifyIconPath):
            options = "--icon=%s" % self.notifyIconPath
        shell = "notify-send %s:%s %s" % ( time.strftime("%Y-%m-%d",time.localtime()), content, options)
        Logger.info(shell)
        os.system(shell)
    
    def detect(self):
        session = os.getenv("DESKTOP_SESSION")
        keywords = {
            "cinnamon":"cinnamon",
            "deepin":"deepin",
            "gnome":"gnome",
            "mate":"mate",
            "plasma":"kde",
            "xfce":"xfce"
        }
        for key in keywords:
            if key in session:
                self.de = keywords[key]
                break

    def randomImage(self):
        self.random = True
        files = [item for item in os.listdir(self.imgFolder) if imghdr.what("%s/%s" % (self.imgFolder, item))]
        self.imgName = files[random.randint(0,len(files))]
        self.imgPath = "%s/%s" % (self.imgFolder, self.imgName)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto",help="auto detect desktop environment(Beta)",action="store_true")
    parser.add_argument("--random",help="random pick image from default folder to set wallpaper",action="store_true")
    parser.add_argument("-d",help="desktop environment: xfce etc")
    parser.add_argument("-c",help="command in your device to set desktop background,{{}} will be replaced with the true images path(not end with \)")
    parser.add_argument("-baseurl",help="[ignore if --random is true] alternative subdomain for bing.com, for example, -baseurl www2.bing.com. "
                                        "must begin with https:// or http://")
    args = parser.parse_args()

    bw = BingWallpaper(args.d,args.c)

    if args.auto:
        ret = bw.detect()
    if args.random:
        ret = bw.randomImage()
    elif args.baseurl:
        ret = bw.setBaseUrl(args.baseurl)
    else:
        path = "/HPImageArchive.aspx?format=js&idx=0&n=1"
        baseURLs = ["https://www.bing.com",
                   "https://www2.bing.com",
                   "https://www4.bing.com",
                   "https://cn.bing.com" ]
        for baseURL in baseURLs:
            url = "%s%s" % ( baseURL, path )
            try:
                rsp = requests.get(url)
            except requests.exceptions.ConnectionError:
                Logger.error("ConnectionError")
            else:
                if rsp.status_code == 200:
                    ret = bw.setBaseUrl(baseURL)
                    break

    Logger.info("preparation ret:"+str(ret))

    if not ret or ret == -1:
        bw.setWallpaper()
