# coding: utf-8

from inputs import *
import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog

def csv_import(csv_path,index_col=0):
    df=pd.read_csv(csv_path,index_col=index_col)
    return df

def create_route():
    print('Please ensure grades, curves and speed limits satisfy operational conditions')
    # Create grades.csv
    grades_data='start,end,grad\n'
    start=num_input('Start','m',digit=3)
    route_start=start
    print('Enter End (m) and Gradient (‰): ')
    while True:
        try:
            grade_data=nums_input(['End','Gradient'],[str(float(start)),None],[None,None],[3,1],[None,None])
            if grade_data=='' and len(grades_data)>15:
                break
            elif grade_data=='':
                print('Grade data cannot be empty')
                continue
        except Exception:
            print('Please ensure')
            print('    - your inputs are 2 valid integers or decimals separated by spaces')
            print('    - Mileposts must be strictly increasing and have at most 3 decimal places')
            print('    - Gradient has at most 1 decimal place')
            print('    - Press Enter on an empty row to finish')
            continue
        end,grad=grade_data
        if end>start:
            grades_data+=','.join([str(float(start)),str(float(end)),str(float(grad))])+'\n'
            start=end
        continue
    route_end=end
    # Create curves.csv
    curves_data='start,end,rad,cant\n'
    print('Enter Start (m), End (m), Radius (m) and Combined Cant (mm): ')
    while True:
        try:
            curve_data=nums_input(['Start','End','Radius','Cant'],[str(float(route_start)),str(float(route_start)),'0','0'],[str(float(route_end)),str(float(route_end)),None,None],[3,3,3,0],[None,None,None,None])
            if curve_data=='':
                break
            start,end,rad,cant=curve_data
            if rad==0 or cant==0:
                raise ValueError
        except Exception:
            print('Please ensure')
            print('    - your inputs are 4 valid integers or decimals separated by spaces')
            print('    - Mileposts must be within range and have at most 3 decimal places')
            print('    - Radius must be positive and has at most 3 decimal places')
            print('    - Cant must be a positive integer')
            print('    - Press Enter on an empty row to finish')
            continue
        if end>start:
            curves_data+=','.join([str(float(start)),str(float(end)),str(float(rad)),str(float(cant))])+'\n'
        elif end<start:
            curves_data+=','.join([str(float(end)),str(float(start)),str(float(rad)),str(float(cant))])+'\n'
        continue
    # Create spd_lims.csv
    spd_lims_data='start,end,spd_lim\n'
    print('Enter Start (m), End (m) and Speed Limit (km/h): ')
    while True:
        try:
            spd_lim_data=nums_input(['Start','End','Speed Limit'],[str(float(route_start)),str(float(route_start)),'0'],[str(float(route_end)),str(float(route_end)),None],[3,3,0],[None,None,None])
            if spd_lim_data=='':
                break
            start,end,spd_lim=spd_lim_data
            if spd_lim==0:
                raise ValueError
        except Exception:
            print('Please ensure')
            print('    - your inputs are 3 valid integers or decimals separated by spaces')
            print('    - Mileposts must be within range and have at most 3 decimal places')
            print('    - Speed Limit must be a positive integer')
            print('    - Press Enter on an empty row to finish')
            continue
        if end>start:
            spd_lims_data+=','.join([str(float(start)),str(float(end)),str(float(spd_lim))])+'\n'
        elif end<start:
            spd_lims_data+=','.join([str(float(end)),str(float(start)),str(float(spd_lim))])+'\n'
        continue
    # Save route data
    root=tk.Tk()
    root.withdraw()
    root.wm_attributes('-topmost',1)
    while True:
        start=input('Enter Origin: ').lstrip(' ').rstrip(' .')
        if start=='':
            start=str(float(route_start))
        end=input('Enter Destination: ').lstrip(' ').rstrip(' .')
        if end=='':
            end=str(float(route_end))
        name=start+' - '+end
        while True:
            save_path=filedialog.askdirectory(title='Select save path',master=root)
            if save_path=='':
                print('Please select a valid path')
                continue
            try:
                routes={route.lower() for route in os.listdir(save_path)}
                break
            except Exception:
                print('Cannot access this folder')
                continue
        if name.lower() in routes:
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
                print('Cannot save route data. Please retry.')
                continue
        elif command=='0':
            print('Please use another route name or save path')
            continue
    try:
        with open(os.path.join(save_path,name,'grades.csv'),'w',encoding='utf-8') as grades_csv:
            grades_csv.write(grades_data)
        with open(os.path.join(save_path,name,'curves.csv'),'w',encoding='utf-8') as curves_csv:
            curves_csv.write(curves_data)
        with open(os.path.join(save_path,name,'spd_lims.csv'),'w',encoding='utf-8') as spd_lims_csv:
            spd_lims_csv.write(spd_lims_data)
        print('Route data saved')
    except Exception:
        print('Cannot save route data')

def reverse_route():
    # Choose a route
    root=tk.Tk()
    root.withdraw()
    root.wm_attributes('-topmost',1)
    while True:
        route_path=filedialog.askdirectory(title='Select a route',master=root).rstrip('/\\')
        if route_path=='':
            root.destroy()
            return
        try:
            grades=csv_import(os.path.join(route_path,'grades.csv'),index_col=None)
            curves=csv_import(os.path.join(route_path,'curves.csv'),index_col=None)
            spd_lims=csv_import(os.path.join(route_path,'spd_lims.csv'),index_col=None)
            grades[['start','end']]=grades[['end','start']]
            grades*=-1
            grades=grades[::-1]
            curves[['start','end']]=curves[['end','start']]
            curves[['start','end']]*=-1
            curves=curves[::-1]
            spd_lims[['start','end']]=spd_lims[['end','start']]
            spd_lims[['start','end']]*=-1
            spd_lims=spd_lims[::-1]
            route_name=os.path.basename(route_path)
            start,end=route_name.split(' - ')
            name=end+' - '+start
            break
        except Exception:
            print('Invalid route data')
            root.destroy()
            return
    # Save reversed route
    while True:
        while True:
            save_path=filedialog.askdirectory(title='Select save path for reversed route',master=root)
            if save_path=='':
                print('Please select a valid path')
                continue
            try:
                routes={route.lower() for route in os.listdir(save_path)}
                break
            except Exception:
                print('Cannot access this folder')
                continue
        if name.lower() in routes:
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
                grades.to_csv(os.path.join(save_path,name,'grades.csv'),index=False)
                curves.to_csv(os.path.join(save_path,name,'curves.csv'),index=False)
                spd_lims.to_csv(os.path.join(save_path,name,'spd_lims.csv'),index=False)
                print('Reversed route data saved')
                root.destroy()
                break
            except Exception:
                print('Cannot save reversed route data. Please retry.')
                continue
        elif command=='0':
            print('Please use another save path')
            continue
