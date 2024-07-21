import os


def validate_port(p:int)-> bool:
    if p < 1 or p > 65535:
        return False
    # check if port is in use
    if os.system(f'lsof -i:{p}') == 0:
        return False
    return True