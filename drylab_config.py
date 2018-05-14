'''

'''
## CSS file to be used for creating the PDF files
CSS_FOR_PDF = '/css/print_services.css'

## template files for generating the PDF files
REQUESTED_CONFIRMATION_SERVICE = 'request_service_template'
RESOLUTION_TEMPLATE = 'resolution_template.html'
OUTPUT_DIR_TEMPLATE ='documents/drylab/' # Directory to store the templates before moving to service folder

## SAMBA settings for connect to bioinfodoc server to create the folder request services
SAMBA_USER_ID = 'lchapado'
SAMBA_USER_PASSWORD = 'chapadomaster'
SAMBA_SHARED_FOLDER_NAME = 'bioinfo_doc'
SAMBA_REMOTE_SERVER_NAME = 'panoramix'
SAMBA_NTLM_USED = True
SAMBA_DOMAIN = 'panoramix'
SAMBA_IP_SERVER = '172.23.2.11'
SAMBA_PORT_SERVER = '445'

SAMBA_SERVICE_FOLDER = 'services'
## Folders to be created when service is accepted
FOLDERS_FOR_SERVICES = ['request', 'resolution', 'result'] # 0= request, 1= resolution, 2 = result (keep order as suggested)
#RESOLUTION_PREFIX = 'Resolution_'


