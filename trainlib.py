# coding: utf-8

from fractions import Fraction
import hashlib
from inputs import *
import json
from math import ceil,isqrt
import os
import pandas as pd
import time
import tkinter as tk
from tkinter import filedialog

# 1. Define fundamental functions

def csv_import(csv_path,index_col=0,dtype=float):
    df=pd.read_csv(csv_path,index_col=index_col,dtype=dtype)
    return df

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
        self.len=self.train_len+2*self.car_len
        self.grads=csv_import(os.path.join(save_path,name,'grads.csv'))
        self.traction_dists=csv_import(os.path.join(save_path,name,'traction_dists.csv'))
        self.traction_times=csv_import(os.path.join(save_path,name,'traction_times.csv'))
        self.traction_adds=csv_import(os.path.join(save_path,name,'traction_adds.csv'))
        self.brake_dists=csv_import(os.path.join(save_path,name,'brake_dists.csv'))
        self.brake_times=csv_import(os.path.join(save_path,name,'brake_times.csv'))

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

    def low_dist(self,grad):
        low_dist=float(self.grads.at[min(grad,float(-self.std_grad)),'data'])
        return low_dist

    def bal_spd(self,grad):
        bal_spd=float(self.grads.at[max(grad,0),'data'])
        return bal_spd

    def traction_dist(self,grad,spd):
        traction_dist=float(self.traction_dists.at[grad,str(spd)])
        return traction_dist

    def traction_time(self,grad,spd):
        traction_time=float(self.traction_times.at[grad,str(spd)])
        return traction_time

    def traction_add(self,grad,spd):
        traction_add=float(self.traction_adds.at[max(grad,float(self.std_grad)),str(spd)])
        return traction_add

    def brake_dist(self,grad,spd):
        brake_dist=float(self.brake_dists.at[grad,str(spd)])
        return brake_dist

    def brake_time(self,grad,spd):
        brake_time=float(self.brake_times.at[grad,str(spd)])
        return brake_time

    def find_traction_spd(self,grad,spd_lim,start_spd,dist_lim):
        bal_spd=self.bal_spd(grad)
        if start_spd>=int(bal_spd) and start_spd<=ceil(bal_spd):
            return start_spd
        elif start_spd<int(bal_spd):
            dist_lim+=self.traction_dist(grad,start_spd)
            left=start_spd
            right=min(spd_lim,int(bal_spd))
            while left<=right:
                mid=(left+right)//2
                traction_dist=self.traction_dist(grad,mid)
                if traction_dist<=dist_lim:
                    left=mid+1
                    traction_spd=mid
                    continue
                else:
                    right=mid-1
                    continue
        elif start_spd>ceil(bal_spd):
            dist_lim+=self.traction_dist(grad,start_spd)
            left=ceil(bal_spd)
            right=start_spd
            while left<=right:
                mid=(left+right)//2
                traction_dist=self.traction_dist(grad,mid)
                if traction_dist<=dist_lim:
                    right=mid-1
                    traction_spd=mid
                    continue
                else:
                    left=mid+1
                    continue
        return traction_spd

    def find_brake_spd(self,grad,spd_lim,end_spd,dist_lim):
        dist_lim+=self.brake_dist(grad,end_spd)
        left=end_spd
        right=spd_lim
        while left<=right:
            mid=(left+right)//2
            brake_dist=self.brake_dist(grad,mid)
            if brake_dist<=dist_lim:
                left=mid+1
                brake_spd=mid
                continue
            else:
                right=mid-1
                continue
        return brake_spd

    def find_sec_spd(self,grad,spd_lim,start_spd,end_spd,dist_lim):
        bal_spd=self.bal_spd(grad)
        if start_spd>=int(bal_spd) and start_spd<=ceil(bal_spd):
            return start_spd
        elif start_spd<int(bal_spd):
            dist_lim+=self.traction_dist(grad,start_spd)+self.brake_dist(grad,end_spd)
            left=max(start_spd,end_spd)
            right=min(spd_lim,int(bal_spd))
            while left<=right:
                mid=(left+right)//2
                sec_dist=self.traction_dist(grad,mid)+self.brake_dist(grad,mid)
                if sec_dist<=dist_lim:
                    left=mid+1
                    sec_spd=mid
                    continue
                else:
                    right=mid-1
                    continue
        elif start_spd>ceil(bal_spd):
            dist_lim+=self.traction_dist(grad,start_spd)+self.brake_dist(grad,end_spd)
            left=max(end_spd,ceil(bal_spd))
            right=start_spd
            while left<=right:
                mid=(left+right)//2
                sec_dist=self.traction_dist(grad,mid)+self.brake_dist(grad,mid)
                if sec_dist<=dist_lim:
                    right=mid-1
                    sec_spd=mid
                    continue
                else:
                    left=mid+1
                    continue
        return sec_spd

    def int_arr(self,grad,brake_spd,enter_dist=0,exit_dist=0,dwell_time=0):
        brake_time=self.brake_time(min(grad,float(-self.std_grad)),brake_spd)
        low_dist=self.low_dist(grad)
        enter_time=(enter_dist-self.len)/self.min_spd*3.6+self.track_time if enter_dist>0 else 0
        exit_time=(exit_dist-self.len)/self.min_spd*3.6+self.track_time if exit_dist>0 else 0
        int_arr=brake_time+low_dist/brake_spd*3.6+enter_time+exit_time+dwell_time
        return int_arr

    def int_dep(self,grad,traction_spd,block_len=0,exit_dist=0):
        traction_add=self.traction_add(grad,traction_spd)
        exit_time=(exit_dist-self.len)/self.min_spd*3.6+self.track_time if exit_dist>0 else 0
        int_dep=traction_add+block_len/min(traction_spd,self.bal_spd(max(grad,float(self.std_grad))))*3.6+exit_time
        return int_dep

    def find_brake_lim(self,grad,int_lim,enter_dist=0,exit_dist=0,dwell_time=0):
        enter_time=(enter_dist-self.len)/self.min_spd*3.6+self.track_time if enter_dist>0 else 0
        exit_time=(exit_dist-self.len)/self.min_spd*3.6+self.track_time if exit_dist>0 else 0
        int_lim-=enter_time+exit_time+dwell_time
        brake_spd=self.min_spd
        int_arr=self.int_arr(grad,brake_spd)
        try:
            while True:
                brake_spd+=1
                new_int_arr=self.int_arr(grad,brake_spd)
                if new_int_arr>int_arr:
                    break
                int_arr=new_int_arr
            left=brake_spd-1
            right=self.max_spd
            while left<=right:
                mid=(left+right)//2
                int_arr=self.int_arr(grad,mid)
                if int_arr<=int_lim:
                    left=mid+1
                    brake_lim=mid
                    continue
                else:
                    right=mid-1
                    continue
            return brake_lim
        except KeyError:
            return self.max_spd if self.int_arr(grad,self.max_spd)<=int_lim else 0
        except UnboundLocalError:
            return 0

    def find_traction_lim(self,grad,int_lim,block_len=0,exit_dist=0):
        exit_time=(exit_dist-self.len)/self.min_spd*3.6+self.track_time if exit_dist>0 else 0
        int_lim-=exit_time
        traction_spd=self.min_spd
        int_dep=self.int_dep(grad,traction_spd,block_len)
        try:
            while True:
                traction_spd+=1
                new_int_dep=self.int_dep(grad,traction_spd,block_len)
                if new_int_dep>int_dep:
                    break
                int_dep=new_int_dep
            left=traction_spd-1
            right=self.max_spd
            while left<=right:
                mid=(left+right)//2
                int_dep=self.int_dep(grad,mid,block_len)
                if int_dep<=int_lim:
                    left=mid+1
                    traction_lim=mid
                    continue
                else:
                    right=mid-1
                    continue
            return traction_lim
        except KeyError:
            return self.max_spd if self.int_dep(grad,self.max_spd,block_len)<=int_lim else 0
        except UnboundLocalError:
            return 0

    def route_data_output(self,route,start_spd,end_spd,exit_dist=0,enter_dist=0):

        # 1. Summarize grades, curves and speed limits

        grades=csv_import(os.path.join(route,'grades.csv'),index_col=None).replace(-0.0,0.0)
        curves=csv_import(os.path.join(route,'curves.csv'),index_col=None).replace(-0.0,0.0)
        spd_lims=csv_import(os.path.join(route,'spd_lims.csv'),index_col=None).replace(-0.0,0.0)
        start=grades['start'].tolist()[0]
        end=grades['end'].tolist()[-1]
        curves['spd_lim']=(curves['rad']*curves['cant']/12).astype(int).apply(isqrt)
        curves=curves[['start','end','spd_lim']]
        spd_lims=pd.concat([curves,spd_lims])
        spd_lims['start']-=self.len/2
        spd_lims['end']+=self.len/2
        secs=sorted(set([start+exit_dist,end-enter_dist])|set(grades['start'])|set(grades['end'])|set(spd_lims['start'])|set(spd_lims['end']))
        secs=secs[secs.index(start+exit_dist):secs.index(end-enter_dist)+1]
        sec_data=[]
        for i in range(len(secs)-1):
            sec_start=float(secs[i])
            sec_end=float(secs[i+1])
            sec_grad=float(grades[(grades['start']<=sec_start)&(grades['end']>=sec_end)]['grad'].iloc[0])
            sec_spd_lims=spd_lims[(spd_lims['start']<=sec_start)&(spd_lims['end']>=sec_end)]['spd_lim']
            sec_spd_lim=min(self.max_spd,int(sec_spd_lims.min())) if not sec_spd_lims.empty else self.max_spd
            sec_data.append([sec_end-sec_start,sec_grad,sec_spd_lim])

        # 2. Judge train behaviour

        for i in range(len(sec_data)):
            sec_len,grad,spd_lim=sec_data[i]
            start_spd=min(start_spd,spd_lim)
            traction_spd=self.find_traction_spd(grad,spd_lim,start_spd,sec_len)
            sec_data[i]+=[start_spd,traction_spd]
            start_spd=traction_spd
        for j in range(len(sec_data))[::-1]:
            sec_len,grad,spd_lim,start_spd,traction_spd=sec_data[j]
            end_spd=min(end_spd,spd_lim)
            brake_spd=self.find_brake_spd(grad,spd_lim,end_spd,sec_len)
            sec_data[j]+=[brake_spd,end_spd]
            end_spd=brake_spd
        for k in range(len(sec_data)):
            sec_len,grad,spd_lim,start_spd,traction_spd,brake_spd,end_spd=sec_data[k]
            bal_spd=self.bal_spd(grad)
            if start_spd<=brake_spd and traction_spd<=end_spd:
                sec_data[k].append('traction')
            elif start_spd<=ceil(bal_spd):
                if start_spd>=brake_spd and traction_spd>end_spd:
                    sec_data[k].append('brake')
                else:
                    sec_data[k].append('sec')
            elif start_spd>ceil(bal_spd):
                if start_spd<=brake_spd and traction_spd>end_spd:
                    sec_data[k].append('sec')
                else:
                    sec_data[k].append('brake')

        # 3. Export train performance simulation results

        with open(os.path.join(route,self.name+'.csv'),'w',encoding='utf-8') as datalog:
            datalog.write('milepost,spd_lim,spd,total_time,total_energy,grad\n')

            # Exiting (if available)

            total_time=0
            total_energy=0
            point=start
            if exit_dist>0:
                datalog.write(','.join(['%.3f'%point,str(self.min_spd),str(0),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%0.0])+'\n')
                total_time+=self.track_time
                total_energy+=self.weight*self.min_spd**2/25/self.energy_rate/3600
                point+=self.len
                datalog.write(','.join(['%.3f'%point,str(self.min_spd),str(self.min_spd),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%0.0])+'\n')
                total_time+=(exit_dist-self.len)/self.min_spd*3.6
                total_energy+=self.weight*self.drag(self.min_spd)*(exit_dist-self.len)/self.energy_rate/3600
                point+=(exit_dist-self.len)
                datalog.write(','.join(['%.3f'%point,str(self.min_spd),str(self.min_spd),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%0.0])+'\n')

            for sec in sec_data:
                sec_len,grad,spd_lim,start_spd,traction_spd,brake_spd,end_spd,status=sec

                # Traction & cruising

                if status=='traction':
                    bal_spd=self.bal_spd(grad)
                    if start_spd>=int(bal_spd) and start_spd<=ceil(bal_spd):
                        spd=start_spd
                        datalog.write(','.join(['%.3f'%point,str(spd_lim),str(spd),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%grad])+'\n')
                        res=self.drag(spd)+grad/100
                        total_time+=sec_len/spd*3.6
                        total_energy+=self.weight*res*sec_len/self.energy_rate/3600 if res>=0 else self.weight*max(res,-self.traction(spd))*sec_len*self.regen_rate/3600
                        point+=sec_len
                        datalog.write(','.join(['%.3f'%point,str(spd_lim),str(spd),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%grad])+'\n')
                        continue
                    elif start_spd<int(bal_spd):
                        traction_point=point+sec_len
                        start_point=point-self.traction_dist(grad,start_spd)
                        start_time=total_time-self.traction_time(grad,start_spd)
                        start_energy=total_energy-self.power*total_time/self.energy_rate/3600
                        for spd in range(start_spd,traction_spd+1):
                            total_time=start_time+self.traction_time(grad,spd)
                            total_energy=start_energy+self.power*total_time/self.energy_rate/3600
                            point=start_point+self.traction_dist(grad,spd)
                            datalog.write(','.join(['%.3f'%point,str(spd_lim),str(spd),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%grad])+'\n')
                        res=self.drag(spd)+grad/100
                        total_time+=(traction_point-point)/spd*3.6
                        total_energy+=self.weight*res*(traction_point-point)/self.energy_rate/3600 if res>=0 else self.weight*max(res,-self.traction(spd))*(traction_point-point)*self.regen_rate/3600
                        point=traction_point
                        datalog.write(','.join(['%.3f'%point,str(spd_lim),str(spd),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%grad])+'\n')
                        continue
                    elif start_spd>ceil(bal_spd):
                        traction_point=point+sec_len
                        start_point=point-self.traction_dist(grad,start_spd)
                        start_time=total_time-self.traction_time(grad,start_spd)
                        start_energy=total_energy-self.power*total_time/self.energy_rate/3600
                        for spd in range(traction_spd,start_spd+1)[::-1]:
                            total_time=start_time+self.traction_time(grad,spd)
                            total_energy=start_energy+self.power*total_time/self.energy_rate/3600
                            point=start_point+self.traction_dist(grad,spd)
                            datalog.write(','.join(['%.3f'%point,str(spd_lim),str(spd),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%grad])+'\n')
                        res=self.drag(spd)+grad/100
                        total_time+=(traction_point-point)/spd*3.6
                        total_energy+=self.weight*res*(traction_point-point)/self.energy_rate/3600 if res>=0 else self.weight*max(res,-self.traction(spd))*(traction_point-point)*self.regen_rate/3600
                        point=traction_point
                        datalog.write(','.join(['%.3f'%point,str(spd_lim),str(spd),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%grad])+'\n')
                        continue

                # Braking

                elif status=='brake':
                    end_point=point+sec_len+self.brake_dist(grad,end_spd)
                    brake_point=end_point-self.brake_dist(grad,brake_spd)
                    spd=brake_spd
                    datalog.write(','.join(['%.3f'%point,str(spd_lim),str(spd),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%grad])+'\n')
                    res=self.drag(spd)+grad/100
                    total_time+=(brake_point-point)/spd*3.6
                    total_energy+=self.weight*res*(brake_point-point)/self.energy_rate/3600 if res>=0 else self.weight*max(res,-self.traction(spd))*(brake_point-point)*self.regen_rate/3600
                    end_time=total_time+self.brake_time(grad,brake_spd)
                    end_energy=total_energy+self.power*total_time*self.regen_rate/3600
                    for spd in range(end_spd,brake_spd+1)[::-1]:
                        total_time=end_time-self.brake_time(grad,spd)
                        total_energy=end_energy-self.power*total_time*self.regen_rate/3600
                        point=end_point-self.brake_dist(grad,spd)
                        datalog.write(','.join(['%.3f'%point,str(spd_lim),str(spd),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%grad])+'\n')
                    continue

                # Traction + braking

                elif status=='sec':
                    bal_spd=self.bal_spd(grad)
                    sec_spd=self.find_sec_spd(grad,spd_lim,start_spd,end_spd,sec_len)
                    if start_spd>=int(bal_spd) and start_spd<=ceil(bal_spd):
                        end_point=point+sec_len+self.brake_dist(grad,end_spd)
                        brake_point=end_point-self.brake_dist(grad,sec_spd)
                        spd=sec_spd
                        datalog.write(','.join(['%.3f'%point,str(spd_lim),str(spd),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%grad])+'\n')
                        res=self.drag(spd)+grad/100
                        total_time+=(brake_point-point)/spd*3.6
                        total_energy+=self.weight*res*(brake_point-point)/self.energy_rate/3600 if res>=0 else self.weight*max(res,-self.traction(spd))*(brake_point-point)*self.regen_rate/3600
                        end_time=total_time+self.brake_time(grad,spd)
                        end_energy=total_energy+self.power*total_time*self.regen_rate/3600
                        for spd in range(end_spd,sec_spd+1)[::-1]:
                            total_time=end_time-self.brake_time(grad,spd)
                            total_energy=end_energy-self.power*total_time*self.regen_rate/3600
                            point=end_point-self.brake_dist(grad,spd)
                            datalog.write(','.join(['%.3f'%point,str(spd_lim),str(spd),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%grad])+'\n')
                        continue
                    elif start_spd<int(bal_spd):
                        end_point=point+sec_len+self.brake_dist(grad,end_spd)
                        brake_point=end_point-self.brake_dist(grad,sec_spd)
                        start_point=point-self.traction_dist(grad,start_spd)
                        start_time=total_time-self.traction_time(grad,start_spd)
                        start_energy=total_energy-self.power*total_time/self.energy_rate/3600
                        for spd in range(start_spd,sec_spd+1):
                            total_time=start_time+self.traction_time(grad,spd)
                            total_energy=start_energy+self.power*total_time/self.energy_rate/3600
                            point=start_point+self.traction_dist(grad,spd)
                            datalog.write(','.join(['%.3f'%point,str(spd_lim),str(spd),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%grad])+'\n')
                        res=self.drag(spd)+grad/100
                        total_time+=(brake_point-point)/spd*3.6
                        total_energy+=self.weight*res*(brake_point-point)/self.energy_rate/3600 if res>=0 else self.weight*max(res,-self.traction(spd))*(brake_point-point)*self.regen_rate/3600
                        end_time=total_time+self.brake_time(grad,spd)
                        end_energy=total_energy+self.power*total_time*self.regen_rate/3600
                        for spd in range(end_spd,sec_spd+1)[::-1]:
                            total_time=end_time-self.brake_time(grad,spd)
                            total_energy=end_energy-self.power*total_time*self.regen_rate/3600
                            point=end_point-self.brake_dist(grad,spd)
                            datalog.write(','.join(['%.3f'%point,str(spd_lim),str(spd),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%grad])+'\n')
                        continue
                    elif start_spd>ceil(bal_spd):
                        end_point=point+sec_len+self.brake_dist(grad,end_spd)
                        brake_point=end_point-self.brake_dist(grad,sec_spd)
                        start_point=point-self.traction_dist(grad,start_spd)
                        start_time=total_time-self.traction_time(grad,start_spd)
                        start_energy=total_energy-self.power*total_time/self.energy_rate/3600
                        for spd in range(sec_spd,start_spd+1)[::-1]:
                            total_time=start_time+self.traction_time(grad,spd)
                            total_energy=start_energy+self.power*total_time/self.energy_rate/3600
                            point=start_point+self.traction_dist(grad,spd)
                            datalog.write(','.join(['%.3f'%point,str(spd_lim),str(spd),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%grad])+'\n')
                        res=self.drag(spd)+grad/100
                        total_time+=(brake_point-point)/spd*3.6
                        total_energy+=self.weight*res*(brake_point-point)/self.energy_rate/3600 if res>=0 else self.weight*max(res,-self.traction(spd))*(brake_point-point)*self.regen_rate/3600
                        end_time=total_time+self.brake_time(grad,spd)
                        end_energy=total_energy+self.power*total_time*self.regen_rate/3600
                        for spd in range(end_spd,sec_spd+1)[::-1]:
                            total_time=end_time-self.brake_time(grad,spd)
                            total_energy=end_energy-self.power*total_time*self.regen_rate/3600
                            point=end_point-self.brake_dist(grad,spd)
                            datalog.write(','.join(['%.3f'%point,str(spd_lim),str(spd),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%grad])+'\n')
                        continue

            # Entering (if available)

            if enter_dist>0:
                datalog.write(','.join(['%.3f'%point,str(self.min_spd),str(self.min_spd),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%0.0])+'\n')
                total_time+=(enter_dist-self.len)/self.min_spd*3.6
                total_energy+=self.weight*self.drag(self.min_spd)*(enter_dist-self.len)/self.energy_rate/3600
                point+=(enter_dist-self.len)
                datalog.write(','.join(['%.3f'%point,str(self.min_spd),str(self.min_spd),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%0.0])+'\n')
                total_time+=self.track_time
                total_energy-=self.weight*self.min_spd**2/25*self.track_regen*self.regen_rate/3600
                point+=self.len
                datalog.write(','.join(['%.3f'%point,str(self.min_spd),str(0),'%.3f'%total_time,'%.3f'%total_energy,'%.1f'%0.0])+'\n')

        return total_time,total_energy

# 3. Define main function

def main(train_path):
    with open(os.path.join(train_path,'train_data.json'),'r',encoding='utf-8') as train_data:
        data=json.load(train_data)
    name=os.path.basename(train_path)
    save_path=os.path.dirname(train_path)
    train=Train(data,name,save_path)
    print('[1] Simulate train performance on a route')
    print('[2] Calculate traction performance')
    print('[3] Calculate braking performance')
    print('[4] Calculate Final Speed of traction')
    print('[5] Calculate Initial Speed of braking')
    print('[6] Calculate Peak Speed on a grade')
    print('[7] Calculate Minimum Curve Radius')
    print('[8] Calculate Curve Speed Limit')
    print('[9] Calculate Arrival Interval')
    print('[10] Calculate Departure Interval')
    print('[11] Calculate Braking Speed Limit')
    print('[12] Calculate Traction Speed Limit')
    print('[0] Exit')
    while True:
        command=input('Select an option: ')
        if command=='1':
            root=tk.Tk()
            root.withdraw()
            root.wm_attributes('-topmost',1)
            while True:
                route_path=filedialog.askdirectory(title='Select a route',master=root).rstrip('/\\')
                if route_path=='':
                    root.destroy()
                    break
                try:
                    grades=csv_import(os.path.join(route_path,'grades.csv'),index_col=None,dtype=str)
                    curves=csv_import(os.path.join(route_path,'curves.csv'),index_col=None,dtype=str)
                    spd_lims=csv_import(os.path.join(route_path,'spd_lims.csv'),index_col=None,dtype=str)
                    test_df=pd.concat([grades,curves,spd_lims])
                    if test_df['start'].apply(lambda start: '.' in start and len(start)-start.index('.')-1).max()>3:
                        print('Invalid route data format')
                        continue
                    elif test_df['end'].apply(lambda end: '.' in end and len(end)-end.index('.')-1).max()>3:
                        print('Invalid route data format')
                        continue
                    elif grades['grad'].apply(lambda grad: '.' in grad and len(grad)-grad.index('.')-1).max()>1:
                        print('Invalid route data format')
                        continue
                    elif curves['rad'].apply(lambda rad: '.' in rad and len(rad)-rad.index('.')-1).max()>3:
                        print('Invalid route data format')
                        continue
                    grades=grades.astype(float)
                    curves=curves.astype(float)
                    spd_lims=spd_lims.astype(float)
                    test_df=test_df.astype(float)
                    test_df['len']=test_df['end']-test_df['start']
                    if test_df['len'].min()<=0:
                        print('Invalid route data format')
                        continue
                    elif grades['start'].tolist()[1:]!=grades['end'].tolist()[:-1]:
                        print('Invalid route data format')
                        continue
                    elif max((curves['cant']%1).max(),(spd_lims['spd_lim']%1).max())>0:
                        print('Invalid route data format')
                        continue
                    elif grades['grad'].min()<-train.max_grad or grades['grad'].max()>train.max_grad:
                        print('Grade too steep')
                        continue
                    elif (curves['rad']*curves['cant']/12).astype(int).apply(isqrt).min()<train.min_spd:
                        print('Curve too sharp')
                        continue
                    elif spd_lims['spd_lim'].min()<train.min_spd:
                        print('Speed limit too low')
                        continue
                    route_len=grades['end'].tolist()[-1]-grades['start'].tolist()[0]
                    exit_dist=float(num_input('Exiting Length','m','%.3f'%train.len,'%.3f'%route_len,3,default=str(0)))
                    start_spd=int(num_input('Initial Speed','km/h',str(train.min_spd),str(train.max_spd),0,default=str(train.max_spd))) if exit_dist==0 else train.min_spd
                    enter_dist=float(num_input('Entering Length','m','%.3f'%train.len,'%.3f'%(route_len-exit_dist),3,default=str(0)))
                    end_spd=int(num_input('Final Speed','km/h',str(train.min_spd),str(train.max_spd),0,default=str(train.max_spd))) if enter_dist==0 else train.min_spd
                    now=time.time()
                    total_time,total_energy=train.route_data_output(route_path,start_spd,end_spd,exit_dist,enter_dist)
                    print('Train performance simulation completed in %.3f s'%(time.time()-now))
                    avgspd=route_len/total_time*3.6
                    print('Travel Distance: %.3f m'%route_len)
                    print('Travel Time: %.3f s'%total_time)
                    print('Energy Consumption: %.3f kWh'%total_energy)
                    print('Average Speed: %.1f km/h'%avgspd)
                    root.destroy()
                    break
                except Exception:
                    print('Invalid route data')
                    continue
            continue
        elif command=='2':
            grad=float(num_input('Gradient','‰',str(-train.max_grad),str(train.max_grad),1,default=str(0)))
            bal_spd=train.bal_spd(grad)
            start_spd=int(num_input('Initial Speed','km/h',str(train.min_spd),str(train.max_spd),0))
            if start_spd>=int(bal_spd) and start_spd<=ceil(bal_spd):
                traction_spd=int(num_input('Final Speed','km/h',str(start_spd),str(start_spd),0))
            elif start_spd<int(bal_spd):
                traction_spd=int(num_input('Final Speed','km/h',str(start_spd),str(int(bal_spd)),0))
            elif start_spd>ceil(bal_spd):
                traction_spd=int(num_input('Final Speed','km/h',str(ceil(bal_spd)),str(start_spd),0))
            traction_dist=train.traction_dist(grad,traction_spd)-train.traction_dist(grad,start_spd)
            traction_time=train.traction_time(grad,traction_spd)-train.traction_time(grad,start_spd)
            traction_energy=train.power*traction_time/train.energy_rate/3600
            print('Traction Distance: %.3f m'%traction_dist)
            print('Traction Time: %.3f s'%traction_time)
            print('Energy Consumption: %.3f kWh'%traction_energy)
            continue
        elif command=='3':
            grad=float(num_input('Gradient','‰',str(-train.max_grad),str(train.max_grad),1,default=str(0)))
            brake_spd=int(num_input('Initial Speed','km/h',str(train.min_spd),str(train.max_spd),0))
            end_spd=int(num_input('Final Speed','km/h',str(train.min_spd),str(brake_spd),0))
            brake_dist=train.brake_dist(grad,brake_spd)-train.brake_dist(grad,end_spd)
            brake_time=train.brake_time(grad,brake_spd)-train.brake_time(grad,end_spd)
            brake_energy=-train.power*brake_time*train.regen_rate/3600
            print('Braking Distance: %.3f m'%brake_dist)
            print('Braking Time: %.3f s'%brake_time)
            print('Energy Consumption: %.3f kWh'%brake_energy)
            continue
        elif command=='4':
            grad=float(num_input('Gradient','‰',str(-train.max_grad),str(train.max_grad),1,default=str(0)))
            start_spd=int(num_input('Initial Speed','km/h',str(train.min_spd),str(train.max_spd),0))
            dist_lim=float(num_input('Traction Distance','m',str(0),None,3))
            traction_spd=train.find_traction_spd(grad,train.max_spd,start_spd,dist_lim)
            traction_dist=train.traction_dist(grad,traction_spd)-train.traction_dist(grad,start_spd)
            traction_time=train.traction_time(grad,traction_spd)-train.traction_time(grad,start_spd)
            traction_energy=train.power*traction_time/train.energy_rate/3600
            res=train.drag(traction_spd)+grad/100
            traction_time+=(dist_lim-traction_dist)/traction_spd*3.6
            traction_energy+=train.weight*res*(dist_lim-traction_dist)/train.energy_rate/3600 if res>=0 else train.weight*max(res,-train.traction(traction_spd))*(dist_lim-traction_dist)*train.regen_rate/3600
            print('Final Speed: '+str(traction_spd)+' km/h')
            print('Traction Time: %.3f s'%traction_time)
            print('Energy Consumption: %.3f kWh'%traction_energy)
            continue
        elif command=='5':
            grad=float(num_input('Gradient','‰',str(-train.max_grad),str(train.max_grad),1,default=str(0)))
            end_spd=int(num_input('Final Speed','km/h',str(train.min_spd),str(train.max_spd),0))
            dist_lim=float(num_input('Braking Distance','m',str(0),None,3))
            brake_spd=train.find_brake_spd(grad,train.max_spd,end_spd,dist_lim)
            brake_dist=train.brake_dist(grad,brake_spd)-train.brake_dist(grad,end_spd)
            brake_time=train.brake_time(grad,brake_spd)-train.brake_time(grad,end_spd)
            brake_energy=-train.power*brake_time*train.regen_rate/3600
            res=train.drag(brake_spd)+grad/100
            brake_time+=(dist_lim-brake_dist)/brake_spd*3.6
            brake_energy+=train.weight*res*(dist_lim-brake_dist)/train.energy_rate/3600 if res>=0 else train.weight*max(res,-train.traction(brake_spd))*(dist_lim-brake_dist)*train.regen_rate/3600
            print('Initial Speed: '+str(brake_spd)+' km/h')
            print('Braking Time: %.3f s'%brake_time)
            print('Energy Consumption: %.3f kWh'%brake_energy)
            continue
        elif command=='6':
            grad=float(num_input('Gradient','‰',str(-train.max_grad),str(train.max_grad),1,default=str(0)))
            start_spd=int(num_input('Initial Speed','km/h',str(train.min_spd),str(train.max_spd),0))
            dist_lim=float(num_input('Grade Length','m',str(0),None,3))
            traction_spd=train.find_traction_spd(grad,train.max_spd,start_spd,dist_lim)
            min_dist=train.brake_dist(grad,start_spd)-dist_lim
            left=train.min_spd
            right=start_spd
            while left<=right:
                mid=(left+right)//2
                brake_dist=train.brake_dist(grad,mid)
                if brake_dist>=min_dist:
                    right=mid-1
                    end_spd=mid
                    continue
                else:
                    left=mid+1
                    continue
            end_spd=int(num_input('Final Speed','km/h',str(end_spd),str(traction_spd),0))
            sec_spd=train.find_sec_spd(grad,train.max_spd,start_spd,end_spd,dist_lim)
            traction_dist=train.traction_dist(grad,sec_spd)-train.traction_dist(grad,start_spd)
            traction_time=train.traction_time(grad,sec_spd)-train.traction_time(grad,start_spd)
            traction_energy=train.power*traction_time/train.energy_rate/3600
            brake_dist=train.brake_dist(grad,sec_spd)-train.brake_dist(grad,end_spd)
            brake_time=train.brake_time(grad,sec_spd)-train.brake_time(grad,end_spd)
            brake_energy=-train.power*brake_time*train.regen_rate/3600
            sec_time=traction_time+brake_time
            sec_energy=traction_energy+brake_energy
            res=train.drag(sec_spd)+grad/100
            sec_time+=(dist_lim-traction_dist-brake_dist)/sec_spd*3.6
            sec_energy+=train.weight*res*(dist_lim-traction_dist-brake_dist)/train.energy_rate/3600 if res>=0 else train.weight*max(res,-train.traction(sec_spd))*(dist_lim-traction_dist-brake_dist)*train.regen_rate/3600
            print('Peak Speed: '+str(sec_spd)+' km/h')
            print('Running Time: %.3f s'%sec_time)
            print('Energy Consumption: %.3f kWh'%sec_energy)
            continue
        elif command=='7':
            spd_lim=int(num_input('Speed Limit','km/h',str(train.min_spd),str(train.max_spd),0,default=str(train.max_spd)))
            cant=int(num_input('Equilibrium Cant','mm',str(1),None,0,default=str(320)))
            rad=12*spd_lim**2/cant
            print('Minimum Radius: %.3f m'%rad)
            continue
        elif command=='8':
            rad=float(num_input('Curve Radius','m',str(0),None,3))
            cant=int(num_input('Equilibrium Cant','mm',str(1),None,0,default=str(320)))
            spd_lim=min(isqrt(int(rad*cant/12)),train.max_spd)
            if spd_lim<train.min_spd:
                print('Curve too sharp')
            else:
                print('Speed Limit: '+str(spd_lim)+' km/h')
            continue
        elif command=='9':
            grad=float(num_input('Gradient','‰',str(-train.max_grad),str(train.max_grad),1,default=str(0)))
            brake_spd=int(num_input('Initial Speed','km/h',str(train.min_spd),str(train.max_spd),0,default=str(train.max_spd)))
            enter_dist=float(num_input('Entering Length','m','%.3f'%train.len,None,3,default=str(0)))
            exit_dist=float(num_input('Exiting Length','m','%.3f'%train.len,None,3,default=str(0))) if enter_dist>0 else 0
            dwell_time=float(num_input('Dwell Time','s',str(0),None,3,default=str(0))) if exit_dist>0 else 0
            int_arr=train.int_arr(grad,brake_spd,enter_dist,exit_dist,dwell_time)
            print('Arrival Interval: %.3f s'%int_arr)
            continue
        elif command=='10':
            grad=float(num_input('Gradient','‰',str(-train.max_grad),str(train.max_grad),1,default=str(0)))
            traction_spd=int(num_input('Final Speed','km/h',str(train.min_spd),str(train.max_spd),0,default=str(train.max_spd)))
            block_len=float(num_input('Block Length','m',str(0),None,3,default=str(0)))
            exit_dist=float(num_input('Exiting Length','m','%.3f'%train.len,None,3,default=str(0)))
            int_dep=train.int_dep(grad,traction_spd,block_len,exit_dist)
            print('Departure Interval: %.3f s'%int_dep)
            continue
        elif command=='11':
            grad=float(num_input('Gradient','‰',str(-train.max_grad),str(train.max_grad),1,default=str(0)))
            int_lim=float(num_input('Arrival Interval','s',str(0),None,3))
            enter_dist=float(num_input('Entering Length','m','%.3f'%train.len,None,3,default=str(0)))
            exit_dist=float(num_input('Exiting Length','m','%.3f'%train.len,None,3,default=str(0))) if enter_dist>0 else 0
            dwell_time=float(num_input('Dwell Time','s',str(0),None,3,default=str(0))) if exit_dist>0 else 0
            brake_lim=train.find_brake_lim(grad,int_lim,enter_dist,exit_dist,dwell_time)
            if brake_lim==0:
                print('Insufficient Train Headway')
            else:
                print('Braking Speed Limit: '+str(brake_lim)+' km/h')
            continue
        elif command=='12':
            grad=float(num_input('Gradient','‰',str(-train.max_grad),str(train.max_grad),1,default=str(0)))
            int_lim=float(num_input('Departure Interval','s',str(0),None,3))
            block_len=float(num_input('Block Length','m',str(0),None,3,default=str(0)))
            exit_dist=float(num_input('Exiting Length','m','%.3f'%train.len,None,3,default=str(0)))
            traction_lim=train.find_traction_lim(grad,int_lim,block_len,exit_dist)
            if traction_lim==0:
                print('Insufficient Train Headway')
            else:
                print('Traction Speed Limit: '+str(traction_lim)+' km/h')
            continue
        elif command=='0':
            break
        else:
            print('Invalid command')
            continue
