import subprocess
import time
import threading
import queue

process = subprocess.Popen(["ffprobe", "-select_streams", "v", "-show_entries", "packet=size:stream=duration", "-of", "compact=p=0:nk=1", "http://192.168.1.169:PORT"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
limit = 25000
last = 0
decoded_q = queue.Queue()

class ffmotion(object):
    def __init__(self):
        #All the threads start in the "__init__" function simultaneously.
        self.thread1 = threading.Thread(target= self.read)
        self.thread1.start()
        
        self.thread2 = threading.Thread(target= self.triggered)
        self.thread2.start()
        
        self.thread3 = threading.Thread(target= self.record)
        self.thread3.start()

    def read(self):
        print("Thread 1")
        print(self.thread1.is_alive())

        #This while statement starts a command in the global varibales to get
        #the bitrate of the IP cameras stream. Once the command is run the bitrate
        #is constantly put into a queue for the "triggered" function.
        while True:
            nextline = process.stdout.readline()
            if nextline == '' and process.poll() is not None:
                break

            if nextline:
                decoded = nextline.decode("utf-8")
                print(decoded)

            try:
                int(decoded.strip())
                decoded_q.put(decoded)
            except:
                pass

    def triggered(self):
        print("Thread 2")
        #The "triggered" function constantly checks the decoded bitrate, if the
        #last decoded bitrate is higher than the last and if above the limit this
        #will trigger a shared variable to become "True".
        self.recording = False
        self.start = False
        while True:
            decoded = decoded_q.get()
            try:
                if int(decoded) > limit and last > limit:
                    print("Last: ", last, " Decoded: ", int(decoded))
                    print("TRIGGERRRRRED")
                    last = 0
                    if self.recording == False:
                        self.start = True
                    else:
                        print("Already recording")
                else:
                    last = int(decoded)
            except:
                pass

    def record(self):
        #Once the "self.start" variable is "True" the "record" function will start
        #to record for "1500" frames this is a minute of recording at 25fps. Once
        #recording has finished the "self.start" variable is set to "False" ready
        #to be triggered again.
        while True:
            try:
                if self.start == True and self.recording == False:
                    print("Recording")
                    self.recording = True
                    self.rec = subprocess.Popen(["sudo", "ffmpeg", "-y", "-i", "http://192.168.1.169:PORT", "-vcodec", "copy", "-r", "25", "-vframes", "1500", "/home/pi/motioncap.mp4"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                poll = self.rec.poll()
                if poll != None:
                    self.recording = False
                    self.start = False
            except:
                pass
        #subprocess.Popen(["sudo", "ffmpeg", "-y", "-i", "http://192.168.1.169:PORT", "-r", "1", "-vframes", "1", "/home/pi/motioncap.jpeg"])

ffmotion()
