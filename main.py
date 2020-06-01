import sys
import os
import argparse
import glob
from typing import Dict, List

from mp3_tagger import MP3File, VERSION_1, VERSION_2, VERSION_BOTH, MP3OpenFileError
import utils
import json


def check_chars(org_str):
    byte_org_str = org_str.encode("utf-8")
    replace_bytes : bytes = b''

    for b_index in range(0, len(byte_org_str)):
        b_str = byte_org_str[b_index:b_index+1]
        if b_str != b"\x00":
            replace_bytes += b_str

    return str(replace_bytes.decode("utf-8"))

def arg_parsing():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--path', dest='src_path', help='source path', required=True)

    args = parser.parse_args()
    args.src_path = args.src_path.strip().replace("\\", "");
    return args


def check_src_path(path):
    if not os.path.exists(path):
        raise Exception("not exists src_path={0}".format(path))

    if os.path.isdir(path):
        return 2

    if os.path.isfile(path):
        return 1


def read_dirs(path, is_recursive):
    df_list = glob.glob(path + "/**/*.mp3", recursive=True)
    df_list.extend(glob.glob(path + "/**/*.MP3", recursive=True))
    return df_list


def clean(file):
    clean_result = {}
    tag_datas : Dict[str,str] = {"artist": "", "song": "", "year": "", "album": ""}

    try:
        mp3_file: MP3File = MP3File(file)
    except MP3OpenFileError as file_e:
        clean_result["STATUS"] = "ERROR"
        clean_result["FILE"] = file
        clean_result["MSG"] = "open error"
        return clean_result

    tags = None
    try:
        tags = mp3_file.get_tags()
    except Exception as e:
        clean_result["STATUS"] = "ERROR"
        clean_result["FILE"] = file
        clean_result["MSG"] = "get_tag_error"
        return clean_result

    if tags is None:
        clean_result["STATUS"] = "ERROR"
        clean_result["FILE"] = file
        clean_result["MSG"] = "tags is None"
        return clean_result

    v2_tag = utils.get_v(tags, "ID3TagV2")
    if v2_tag is None:
        clean_result["STATUS"] = "ERROR"
        clean_result["FILE"] = file
        clean_result["MSG"] = "Not Exist ID3TagV2"
        return clean_result

    for k in tag_datas:
        tag_value = utils.get_v(v2_tag, k)
        if tag_value is None:
            tag_value = ""

        tag_datas[k] = tag_value.strip().replace(" ", "_")

    clean_result["STATUS"] = "NORMAL"
    clean_result["FILE"] = file
    clean_result["DATA"] = tag_datas

    return clean_result


if __name__ == "__main__":
    input_args = arg_parsing()

    src_path = input_args.src_path
    check_flag = check_src_path(src_path)

    output_file = "{0}/mp3_clean.out".format(os.path.abspath("."))

    if check_flag < 0:
        sys.exit(check_flag)

    src_files = []

    if 1 == check_flag:
        src_files.append(src_path)
    elif 2 == check_flag:
        recursive_dir_list = read_dirs(src_path, True)
        for dir_file in recursive_dir_list:
            print(dir_file)
            if os.path.isfile(dir_file):
                src_files.append(dir_file)

    write_file = open(output_file, "w", encoding="utf-8")
    i = 0
    artists={}
    for src_file in src_files:
        if src_file.endswith(".MP3") or src_file.find(" "):
            to_rename_file = src_file[0:-4] + ".mp3"
            os.renames(src_file, to_rename_file)
            src_file = to_rename_file

        clean_meta = clean(src_file)
        artist = utils.get_v(clean_meta["DATA"], "artist")
        if artist is None:
            artist = ""

        artist = check_chars(artist)

        write_file.write(json.dumps(clean_meta, ensure_ascii=False) + "\n")
        artists[artist] = artist
        sorted(artists)
        if i >= 100:
            print("process_cnt={0}".format(i))
            i = 0
        else:
            i = i + 1

    for artist in artists:
        print(artist)

    write_file.write(json.dumps(artists,ensure_ascii=False)+"\n")
    write_file.flush()
    write_file.close()
