import os


def validate_port(ctx,param,value)-> bool:
    if value < 1 or value > 65535:
        return False
    # check if port is in use
    if os.system(f'lsof -i:{value}') == 0:
        return False
    return True