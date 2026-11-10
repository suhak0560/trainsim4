# coding: utf-8

from fractions import Fraction
import re

def BigFrac(exp:str):
    fracs=exp.split('/')
    bf=Fraction(fracs[0])
    for frac in fracs[1:]:
        bf/=Fraction(frac)
    return bf

def val_input(name,min:str=None,min_equal=True,max:str=None,max_equal=True,default:str=None):
    min=BigFrac(min) if min!=None else None
    max=BigFrac(max) if max!=None else None
    while True:
        print('Enter '+name+': \033[s',end='')
        val=input()
        if default!=None and val=='':
            print('\033[u'+default)
            return BigFrac(default)
        try:
            if re.match(r'^[-0-9./]+$',val)==None:
                raise ValueError
            val=BigFrac(val)
            if min!=None:
                if val<min:
                    raise ValueError
                elif min_equal==False and val==min:
                    raise ValueError
            if max!=None:
                if val>max:
                    raise ValueError
                elif max_equal==False and val==max:
                    raise ValueError
            return val
        except Exception:
            print('Please ensure your input')
            print('    - is a valid integer, decimal or fraction')
            if min!=None:
                if min_equal==False:
                    print('    - greater than '+str(min))
                else:
                    print('    - greater than or equal to '+str(min))
            if max!=None:
                if max_equal==False:
                    print('    - smaller than '+str(max))
                else:
                    print('    - smaller than or equal to '+str(max))
            if default!=None:
                print('    - '+default+' by default')
            continue

def vals_input(names,mins,mins_equal,maxs,maxs_equal,defaults):
    mins=[BigFrac(min) if min!=None else None for min in mins]
    maxs=[BigFrac(max) if max!=None else None for max in maxs]
    print('\033[s',end='')
    vals=input()
    if defaults!=None and vals.strip()=='':
        print('\033[u'+' '.join(defaults))
        return [BigFrac(default) for default in defaults]
    vals=vals.split()
    if len(vals)!=len(names):
        raise ValueError
    for i in range(len(vals)):
        if re.match(r'^[-0-9./]+$',vals[i])==None:
            raise ValueError
        vals[i]=BigFrac(vals[i])
        if mins[i]!=None:
            if vals[i]<mins[i]:
                raise ValueError
            elif mins_equal[i]==False and vals[i]==mins[i]:
                raise ValueError
        if maxs[i]!=None:
            if vals[i]>maxs[i]:
                raise ValueError
            elif maxs_equal[i]==False and vals[i]==maxs[i]:
                raise ValueError
    return vals

def num_input(name,unit=None,min:str=None,max:str=None,digit:int=None,mult:str=None,default:str=None):
    prompts=[]
    if unit!=None:
        prompts.append(unit)
    if min!=None and max!=None:
        prompts.append(min+'~'+max)
    elif min!=None:
        prompts.append('≥'+min)
    elif max!=None:
        prompts.append('≤'+max)
    min=Fraction(min) if min!=None else None
    max=Fraction(max) if max!=None else None
    mult=Fraction(mult) if mult!=None else None
    while True:
        if len(prompts)==0:
            print('Enter '+name+': \033[s',end='')
        else:
            print('Enter '+name+' ('+', '.join(prompts)+'): \033[s',end='')
        num=input()
        if default!=None and num=='':
            print('\033[u'+default)
            return Fraction(default)
        try:
            if re.match(r'^[-0-9.]+$',num)==None:
                raise ValueError
            if digit!=None and '.' in num and len(num)>num.index('.')+digit+1:
                raise ValueError
            num=Fraction(num)
            if min!=None and num<min:
                raise ValueError
            if max!=None and num>max:
                raise ValueError
            if mult!=None and num%mult!=0:
                raise ValueError
            return num
        except Exception:
            print('Please ensure your input')
            if digit==0:
                print('    - is a valid integer')
            else:
                print('    - is a valid integer or decimal')
            if min!=None or max!=None:
                print('    - within given range')
            if digit==1:
                print('    - has at most '+str(digit)+' decimal place')
            elif digit:
                print('    - has at most '+str(digit)+' decimal places')
            if mult!=None:
                print('    - is a multiple of '+str(float(mult)))
            if default!=None:
                print('    - '+default+' by default')
            continue

def nums_input(names,mins,maxs,digits,mults):
    mins=[Fraction(min) if min!=None else None for min in mins]
    maxs=[Fraction(max) if max!=None else None for max in maxs]
    mults=[Fraction(mult) if mult!=None else None for mult in mults]
    nums=input()
    if nums.strip()=='':
        return ''
    nums=nums.split()
    if len(nums)!=len(names):
        raise ValueError
    for i in range(len(nums)):
        if re.match(r'^[-0-9.]+$',nums[i])==None:
            raise ValueError
        if digits[i]!=None and '.' in nums[i] and len(nums[i])>nums[i].index('.')+digits[i]+1:
            raise ValueError
        nums[i]=Fraction(nums[i])
        if mins[i]!=None and nums[i]<mins[i]:
            raise ValueError
        if maxs[i]!=None and nums[i]>maxs[i]:
            raise ValueError
        if mults[i]!=None and nums[i]%mults[i]!=0:
            raise ValueError
    return nums
