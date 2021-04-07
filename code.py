
from __future__ import  print_function

import face_recognition
 
import cv2 ,pickle, os, time
 
import numpy as np

import sys, httplib2, datetime, io

from time import gmtime, strftime

from apiclient import discovery

import oauth2client

from oauth2client import tools, file, client

from datetime import date,datetime

import smtplib

from email.mime.text import MIMEText

from email.mime.image import MIMEImage

from email.mime.multipart import MIMEMultipart

import _thread

from googleapiclient.http import MediaIoBaseDownload

from googleapiclient.discovery import build

from google_auth_oauthlib.flow import InstalledAppFlow

from google.auth.transport.requests import Request

import imutils

from imutils import paths

os.environ["PYTHONPATH"] ="<add_your_path_to_python location>"


SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def main():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=1337)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token, protocol=0)
    service = build('drive', 'v3', credentials=creds)

    folder_name = ''
    folder_id = ''
    location = ''

    folder = service.files().list(
            q=f"name contains '<put folder name> ' and mimeType='application/vnd.google-apps.folder'",
            fields='files(id, name, parents)').execute()

    total = len(folder['files'])
    if total != 1:
        print(f'{total} folders found')
        if total == 0:
            sys.exit(1)
        prompt = '<choose the folder name>'
        for i in range(total):
            prompt += f'[{i}]: {get_full_path(service, folder["files"][i])}\n'
        prompt += '\nYour choice: '
        choice = int(input(prompt))
        if 0 <= choice and choice < total:
            folder_id = folder['files'][choice]['id']
            folder_name = folder['files'][choice]['name']
        else:
            sys.exit(1)
    else:
        folder_id = folder['files'][0]['id']
        folder_name = folder['files'][0]['name']

    print(f'{folder_name}')
    download_folder(service, folder_id, location, folder_name)

def get_full_path(service, folder):

    if not 'parents' in folder:
        return folder['name']
    files = service.files().get(fileId=folder['parents'][0], fields='id, name, parents').execute()
    path = files['name'] + ' > ' + folder['name']
    while 'parents' in files:
        files = service.files().get(fileId=files['parents'][0], fields='id, name, parents').execute()
        path = files['name'] + ' > ' + path
    return path

def download_folder(service, folder_id, location, folder_name):

    if not os.path.exists(location + folder_name):
        os.makedirs(location + folder_name)
    location += folder_name + '/'

    result = []
    page_token = None
    while True:
        files = service.files().list(
                q=f"'{folder_id}' in parents",
                fields='nextPageToken, files(id, name, mimeType)',
                pageToken=page_token,
                pageSize=1000).execute()
        result.extend(files['files'])
        page_token = files.get("nextPageToken")
        if not page_token:
            break

    result = sorted(result, key=lambda k: k['name'])

    total = len(result)
    current = 1
    for item in result:
        file_id = item['id']
        filename = item['name']
        mime_type = item['mimeType']
        print(f' {filename} {mime_type} ({current}/{total})')
        if mime_type == 'application/vnd.google-apps.folder':
            download_folder(service, file_id, location, filename)
        elif not os.path.isfile(location + filename):
            download_file(service, file_id, location, filename, mime_type)
        current += 1

def download_file(service, file_id, location, filename, mime_type):

    if 'vnd.google-apps' in mime_type:
        request = service.files().export_media(fileId=file_id,
                mimeType='application/pdf')
        filename += '.pdf'
    else:
        request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(location + filename, 'wb')
    downloader = MediaIoBaseDownload(fh, request, 1024 * 1024 * 1024)
    done = False
    while done is False:
        try:
            status, done = downloader.next_chunk()
        except:
            fh.close()
            os.remove(location + filename)
            sys.exit(1)
        print(f'\rDownload {int(status.progress() * 100)}%.', end='')
        sys.stdout.flush()
    print('')

if __name__ == '__main__':
    main()

def SendMail(ImgFileName):
    
    img_data = open(ImgFileName, 'rb').read()
    
    msg = MIMEMultipart()
    
    msg['Subject'] = 'subject'
    
    msg['From'] = '<sender email address>'
    
    msg['To'] = '<recipient mail address>'

    text = MIMEText("test")
    
    msg.attach(text)
    
    image = MIMEImage(img_data, name=os.path.basename(ImgFileName))
    
    msg.attach(image)

    s = smtplib.SMTP('smtp.gmail.com', 587)
    
    s.ehlo()
    
    s.starttls()
    
    s.ehlo()
    
    s.login('<your email id>', '<your password>' )
    
    s.sendmail(msg['From'], msg['To'], msg.as_string())
    
    s.quit()

def addface() :
    
    print("[INFO] quantifying faces...")
    imagePaths = list(paths.list_images("<add_folder_Path_here>"))

    # initialize the list of known encodings and known names
    knownEncodings = []
    knownNames = []

    # loop over the image paths
    for (i, imagePath) in enumerate(imagePaths):
            # extract the person name from the image path
            print("[INFO] processing image {}/{}".format(i + 1,
                    len(imagePaths)))
            name = imagePath.split(os.path.sep)[-2]

            # load the input image and convert it from RGB (OpenCV ordering)
            # to dlib ordering (RGB)
            image = cv2.imread(imagePath)
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # detect the (x, y)-coordinates of the bounding boxes
            # corresponding to each face in the input image
            boxes = face_recognition.face_locations(rgb,
                    model='hog')

            # compute the facial embedding for the face
            encodings = face_recognition.face_encodings(rgb, boxes)

            # loop over the encodings
            for encoding in encodings:
                    # add each encoding + name to our set of known names and
                    # encodings
                    knownEncodings.append(encoding)
                    knownNames.append(name)

    # dump the facial encodings + names to disk
    print("[INFO] serializing encodings...")
    data = {"encodings": knownEncodings, "names": knownNames}
    f = open("encode.dat", "wb")
    f.write(pickle.dumps(data))
    f.close() 
      
    print("*********succesfully added*****************")

def detectface() :
     
        # load the known faces and embeddings
    print("[INFO] loading encodings...")
    data = pickle.loads(open("encode.dat", "rb").read())

    # initialize the video stream and pointer to output video file, then
    # allow the camera sensor to warm up
    print("[INFO] starting video stream...")
    #url= "http://192.168.43.74:8080/video"
    vs = cv2.VideoCapture(0)
    time.sleep(2.0)
    global name
    mod=[]

    # loop over frames from the video file stream
    while True:
            # grab the frame from the threaded video stream
            _,frame = vs.read()
            
            # convert the input frame from BGR to RGB then resize it to have
            # a width of 750px (to speedup processing)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb = imutils.resize(frame, width=750)
            r = frame.shape[1] / float(rgb.shape[1])

            # detect the (x, y)-coordinates of the bounding boxes
            # corresponding to each face in the input frame, then compute
            # the facial embeddings for each face
            boxes = face_recognition.face_locations(rgb,
                    model="hog")
            encodings = face_recognition.face_encodings(rgb, boxes)
            names = []

            # loop over the facial embeddings
            for encoding in encodings:
                    # attempt to match each face in the input image to our known
                    # encodings
                    matches = face_recognition.compare_faces(data["encodings"],
                            encoding, tolerance=0.49)
                    name = "Unknown"

                    # check to see if we have found a match
                    if True in matches:
                            # find the indexes of all matched faces then initialize a
                            # dictionary to count the total number of times each face
                            # was matched
                            matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                            counts = {}

                            # loop over the matched indexes and maintain a count for
                            # each recognized face face
                            for i in matchedIdxs:
                                    name = data["names"][i]
                                    counts[name] = counts.get(name, 0) + 1

                            # determine the recognized face with the largest number
                            # of votes (note: in the event of an unlikely tie Python
                            # will select first entry in the dictionary)
                            name = max(counts, key=counts.get)
                            
                    
                    # update the list of names
                    names.append(name)

            # loop over the recognized faces
            for ((top, right, bottom, left), name) in zip(boxes, names):
                    # rescale the face coordinates
                    top = int(top * r)
                    right = int(right * r)
                    bottom = int(bottom * r)
                    left = int(left * r)

                    # draw the predicted face name on the image
                    cv2.rectangle(frame, (left, top), (right, bottom),
                            (0, 255, 0), 2)
                    y = top - 15 if top - 15 > 15 else top + 15
                    cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
                            0.75, (0, 255, 0), 2)
                    if(name in data["names"]):
                        if _:
                            cv2.imwrite('caught.jpg',frame)
                     
                    mod.append(name)
                
                
                    if(mod.count(name)<=1):

                        time.sleep(2)

                        _thread.start_new_thread(SendMail, ('caught.jpg', ))
                    
            cv2.imshow("Frame", frame)
            
            if(cv2.waitKey(1) & 0xFF ==ord('q')):
               print("***********PROGRAM STOPPED**************")
               break

    # do a bit of cleanup
    vs.release()
    cv2.destroyAllWindows()
    


addface()

detectface()







