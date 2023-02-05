from argparse import ArgumentParser

from pathvalidate.argparse import validate_filename_arg, validate_filepath_arg

parser = ArgumentParser()
parser.add_argument("--filepath", type=validate_filepath_arg)
parser.add_argument("--filename", type=validate_filename_arg)
options = parser.parse_args()

if options.filename:
    print("filename: {}".format(options.filename))

if options.filepath:
    print("filepath: {}".format(options.filepath))


