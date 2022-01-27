import os
from datetime import datetime

from PIL import Image


def touch(path):
    """
    Function which has similar behaviour as the 'touch' bash command. It checks
    whether specified file exists. If the file does not exist, the function
    creates it without any content. If the file already exists, it changes the
    last modified time of the file, but does not change content whatsoever.
    :param path: string
        path to the file
    :return: None
    """
    basedir = os.path.dirname(path)
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    with open(path, 'a'):
        os.utime(path, None)


def fkin_copy_file(src, dst):
    '''
    I can already hear: why another file copy function FFS?. A simple answer: This function simply copies
    the damned file to given destination, no matter whether the file or path exists or not. I'm sick of using
    os.makedirs or touch everytime I want write a goddamned backup file. Fuck vanilla shutil.copy as well as
    using os.system to copy the files. As long as I have permission, copy the damned file!
    This should be standard.
    :param src: file to be copied
    :param dst: destination path
    :return: None
    '''
    from shutil import copy

    touch(dst)
    copy(src, dst)


def fkin_move_file(src, dst):
    '''
    I can already hear: why another file move function FFS?. A simple answer: This function simply moves
    the damned file to given destination, no matter whether the file or path exists or not. I'm sick of using
    os.makedirs or touch everytime I want write a goddamned backup file. Fuck vanilla shutil.move as well as
    using os.system to move the files. As long as I have permission, move the damned file!
    This should be standard.
    :param src: file to be copied
    :param dst: destination path
    :return: None
    '''
    from shutil import move

    touch(dst)
    move(src, dst)

def get_date_taken_from_exif(path, format='%Y-%m-%d %H:%M:%S'):
    """
    Gets the date of the picture from exif.
    :param path: <file-like string> Image path
    :param format: <datetime format string> desired output format
    :return: <datetime.datetime>
    """
    date = Image.open(path)._getexif()[36867]
    date = datetime.strptime(date, '%Y:%m:%d %H:%M:%S')

    return date.strftime(format)
