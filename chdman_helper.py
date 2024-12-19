#! /usr/bin/env python3
'''
Helper script for batch chdman jobs
'''

# imports
from pathlib import Path
from subprocess import run
import argparse

# constants
CHDMAN_COMPRESS_FORMATS = {'auto', 'cd', 'dvd', 'ld', 'raw'}
DISC_IMAGE_EXTS = {'.cue', '.gdi', '.iso'}
FORMAT_TO_EXT = {'cd':'.cue', 'dvd':'.iso', 'ld':'.avi', 'raw':'.raw'}
TAG_TO_FORMAT = {'CHT2':'cd', 'DVD':'dvd'}

# find default chdman.exe path if it exists
DEFAULT_CHDMAN_PATH = None
tmp = sorted(Path(__file__).parent.glob('chdman*.exe'))
if len(tmp) != 0:
    DEFAULT_CHDMAN_PATH = tmp[-1].resolve()

# parse user arguments
def parse_args():
    # set up program-level arguments
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--chdman_path', required=False, type=str, default=DEFAULT_CHDMAN_PATH, help="Path to chdman.exe")
    parser.add_argument('--dryrun', action="store_true", help="Print Commands (instead of running)")

    # set up sub-parsers
    sub_parsers = parser.add_subparsers(dest='command', required=True)
    parser_compress = sub_parsers.add_parser('compress', help="Compress a disc image into a CHD file")
    parser_decompress = sub_parsers.add_parser('decompress', help="Decompress a CHD file into a disc image")
    parser_info = sub_parsers.add_parser('info', help="Display information about a CHD file")

    # set up `compress` arguments
    parser_compress.add_argument('-i', '--input', required=True, type=str, help="Input File/Folder")
    parser_compress.add_argument('-o', '--output', required=True, type=str, help="Output File/Folder")
    parser_compress.add_argument('-f', '--format', required=False, type=str, default='auto', help="Output CHD Format (options: %s)" % ', '.join(sorted(CHDMAN_COMPRESS_FORMATS)))

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
def run_compress(input_path, output_path, output_format='auto', chdman_path=DEFAULT_CHDMAN_PATH, dryrun=False):
    # first check and handle output
    if output_path.is_file():
        raise ValueError("Output file exists: %s" % args.output)
    if output_path.suffix.strip().lower() != '.chd':
        if dryrun:
            print('mkdir -p %s' % output_path)
        else:
            output_path.mkdir(parents=True, exist_ok=True)

    # input is a file, so run `chdman.exe` to compress to `.chd`
    if input_path.is_file():
        if input_path.suffix.strip().lower() not in DISC_IMAGE_EXTS:
            raise ValueError("Invalid input file extension: %s" % input_path)

        # determine output file path
        if output_path.suffix.strip().lower() == '.chd':
            output_chd_path = output_path
        else:
            output_chd_path = (output_path / input_path.stem).with_suffix('.chd')

        # determine output CHD format (might need to make the logic more complex here)
        if output_format == 'auto':
            if input_path.suffix.strip().lower() in {'.cue', '.gdi'} or input_path.stat().st_size < 783216000:
                output_format = 'cd'
            else:
                output_format = 'dvd'

        # run `chdman.exe` to compress
        command = [chdman_path, 'create%s' % output_format, '--input', input_path, '--output', output_chd_path]
        print(' '.join(str(x) for x in command))
        if not dryrun:
            run(command)
            print()

    # input is a directory, so recurse on all disc image files
    elif input_path.is_dir():
        if output_path.suffix.strip().lower() == '.chd':
            raise ValueError("Input path was a directory, so output path must be a directory as well: %s" % output_path)
        for p in input_path.rglob('*.*'):
            if p.is_file() and p.suffix.strip().lower() in DISC_IMAGE_EXTS:
                run_compress(
                    p,
                    output_path,
                    output_format=output_format,
                    chdman_path=chdman_path,
                    dryrun=dryrun,
                )
    else:
        raise ValueError("Input path not found: %s" % input_path)

# decompress
def run_decompress(input_path, output_path, chdman_path=DEFAULT_CHDMAN_PATH, dryrun=False):
    # first check and handle output
    if output_path.is_file():
        raise ValueError("Output file exists: %s" % args.output)
    if output_path.suffix.strip().lower() not in DISC_IMAGE_EXTS:
        if dryrun:
            print('mkdir -p %s' % output_path)
        else:
            output_path.mkdir(parents=True, exist_ok=True)

    # input is a file, so run `chdman.exe` to decompress a `.chd`
    if input_path.is_file():
        if input_path.suffix.strip().lower() != '.chd':
            raise ValueError("Input file must be a CHD: %s" % input_path)

        # infer output format from CHD
        output_format = None
        command_info = [chdman_path, 'info', '--input', input_path]
        print(' '.join(str(x) for x in command_info))
        proc = run(command_info, capture_output=True)
        for line in proc.stdout.decode().splitlines():
            if line.startswith('Metadata:'):
                try:
                    output_format = TAG_TO_FORMAT[line.split("Tag='")[1].split("'")[0].strip().upper()]
                    break
                except:
                    pass
        if output_format is None:
            raise ValueError("Unable to infer image format: %s" % input_path)
        if output_path.suffix.strip().lower() in DISC_IMAGE_EXTS:
            output_img_path = output_path
        else:
            output_img_path = (output_path / input_path.stem).with_suffix(FORMAT_TO_EXT[output_format])

        # run `chdman.exe` to decompress
        command = [chdman_path, 'extract%s' % output_format, '--input', input_path, '--output', output_img_path]
        if output_format == 'cd':
            command += ['--outputbin', (output_img_path.parent / output_img_path.stem).with_suffix('.bin')]
        print(' '.join(str(x) for x in command))
        if not dryrun:
            run(command)
            print()

    # input is a directory, so recurse on all `.chd` files
    elif input_path.is_dir():
        if output_path.suffix.strip().lower() in DISC_IMAGE_EXTS:
            raise ValueError("Input path was a directory, so output path must be a directory as well: %s" % output_path)
        for p in input_path.rglob('*.*'):
            if p.is_file() and p.suffix.strip().lower() == '.chd':
                run_decompress(
                    p,
                    output_path=output_path,
                    chdman_path=chdman_path,
                    dryrun=dryrun,
                )
    else:
        raise ValueError("Input path not found: %s" % input_path)

# info
def run_info(input_path, chdman_path=DEFAULT_CHDMAN_PATH, verbose=False, print_header=True, dryrun=False):
    # input is a file, so run `chdman.exe info` on it
    if input_path.is_file():
        if input_path.suffix.strip().lower() != '.chd':
            raise ValueError("Input file must be CHD: %s" % input_path)
        command = [chdman_path, 'info', '--input', input_path]
        if verbose:
            command.append('--verbose')
        if dryrun:
            print(' '.join(str(x) for x in command))
        else:
            proc = run(command, capture_output=True)
            out = [[v.strip() for v in l.split(':')] for l in proc.stdout.decode().splitlines() if ': ' in l]
            if print_header:
                print('\t'.join(k for k,v in out))
            print('\t'.join(v for k,v in out))

    # input is a directory, so recurse on all `.chd` files
    elif input_path.is_dir():
        count = 0
        for p in input_path.rglob('*.*'):
            if p.is_file() and p.suffix.strip().lower() == '.chd':
                run_info(
                    p,
                    chdman_path=chdman_path,
                    verbose=verbose,
                    print_header=(count == 0),
                    dryrun=dryrun,
                )
                count += 1
    else:
        raise ValueError("Input path not found: %s" % input_path)

# main program logic
def main():
    args = parse_args()
    if args.command == 'compress':
        run_compress(
            input_path=args.input,
            output_path=args.output,
            output_format=args.format,
            chdman_path=args.chdman_path,
            dryrun=args.dryrun,
        )
    elif args.command == 'decompress':
        run_decompress(
            input_path=args.input,
            output_path=args.output,
            chdman_path=args.chdman_path,
            dryrun=args.dryrun,
        )
    elif args.command == 'info':
        run_info(
            input_path=args.input,
            chdman_path=args.chdman_path,
            verbose=args.verbose,
            dryrun=args.dryrun,
        )
    else:
        raise ValueError("Invalid command: %s" % args.command)

# run program
if __name__ == "__main__":
    main()
