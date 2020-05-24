#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from apiclient.discovery import build
from pytube import YouTube
from moviepy.editor import VideoFileClip
import os, sys, time

DATE_FORMAT_STR = '%Y-%m-%d'
DATETIME_FORMAT_STR = '%Y-%m-%dT%H:%M:%SZ'
DEFAULT_DOWNLOAD_FLAG = False
DEFAULT_DOWNLOAD_START_TIME = '1970-01-01T00:00:00Z'
DOWNLOAD_LIST_FILE_NAME = 'download_list.txt'
DOWNLOAD_RETRY_DESCRIPTION = ['st', 'nd', 'rd', 'th']
# Default retry times
DOWNLOAD_RETRY_TIMES = 3
ENTER_STR = '\r\n'
FILE_ENCODING = 'UTF-8'
LINE_SPLIT_STR = ', '
VIDEO_FORMAT = '.mp4'
VIDEO_URI_BASE = 'https://www.youtube.com/watch?v='

download_dir, download_list_file = '', ''

# Downloading video from youtube by a channel name.
# If generate_download_list_flag == False then download files directly without updating the downloading list.
def download_videos(generate_download_list_flag=True):
    if download_dir == '':
        init_global_parameters()

    if generate_download_list_flag:
        generate_download_list()

    current_retry_times = 0
    # Looping by retry times.
    while current_retry_times <= DOWNLOAD_RETRY_TIMES:
        with open(download_list_file, 'r', encoding=FILE_ENCODING) as existed_file:
            lines = existed_file.readlines()

        if (current_retry_times == 0):
            print('Start downloading process...')
        else:
            print('Start {} times retry...'.format(str(current_retry_times) + DOWNLOAD_RETRY_DESCRIPTION[(current_retry_times % 10) - 1 if (current_retry_times % 10 < len(DOWNLOAD_RETRY_DESCRIPTION)) else (len(DOWNLOAD_RETRY_DESCRIPTION) - 1)]))

        # Calculating some downloading task indicators.
        existed_download_file_number = len(list(filter(lambda x: x.strip(ENTER_STR).split(LINE_SPLIT_STR)[-1] == str(not DEFAULT_DOWNLOAD_FLAG), lines)))
        planned_download_file_number = len(list(filter(lambda x: x.strip(ENTER_STR).split(LINE_SPLIT_STR)[-1] == str(DEFAULT_DOWNLOAD_FLAG), lines)))
        print('Existed download videos: {}, planned download videos: {}'.format(existed_download_file_number, planned_download_file_number))
        current_line_number, current_download_number = 0, 0
        # Looping by downloading list file lines.
        while current_line_number < len(lines):
            line = lines[current_line_number].strip(ENTER_STR)
            # Only handle the records that have not been downloaded.
            if line.split(LINE_SPLIT_STR)[-1] == str(DEFAULT_DOWNLOAD_FLAG):
                current_download_video_file_name = os.path.join(download_dir, line.split(LINE_SPLIT_STR)[1])

                # Deleting existed file.
                if os.path.exists(current_download_video_file_name):
                    os.remove(current_download_video_file_name)
                try: 
                    yt = YouTube(VIDEO_URI_BASE + line.split(LINE_SPLIT_STR)[0])
                    # Picking up the high quality video.
                    current_download_video_file = yt.streams.filter(progressive=True).first().download(download_dir)
                    os.rename(current_download_video_file, current_download_video_file_name)

                    # Estimating the download result through calculate the downloaded file's duration and the original file's duration.
                    if (abs(VideoFileClip(current_download_video_file_name).duration) - time_convert(line.split(LINE_SPLIT_STR)[-2]) < 1):
                        lines[current_line_number] = line[: -len(line.split(LINE_SPLIT_STR)[-1])] + str(not DEFAULT_DOWNLOAD_FLAG) + ENTER_STR
                        current_download_number += 1
                        print('Download ---  %s  --- Done!' % line.split(LINE_SPLIT_STR)[1])
                        with open(download_list_file, 'w', encoding=FILE_ENCODING) as wirtten_file:
                            wirtten_file.write(''.join(lines))
                    else:
                        os.remove(current_download_video_file_name)
                        print('Download --- %s --- Failed, System will try it again!' % line.split(LINE_SPLIT_STR)[1])
                except Exception as e: 
                    print("Some Error happend while downloading files! %s" % e)
                    break
            current_line_number += 1

        print('This time, planned download videos: {}, actual download videos: {}'.format(planned_download_file_number, current_download_number))
        if planned_download_file_number == current_download_number:
            print('Download Completed!') 
            break
        else:
            if current_retry_times == DOWNLOAD_RETRY_TIMES:
                print('The last time retry, still have {} videos cannot be downloaded. Please retry at another time.'.format(planned_download_file_number - current_download_number))
            current_retry_times += 1

# Initializing global parameters.
def init_global_parameters():
    global download_dir, download_list_file
    download_dir = os.path.join(download_root_dir, channel_name)
    download_list_file = os.path.join(download_dir, DOWNLOAD_LIST_FILE_NAME);

# Generating or updating the downloading list based on channel name for the next downloading.
def generate_download_list():
    if download_dir == '':
        init_global_parameters()

    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    init_flag, update_flag, channel_id, playlist_id, download_start_time, download_list = False, True, '', '', '', ['']
    current_datetime = time.time()
    # File existed.
    if os.path.exists(download_list_file):
        with open(download_list_file, 'r', encoding=FILE_ENCODING) as original_file:
            lines = original_file.readlines()
            # Getting prerequisite parameters from file.
        extra_info = lines[-1].strip(ENTER_STR)
        channel_id = extra_info.split(LINE_SPLIT_STR)[0]
        playlist_id = extra_info.split(LINE_SPLIT_STR)[1]
        download_start_time = extra_info.split(LINE_SPLIT_STR)[2]
        # Deleting the last line
        lines.pop()
        # For the purpuse of saving quota cost, executing remote updating procedure once a day.
        if time.strftime(DATE_FORMAT_STR, time.localtime(os.path.getmtime(download_list_file))) == time.strftime(DATE_FORMAT_STR, time.localtime(current_datetime)):
            for line in lines:
                line = line.strip(ENTER_STR)
                download_list.append(line[: -len(line.split(LINE_SPLIT_STR)[-1])])
                # Comparing the difference of video clips duration.
                download_list.append(video_download_status(os.path.join(download_dir, line.split(LINE_SPLIT_STR)[1]), line.split(LINE_SPLIT_STR)[2]))
                download_list.append(ENTER_STR) 
            update_flag = False
    else:
        download_start_time = DEFAULT_DOWNLOAD_START_TIME
        init_flag = True

    if update_flag:
        youtube = build('youtube', 'v3', developerKey = api_key)
        # First executing.
        if init_flag:
            # quota cost: channels.list(1 unit) + return 'contentDetails' part(2 units) = 3 units
            channel_info = youtube.channels().list(part = 'contentDetails', forUsername = channel_name).execute()['items'][0]
            channel_id = channel_info['id']
            playlist_id = channel_info['contentDetails']['relatedPlaylists']['uploads']

        next_page_token = None
        while 1:
            # Getting videos' id and name.
            # quota cost: playlistItems.list(1 unit) + return 'snippet' part(2 units) = 3 units
            video_basic_info_list = youtube.playlistItems().list(playlistId = playlist_id, 
                                                                 part = 'snippet', 
                                                                 pageToken = next_page_token, 
                                                                 # Only grabbing the increment videos list after the last downloading except for the first time.
                                                                 publishedAfter = download_start_time, 
                                                                 maxResults = 50).execute()['items']

            video_dict = {}
            for item in video_basic_info_list:
                video_dict[item['snippet']['resourceId']['videoId']] = item['snippet']['title'].replace(':', '').replace(',', '').replace('.', '').replace('#', '').replace('?', '').replace('!', '').replace('\'','') + VIDEO_FORMAT

            # Getting videos' id and duration.
            # quota cost: videos.list(1 unit) + return 'contentDetails' part(2 units) = 3 units
            video_extra_info_list = youtube.videos().list(id = ','.join(video_dict.keys()), 
                                                          part='contentDetails', 
                                                          maxResults = 50).execute()['items']
            for item in video_extra_info_list:
                download_list.append(item['id'])
                download_list.append(LINE_SPLIT_STR)
                download_list.append(video_dict[item['id']])
                download_list.append(LINE_SPLIT_STR)
                download_list.append(item['contentDetails']['duration'])
                download_list.append(LINE_SPLIT_STR)
                download_list.append(video_download_status(os.path.join(download_dir, video_dict[item['id']]), item['contentDetails']['duration']))
                download_list.append(ENTER_STR)                 

            next_page_token = video_basic_info_list.get('nextPageToken')

            if next_page_token is None:
                break
            
    # Storing prerequisite parameters for the next downloading.
    download_list.append(channel_id)
    download_list.append(LINE_SPLIT_STR)
    download_list.append(playlist_id)
    download_list.append(LINE_SPLIT_STR)
    download_list.append(time.strftime(DATETIME_FORMAT_STR, time.localtime(current_datetime)))
    download_list.append(ENTER_STR)

    fo = open(download_list_file, 'wb')
    try: 
        fo.write(''.join(download_list).encode(FILE_ENCODING))
    except Exception as e: 
        print("Some Error happened while preparing the downloading list! %s" % e) 
    fo.close()

    print('The downloading list prepared completely!')

# Estimating video clip downloading status.
def video_download_status(video_file_name, video_duration):
    if ((not os.path.exists(video_file_name)) or (abs(VideoFileClip(video_file_name).duration - time_convert(video_duration)) > 1)):
        return str(DEFAULT_DOWNLOAD_FLAG)
    else:
        return str(not DEFAULT_DOWNLOAD_FLAG)

# Video clip duration formation.
def time_convert(duration):
    M, H = 60, 60**2
    duration = duration[2:] 
    hour = 0.00
    minute = 0.00
    second = 0.00
    if duration.find('H') > -1:
        hour = float(duration.split('H')[0])
        duration = duration.split('H')[1]
    if duration.find('M') > -1:
        minute = float(duration.split('M')[0])
        duration = duration.split('M')[1]
    if duration.find('S') > -1:
        second = float(duration.split('S')[0])
    return hour * H + minute * M + second

if __name__ == '__main__':
    # Initializing a few important parameters.
    api_key, channel_name, download_root_dir = None, None, None
    arg_number = len(sys.argv)
    if arg_number > 1:
        api_key = sys.argv[1]
    if arg_number > 2:
        channel_name = sys.argv[2]
    if arg_number > 3:
        download_root_dir = sys.argv[3]

    if api_key == None:
        api_key = input('Please enter your google developer api key for youtube data v3: ')
        if api_key.strip() == '':
            print('The api key cannot be empty! The program exit...')
            sys.exit()

    if channel_name == None:
        channel_name = input('Please enter the youtube channel owner\'s username: ')
        if channel_name.strip() == '':
            print('The youtube channel owner\'s username cannot be empty! The program exit...')
            sys.exit()

    if download_root_dir == None:
        download_root_dir = input('Please enter the download files\' root path: ')
        if download_root_dir.strip() == '':
            print('The program will use the current path as the root path.')

    # main procedure
    download_videos()
