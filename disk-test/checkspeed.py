#!/bin/python3
# -*- coding: utf-8 -*-

'''
MonkeyTest -- test your hard drive read-write speed in Python
A simplistic script to show that such system programming
tasks are possible and convenient to be solved in Python

The file is being created, then written with random data, randomly read
and deleted, so the script doesn't waste your drive

(!) Be sure, that the file you point to is not something
    you need, cause it'll be overwritten during test

Runs on both Python3 and 2, despite that I prefer 3
Has been tested on 3.5 and 2.7 under ArchLinux
Has been tested on 3.5.2 under Ubuntu Xenial
# https://github.com/thodnev/MonkeyTest
'''

import os, sys, errno
from random import shuffle
import argparse
import json

try:  # if Python >= 3.3 use new high-res counter
    from time import perf_counter as time_time
except ImportError:  # else select highest available resolution counter
    if sys.platform[:3] == 'win':
        from time import clock as time_time
    else:
        from time import time_time


def bytesToHumanReadable(num, suffix='B'):
    num=float(num)
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            if num.is_integer():
                return '{} {}{}'.format(int(num),unit,suffix)
            else:
                return '{:3.2f} {}{}'.format(num,unit,suffix)
        num /= 1024.0
    if num.is_integer():
        return '{} {}{}'.format(int(num),'Yi',suffix)
    else:
        return '{:.2f} {}{}'.format(num,'Yi',suffix)

def strIsFloat(str_to_check):
    try:
        float(str_to_check)
        return True
    except:
        return False


def parseNumericDict(num_dict):
    new_dict={}
    for k,v in num_dict.items():
        if type(v) is str:
            if strIsFloat(v) or not v.strip()[0].isnumeric():
                new_dict[k]=v
            else:
                str_part=''
                numeric_part=''
                for c in v:
                    if c.isnumeric() or c=='.':
                        numeric_part+=c 
                    else:
                        str_part+=c
                numeric_part=float(numeric_part)
                if numeric_part.is_integer:
                    numeric_part=int(numeric_part)
                new_dict['{} ({})'.format(k,str_part.strip())]=numeric_part
        else:
            new_dict[k]=v
    return new_dict

class Benchmark:

    DEFAULT_FILE_ON_TMP=False
    LINE_BUFFER_SIZE=20
    ROUND_PRECISION=5

    def __init__(self, file,write_mb, write_block_kb, read_block_b):
        self.file = file
        self.write_mb = write_mb
        self.write_block_kb = write_block_kb
        self.read_block_b = read_block_b
        wr_blocks = int(self.write_mb * 1024 / self.write_block_kb)
        rd_blocks = int(self.write_mb * 1024 * 1024 / self.read_block_b)
        self.write_results = self.write_test( 1024 * self.write_block_kb, wr_blocks)
        self.read_results = self.read_test(self.read_block_b, rd_blocks)

    def write_test(self, block_size, blocks_count, show_progress=True):
        '''
        Tests write speed by writing random blocks, at total quantity
        of blocks_count, each at size of block_size bytes to disk.
        Function returns a list of write times in sec of each block.
        '''
        f = os.open(self.file, os.O_CREAT | os.O_WRONLY, 0o777)  # low-level I/O

        took = []
        for i in range(blocks_count):
            if show_progress:
                # dirty trick to actually print progress on each iteration
                sys.stdout.write('\rWriting: {:.2f} %'.format((i + 1) * 100 / blocks_count))
                sys.stdout.flush()
            buff = os.urandom(block_size)
            start = time_time()
            os.write(f, buff)
            os.fsync(f)  # force write to disk
            t = time_time() - start
            took.append(t)

        os.close(f)
        if show_progress:
            sys.stdout.write('\r{}'.format(' '*Benchmark.LINE_BUFFER_SIZE)) # clear the line
            sys.stdout.flush()
            sys.stdout.write('\r')
        return took

    def read_test(self, block_size, blocks_count, show_progress=True):
        '''
        Performs read speed test by reading random offset blocks from
        file, at maximum of blocks_count, each at size of block_size
        bytes until the End Of File reached.
        Returns a list of read times in sec of each block.
        '''
        f = os.open(self.file, os.O_RDONLY, 0o777)  # low-level I/O
        # generate random read positions
        offsets = list(range(0, blocks_count * block_size, block_size))
        shuffle(offsets)

        took = []
        for i, offset in enumerate(offsets, 1):
            if show_progress and i % int(self.write_block_kb * 1024 / self.read_block_b) == 0:
                # read is faster than write, so try to equalize print period
                sys.stdout.write('\rReading: {:.2f} %'.format((i + 1) * 100 / blocks_count))
                sys.stdout.flush()
            start = time_time()
            os.lseek(f, offset, os.SEEK_SET)  # set position
            buff = os.read(f, block_size)  # read from position
            t = time_time() - start
            if not buff: break  # if EOF reached
            took.append(t)
        os.close(f)
        if show_progress:
            sys.stdout.write('\r{}'.format(' '*Benchmark.LINE_BUFFER_SIZE)) # clear the line
            sys.stdout.flush()
            sys.stdout.write('\r')
        return took

    def print_result(self):
        results=self.get_results()
        result_str="Full path of file: {}\n\nWritten {} took {}\nWrite speed is {}\n\tmax: {}, min: {}\n\nRead {} spread in {} blocks of {} took {}\nRead speed is {}\n\tmax: {}, min: {}\n\n".format(results['Test file full path'],
        results['Test file size'],results['Write time'],results['Write speed (avg)'],results['Write speed (max)'],results['Write speed (min)'],
        results['Test file size'],results['Read blocks'],results['Read block size'],results['Read time'],results['Read speed (avg)'],results['Read speed (max)'],results['Read speed (min)'])
        print(result_str)

    def get_json_result(self,output_file):
        results_json = parseNumericDict(self.get_results())
        with open(output_file,'w') as f:
            json.dump(results_json,f)

    def get_results(self):
        results = {}
        results["Test file full path"] = os.path.abspath(self.file) 
        results["Test file size"] = bytesToHumanReadable(self.write_mb*1024*1024)
        results["Write time"] = '{} s'.format(round(sum(self.write_results),Benchmark.ROUND_PRECISION))
        results["Write speed (avg)"] = bytesToHumanReadable(self.write_mb*1024*1024 / sum(self.write_results),'B/s')
        results["Write speed (max)"] = bytesToHumanReadable(self.write_block_kb*1024 / min(self.write_results),'B/s')
        results["Write speed (min)"] = bytesToHumanReadable(self.write_block_kb*1024 / max(self.write_results),'B/s')
        results["Write block size"] = bytesToHumanReadable(self.write_block_kb)
        results["Read blocks"] = len(self.read_results)
        results["Read time"] = '{} s'.format(round(sum(self.read_results),Benchmark.ROUND_PRECISION))
        results["Read speed (avg)"] = bytesToHumanReadable(self.write_mb*1024*1024 / sum(self.read_results),'B/s')
        results["Read speed (max)"] = bytesToHumanReadable(self.read_block_b / (min(self.read_results)),'B/s')
        results["Read speed (min)"] = bytesToHumanReadable(self.read_block_b / (max(self.read_results)),'B/s')
        results["Read block size"] = bytesToHumanReadable(self.read_block_b)
        return results

    def tear_down(self):
        try:
            os.remove(self.file)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise e

    def __del__(self):
        self.tear_down()

    @staticmethod
    def get_args():
        if Benchmark.DEFAULT_FILE_ON_TMP:
            default_test_file='/tmp/.disk_performance_test.tmp'
        else:
            default_test_file='.disk_performance_test.tmp' # to use the current location as the test location
        parser = argparse.ArgumentParser(description='Arguments', formatter_class = argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('-f','--file',required=False,action='store',default=default_test_file,help='The file to read/write to')
        parser.add_argument('-s','--size',required=False,action='store',type=int,default=256,help='Total MB to write')
        parser.add_argument('-w', '--write-block-size',required=False,action='store',type=int,default=1024,help='The block size for writing in bytes')
        parser.add_argument('-r', '--read-block-size',required=False,action='store',type=int,default=512,help='The block size for reading in bytes')
        parser.add_argument('-j', '--json',required=False,action='store',help='Output to json file')
        args=parser.parse_args()
        return args


def main():
    args = Benchmark.get_args()
    benchmark = Benchmark(args.file, args.size, args.write_block_size, args.read_block_size)
    if args.json is not None:
        benchmark.get_json_result(args.json)
    else:
        benchmark.print_result()

if __name__ == "__main__":
    main()