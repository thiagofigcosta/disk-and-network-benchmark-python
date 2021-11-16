#!/bin/python3
# -*- coding: utf-8 -*-

# modified from: https://github.com/amjadsde/Speed-Test

import sys, time, socket, random, argparse, json

try:  # if Python >= 3.3 use new high-res counter
    from time import perf_counter as time_time
except ImportError:  # else select highest available resolution counter
    if sys.platform[:3] == 'win':
        from time import clock as time_time
    else:
        from time import time as time_time

has_raw_input=True
try:
    raw_input
except NameError:
    has_raw_input=False
if sys.version_info[0]==2 and has_raw_input:
    input=raw_input


def secToHumanReadable(sec,suffix='s'):
    sec=float(sec)
    if sec == 0:
        return '{} {}'.format(int(sec),suffix)
    for unit in ['','m','u','n','p','f','a','z']:
        if abs(sec) >= 1:
            if sec.is_integer():
                return '{} {}{}'.format(int(sec),unit,suffix)
            else:
                return '{:3.2f} {}{}'.format(sec,unit,suffix)
        sec *= 1000.0
    if sec.is_integer():
        return '{} {}{}'.format(int(sec),'y',suffix)
    else:
        return '{:.2f} {}{}'.format(sec,'y',suffix)

def bitsToHumanReadable(num, suffix='b'):
    num=float(num)
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1000.0:
            if num.is_integer():
                return '{} {}{}'.format(int(num),unit,suffix)
            else:
                return '{:3.2f} {}{}'.format(num,unit,suffix)
        num /= 1000.0
    if num.is_integer():
        return '{} {}{}'.format(int(num),'Y',suffix)
    else:
        return '{:.2f} {}{}'.format(num,'Y',suffix)

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
    SHOW_PROGRESS=True
    USE_THE_SAME_BUFFER=True
    LINE_BUFFER_SIZE=20
    ROUND_PRECISION=5

    def __init__(self, server_address,server_port,transfer_mb,block_size_b):
        self.server_address=server_address
        self.server_port=server_port
        self.transfer_mb=transfer_mb
        self.block_size_b=block_size_b
        count=int(self.transfer_mb * 1024 * 1024 / self.block_size_b)
        self.transfer_results = self.client_transfer_test(count)

    @staticmethod
    def random_bytearray(n):
        return bytearray(map(random.getrandbits,(8,)*n))

    def client_transfer_test(self,blocks_count,show_progress=SHOW_PROGRESS):
        t_b4_sock_open = time_time()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        t_after_sock_open = time_time()
        s.connect((self.server_address, int(self.server_port)))
        self.ping_connect = time_time()-t_after_sock_open
        if Benchmark.USE_THE_SAME_BUFFER:
            buffer = Benchmark.random_bytearray(self.block_size_b)
        took = []
        for c in range(blocks_count):
            if show_progress:
                # dirty trick to actually print progress on each iteration
                sys.stdout.write('\rTransfering: {:.2f} %'.format((c + 1) * 100 / blocks_count))
                sys.stdout.flush()
            if not Benchmark.USE_THE_SAME_BUFFER:
                buffer = Benchmark.random_bytearray(self.block_size_b)
            t_b4_send=time_time()
            s.send(buffer)
            took.append(time_time()-t_b4_send)
        if show_progress:
            sys.stdout.write('\r{}'.format(' '*Benchmark.LINE_BUFFER_SIZE)) # clear the line
            sys.stdout.flush()
            sys.stdout.write('\r')
        s.shutdown(socket.SHUT_WR)
        t_b4_sock_close = time_time()
        data = s.recv(self.block_size_b)
        self.ping_disconnect = time_time()-t_b4_sock_close
        return took

    def get_results(self):
        results = {}
        results["Server address"] = '{}:{}'.format(self.server_address,self.server_port) 
        results["Transfer size"] = bytesToHumanReadable(self.transfer_mb*1024*1024)
        results["Transfer time"] = '{} s'.format(round(sum(self.transfer_results),Benchmark.ROUND_PRECISION))
        results["Connect latency"] = secToHumanReadable(self.ping_connect)
        results["Disconnect latency"] = secToHumanReadable(self.ping_disconnect)
        results["Average latency"] = secToHumanReadable((self.ping_connect+self.ping_disconnect)/2)
        results["Transfer speed (avg)"] = bitsToHumanReadable(self.transfer_mb*1024*1024*8 / sum(self.transfer_results),'bps')
        results["Transfer speed (max)"] = bitsToHumanReadable(self.block_size_b*8 / min(self.transfer_results),'bps')
        results["Transfer speed (min)"] = bitsToHumanReadable(self.block_size_b*8 / max(self.transfer_results),'bps')
        results["Transfer block size"] = bytesToHumanReadable(self.block_size_b)
        results["Amount of blocks"] = len(self.transfer_results)
        return results

    def print_result(self):
        results=self.get_results()
        result_str="Server address: {}\n\nTransfered {} across {} blocks of {} took {}\nTransfer speed is {}\n\tmax: {}, min: {}\nAverage latency: {}\nConnect latency: {}\nDisconnect latency: {}\n\n".format(results['Server address'],
        results['Transfer size'],results['Amount of blocks'],results['Transfer block size'],results['Transfer time'],results['Transfer speed (avg)'],results['Transfer speed (max)'],results['Transfer speed (min)'],
        results['Average latency'],results['Connect latency'],results['Disconnect latency'])
        print(result_str)

    def get_json_result(self,output_file):
        results_json = parseNumericDict(self.get_results())
        with open(output_file,'w') as f:
            json.dump(results_json,f)

    @staticmethod
    def get_args():
        parser = argparse.ArgumentParser(description='Arguments', formatter_class = argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('-a','--ip-address',required=False,action='store',default=None,help='The server IP address')
        parser.add_argument('-p','--port',required=False,action='store',default=None,help='The server port')
        parser.add_argument('-s','--size',required=False,action='store',type=int,default=256,help='Total MB to transfer')
        parser.add_argument('-b', '--block-size',required=False,action='store',type=int,default=1048576,help='The block size for transfer in bytes')
        parser.add_argument('-j', '--json',required=False,action='store',help='Output to json file')
        args=parser.parse_args()
        return args

def main():
    args = Benchmark.get_args()
    if args.ip_address is None:
        args.ip_address=input('Server IP: ')
    if args.port is None:
        args.port=input('Server port: ')

    benchmark = Benchmark(args.ip_address, args.port, args.size, args.block_size)

    if args.json is not None:
        benchmark.get_json_result(args.json)
    else:
        benchmark.print_result()

if __name__ == "__main__":
    main()