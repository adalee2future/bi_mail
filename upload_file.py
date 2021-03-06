# -*- coding: utf-8 -*-

import os
import datetime
from helper import OSS_ENABLE

if OSS_ENABLE:
    import oss2
    from helper import ODPS_LOGIN, OSS_ENDPOINT, OSS_BUCKET, OSS_FOLDER
else:
    raise Exception("oss not enable, plese set it in main.cfg")

DEFAULT_FOLDER = OSS_FOLDER
EXPIRE_SECONDS = 60 * 60 * 24

def login_bucket(bucket_name=OSS_BUCKET, account="default"):
    login_info = ODPS_LOGIN[account]
    auth = oss2.Auth(login_info['access_id'], login_info['secret_access_key'])
    service = oss2.Service(auth, OSS_ENDPOINT)
    bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET)

    return bucket

def upload_file_to_oss(filename, oss_filename=None, folder=DEFAULT_FOLDER, bucket_name=OSS_BUCKET):
    bucket = login_bucket(OSS_BUCKET)

    file_creation_time = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
    if oss_filename is None:
        oss_filename = file_creation_time.strftime('_%Y-%m-%d_%H:%M:%S').join(os.path.splitext(os.path.basename(filename)))
    if folder is not None:
        oss_filename = '{}/{}'.format(folder, oss_filename)
    bucket.put_object_from_file(oss_filename, filename)
    print("uploaded oss filename:", oss_filename)
    bucket.update_object_meta(oss_filename, {'Content-Disposition': 'attachment'})
    return oss_filename

def upload_text_to_oss(oss_filename, text, folder=DEFAULT_FOLDER, bucket_name=OSS_BUCKET):
    bucket = login_bucket(OSS_BUCKET)
    if folder is not None:
        oss_filename = '{}/{}'.format(folder, oss_filename)
    bucket.put_object(oss_filename, text)
    print("uploaded oss filename:", oss_filename)
    return oss_filename

def get_file_url(oss_filename, expires=EXPIRE_SECONDS):
    bucket = login_bucket(OSS_BUCKET)
    return bucket.sign_url('GET', oss_filename, expires)
