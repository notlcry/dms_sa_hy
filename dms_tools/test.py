import argparse

args = "-p 52"



def parseoption(option,flag):
    if option is None:
        return None
    arrays = option.strip().split(" ")
    for index,item in enumerate(arrays):
        if item.strip() == flag:
            for idx in range(index+1,len(arrays)):
                if arrays[idx].strip() != "":
                    return arrays[idx]
    return None


print parseoption(args,"-w")