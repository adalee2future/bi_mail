# -*- coding: utf-8 -*-

import oss2
import os
import datetime

ENDPOINT = 'oss-cn-shanghai.aliyuncs.com'
DEFAULT_BUCKET = 'owitho-bi-mail-attachments'
DEFAULT_FOLDER = None
EXPIRE_SECONDS = 60 * 60 * 24

def login_bucket(bucket_name=DEFAULT_BUCKET):
    auth = oss2.Auth(os.environ.get('access_id'), os.environ.get('access_key'))
    service = oss2.Service(auth, ENDPOINT)
    bucket = oss2.Bucket(auth, ENDPOINT, DEFAULT_BUCKET)

    return bucket

def upload_file_to_oss(filename, oss_filename=None, folder=DEFAULT_FOLDER, bucket_name=DEFAULT_BUCKET):
    bucket = login_bucket(DEFAULT_BUCKET)

    file_creation_time = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
    if oss_filename is None:
        oss_filename = file_creation_time.strftime('_%Y-%m-%d_%H:%M:%S').join(os.path.splitext(os.path.basename(filename)))
    if folder is not None:
        oss_filename = '{}/{}'.format(folder, oss_filename)
    bucket.put_object_from_file(oss_filename, filename)
    print("uploaded oss filename:", oss_filename)
    return oss_filename

def upload_text_to_oss(oss_filename, text, folder=DEFAULT_FOLDER, bucket_name=DEFAULT_BUCKET):
    bucket = login_bucket(DEFAULT_BUCKET)
    if folder is not None:
        oss_filename = '{}/{}'.format(folder, oss_filename)
    bucket.put_object(oss_filename, text)
    print("uploaded oss filename:", oss_filename)
    return oss_filename

def get_file_url(oss_filename, expires=EXPIRE_SECONDS):
    bucket = login_bucket(DEFAULT_BUCKET)
    return bucket.sign_url('GET', oss_filename, expires)