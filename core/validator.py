import os
import click

def validate_port(ctx,param,value:int) -> int:
    if value < 1 or value > 65535:
        raise click.BadParameter('Port must be between 1 and 65535')
    # check if port is in use
    if os.system(f'lsof -i:{value}') == 0:
        raise click.BadParameter(f'Port {value} is in use')
    return value