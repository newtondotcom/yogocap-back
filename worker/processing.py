import random
import os
import re
from typing import Iterator, TextIO
from styles import *
from utils import *
from silent import *
from emojis import *
from gen import *
import ffmpeg

# http://www.looksoftware.com/help/v11/Content/Reference/Language_Reference/Constants/Color_constants.htm
# rouge, jaune, vert

# Constants for subtitle colors
colors = ["\\2c&&H000000FF&", "\\2c&H0000FFFF&", "\\2c&H0000FF00&"]
colors2 = ["\\1c&H0000FF&", "\\1c&H00FFFF&", "\\1c&H00FF00&"]

# Global variables (consider avoiding global variables if possible)
tab = []       # Stores extracted words and timings
new_tab = []   # Stores grouped and formatted subtitle segments
words = []     # Placeholder for extracted transcriptions
styles = gen_styles()  # List of predefined subtitle styles

def populate_tabs(words):
    """Extracts words and timings from transcriptions and populates 'tab'."""
    for s in words:
        for i in range(len(s['words'])):
            word = s['words'][i]['word']
            if len(s['words'][i]) == 1:
                break
            start = s['words'][i]['start']
            end = s['words'][i]['end']
            if i == len(s['words']) - 1:
                tab.append([start, end, word, True])  # Last word in a sentence
            else:
                tab.append([start, end, word, False])  # Intermediate word

def analyse_tab_durations():
    """Calculates average time and length of words in 'tab' for grouping."""
    moyenne_time = 0
    moyenne_length = 0
    for j in tab:
        start = j[0]
        end = j[1]
        word = j[2]
        moyenne_time += (end - start)
        moyenne_length += len(word)
    moyenne_length = moyenne_length / len(tab)
    moyenne_time = moyenne_time / len(tab)
    
    retenue = 0
    seuil = 0.10  # Proximity threshold for grouping words
    # Contain words within a group based on specified criteria
    for j in range(len(tab)):
        if retenue > 0:
            retenue -= 1
        else:
            retenue = group_words_based_on_threshold(tab, new_tab, seuil, j, moyenne_time, moyenne_length)

def write_ass_file_aligned(file: TextIO, position):
    """Writes formatted subtitles to an ASS file."""

    position_subtitle = ""
    if position == "center":
        position_subtitle = "\\an5"
    else:
        position_subtitle = "\\an2"

    file.write("[Script Info]\n")
    file.write("ScriptType: v4.00\n")
    file.write("Collisions: Normal\n")
    file.write("PlayDepth: 0\n")
    file.write("\n")
    file.write("[V4+ Styles]\n")
    file.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColor, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding, WrapStyle\n")
    for j in styles:
        file.write(j)
    file.write("\n")
    file.write("[Events]\n")
    file.write("Format: Layer, Start, End, Style, Actor, MarginL, MarginR, MarginV, Effect, Text\n")
    
    i_color = 0
    for s in new_tab:
        localtext = ""
        globalstart = s[0][0]
        globalend = s[-1][1]
        color = colors[i_color]
        i_color = (i_color + 1) % len(colors)
        
        # Generate boilerplate style and text for each subtitle segment
        boiler = "{\\k40\\fad(0,0)\\be1\\b\\bord2\\shad1\\1c&&HFFFFFF&\\3c&H000000&\\q1\\b700" + position_subtitle + color + "} "
        localtext = boiler
        
        if len(s) == 4:
            # Format specific segments within a group
            boiler = "{\\fad(0,0)\\be1\\b\\bord2\\shad1\\1c&&HFFFFFF&\\3c&H000000&\\q1\\b700" + position_subtitle + color + "} "
            localtext = boiler
            
            first_start = s[0][0]
            first_end = s[1][1]
            second_start = s[2][0]
            second_end = s[3][1]
            
            diff = abs(round(float(first_end - first_start) * 100))
            duration = "{" + colors[i_color] + "\\k" + str(diff) + "}"
            localtext += duration + s[0][2].upper() + " " + s[1][2].upper() + "\\N "
            
            i_color = (i_color + 1) % len(colors)
            color = colors[i_color]
            diff2 = abs(round(float(second_end - second_start) * 100))
            diff3 = abs(round(float(second_start - first_start) * 100))
            diff4 = abs(round(float(second_end - first_start) * 100))
            duration2 = "{" + colors[i_color] + "\\k" + str(diff2) + "\\t(" + str(diff3) + "," + str(diff4) + ",\\fscx110)" + "\\t(" + str(diff3) + "," + str(diff4) + ",\\fscy110)}"
            localtext += duration2 + s[2][2].upper() + " " + s[3][2].upper()
        else:
            # Format individual words within a segment
            for segment in s:
                word = segment[2]
                start = segment[0]
                end = segment[1]
                delta = end - start
                duration = "{\\k" + str(abs(round(delta * 100))) + "}"
                localtext += duration + word.upper() + " "
        
        style = "s" + str(random.randint(0, len(styles) - 1))
            
        # Split long lines into multiple lines for readability
        words = localtext.split("{\q1")
        if len(words) == 5:
            localtext = "{\q1" + words[1] + "{\q1" + words[2] + "\\N{\q1" + words[3] + "{\q1" + words[4]

        # Write formatted subtitle event to the ASS file
        file.write(f"Dialogue: 0,{format_seconds_to_hhmmss(globalstart)},{format_seconds_to_hhmmss(globalend)},{style},,50,50,20,fx,{localtext}\n")

def write_ass_file_non_aligned(contents,file: TextIO):
    """Writes formatted subtitles to an ASS file."""
    file.write("[Script Info]\n")
    file.write("ScriptType: v4.00\n")
    file.write("Collisions: Normal\n")
    file.write("PlayDepth: 0\n")
    file.write("\n")
    file.write("[V4+ Styles]\n")
    file.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColor, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding, WrapStyle\n")
    # file.write 
    file.write("\n")
    file.write("[Events]\n")
    file.write("Format: Layer, Start, End, Style, Actor, MarginL, MarginR, MarginV, Effect, Text\n")
    
    i_color = 0
    for s in contents:            
        #f"{format_timestamp(segment['start'], always_include_hours=True)} --> "
        #f"{format_timestamp(segment['end'], always_include_hours=True)}\n"
        #f"{segment['text'].strip().replace('-->', '->')}\n",

        file.write(f"Dialogue: 0,{format_seconds_to_hhmmss(s['start'])},{format_seconds_to_hhmmss(s['end'])},,,50,50,20,fx,{s['text'].strip().replace('-->', '->')}\n")

def process_video(path_in, path_out, emoji, lsilence, isVideoAligned, position):
    """Processes a video based on specified parameters."""
    global tab, new_tab, words
    tab = []       # Reset tab for each video processing task
    new_tab = []   # Reset new_tab for each video processing task
    words = []     # Reset words for each video processing task

    ass_path = os.path.join("temp", f"{extract_filename_without_extension(path_in)}.ass")  # Define ASS file path
    
    audio_path = extract_audio_from_videos([path_in])[path_in]  # Get audio file path from video

    words, time_transcription, time_alignment = get_transcribe(audio_path)  # Transcribe audio to extract words

    time_encoding = 0
    if isVideoAligned:
        time_encoding = video_aligned(words, ass_path, emoji, path_in, path_out, lsilence,position)  # Process aligned video
    else:
        time_encoding = video_non_aligned(words, ass_path, emoji, path_in, path_out)  # Process non-aligned video

    return time_encoding,time_transcription,time_alignment

def video_non_aligned(words, ass_path, emoji, path_in, path_out):
    """Processes a non-aligned video with generated subtitles."""

    # Write the ass file with content from faster-whipser transcription
    with open(ass_path, "w", encoding="utf-8") as srt:
        write_ass_file_non_aligned(words, file=srt)  # Write transcript to SRT file

    # Get the dimensions (width and height) of the input video
    width, height = get_video_dimensions(video_path=path_in)

    # simply overlay the ASS script on the video
    time_encoding = overlay_images_on_video(
        in_path=path_in,
        out_path=path_out,
        emojis_list=None,
        width=width,
        height=height,
        ass=ass_path
    )
    return time_encoding

def video_aligned(words, ass_path, emoji, path_in, path_out, lsilence, position):
    # Get the dimensions (width and height) of the input video
    width, height = get_video_dimensions(video_path=path_in)

    # Generate ASS script file based on the provided words
    populate_tabs(words=words)

    # Analyze and process the durations and grouping of words
    analyse_tab_durations() 
        
    # Write the ASS script to a file at the specified path
    with open(ass_path, "w", encoding="utf-8") as ass:
        write_ass_file_aligned(file=ass,position=position)

    # Define a list of emojis with their start and end times
    emojis_list = [("1", 1.523, 5.518), ("2", 10.5, 15.5), ("3", 20.5, 25.5)]

    time_encoding = 0

    # Overlay emojis on the input video if emoji flag is True
    if emoji:
        time_encoding = overlay_images_on_video(
            in_path=path_in,
            out_path=path_out,
            emojis_list=emojis_list,
            width=width,
            height=height,
            ass=ass_path
        )
    else:
        # If no emojis are provided, simply overlay the ASS script on the video
        time_encoding = overlay_images_on_video(
            in_path=path_in,
            out_path=path_out,
            emojis_list=None,
            width=width,
            height=height,
            ass=ass_path
        )

    # Remove silent parts from the output video if lsilence flag is True
    if lsilence:
        rm_silent_parts(path_out, path_out)
        
    return time_encoding