#! /usr/bin/env python3
'''
Subsample a given genome sequence dataset (FASTA format) with collection dates (LSD2 format).
'''
from gzip import open as gopen
from os.path import isdir, isfile
from random import sample
from sys import stderr, stdin, stdout
import argparse

# main script
if __name__ == "__main__":
    # parse args
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-is', '--in_seqs', required=True, type=str, help="Input Sequences (FASTA format)")
    parser.add_argument('-id', '--in_dates', required=True, type=str, help="Input Dates (LSD2 format)")
    parser.add_argument('-n', '--num_seqs', required=True, type=int, help="Number of Output Sequences")
    parser.add_argument('-os', '--out_seqs', required=True, type=str, help="Output Sequences (FASTA format)")
    parser.add_argument('-od', '--out_dates', required=True, type=str, help="Output Dates (LSD2 format)")
    args = parser.parse_args()
    if args.num_seqs < 1:
        raise ValueError("Number of seqences must be positive: %s" % args.num_seqs)

    # open input files
    if args.in_seqs == args.in_dates:
        raise ValueError("Input files cannot be the same")
    in_files = list()
    for fn in [args.in_seqs, args.in_dates]:
        if isfile(fn):
            if fn.lower().endswith('.gz'):
                in_files.append(gopen(fn, 'rt'))
            else:
                in_files.append(open(fn, 'r'))
        elif fn == 'stdin':
            in_files.append(stdin)
        else:
            raise ValueError("Input file not found: %s" % fn)
    f_in_seqs, f_in_dates = in_files

    # open output files
    if args.out_seqs == args.out_dates:
        raise ValueError("Output files cannot be the same")
    for fn in [args.out_seqs, args.out_dates]:
        if isfile(fn) or isdir(fn):
            raise ValueError("Output file exists: %s" % fn)
    out_files = list()
    for fn in [args.out_seqs, args.out_dates]:
        if fn.lower().endswith('.gz'):
            out_files.append(gopen(fn, 'wt', compresslevel=9))
        elif fn == 'stdout':
            out_files.append(stdout)
        elif fn == 'stderr':
            out_files.append(stderr)
        else:
            out_files.append(open(fn, 'w'))
    f_out_seqs, f_out_dates = out_files

    # load input dates
    dates = dict()
    for i, l in enumerate(f_in_dates):
        if i == 0:
            try:
                tot_in_seqs = int(l)
            except:
                raise ValueError("Malformed input dates file: %s" % args.in_dates)
        else:
            parts = [v.strip() for v in l.strip().split()]
            if len(parts) == 2:
                curr_name, curr_date = parts
            elif len(parts) == 1:
                curr_name = parts[0]; curr_date = None # missing date
            else:
                raise ValueError("Malformed input dates file: %s" % args.in_dates)
            if curr_name in dates:
                raise ValueError("Duplicate label in input dates file: %s" % curr_name)
            dates[curr_name] = curr_date
    if tot_in_seqs != len(dates):
        raise ValueError("Total number of dates in first line doesn't match actual number of dates: %s" % args.in_dates)

    # remove missing dates
    dates = {k:v for k,v in dates.items() if v is not None}
    if len(dates) < args.num_seqs:
        raise ValueError("Fewer sequences with dates (%d) than num_seqs (%d)" % (len(dates), args.num_seqs))

    # subsample sequences
    out_names = set(sample(list(dates.keys()), args.num_seqs))
    if len(out_names) != args.num_seqs:
        raise RuntimeError("The length of out_names (%d) does not equal num_seqs (%d)" % (len(out_names), args.num_seqs))
    f_out_dates.write('%d\n' % args.num_seqs)
    lines = [l.strip() for l in f_in_seqs]
    for i in range(0, len(lines), 2):
        if not lines[i].startswith('>'):
            raise ValueError("Input sequences file must be one-line FASTA without empty lines")
        curr_name = lines[i][1:].strip()
        if curr_name in out_names:
            out_names.remove(curr_name)
            f_out_dates.write('%s %s\n' % (curr_name, dates[curr_name]))
            f_out_seqs.write('>%s\n%s\n' % (curr_name, lines[i+1]))
    f_out_dates.close(); f_out_seqs.close()
