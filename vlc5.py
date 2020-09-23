import RPi.GPIO as GPIO
#from time import sleep
import time
import subprocess
#import os
import threading
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import os.path
from os import path
import json
import math
from datetime import datetime


PinIn = 12
ch = ""
ch_buff = "0"
playlist = []
mute = False
volume = 0
mode = "null"


content = open("/scripts/TV/ir_code.json", "r").read()
obj = json.loads(content)


#---------------

row_space = 27
top_padding = 65

menuTitlePos = (25, 15)
prevImgSize = (720, 380)
prevImgSize2 = (1280, 720)
prevImgColor = (0, 0, 0)
menu_title_color = (246, 255, 227, 255)
menu_item_color = (255, 255, 255, 255)
menu_sel_item_color = (216, 222, 51, 255)

hrLineColor = (150, 150, 150, 255)
hrLineTopPos = (15, 35)
hrLineBotPos = (15, 325)

menu_count_items = 0
menu_item_position = 0
menu_row_position = 0
menu_item_count = 10
menu_row_count = 0
menu_group = ""
menu_item_addr = ""
menu_command = ""

fontLite = "/scripts/TV/Roboto-Light.ttf"
fontBold = "/scripts/TV/Roboto-Black.ttf"

menuHrLine = "__________________________________________________________________________________________________"
numStrWrap = "   "

pointHeight = 313
point = 180
pointText = 30



recording = False

json_menu = open("/scripts/TV/menu.json", "r").read()

#---------------


digits = obj["buttons"]["digits"]
commands = obj["buttons"]["commands"]




GPIO.setmode(GPIO.BOARD)
GPIO.setup(PinIn,GPIO.IN)

def hello():

    os.system("killall fim")
    p2 = subprocess.Popen(['fim', '-a', '/scripts/TV/hello.jpg'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def getPlaylist():

    global playlist
    
    playlist = []
    
    pl = open("/scripts/TV/playlist.txt", "r").read()

    content = open("/scripts/TV/playlist/" + pl, "r").read()
    split = content.split("\n#")

    i = 0
    for x in split:

        try:
        
            name = x.split("\n")[0].split(",")[1].rstrip()
            source = x.split("\n")[1].rstrip()
            #print(str(i) + " " + name)
            playlist.append({"name": name, "source": source})
            
            i = i + 1
            
        except Exception:
            
            pass
            

def ConvertHex(BinVal): #Converts binary data to hexidecimal
	tmpB2 = int(str(BinVal), 2)
	return hex(tmpB2)
    
   		
def getData(): #Pulls data from sensor
	num1s = 0 #Number of consecutive 1s
	command = [] #Pulses and their timings
	binary = 1 #Decoded binary command
	previousValue = 0 #The previous pin state
	value = GPIO.input(PinIn) #Current pin state
	
	while value: #Waits until pin is pulled low
		value = GPIO.input(PinIn)
	
	startTime = datetime.now() #Sets start time
	
	while True:
		if value != previousValue: #Waits until change in state occurs
			now = datetime.now() #Records the current time
			pulseLength = now - startTime #Calculate time in between pulses
			startTime = now #Resets the start time
			command.append((previousValue, pulseLength.microseconds)) #Adds pulse time to array (previous val acts as an alternating 1 / 0 to show whether time is the on time or off time)
		
		#Interrupts code if an extended high period is detected (End Of Command)	
		if value:
			num1s += 1
		else:
			num1s = 0
		
		if num1s > 10000:
			break
		
		#Reads values again
		previousValue = value
		value = GPIO.input(PinIn)
		
	#Covers data to binary
	for (typ, tme) in command:
		if typ == 1:
			if tme > 1000: #According to NEC protocol a gap of 1687.5 microseconds repesents a logical 1 so over 1000 should make a big enough distinction
				binary = binary * 10 + 1
			else:
				binary *= 10
				
	if len(str(binary)) > 34: #Sometimes the binary has two rouge charactes on the end
		binary = int(str(binary)[:34])
		
	return binary


def runTest():

    command = ConvertHex(getData())
    return command


def playVideo(video):
    
    path = "/scripts/TV/recording/"
    
    previewLabel("Воспроизведение видео: " + video)
    os.system("killall vlc")
    p = subprocess.Popen(['vlc', path + video, "--meta-title=" + video], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def switchOnChannel(channel):
        
    global p

    os.system("killall vlc")
    
    if recording == False:
    
        p = subprocess.Popen(['vlc', playlist[channel]["source"], "--meta-title=" + str(channel) + " "+playlist[channel]["name"]], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    else:
    
        now = datetime.now()
            
        year = now.strftime("%Y")
        #print("year:", year)

        month = now.strftime("%m")
        #print("month:", month)

        day = now.strftime("%d")
        #print("day:", day)

        time = now.strftime("%H:%M:%S")
        #print("time:", time)

        #date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
        date_time = now.strftime("%m-%d-%Y_%H-%M-%S")
        #print("date and time:",date_time)    
        
        
        os.system("killall vlc")
        p = subprocess.Popen(['vlc', playlist[channel]["source"], '--sout=#duplicate{dst=display,vcodec=H263,vb=256,scale=1,acodec=mp3,ab=128,channels=2,dst=std{access=file,mux=ts,dst="/scripts/TV/recording/'+playlist[channel]["name"]+'_'+date_time+'.mpg"}}'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        #os.system('vlc ' + playlist[channel]["source"] + ' --sout=#duplicate{dst=display,vcodec=H263,vb=256,scale=1,acodec=mp3,ab=128,channels=2,dst=std{access=file,mux=ts,dst="recording/video.mpg"}}')
        
def previewChannel(channel="", chname="", functext=""):
    
    file = "ch_img.png"
    if path.exists(file):
        os.remove("/scripts/TV/"+file)
    else:
        pass
    
    ch_size = 23*len(channel)
    
    
    
    img = Image.new('RGB', prevImgSize2, color = prevImgColor)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(fontBold, 35)
    draw.text((25, 25), channel, font=font, fill=(255, 255, 255, 255))
    draw.text(((38 + ch_size), 25), chname, font=font, fill=(202, 156, 247, 255))
    draw.text((25, 75), functext, font=font, fill=(194, 163, 52, 255))
    img.save("/scripts/TV/"+file)

    os.system("killall fim")
    p2 = subprocess.Popen(['fim', '-a', '/scripts/TV/ch_img.png'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def previewLabel(chname=""):
    
    file = "ch_img.png"
    if path.exists(file):
        os.remove("/scripts/TV/"+file)
    else:
        pass
    
    
    img = Image.new('RGB', prevImgSize2, color = prevImgColor)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(fontBold, 35)
    draw.text((25, 25), chname, font=font, fill=(202, 156, 247, 255))
    img.save("/scripts/TV/"+file)

    os.system("killall fim")
    p2 = subprocess.Popen(['fim', '-a', '/scripts/TV/ch_img.png'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def setChannel():

    global ch
    global ch_buff
    
    print(">>>"+ch+" - "+str(len(playlist)))
    
    if len(ch) == 0:
        previewChannel("Error: Channel number is empty")
        print("channel number is empty")
    else:
    
        if int(ch) > len(playlist)-1:
            text = "Error: Channel " + str(len(playlist)-1)+" is maximum"
            previewChannel(text)
            print(text)
        else:
            previewChannel(ch, playlist[int(ch)]["name"])
            switchOnChannel(int(ch))
            print("switch on channel: " + ch)

        ch_buff = ch
        ch = ""

def nextPrevChannel(com):
    
    global ch_buff
    count_ch = len(playlist)
    
    if com == 1:
        
        if count_ch-1 == int(ch_buff):
            ch_buff = "0"
        else:
            ch_buff = str(int(ch_buff) + 1)
        
        
        
    elif com == 0:
        
        if ch_buff == "0":
            ch_buff = str(count_ch-1)
        else:
            ch_buff = str(int(ch_buff) - 1)
        
    
    previewChannel(ch_buff, playlist[int(ch_buff)]["name"])
    print("c: "+ch_buff)
    switchOnChannel(int(ch_buff))


def setDigits(string_int):

    global ch
    ch = ch + string_int
    print("integer: " + string_int)
    print("set channel: " + ch)
        
    #previewChannel(ch)


        


    
def menu(index=0, row=0):
    
    global row_space
    global top_padding
    global menu_title_color
    global menu_item_color
    global menu_sel_item_color
    global menu_count_items
    global menu_item_position
    global menu_item_addr
    global menu_row_count
    global json_menu
    
    menu_item_count = 10
    
    obj = json.loads(json_menu)
    
    menuGroups = obj["MenuGroups"]
    
    file = "menu.png"
    if path.exists(file):
        os.remove("/scripts/TV/"+file)
    else:
        pass
        

    img = Image.new('RGB', prevImgSize, color = prevImgColor)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(fontLite, 17)
    fontTitle = ImageFont.truetype(fontBold, 25)
    fontHr = ImageFont.truetype(fontLite, 17)
    fontSpec = ImageFont.truetype(fontLite, 80)
    fontSpecText = ImageFont.truetype(fontLite, 15)

    draw.text(menuTitlePos, obj["title"], font=fontTitle, fill=menu_title_color)
    
    draw.text(hrLineTopPos, menuHrLine, font=fontHr, fill=hrLineColor)     #hr up 
    draw.text(hrLineBotPos, menuHrLine, font=fontHr, fill=hrLineColor)     #hr bottom


#-----------------------------------------
    itemlist = []
    i = 0
    for x in menuGroups:
        
        if menuGroups[i]["type"] == "menu":
        
            itemlist.append(menuGroups[i])
        
        i = i + 1
#--------------------------------------------

    
    z = 0 # lines
    items = 0
    count_items = len(itemlist)
    rows = math.floor(len(itemlist) / menu_item_count)

    g = count_items - (menu_item_count * row)
    if g < menu_item_count:
        if index >= g:
            index = g-1
            menu_item_position = index

    for x in itemlist:
    

        zi = z - menu_item_count * row
        zi_start = menu_item_count * row - 1
        zi_end = menu_item_count * (row + 1) - 1

        if z > zi_start:

            if zi == index:
            
                draw.text((25, (row_space * zi) + top_padding), "• " + itemlist[z]["title"], font=font, fill=menu_sel_item_color)
                menu_item_addr = itemlist[z]["groupName"]
                
            else:
                
                draw.text((25, (row_space * zi) + top_padding), "  " + itemlist[z]["title"], font=font, fill=menu_item_color)   
                
            items = items + 1
            
        z = z + 1
        
        if z > zi_end:
        
            break

    menu_count_items = items
    menu_row_count = rows
    
    draw.text((15, pointHeight), "•", font=fontSpec, fill=(245, 81, 66, 255))   
    draw.text((15 + pointText, pointHeight + 38), "Список каналов", font=fontSpecText, fill=(255, 255, 255, 255))   
    
    draw.text((15 + point, pointHeight), "•", font=fontSpec, fill=(26, 135, 37, 255))   
    draw.text((15 + point + pointText, pointHeight + 38), "Фаворит. список", font=fontSpecText, fill=(255, 255, 255, 255))   
    
    draw.text((15 + (point * 2), pointHeight), "•", font=fontSpec, fill=(226, 232, 44, 255))   
    draw.text((15 + point * 2 + pointText, pointHeight + 38), "Плейлисты", font=fontSpecText, fill=(255, 255, 255, 255))   
    
    draw.text((15 + (point * 3), pointHeight), "•", font=fontSpec, fill=(44, 129, 232, 255))   
    draw.text((15 + point * 3 + pointText, pointHeight + 38), "Видеозаписи", font=fontSpecText, fill=(255, 255, 255, 255))   


#-------------------------------------------

    img.save("/scripts/TV/"+file)


    os.system("killall fim")
    p2 = subprocess.Popen(['fim', '-a', '/scripts/TV/menu.png'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print("item addr: " + menu_item_addr)



def subMenu(group="", index=0, row=0):
   
    global row_space
    global top_padding
    global menu_title_color
    global menu_item_color
    global menu_sel_item_color
    global menu_count_items
    global menu_item_position
    global menu_item_addr
    global menu_row_count
    global menu_command
    global json_menu
    
    menu_item_count = 10

    
    obj = json.loads(json_menu)
    
    menuGroups = obj["MenuGroups"]

    file = "menu.png"
    if path.exists(file):
        os.remove("/scripts/TV/"+file)
    else:
        pass
        
    img = Image.new('RGB', prevImgSize, color = prevImgColor)
    draw = ImageDraw.Draw(img)
        
    font = ImageFont.truetype(fontLite, 17)
    fontSpec = ImageFont.truetype(fontLite, 80)
    fontSpecText = ImageFont.truetype(fontLite, 15)
    fontTitle = ImageFont.truetype(fontBold, 25)
    fontText = ImageFont.truetype(fontLite, 15)
    fontHr = ImageFont.truetype(fontLite, 17)

    itemtype = ""
    i = 0
    for x in menuGroups:
        
        items = menuGroups[i]["items"]
        
        if menuGroups[i]["groupName"] == group:
            
            menu_count_items = len(items)
            
            draw.text(menuTitlePos, menuGroups[i]["title"], font=fontTitle, fill=menu_title_color)
                        
            draw.text(hrLineTopPos, menuHrLine, font=fontHr, fill=hrLineColor)     #hr up 
            draw.text(hrLineBotPos, menuHrLine, font=fontHr, fill=hrLineColor)     #hr bottom

#--------------------------------------

            itemlist = []
            a = 0
            for y in items:
                
                if items[a]["type"] == "item":
                
                    itemtype = "items"
                    
                    itemlist.append(items[a])
                    
                                
                if items[a]["type"] == "text":
                
                    draw.text((25, (row_space * a) + top_padding), items[a]["text"], font=fontText, fill=(120, 120, 120, 255))
                
                elif items[a]["type"] == "textfile":
                
                    txtfile = open("/scripts/TV/" + items[a]["file"], "r").read()
                    draw.text((25, (row_space * a) + top_padding), txtfile, font=fontText, fill=(120, 120, 120, 255))
                
                elif items[a]["type"] == "command":
                
                    if items[a]["name"] == "show_playlist_lists":
                        pass
#==========================================

                        
                        sd = os.listdir("/scripts/TV/playlist/")                        
                        try:
                            pl = open("/scripts/TV/playlist.txt", "r").read()
                        except:
                            pl = ""


                        
                        z = 0 # lines
                        items = 0
                        count_items = len(sd)
                        rows = math.floor(len(sd) / menu_item_count - 0.1)

                        g = count_items - (menu_item_count * row)
                        if g < menu_item_count:
                            if index >= g:
                                index = g-1
                                menu_item_position = index

                        for x in sd:
                        
                            name = x.rstrip()
                            
                            if pl == name:
                                setted = "[ √ ]   "
                            else:
                                setted = "[    ]   "
                            

                            zi = z - menu_item_count * row
                            zi_start = menu_item_count * row - 1
                            zi_end = menu_item_count * (row + 1) - 1

                            if z > zi_start:
                                
                                if zi == index:
                                
                                    draw.text((25, (row_space * zi) + top_padding), "• " + str(z) + numStrWrap + setted + name, font=font, fill=menu_sel_item_color)
                                    menu_command = "set_playlist:" + name
                                    
                                else:
                                    
                                    draw.text((25, (row_space * zi) + top_padding), "  " + str(z) + numStrWrap + setted + name, font=font, fill=menu_item_color)   
                                    
                                items = items + 1
                                
                                
                            z = z + 1
                            
                            if z > zi_end:
                            
                                break

                        menu_count_items = items
                        menu_row_count = rows
                        

                        
                        draw.text((15, pointHeight), "•", font=fontSpec, fill=(245, 81, 66, 255))   
                        draw.text((15 + pointText, pointHeight + 38), "Удалить", font=fontSpecText, fill=(255, 255, 255, 255))   
                        
                        draw.text((15 + point, pointHeight), "•", font=fontSpec, fill=(26, 135, 37, 255))   
                        draw.text((15 + point + pointText, pointHeight + 38), "-", font=fontSpecText, fill=(255, 255, 255, 255))   
                        
                        draw.text((15 + (point * 2), pointHeight), "•", font=fontSpec, fill=(226, 232, 44, 255))   
                        draw.text((15 + point * 2 + pointText, pointHeight + 38), "-", font=fontSpecText, fill=(255, 255, 255, 255))   
                        
                        draw.text((15 + (point * 3), pointHeight), "•", font=fontSpec, fill=(44, 129, 232, 255))   
                        draw.text((15 + point * 3 + pointText, pointHeight + 38), "-", font=fontSpecText, fill=(255, 255, 255, 255))   

                  
                    
                    elif items[a]["name"] == "show_channel_list":
 
#==========================================                    
     
                        
                        z = 0 # lines
                        items = 0
                        count_items = len(playlist)
                        rows = math.floor(len(playlist) / menu_item_count - 0.1)
                
                        g = count_items - (menu_item_count * row)
                        if g < menu_item_count:
                            if index >= g:
                                index = g-1
                                menu_item_position = index

                        for x in playlist:
                        
                            zi = z - menu_item_count * row
                            zi_start = menu_item_count * row - 1
                            zi_end = menu_item_count * (row + 1) - 1



                            if z > zi_start:
                                                 
                                if zi == index:
                                    draw.text((25, (row_space * zi) + top_padding), "• " + str(z) + numStrWrap + playlist[z]["name"], font=font, fill=menu_sel_item_color)
                                    menu_command = "switch_on_channel:" + str(z)
                                else:
                                    draw.text((25, (row_space * zi) + top_padding), "  " + str(z) + numStrWrap + playlist[z]["name"], font=font, fill=menu_item_color)
                                
                                items = items + 1
                                
                            z = z + 1
                            
                            if z > zi_end:
                            
                                break

                        menu_count_items = items
                        menu_row_count = rows
                       
            
                        draw.text((15, pointHeight), "•", font=fontSpec, fill=(245, 81, 66, 255))   
                        draw.text((15 + pointText, pointHeight + 38), "Удалить", font=fontSpecText, fill=(255, 255, 255, 255))   
                        
                        draw.text((15 + point, pointHeight), "•", font=fontSpec, fill=(26, 135, 37, 255))   
                        draw.text((15 + point + pointText, pointHeight + 38), "-", font=fontSpecText, fill=(255, 255, 255, 255))   
                        
                        draw.text((15 + (point * 2), pointHeight), "•", font=fontSpec, fill=(226, 232, 44, 255))   
                        draw.text((15 + point * 2 + pointText, pointHeight + 38), "-", font=fontSpecText, fill=(255, 255, 255, 255))   
                        
                        draw.text((15 + (point * 3), pointHeight), "•", font=fontSpec, fill=(44, 129, 232, 255))   
                        draw.text((15 + point * 3 + pointText, pointHeight + 38), "-", font=fontSpecText, fill=(255, 255, 255, 255))   

                        
                    elif items[a]["name"] == "show_videos":
                        
#==========================================
                        menu_item_count = 10



                        sd = os.listdir("/scripts/TV/recording/")                        
                        
                        z = 0 # lines
                        items = 0
                        count_items = len(sd)
                        rows = math.floor(len(sd) / menu_item_count - 0.1)

                        g = count_items - (menu_item_count * row)
                        if g < menu_item_count:
                            if index >= g:
                                index = g-1
                                menu_item_position = index

                        for x in sd:
                        
                            name = x.rstrip()

                            zi = z - menu_item_count * row
                            zi_start = menu_item_count * row - 1
                            zi_end = menu_item_count * (row + 1) - 1

                            if z > zi_start:
                                
                                if zi == index:
                                
                                    draw.text((25, (row_space * zi) + top_padding), "• " + str(z) + numStrWrap + name, font=font, fill=menu_sel_item_color)
                                    menu_command = "play_video:" + name
                                    
                                else:
                                    
                                    draw.text((25, (row_space * zi) + top_padding), "  " + str(z) + numStrWrap + name, font=font, fill=menu_item_color)   
                                    
                                items = items + 1
                                
                                
                            z = z + 1
                            
                            if z > zi_end:
                            
                                break
 
                        menu_count_items = items
                        menu_row_count = rows
            
                        draw.text((15, pointHeight), "•", font=fontSpec, fill=(245, 81, 66, 255))   
                        draw.text((15 + pointText, pointHeight + 38), "Удалить", font=fontSpecText, fill=(255, 255, 255, 255))   
                        
                        draw.text((15 + point, pointHeight), "•", font=fontSpec, fill=(26, 135, 37, 255))   
                        draw.text((15 + point + pointText, pointHeight + 38), "-", font=fontSpecText, fill=(255, 255, 255, 255))   
                        
                        draw.text((15 + (point * 2), pointHeight), "•", font=fontSpec, fill=(226, 232, 44, 255))   
                        draw.text((15 + point * 2 + pointText, pointHeight + 38), "-", font=fontSpecText, fill=(255, 255, 255, 255))   
                        
                        draw.text((15 + (point * 3), pointHeight), "•", font=fontSpec, fill=(44, 129, 232, 255))   
                        draw.text((15 + point * 3 + pointText, pointHeight + 38), "-", font=fontSpecText, fill=(255, 255, 255, 255))   


            
#==========================================                    
                   # break
                    
                a = a + 1
            
        i = i + 1


    if itemtype == "items":
        
        z = 0 # lines
        items = 0
        count_items = len(itemlist)
        rows = math.floor(len(itemlist) / menu_item_count - 0.1)

        g = count_items - (menu_item_count * row)
        if g < menu_item_count:
            if index >= g:
                index = g-1
                menu_item_position = index

        for x in itemlist:
        

            zi = z - menu_item_count * row
            zi_start = menu_item_count * row - 1
            zi_end = menu_item_count * (row + 1) - 1

            if z > zi_start:

                if zi == index:
                
                    draw.text((25, (row_space * zi) + top_padding), "• " + itemlist[z]["title"], font=font, fill=menu_sel_item_color)
                    menu_item_addr = itemlist[z]["name"]
                    
                else:
                    
                    draw.text((25, (row_space * zi) + top_padding), "  " + itemlist[z]["title"], font=font, fill=menu_item_color)   
                    
                items = items + 1
                
            z = z + 1
            
            if z > zi_end:
            
                break

        menu_count_items = items
        menu_row_count = rows
        
        
        draw.text((15, pointHeight), "•", font=fontSpec, fill=(245, 81, 66, 255))   
        draw.text((15 + pointText, pointHeight + 38), "Список каналов", font=fontSpecText, fill=(255, 255, 255, 255))   
        
        draw.text((15 + point, pointHeight), "•", font=fontSpec, fill=(26, 135, 37, 255))   
        draw.text((15 + point + pointText, pointHeight + 38), "Фаворит. список", font=fontSpecText, fill=(255, 255, 255, 255))   
        
        draw.text((15 + (point * 2), pointHeight), "•", font=fontSpec, fill=(226, 232, 44, 255))   
        draw.text((15 + point * 2 + pointText, pointHeight + 38), "Плейлисты", font=fontSpecText, fill=(255, 255, 255, 255))   
        
        draw.text((15 + (point * 3), pointHeight), "•", font=fontSpec, fill=(44, 129, 232, 255))   
        draw.text((15 + point * 3 + pointText, pointHeight + 38), "Видеозаписи", font=fontSpecText, fill=(255, 255, 255, 255))   

        
        
        #print(" 8888888888888888888888 "+str(itemlist)+" 888888888888888888888888")



    img.save("/scripts/TV/"+file)

    os.system("killall fim")
    p2 = subprocess.Popen(['fim', '-a', '/scripts/TV/menu.png'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print("item addr: " + menu_item_addr)

def move(direction):

    global mode
    global menu_item_position
    global menu_row_position
    
    
    
    
    
    if direction == "up":
        
        if menu_item_position < 1:
            menu_item_position = menu_count_items - 1
        else:
            menu_item_position = menu_item_position - 1
                        
        if mode == "menu":
            menu(menu_item_position, menu_row_position)
        elif mode == "submenu":
            subMenu(menu_group, menu_item_position, menu_row_position)
            print("group: " + menu_group)
        else:
            pass
                
    elif direction == "down":
        
        if (menu_count_items - 1) == menu_item_position:
            menu_item_position = 0
        else:
            menu_item_position = menu_item_position + 1
                        
        if mode == "menu":
            menu(menu_item_position, menu_row_position)
        elif mode == "submenu":
            subMenu(menu_group, menu_item_position, menu_row_position)
            print("group: " + menu_group)
        else:
            pass
                
                
    elif direction == "left":
    
        if menu_row_position < 1:
            menu_row_position = menu_row_count
        else:
            menu_row_position = menu_row_position - 1
        
        if mode == "menu":
            menu(menu_item_position, menu_row_position)
        elif mode == "submenu":
            subMenu(menu_group, menu_item_position, menu_row_position)
            print("group: " + menu_group)
        else:
            pass
                              
        
    elif direction == "right":
    
        if (menu_row_count) == menu_row_position:
            menu_row_position = 0
        else:
            menu_row_position = menu_row_position + 1
         
         
        if mode == "menu":
            menu(menu_item_position, menu_row_position)
        elif mode == "submenu":
            subMenu(menu_group, menu_item_position, menu_row_position)
            print("group: " + menu_group)
        else:
            pass


def setPlaylist(playlist):

    global ch_buff
    f = open("/scripts/TV/playlist.txt", "w")
    f.write(playlist)
    f.close()
    getPlaylist()
    ch_buff = "0"
    print("Playlist "+playlist+" is setted!")



getPlaylist()
hello()


while True:

    print("item pos: " + str(menu_item_position))
    print("mode: " + mode)
    code = runTest()
    
    uncnown_flag = True
    
    if len(code) == 11:
    
        print("code:"+code)

        for x in digits:
            if code == digits[x]:
                print("ch: " + x)
                uncnown_flag = False
                setDigits(x)
                break

        for x in commands:
            if code == x["code"]:
                print("command: " + x["name"])
                uncnown_flag = False
                
                if x["name"] == "enter":
                    
                    
                    if mode == "null":
                        setChannel()
                    elif mode == "menu":
                    
                        menu_item_position = 0
                    
                        menu_group = menu_item_addr
                        subMenu(menu_item_addr, 0)
                        mode = "submenu"
                        print("group: " + menu_group)
                        
                    elif mode == "submenu":
                    
                        command = menu_command.split(":")
                        
                        if command[0] == "set_playlist":
                        
                            playlist = command[1]
                            print("PL1: " + playlist)
                            setPlaylist(playlist)
                            subMenu(menu_item_addr, menu_item_position, 0)
                            menu_command = ""

                        elif command[0] == "play_video":
                        
                            mode = "video"
                            playVideo(command[1])
                        
                        elif command[0] == "switch_on_channel":
                        
                            menu_item_position = 0
                        
                            channel = command[1]
                            ch_buff = channel
                            
                            mode = "null"
                            previewChannel(ch_buff, playlist[int(ch_buff)]["name"])
                            switchOnChannel(int(ch_buff))
                            ch = ""
                            
                        else:
                        
                        
                            menu_item_position = 0
                            menu_group = menu_item_addr
                            subMenu(menu_item_addr, 0)
                        
                        
                        
                        menu_row_position = 0
                    else:
                        pass
                    
                
                elif x["name"] == "chUp":
                    
                    if mode == "null":
                    
                        if recording == True:
                    
                            recording = False
                        
                        else:    

                            nextPrevChannel(1)
                    
                elif x["name"] == "chDown":
                    
                    if mode == "null":
                    
                        if recording == True:
                    
                            recording = False
                        
                        else:    

                            nextPrevChannel(0)
                    
                    
                elif x["name"] == "volUp":
                    
                    if mode == "null":
                        p.stdin.write("volup\n".encode())
                        p.stdin.flush()
                    
                elif x["name"] == "volDown":
                    
                    if mode == "null":
                        p.stdin.write("voldown\n".encode())
                        p.stdin.flush()
                    
                elif x["name"] == "play":
                    
                    if mode == "null":
                        p.stdin.write("play\n".encode())
                        p.stdin.flush()
                        previewChannel(ch_buff, playlist[int(ch_buff)]["name"], "Запуск...")

                elif x["name"] == "pause":
                    
                    if mode == "null":
                        p.stdin.write("pause\n".encode())
                        p.stdin.flush()
                    
                elif x["name"] == "stop":
                    
                    if mode == "null":
                    
                        if recording == True:
                    
                            recording = False
                    
                            previewChannel(ch_buff, playlist[int(ch_buff)]["name"], "Запись остановлена")
                            switchOnChannel(int(ch_buff))
                            ch = ""
                        
                        else:
                    
                            p.stdin.write("stop\n".encode())
                            p.stdin.flush()
                            previewChannel(ch_buff, playlist[int(ch_buff)]["name"], "Остановлено")
                    
                elif x["name"] == "poweroff":
                    
                    os.system("sudo poweroff")
                    
                elif x["name"] == "reboot":
                    
                    os.system("sudo reboot")
                    
                elif x["name"] == "cancel":
                    
                    if mode == "null":
                        ch = ""
                    else:
                        mode = "null"
                        previewChannel(ch_buff, playlist[int(ch_buff)]["name"])
                        switchOnChannel(int(ch_buff))
                        ch = ""
                    
                    menu_item_position = 0
                    
                    
                elif x["name"] == "red":
                
                    
                    menu_item_count = 10

                    row = str(int(ch_buff) / menu_item_count)
                    
                    for s in row:
                        if s == ".":
                            row = row.split(".")[0]
                            break

                
                    mode = "submenu"
                    menu_item_position = int(ch_buff) - (menu_item_count * int(row))
                    menu_row_position = int(row)
                    menu_group = "channel_list"
                    menu_command = "show_channel_list"
                    item_pos = menu_item_position + (menu_item_count * menu_row_position)
                    os.system("killall vlc")    
                    
                    subMenu(menu_group, int(ch_buff), menu_row_position)


 
                elif x["name"] == "green":



                
                    mode = "submenu"
                    menu_item_position = 0
                    menu_row_position = 0
                    menu_group = "favorite"
                    #menu_command = "show_playlist_lists"
                    #menu_item_addr = "change_playlist"

                    os.system("killall vlc")    
                    
                    subMenu(menu_group, menu_item_position, menu_row_position)

                
                elif x["name"] == "yellow":
                
                    

                
                    mode = "submenu"
                    menu_item_position = 0
                    menu_row_position = 0
                    menu_group = "change_playlist"
                    menu_command = "show_playlist_lists"
                    menu_item_addr = "change_playlist"

                    os.system("killall vlc")    
                    
                    subMenu(menu_group, menu_item_position, menu_row_position)

                
                elif x["name"] == "blue":
                
                    mode = "submenu"
                    menu_item_position = 0
                    menu_row_position = 0
                    menu_group = "videos"
                    menu_command = "show_videos"
                    menu_item_addr = ""

                    os.system("killall vlc")    
                    
                    subMenu(menu_group, menu_item_position, menu_row_position)
                
                elif x["name"] == "up":
                    
                    if mode != "null":
                        move("up")
                    
                elif x["name"] == "down":
                
                    if mode != "null":
                        move("down")
                    
                elif x["name"] == "left":
                
                    if mode != "null":
                        move("left")
                    
                elif x["name"] == "right":
                
                    if mode != "null":
                        move("right")
                    
                elif x["name"] == "rec":
                
                    if recording == False:
                    
                        recording = True
                        
                        previewChannel(ch_buff, playlist[int(ch_buff)]["name"], "Запись")
                        switchOnChannel(int(ch_buff))
                        ch = ""
                        
                    else:
                    
                        recording = False
                
                        previewChannel(ch_buff, playlist[int(ch_buff)]["name"], "Запись остановлена")
                        switchOnChannel(int(ch_buff))
                        ch = ""
                
                elif x["name"] == "source":
                    
                    mode = "menu"
                    menu_item_position = 0
                    menu_row_position = 0
                    menu_group = ""
                    menu_command = ""
                    
                    os.system("killall vlc")
                    menu()
                    
                elif x["name"] == "mute":
                    
                    if mode == "null":
                    
                        if mute == False:
                            p.stdin.write("volume 0\n".encode())
                            p.stdin.flush()
                            mute = True
                        else:
                            p.stdin.write("volume 150\n".encode())
                            p.stdin.flush()
                            mute = False
                            
                break
        
        if uncnown_flag:
            print("uncnown code: " + code)

        
    
GPIO.cleanup()