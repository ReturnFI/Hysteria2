from fastapi import APIRouter, HTTPException, UploadFile, File
from ..schema.config.hysteria import ConfigFile, GetPortResponse, GetSniResponse
from ..schema.response import DetailResponse
from fastapi.responses import FileResponse
import shutil
import zipfile
import tempfile
# from ..schema.config.hysteria import InstallInputBody
import os
import cli_api

router = APIRouter()


# Change: Installing and uninstalling Hysteria2 is possible only through the CLI
# @router.post('/install', response_model=DetailResponse, summary='Install Hysteria2')
# async def install(body: InstallInputBody):
#     """
#     Installs Hysteria2 on the given port and uses the provided or default SNI value.

#     Args:
#         body: An instance of InstallInputBody containing the new port and SNI value.

#     Returns:
#         A DetailResponse with a message indicating the Hysteria2 installation was successful.

#     Raises:
#         HTTPException: if an error occurs while installing Hysteria2.
#     """
#     try:
#         cli_api.install_hysteria2(body.port, body.sni)
#         return DetailResponse(detail=f'Hysteria2 installed successfully on port {body.port} with SNI {body.sni}.')
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


# @router.delete('/uninstall', response_model=DetailResponse, summary='Uninstall Hysteria2')
# async def uninstall():
#     """
#     Uninstalls Hysteria2.

#     Returns:
#         A DetailResponse with a message indicating the Hysteria2 uninstallation was successful.

#     Raises:
#         HTTPException: if an error occurs while uninstalling Hysteria2.
#     """
#     try:
#         cli_api.uninstall_hysteria2()
#         return DetailResponse(detail='Hysteria2 uninstalled successfully.')
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.patch('/update', response_model=DetailResponse, summary='Update Hysteria2')
async def update():
    """
    Updates Hysteria2.

    Returns:
        A DetailResponse with a message indicating the Hysteria2 update was successful.

    Raises:
        HTTPException: if an error occurs while updating Hysteria2.
    """
    try:
        cli_api.update_hysteria2()
        return DetailResponse(detail='Hysteria2 updated successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/get-port', response_model=GetPortResponse, summary='Get Hysteria2 port')
async def get_port_api():
    """
    Retrieves the port for Hysteria2.

    Returns:
        A GetPortResponse containing the Hysteria2 port.

    Raises:
        HTTPException: if an error occurs while getting the Hysteria2 port.
    """
    try:
        if port := cli_api.get_hysteria2_port():
            return GetPortResponse(port=port)
        else:
            raise HTTPException(status_code=404, detail='Hysteria2 port not found.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/set-port/{port}', response_model=DetailResponse, summary='Set Hysteria2 port')
async def set_port_api(port: int):
    """
    Sets the port for Hysteria2.

    Args:
        port: The new port value.

    Returns:
        A DetailResponse with a message indicating the Hysteria2 port change was successful.

    Raises:
        HTTPException: if an error occurs while changing the Hysteria2 port.
    """
    try:
        cli_api.change_hysteria2_port(port)
        return DetailResponse(detail=f'Hysteria2 port changed to {port} successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/get-sni', response_model=GetSniResponse, summary='Get Hysteria2 SNI')
async def get_sni_api():
    '''
    Retrieves the SNI for Hysteria2.

    Returns:
        A GetSniResponse containing the Hysteria2 SNI.

    Raises:
        HTTPException: if an error occurs while getting the Hysteria2 SNI.
    '''
    try:
        if sni := cli_api.get_hysteria2_sni():
            return GetSniResponse(sni=sni)
        else:
            raise HTTPException(status_code=404, detail='Hysteria2 SNI not found.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/set-sni/{sni}', response_model=DetailResponse, summary='Set Hysteria2 SNI')
async def set_sni_api(sni: str):
    """
    Sets the SNI for Hysteria2.

    Args:
        sni: The new SNI value.

    Returns:
        A DetailResponse with a message indicating the Hysteria2 SNI change was successful.

    Raises:
        HTTPException: if an error occurs while changing the Hysteria2 SNI.
    """
    try:
        cli_api.change_hysteria2_sni(sni)
        return DetailResponse(detail=f'Hysteria2 SNI changed to {sni} successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/backup', response_class=FileResponse, summary='Backup Hysteria2 configuration')
async def backup_api():
    """
    Backups the Hysteria2 configuration and sends the backup ZIP file.
    """
    try:
        cli_api.backup_hysteria2()
        backup_dir = "/opt/hysbackup/"  # TODO: get this path from .env

        if not os.path.isdir(backup_dir):
            raise HTTPException(status_code=500, detail="Backup directory does not exist.")

        files = [f for f in os.listdir(backup_dir) if f.endswith('.zip')]
        files.sort(key=lambda x: os.path.getctime(os.path.join(backup_dir, x)), reverse=True)
        latest_backup_file = files[0] if files else None

        if latest_backup_file:
            backup_file_path = os.path.join(backup_dir, latest_backup_file)

            if not backup_file_path.startswith(backup_dir):
                raise HTTPException(status_code=400, detail="Invalid backup file path.")

            if not os.path.exists(backup_file_path):
                raise HTTPException(status_code=404, detail="Backup file not found.")

            return FileResponse(path=backup_file_path, filename=os.path.basename(backup_file_path), media_type="application/zip")
        else:
            raise HTTPException(status_code=500, detail="No backup file found after backup process.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error: {str(e)}')


@router.post('/restore', response_model=DetailResponse, summary='Restore Hysteria2 Configuration')
async def restore_api(file: UploadFile = File(...)):
    try:

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name

        if not zipfile.is_zipfile(temp_path):
            os.unlink(temp_path)
            raise HTTPException(status_code=400, detail="Invalid file type. Must be a ZIP file.")

        required_files = {"ca.key", "ca.crt", "users.json", "config.json", ".configs.env"}
        with zipfile.ZipFile(temp_path, 'r') as zip_ref:
            zip_contents = set(zip_ref.namelist())
            missing_files = required_files - zip_contents
            
            if missing_files:
                os.unlink(temp_path)
                raise HTTPException(
                    status_code=400, 
                    detail=f"Backup file is missing required files: {', '.join(missing_files)}"
                )

        dst_dir_path = '/opt/hysbackup/'  # TODO: get this path from .env
        os.makedirs(dst_dir_path, exist_ok=True)
        
        dst_path = os.path.join(dst_dir_path, file.filename)  # type: ignore
        shutil.move(temp_path, dst_path)
        cli_api.restore_hysteria2(dst_path)
        return DetailResponse(detail='Hysteria2 restored successfully.')

    except HTTPException as e:
        raise e
    except Exception as e:
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f'Error: {str(e)}')


@router.get('/enable-obfs', response_model=DetailResponse, summary='Enable Hysteria2 obfs')
async def enable_obfs():
    """
    Enables Hysteria2 obfs.

    Returns:
        A DetailResponse with a message indicating the Hysteria2 obfs was enabled successfully.

    Raises:
        HTTPException: if an error occurs while enabling Hysteria2 obfs.
    """
    try:
        cli_api.enable_hysteria2_obfs()
        return DetailResponse(detail='Hysteria2 obfs enabled successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/disable-obfs', response_model=DetailResponse, summary='Disable Hysteria2 obfs')
async def disable_obfs():
    """
    Disables Hysteria2 obfs.

    Returns:
        A DetailResponse with a message indicating the Hysteria2 obfs was disabled successfully.

    Raises:
        HTTPException: if an error occurs while disabling Hysteria2 obfs.
    """
    try:
        cli_api.disable_hysteria2_obfs()
        return DetailResponse(detail='Hysteria2 obfs disabled successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/enable-masquerade/{domain}', response_model=DetailResponse, summary='Enable Hysteria2 masquerade')
async def enable_masquerade(domain: str):
    """
    Enables Hysteria2 masquerade for the given domain.

    Args:
        domain: The domain to enable Hysteria2 masquerade for.

    Returns:
        A DetailResponse with a message indicating the Hysteria2 masquerade was enabled successfully.

    Raises:
        HTTPException: if an error occurs while enabling Hysteria2 masquerade.
    """
    try:
        cli_api.enable_hysteria2_masquerade(domain)
        return DetailResponse(detail='Hysteria2 masquerade enabled successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/disable-masquerade', response_model=DetailResponse, summary='Disable Hysteria2 masquerade')
async def disable_masquerade():
    """
    Disables Hysteria2 masquerade.

    Returns:
        A DetailResponse with a message indicating the Hysteria2 masquerade was disabled successfully.

    Raises:
        HTTPException: if an error occurs while disabling Hysteria2 masquerade.
    """
    try:
        cli_api.disable_hysteria2_masquerade()
        return DetailResponse(detail='Hysteria2 masquerade disabled successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/file', response_model=ConfigFile, summary='Get Hysteria2 configuration file')
async def get_file():
    """
    Gets the Hysteria2 configuration file.

    Returns:
        A JSONResponse containing the Hysteria2 configuration file.

    Raises:
        HTTPException: if an error occurs while getting the Hysteria2 configuration file.
    """
    try:
        if config_file := cli_api.get_hysteria2_config_file():
            return ConfigFile(root=config_file)
        else:
            raise HTTPException(status_code=404, detail='Hysteria2 configuration file not found.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.post('/file', response_model=DetailResponse, summary='Update Hysteria2 configuration file')
async def set_file(body: ConfigFile):
    """
    Updates the Hysteria2 configuration file.

    Args:
        file: The Hysteria2 configuration file to update.

    Returns:
        A DetailResponse with a message indicating the Hysteria2 configuration file was updated successfully.

    Raises:
        HTTPException: if an error occurs while updating the Hysteria2 configuration file.
    """
    try:
        cli_api.set_hysteria2_config_file(body.root)
        cli_api.restart_hysteria2()
        return DetailResponse(detail='Hysteria2 configuration file updated successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')
