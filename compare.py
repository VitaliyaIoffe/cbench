#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Nicely formats results generated by example.lua

from __future__ import print_function
import os
import json
import argparse

TEST_JUST = 8

##
# Calculate the median of the list of numbers.
# @param lst Not empty list of numbers.
# @retval One number - median of the list.
#
def median(lst):
    assert(lst)
    lst = sorted(lst)
    n = len(lst)
    if not n % 2:
        # If the list has odd length then return the average of
        # the middle elements.
        return (lst[n / 2] + lst[n / 2 - 1]) / 2
    return lst[n / 2]

##
# Print the report with comparison of benchmark results from
# two directories - with benchmarks results of old tarantool and
# with new tarantool.
# @param dir_old Directory with old tarantool reports.
# @param dir_new Directory with new tarantool reports.
#
def compare_dirs(dir_old, dir_new):
    files_old = sorted(os.listdir(dir_old))
    files_new = sorted(os.listdir(dir_new))
    if len(files_old) != len(files_new):
        print('For --dirs the files count must be same in both directories')
        return -1
    comparison = {}
    # key - space index type
    # value - map of request types which has following format:
    #   key - request type
    #   value - list of percents

    # Read each files pair in the cycle and compare them.
    for file_old, file_new in zip(files_old, files_new):
        bench_result_old = None
        bench_result_new = None
        try:
            with open(os.path.join(dir_old, file_old)) as f:
                bench_result_old = json.loads(f.read())
            with open(os.path.join(dir_new, file_new)) as f:
                bench_result_new = json.loads(f.read())
        except Exception as e:
            print('Skip files: {}, {}'.format(file_old, file_new))
            continue
        if len(bench_result_old) != len(bench_result_new):
            print('Benchmarks must contain same spaces count')
            return -1
        # Iterate over index types from the current files pair.
        index_count = len(bench_result_old)
        for i in range(index_count):
            one_bench_old = bench_result_old[i]
            one_bench_new = bench_result_new[i]
            index_type = one_bench_old[0]
            if index_type != one_bench_new[0]:
                print('Benchmark must contain same index types')
                return -1
            index_type_bench = {}
            if index_type not in comparison:
                comparison[index_type] = index_type_bench
            else:
                index_type_bench = comparison[index_type]

            requests_count = len(one_bench_old[1])
            if requests_count != len(one_bench_new[1]):
                print('Benchmark must contain same request types count')
                return -1
            # Iterate over request types in the current index
            # benchmark.
            for j in range(requests_count):
                request_old = one_bench_old[1][j]
                request_new = one_bench_new[1][j]
                request_type = request_old[0]
                if request_type != request_new[0]:
                    print('Benchmark must contain same request types')
                    return -1
                percents = []
                if request_type not in index_type_bench:
                    index_type_bench[request_type] = percents
                else:
                    percents = index_type_bench[request_type]
                percents.append(((request_new[1] - request_old[1]) / request_old[1]) * 100)
    # After comparison accumulation print the table.
    for index_type, requests in comparison.items():
        print(index_type)
        print('|', 'Test'.center(TEST_JUST), '| percents')
        print('|', '-'*TEST_JUST, '|---------')
        for request, percents in requests.items():
            print('|', request.center(TEST_JUST), '| ', end='')
            print('average={:.2f}%'.format(sum(percents)/len(percents)).center(15), end='')
            print(', ', 'median={:.2f}%'.format(median(percents)).center(15), end='')
            print(', ', 'values= [', ', '.join(map(lambda x: '{:.2f}%'.format(x).center(9), percents)), ']')
        print()


def compare_files(files):
    RPS_JUST=9
    PERCENT_JUST=10

    assert(len(files) > 0)

    results = []
    names = []
    for fname in files:
        with open(fname) as f:
            results.append(json.loads(f.read()))
            name = os.path.splitext(os.path.basename(fname))[0]
            names.append(name)
    print(' vs '.join(names))
    print()

    # Check sizes
    wlnum = len(results[0])
    for res in results:
        assert (wlnum == len(res))

    for wls in zip(*results):
        for (wlname, _wldata) in wls[1:]:
            assert(wls[0][0] == wlname)

        wlname = wls[0][0]
        print(wlname)
        print('-' * len(wlname))
        print()

        # Print headers
        print('|', 'Test'.center(TEST_JUST), '|', names[0].center(RPS_JUST), '|', end='')
        for name in names[1:]:
            print(name.center(RPS_JUST + PERCENT_JUST + 1), '|', end='')
        print()

        # Print hline
        print('|', '-' * TEST_JUST, '|', '-' * RPS_JUST, '|', end='')
        for k in wls[1:]:
            print('-' * (RPS_JUST + PERCENT_JUST + 1), '|', end='')
        print()

        for tests in zip(*[x[1] for x in wls]):
            for test in tests[1:]:
                assert(tests[0][0] == test[0])

            print('|', tests[0][0].rjust(TEST_JUST), '|', end='')
            base = tests[0][1]
            print(("%.0f" % base).rjust(RPS_JUST), '|', end='')
            for test in tests[1:]:
                rps = test[1]
                delta = (((rps / base) - 1.0) * 100)
                print(("%.f" % rps).rjust(RPS_JUST), end='')
                print(("(%.2f%%)" % delta).rjust(PERCENT_JUST), '|', end='')
            print()
        print()

def main():
    parser = argparse.ArgumentParser(description='Compare cbench results')
    parser.add_argument('--dirs', nargs=2, required=False, metavar=('old_dir', 'new_dir'))
    parser.add_argument('--files', nargs='+', required=False, metavar='file_name')
    args = parser.parse_args()
    if not args.dirs and not args.files:
        print('Use --dirs or --files arguments')
        return -1
    if args.dirs:
        return compare_dirs(args.dirs[0], args.dirs[1])
    else:
        return compare_files(args.files)
    print(args)

if __name__ == '__main__':
    main()

