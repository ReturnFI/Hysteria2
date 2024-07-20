import subprocess

def generate_password() -> str:
    '''
    Generates a random password using pwgen for user.
    Could raise subprocess.CalledProcessError
    '''
    result = subprocess.check_output(['pwgen', '-s', '32', '1'])
    return result.decode().strip()