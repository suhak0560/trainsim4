# coding: utf-8

from fractions import Fraction
import hashlib
from inputs import *
import json
import os
from math import ceil
from scipy.optimize import root
import time
import tkinter as tk
from tkinter import filedialog

# 1. Define fundamental functions

def get_hash(path):
    hash=hashlib.new('sha256')
    with open(path,'rb') as file:
        for chunk in iter(lambda: file.read(131072),b''):
            hash.update(chunk)
    return hash.hexdigest()

# 2. Define train object

class Train:
    def __init__(self,data,name,save_path):
        self.min_spd=int(data['min_spd'])
        self.max_spd=int(data['max_spd'])
        self.power=float(Fraction(data['power']))
        self.weight=float(Fraction(data['weight']))
        self.a=float(Fraction(data['drag']['a']))
        self.b=float(Fraction(data['drag']['b']))
        self.c=float(Fraction(data['drag']['c']))
        self.A=float(Fraction(data['brake']['A']))
        self.B=float(Fraction(data['brake']['B']))
        self.C=float(Fraction(data['brake']['C']))
        self.max_grad=Fraction(data['max_grad'])
        self.std_grad=Fraction(data['std_grad'])
        self.car_len=float(Fraction(data['car_len']))
        self.train_len=float(Fraction(data['train_len']))
        self.track_time=float(Fraction(data['track_time']))
        self.track_regen=float(Fraction(data['track_regen']))
        self.energy_rate=float(Fraction(data['energy_rate']))
        self.regen_rate=float(Fraction(data['regen_rate']))
        self.name=name
        self.save_path=save_path
        if self.min_spd%20==0:
            self.inv_incr=1
        elif self.min_spd%10==0:
            self.inv_incr=4
        else:
            self.inv_incr=1000
        self.len=self.train_len+2*self.car_len

    def drag(self,spd):
        drag=self.a*spd**2/10000+self.b*spd/100+self.c
        return drag

    def brake(self,spd):
        brake=self.A/(self.B+spd/100)+self.C
        return brake

    def traction(self,spd):
        traction=self.power/self.weight/spd*3.6
        return traction

    def acc(self,grad,spd):
        acc=self.traction(spd)-self.drag(spd)-grad/100
        return acc

    def dec(self,grad,spd):
        dec=self.brake(spd)+self.drag(spd)+grad/100
        return dec

    def bal_spd(self,grad):
        if grad<=0:
            bal_spd=self.max_spd
        else:
            bal_spd=min(self.max_spd,float(root(lambda spd: self.a*spd**3/10000+self.b*spd**2/100+(self.c+grad/100)*spd-self.power/self.weight*3.6,self.power/self.weight*3.6/(self.c+grad/100)).x[0]))
        return bal_spd

    def grad_data_output(self):
        grads='grads,data\n'
        for grad in range(int(-self.max_grad*10),int(-self.std_grad*10)+1):
            grad/=10
            low_dist=self.min_spd**2/25/(self.brake(self.min_spd)+grad/100)+2*self.car_len
            grads+=','.join(['%.1f'%grad,str(round(low_dist*self.inv_incr)/self.inv_incr)])+'\n'
        for grad in range(0,int(self.max_grad*10)+1):
            grad/=10
            bal_spd=self.bal_spd(grad)
            grads+=','.join(['%.1f'%grad,'%.4f'%bal_spd])+'\n'
        with open(os.path.join(self.save_path,self.name,'grads.csv'),'w',encoding='utf-8') as database:
            database.write(grads)

    def traction_data_output(self):
        traction_dists='traction_dists,'+','.join(list(str(spd) for spd in range(self.min_spd,self.max_spd+1)))+'\n'
        traction_times='traction_times,'+','.join(list(str(spd) for spd in range(self.min_spd,self.max_spd+1)))+'\n'
        traction_adds='traction_adds,'+','.join(list(str(spd) for spd in range(self.min_spd,self.max_spd+1)))+'\n'
        for grad in range(int(-self.max_grad*10),int(self.max_grad*10)+1):
            grad/=10
            new_traction_dists=[0]
            new_traction_times=[0]
            if grad>=float(self.std_grad):
                bal_spd=self.bal_spd(grad)
                new_traction_adds=[0]
            spd=self.min_spd
            traction_acc=self.acc(grad,spd)
            while spd<self.max_spd:
                spd+=1
                new_traction_acc=self.acc(grad,spd)
                traction_time=0.576/(traction_acc+new_traction_acc)
                traction_dist=(spd-0.5)*traction_time/3.6
                if abs(traction_dist)>2**43:
                    raise ZeroDivisionError
                new_traction_dists.append(new_traction_dists[-1]+traction_dist)
                new_traction_times.append(new_traction_times[-1]+traction_time)
                if grad>=float(self.std_grad):
                    new_traction_adds.append(new_traction_times[-1]-new_traction_dists[-1]/min(spd,bal_spd)*3.6)
                traction_acc=new_traction_acc
            new_traction_dists=['%.1f'%grad]+[str(round(traction_dist*self.inv_incr)/self.inv_incr) for traction_dist in new_traction_dists]
            new_traction_times=['%.1f'%grad]+['%.3f'%traction_time for traction_time in new_traction_times]
            if grad>=float(self.std_grad):
                new_traction_adds=['%.1f'%grad]+['%.3f'%traction_add for traction_add in new_traction_adds]
            traction_dists+=','.join(new_traction_dists)+'\n'
            traction_times+=','.join(new_traction_times)+'\n'
            if grad>=float(self.std_grad):
                traction_adds+=','.join(new_traction_adds)+'\n'
        with open(os.path.join(self.save_path,self.name,'traction_dists.csv'),'w',encoding='utf-8') as database:
            database.write(traction_dists)
        with open(os.path.join(self.save_path,self.name,'traction_times.csv'),'w',encoding='utf-8') as database:
            database.write(traction_times)
        with open(os.path.join(self.save_path,self.name,'traction_adds.csv'),'w',encoding='utf-8') as database:
            database.write(traction_adds)

    def brake_data_output(self):
        brake_dists='brake_dists,'+','.join(list(str(spd) for spd in range(self.min_spd,self.max_spd+1)))+'\n'
        brake_times='brake_times,'+','.join(list(str(spd) for spd in range(self.min_spd,self.max_spd+1)))+'\n'
        for grad in range(int(-self.max_grad*10),int(self.max_grad*10)+1):
            grad/=10
            new_brake_dists=[0]
            new_brake_times=[0]
            spd=self.min_spd
            brake_dec=self.dec(grad,spd)
            while spd<self.max_spd:
                spd+=1
                new_brake_dec=self.dec(grad,spd)
                brake_time=0.576/(brake_dec+new_brake_dec)
                brake_dist=(spd-0.5)*brake_time/3.6
                new_brake_dists.append(new_brake_dists[-1]+brake_dist)
                new_brake_times.append(new_brake_times[-1]+brake_time)
                brake_dec=new_brake_dec
            new_brake_dists=['%.1f'%grad]+[str(round(brake_dist*self.inv_incr)/self.inv_incr) for brake_dist in new_brake_dists]
            new_brake_times=['%.1f'%grad]+['%.3f'%brake_time for brake_time in new_brake_times]
            brake_dists+=','.join(new_brake_dists)+'\n'
            brake_times+=','.join(new_brake_times)+'\n'
        with open(os.path.join(self.save_path,self.name,'brake_dists.csv'),'w',encoding='utf-8') as database:
            database.write(brake_dists)
        with open(os.path.join(self.save_path,self.name,'brake_times.csv'),'w',encoding='utf-8') as database:
            database.write(brake_times)

# 3. Define main function

def main():
    # Enter base speed and max speed
    min_spd=num_input('Base Speed','km/h','1',digit=0)
    max_spd=num_input('Max Speed','km/h',str(min_spd),digit=0)
    if min_spd%20==0:
        inv_incr=1
    elif min_spd%10==0:
        inv_incr=4
    else:
        inv_incr=1000
    # Enter power and weight
    power=val_input('Power (kW)','0',False)
    weight=val_input('Weight (t)','0',False)
    # Enter drag coefficients
    print('Drag (kN/t): a(v/100)²+b(v/100)+c')
    while True:
        try:
            print('Enter a, b, c: ',end='')
            a,b,c=vals_input(['a','b','c'],['0','0','0'],[True,True,True],[None,None,None],[True,True,True],['0','0','0'])
            min_acc=power/weight/max_spd*Fraction('3.6')-(a*max_spd**2/10000+b*max_spd/100+c)
            if min_acc<0:
                raise ValueError
            break
        except Exception:
            print('Please ensure your inputs')
            print('    - are 3 valid integers, decimals or fractions separated by spaces')
            print('    - all greater than or equal to 0')
            print('    - allow for a non-negative acceleration at maximum speed')
            print('    - 0, 0, 0 by default')
            continue
    max_acc=power/weight/min_spd*Fraction('3.6')-(a*min_spd**2/10000+b*min_spd/100+c)
    # Enter brake coefficients
    print('Braking Force (kN/t): A/(B+v/100)+C')
    while True:
        try:
            print('Enter A, B, C: ',end='')
            A,B,C=vals_input(['A','B','C'],['0','0','0'],[True,True,True],[None,None,None],[True,True,True],['2.4','1.2','0'])
            min_dec=min([A/(B+spd/Fraction('100'))+C+(a*spd**2/10000+b*spd/100+c) for spd in range(int(min_spd),int(max_spd)+1)])
            min_dec=min(min_dec,A/(B+min_spd/100)+C)
            if min_dec<=0:
                raise ValueError
            break
        except Exception:
            print('Please ensure your inputs')
            print('    - are 3 valid integers, decimals or fractions separated by spaces')
            print('    - all greater than or equal to 0')
            print('    - allow for a positive deceleration at any speed')
            print('    - 2.4, 1.2, 0 by default')
            continue
    min_btr=min([(A/(B+spd/Fraction('100'))+C)/(power/weight/spd*Fraction('3.6')) for spd in range(int(min_spd),int(max_spd)+1)])
    # Enter maximum gradient and standard gradient
    max_grad=num_input('Maximum Gradient','‰','0','%.1f'%(min(int(max_acc*1000),ceil(min_dec*1000)-1)/10),digit=1)
    std_grad=num_input('Standard Gradient','‰','0','%.1f'%float(max_grad),digit=1)
    # Enter track data
    car_len=num_input('Car Length','m','0',mult=str(float(1/inv_incr)))
    train_len=num_input('Train Length','m',str(float(car_len)),mult=str(float(2/inv_incr)))
    track_time=num_input('Station Track Clearance Time','s','0',digit=3,default='%.3f'%((train_len+car_len)/min_spd*7.2))
    track_regen=val_input('Approaching Regen Ratio','0',True,'1',True,'2/3')
    # Enter energy efficiencies
    energy_rate=val_input('Energy Efficiency','0',False,'1',True,'1/1.2')
    regen_rate=val_input('Regen Efficiency','0',True,str(min_btr),True,str(min(min_btr,1))+'/1.2')
    # Create folder
    root=tk.Tk()
    root.withdraw()
    root.wm_attributes('-topmost',1)
    while True:
        name=input('Enter Train Name: ').lstrip(' ').rstrip(' .')
        if name=='':
            print('Train name cannot be empty')
            continue
        while True:
            save_path=filedialog.askdirectory(title='Select save path',master=root)
            if save_path=='':
                print('Please select a valid path')
                continue
            try:
                trains={train.lower() for train in os.listdir(save_path)}
                break
            except Exception:
                print('Cannot access this folder')
                continue
        if name.lower() in trains:
            while True:
                command=input(name+' already exists, replace it? ([1] Yes, [0] No): ')
                if command=='1' or command=='0':
                    break
                else:
                    print('Invalid command')
                    continue
        else:
            command='1'
        if command=='1':
            try:
                os.makedirs(os.path.join(save_path,name),exist_ok=True)
                root.destroy()
                break
            except Exception:
                print('Cannot save train data. Please retry.')
                continue
        elif command=='0':
            print('Please use another train name or save path')
            continue
    # Save train data
    try:
        data={'min_spd':str(min_spd),'max_spd':str(max_spd),'power':str(power),'weight':str(weight),
              'drag':{'a':str(a),'b':str(b),'c':str(c)},'brake':{'A':str(A),'B':str(B),'C':str(C)},
              'max_grad':'%.1f'%float(max_grad),'std_grad':'%.1f'%float(std_grad),
              'car_len':str(float(car_len)),'train_len':str(float(train_len)),
              'track_time':'%.3f'%float(track_time),'track_regen':str(track_regen),
              'energy_rate':str(energy_rate),'regen_rate':str(regen_rate)}
        with open(os.path.join(save_path,name,'train_data.json'),'w',encoding='utf-8') as train_data:
            json.dump(data,train_data)
        train=Train(data,name,save_path)
        now=time.time()
        train.grad_data_output()
        train.traction_data_output()
        train.brake_data_output()
        with open(os.path.join(save_path,name,'hash.txt'),'w',encoding='utf-8') as hashlist:
            hashlist.write(get_hash(os.path.join(save_path,name,'train_data.json'))+'\n')
            hashlist.write(get_hash(os.path.join(save_path,name,'grads.csv'))+'\n')
            hashlist.write(get_hash(os.path.join(save_path,name,'traction_dists.csv'))+'\n')
            hashlist.write(get_hash(os.path.join(save_path,name,'traction_times.csv'))+'\n')
            hashlist.write(get_hash(os.path.join(save_path,name,'traction_adds.csv'))+'\n')
            hashlist.write(get_hash(os.path.join(save_path,name,'brake_dists.csv'))+'\n')
            hashlist.write(get_hash(os.path.join(save_path,name,'brake_times.csv'))+'\n')
        print('Train data saved in %.3f s'%(time.time()-now))
    except Exception:
        print('Cannot save train data')
