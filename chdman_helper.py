#! /usr/bin/env python3
'''
Helper script for batch chdman jobs
'''

# imports
from pathlib import Path
from subprocess import run
import argparse

# constants
DEFAULT_CHDMAN_PATH = None

# find default chdman.exe path if it exists
tmp = sorted(Path(__file__).parent.glob('chdman*.exe'))
if len(tmp) != 0:
    DEFAULT_CHDMAN_PATH = tmp[-1].resolve()

# parse user arguments
def parse_args():
    # set up program-level arguments
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--chdman_path', required=False, type=str, default=DEFAULT_CHDMAN_PATH, help="Path to chdman.exe")

    # set up sub-parsers
    sub_parsers = parser.add_subparsers(dest='command', required=True)
    parser_compress = sub_parsers.add_parser('compress', help="Compress a disc image into a CHD file")
    parser_decompress = sub_parsers.add_parser('decompress', help="Decompress a CHD file into a disc image")
    parser_info = sub_parsers.add_parser('info', help="Display information about a CHD file")

    # set up `compress` arguments
    parser_compress.add_argument('-i', '--input', required=True, type=str, help="Input File/Folder")
    parser_compress.add_argument('-o', '--output', required=True, type=str, help="Output File/Folder")

    # set up `decompress` arguments
    parser_decompress.add_argument('-i', '--input', required=True, type=str, help="Input File/Folder")
    parser_decompress.add_argument('-o', '--output', required=True, type=str, help="Output File/Folder")

    # set up `info` arguments
    parser_info.add_argument('-i', '--input', required=True, type=str, help="Input File/Folder")
    parser_info.add_argument('-v', '--verbose', action="store_true", help="Verbose Mode")

    # parse args and check for validity
    args = parser.parse_args()
    if args.chdman_path is None:
        raise ValueError("Must specify chdman.exe path: --chdman_path")
    else:
        args.chdman_path = Path(args.chdman_path)
    if hasattr(args, 'input'):
        args.input = Path(args.input)
        if not (args.input.is_file() or args.input.is_dir()):
            raise ValueError("Input path not found: %s" % args.input)
    if hasattr(args, 'output'):
        args.output = Path(args.output)
        if args.output.is_file():
            raise ValueError("Output file exists: %s" % args.output)
    return args

# compress
def run_compress(input_path, output_path, chdman_path=DEFAULT_CHDMAN_PATH):
    raise NotImplementedError("compress") # TODO

# decompress
def run_decompress(input_path, output_path, chdman_path=DEFAULT_CHDMAN_PATH):
    raise NotImplementedError("decompress") # TODO

# info
def run_info(input_path, chdman_path=DEFAULT_CHDMAN_PATH, verbose=False, print_header=True):
    if input_path.is_file():
        if input_path.suffix.strip().lower() != '.chd':
            raise ValueError("Input file must be CHD: %s" % input_path)
        command = [chdman_path, 'info', '--input', input_path]
        if verbose:
            command.append('--verbose')
        proc = run(command, capture_output=True)
        out = [[v.strip() for v in l.split(':')] for l in proc.stdout.decode().splitlines() if ': ' in l]
        if print_header:
            print('\t'.join(k for k,v in out))
        print('\t'.join(v for k,v in out))
    elif input_path.is_dir():
        count = 0
        for p in input_path.rglob('*'):
            if p.is_file() and p.suffix.strip().lower() == '.chd':
                run_info(p, chdman_path=chdman_path, verbose=verbose, print_header=(count == 0))
                count += 1
    else:
        raise ValueError("Input path not found: %s" % input_path)

# main program logic
def main():
    args = parse_args()
    if args.command == 'compress':
        run_compress(input_path=args.input, output_path=args.output, chdman_path=args.chdman_path)
    elif args.command == 'decompress':
        run_decompress(input_path=args.input, output_path=args.output, chdman_path=args.chdman_path)
    elif args.command == 'info':
        run_info(input_path=args.input, chdman_path=args.chdman_path, verbose=args.verbose)
    else:
        raise ValueError("Invalid command: %s" % args.command)

# run program
if __name__ == "__main__":
    main()
