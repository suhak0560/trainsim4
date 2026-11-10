# coding: utf-8

import hashlib
import os
import routeeditor
import time
import tkinter as tk
from tkinter import filedialog
import traineditor
import trainlib

def get_hash(path):
    hash=hashlib.new('sha256')
    with open(path,'rb') as file:
        for chunk in iter(lambda: file.read(131072),b''):
            hash.update(chunk)
    return hash.hexdigest()

def main():
    print('Welcome!')
    print('[1] Simulate a train')
    print('[2] Create a train')
    print('[3] Create a route')
    print('[4] Reverse a route')
    print('[0] Exit')
    while True:
        command=input('Select an option: ')
        if command=='1':
            root=tk.Tk()
            root.withdraw()
            root.wm_attributes('-topmost',1)
            while True:
                train_path=filedialog.askdirectory(title='Select a train',master=root).rstrip('/\\')
                if train_path=='':
                    root.destroy()
                    break
                try:
                    with open(os.path.join(train_path,'hash.txt'),'r',encoding='utf-8') as hashlist:
                        hashes=hashlist.readlines()
                    new_hashes=[]
                    new_hashes.append(get_hash(os.path.join(train_path,'train_data.json'))+'\n')
                    new_hashes.append(get_hash(os.path.join(train_path,'grads.csv'))+'\n')
                    new_hashes.append(get_hash(os.path.join(train_path,'traction_dists.csv'))+'\n')
                    new_hashes.append(get_hash(os.path.join(train_path,'traction_times.csv'))+'\n')
                    new_hashes.append(get_hash(os.path.join(train_path,'traction_adds.csv'))+'\n')
                    new_hashes.append(get_hash(os.path.join(train_path,'brake_dists.csv'))+'\n')
                    new_hashes.append(get_hash(os.path.join(train_path,'brake_times.csv'))+'\n')
                    if new_hashes!=hashes:
                        raise ValueError
                    trainlib.main(train_path)
                    root.destroy()
                    break
                except Exception:
                    print('Invalid train data')
                    continue
            continue
        elif command=='2':
            traineditor.main()
            continue
        elif command=='3':
            routeeditor.create_route()
            continue
        elif command=='4':
            routeeditor.reverse_route()
            continue
        elif command=='0':
            print('Thank you!')
            time.sleep(2)
            break
        else:
            print('Invalid command')
            continue

if __name__=='__main__':
    main()
