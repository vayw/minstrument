#!/usr/bin/env python

# utility for handling with my music files

import subprocess
import os
import sys
import argparse
import configparser
# don't know if it's necessary to use python libraries to work with flac
# and ogg files. For beginning let's stop on commandline utilities
# Will be nice to check it's availability


# function checks presence of utility in system
# returns 1 if available, and 0 if not
def get_util_present(_util):
    try:
        result = subprocess.check_call(['which', _util], stdout=subprocess.DEVNULL)
        if result == 0:
            print (_util, "found")
            is_available = 1
    except CalledProcessError:
        print (_util, "not available.")
        is_available = 0
    return is_available

# function returns list of tags
def get_track_data(filename, tagger):
    tagInUtility = tagger["tagUtility"]
    tagParams = tagger['params'].split()
    cmd = [tagInUtility] + tagParams + [filename]
    try:
        tags_string = subprocess.check_output(cmd)
    except CalledProcessError:
        print ("something gone wrong while getting tags!")
    tag_list = tags_string.decode("utf-8").split("\n")
    tag_list.pop()
    return tag_list

# function writes tags to file
# only for vorbiscomment
def set_ogg_track_data(_filename, _path, _taglist):
    cmd = ["vorbiscomment"] + ["-w"] + [_path + _filename]
    for tag in _taglist:
        # we need quted string, so lets add qutes to tag
        #escaped_tag = tag.replace(" ", "\ ")
        cmd.append("-t")
        cmd.append(tag)
    try:
        result = subprocess.check_call(cmd)
    except Exception as e:
        print(e)
    if result == 0:
        print (_filename, "tags updated")
    else:
        print ("error!!", _filename, "not updated!")

# let's try to find album directory in musicDir
# we assume that directory is called like album. If it's not, we can make 
# several assumptions, and wait for user agreement
def get_album_dir_hard(_tags_list, _filename, musicDir):
    _tags_count = 0 # we need 3 tags found to break the cicle
    # For beginning will get artist, album and release year
    for i in _tags_list:
        # as tags have no spec for writing let's capitalize our string
        _our_string = i.capitalize()
        if _our_string.startswith("ARTIST"):
            _artist = i[len("ARTIST="):]
            _tags_count+=1
        elif _our_string.startswith("ALBUM"):
            _album = i[len("ALBUM="):]
            _tags_count+=1
        elif _our_string.startswith("DATE"):
            _release_date = i[len("DATE="):]
            _tags_count+=1
        # now check tags_count
        if _tags_count == 3:
            break

    # now we can check existence of couple of paths
    _path = musicDir + _artist + "/" + _album
    if os.path.exists(_path):
        return _path
    _path = musicDir + _artist + "/" + _release_date + " - " + _album
    if os.path.exists(_path):
        return _path
    # if all our hopes are collapsed, start guessing and collect paths and rating
    # of it's accuracy
    _folders = []
    for _dir in os.listdir(musicDir):
        if _dir == _artist:
            # Oh! Great! we have folder named exactly as our artist
            for _album_dir in os.listdir(musicDir + _dir):
                if _album in _album_dir and _release_date in _album_dir:
                    # Awesome! we have folder which contains album name and
                    # and release date too
                    _folders.append((musicDir + _dir + "/" + _album_dir, 90))
                elif _album in _album_dir:
                    # It's also good, we still pretty close
                    _folders.append((musicDir + _dir + "/" + _album_dir, 85))
                elif _album.capitalized() in _album_dir.capitalized():
                    # Well, what's the difference?
                    _folders.append((musicDir + _dir + "/" + _album_dir, 84))
        if _artist in _dir:
            # okay, it contains artist name, but let's check album
            # Also let's check lenght of our folders, 'cause if it's have
            # a huge difference, it's probably not that we looking for
            # just a couple of versions taken from the sky
            if len(_dir) <= len(_artist)+4: # maybe it has article 
                _accuracy = 10
            elif len(_dir) <= len(_artist)+10: # what if she\he has a surname?
                _accuracy = 20
            elif len(_dir) <= len(_artist)+20: # what if she\he has a long surname?
                _accuracy = 40
            else:
                break # Nah! it's just a mistake

            for _album_dir in os.listdir(musicDir + _dir):
                if _album in _album_dir and _release_date in _album_dir:
                    # Awesome! we have folder which contains album name and
                    # and release date too
                    _folders.append((musicDir + _dir + "/" + _album_dir, 90 - _accuracy))
                elif _album in _album_dir:
                    # It's also good, we still pretty close
                    _folders.append((musicDir + _dir + "/" + _album_dir, 85 - _accuracy))
                elif _album.capitalized() in _album_dir.capitalized():
                    # Well, what's the difference?
                    _folders.append((musicDir + _dir + "/" + _album_dir, 84 - _accuracy))

    # okay, hope we have one options, but if not, let's ask user to point to folder
    if len(_folders) == 0:
        print("Unfortunately seems like there is no suitable folder in", musicDir)
        print("can you provide path?")
        _answer = input("yes/No: ")
        if _answer is "yes" or _answer is "y":
            print("please type path to folder")
            _user_path = input("--> ")
            return _user_path
        else:
            sys.exit("have no tracks to tag!")
    elif len(_folders) == 1:
        return _folder[0][0]
    else:
        print("suddenly we have more than one option, please choose the right one:")
        for i in range(0,len(_folders)):
            print(i, _folders[i][0])
        _test = True
        while _test:
            _user_choice = input("-> ")
            try:
                _user_path =  _folders[int(_user_choice)][0]
                _test = False
            except (IndexError, TypeError, ValueError):
                print("please, type again")
        return _user_path

def get_album_dir(_file, inFileType, musicDir):
    _file = _file[:len(_file)-len(inFileType)]
    _find_result = subprocess.check_output(["find", musicDir, "-iname", _file + "*"])
    _dir_list = _find_result.decode("utf-8").splitlines()
    if len(_dir_list) == 0:
        # go and try get_album_dir_hard method
        return -1
    elif len(_dir_list) == 1:
        _dir = os.path.dirname(_dir_list[0]) 
        return _dir + "/"
    else:
        print("suddenly we have more than one option, please choose the right one:")
        for i in range(0,len(_dir_list)):
            print(i, _dir_list[i])
        _test = True
        while _test:
            _user_choice = input("-> ")
            try:
                _dir = _dir_list[int(_user_choice)]
                _test = False
            except (IndexError, TypeError, ValueError):
                print("please, type again")
        return _dir

def create_config(cfg):
    config = configparser.ConfigParser()
    _dir = input("enter path to your music library: ")
    if _dir[-1] is not "/":
        _dir = _dir + "/"
    if os.path.isdir(_dir) == False:
        print("Seems like this path is invalid, don't forget to create it.")

    config["general"] = {"musicDir": _dir,
                        "inFileType": "flac",
                        "outFileType": "ogg"}
    config["flac"] = {"tagUtility": "metaflac",
                    "params": "--export-tags-to -"}
    config["ogg"] = {"tagUtility": "vorbiscomment"}

    try:
        with open(cfg, 'x') as configfile:
            config.write(configfile)
        print("config created..")
        return config
    except Exception as e:
        print("oops! something went wrong with creating config file!")
        print(e)

def main():
    # now we work with commandline arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--indir", help="directory, containing audio files with tags")
    parser.add_argument("-o", "--outdir", help="directory, containing untagged files")
    parser.add_argument("-m", "--musicdir", help="directory with music collection")
    args = parser.parse_args()

    # let's check config and create it if we don't have it
    _cfg = os.path.expanduser("~") + "/.config/minstrument.cfg"
    if os.path.isfile(_cfg):
        _config = configparser.ConfigParser()
        _config.read(_cfg)
    else:
        _config = create_config(_cfg)

    # now check available utils
    available_utils = {}
    for key in _config:
        try:
            available_utils[key] = get_util_present(_config[key]['tagUtility'])
        except:
            pass
    if len(available_utils) < 2:
        sys.exit("not enough utils available!")

    tag_collection = {}
    files_list = []

    # now get tags for each file in directory (if it's audio file)
    if args.indir is None:
        args.indir = "./"
    if args.musicdir is None:
        args.musicdir = _config['general']['musicDir']
    _inFileType = _config['general']['inFileType']
    _outFileType = _config['general']['outFileType']

    for i in os.listdir(args.indir):
        if i.endswith(_inFileType):
            _ipath = args.indir + "/" + i
            _ipath = os.path.normpath(_ipath)
            tags = get_track_data(_ipath, _config[_inFileType])
            tag_collection[i] = tags
            files_list.append(i)
    if len(files_list) < 1:
        if args.indir == None:
            sys.exit("no tracks found in current dir")
        else:
            sys.exit("no tracks found in " + args.indir)

    # now we can find directory with our untagged music.
    _folder = get_album_dir(files_list[-1], _inFileType, args.musicdir)
    if _folder == -1:
        _folder = get_album_dir_hard(tag_collection[files_list[-1]], files_list[-1], args.musicdir)
    print("files found in", _folder, "...")
    if _config['general']['outfiletype'] == "ogg":
        for _name in files_list:
            _new_name = _name[:len(_name) - len(_inFileType)] + _outFileType
            set_ogg_track_data(_new_name, _folder, tag_collection[_name])

if __name__ == "__main__":
    main()