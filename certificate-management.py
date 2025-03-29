import os
import hvac
import subprocess
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from colorama import Fore, Style, init
import atexit


VAULT_ADDR = 'http://127.0.0.1:8200'
with open('vault_token.txt', 'r') as f:
    VAULT_TOKEN = f.read().strip()
MOUNT_POINT = 'certs'

client = hvac.Client(url=VAULT_ADDR)
client.token = VAULT_TOKEN

# Verify the token is valid
if not client.is_authenticated():
    raise EnvironmentError("Invalid Vault Token")

BACKUP_DIR = 'cert_backups'
os.makedirs(BACKUP_DIR, exist_ok=True)

def generate_certs(n):
    for i in range(n):
        cert_name = f'fake_cert_{i + 1}'
        subprocess.run([
            'openssl', 'req', '-x509', '-nodes', '-newkey', 'rsa:2048',
            '-keyout', f'{cert_name}.key', '-out', f'{cert_name}.crt', '-days', '365',
            '-subj', f'/CN={cert_name}/O=FakeOrg'
        ])
        print(f'{Fore.GREEN}Generated: {cert_name}{Style.RESET_ALL}')


def verify_certs():
    certs = [f for f in os.listdir() if f.endswith('.crt')]
    for cert_file in certs:
        with open(cert_file, 'rb') as f:
            cert_data = f.read()
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            print(f'{Fore.CYAN}Certificate: {cert_file}{Style.RESET_ALL}')
            print(f'  {Fore.YELLOW}Subject: {cert.subject}{Style.RESET_ALL}')
            print(f'  {Fore.YELLOW}Issuer: {cert.issuer}{Style.RESET_ALL}')
            print(f'  {Fore.YELLOW}Expiry: {cert.not_valid_after}{Style.RESET_ALL}')
            print(f'  {Fore.YELLOW}Serial Number: {cert.serial_number}{Style.RESET_ALL}')
            print('-' * 40)

def backup_and_rotate():
    certs = [f for f in os.listdir() if f.endswith(".crt")]
    
    if not certs:
        print(f"{Fore.RED}❌ No certificates found for backup and rotation!{Style.RESET_ALL}")
        return

    for cert_file in certs:
        key_file = cert_file.replace(".crt", ".key")

        # Ensure both key and cert exist
        if not os.path.exists(key_file):
            print(f"{Fore.YELLOW}⚠️ Skipping {cert_file} - Missing private key!{Style.RESET_ALL}")
            continue

        # Read cert and key
        with open(cert_file, "r") as c, open(key_file, "r") as k:
            cert = c.read()
            key = k.read()

        # Backup old cert and key The paths are same 
        backup_cert_path = os.path.join(BACKUP_DIR, cert_file)
        backup_key_path = os.path.join(BACKUP_DIR, key_file)

        with open(backup_cert_path, "w") as bc, open(backup_key_path, "w") as bk:
            bc.write(cert)
            bk.write(key)

        print(f"{Fore.GREEN}✅ Backed up: {backup_cert_path} and {backup_key_path}{Style.RESET_ALL}")

        # Generate new cert and key
        new_cert_name = cert_file.replace(".crt", "_new")
        subprocess.run([
            'openssl', 'req', '-x509', '-nodes', '-newkey', 'rsa:2048',
            '-keyout', f'{new_cert_name}.key', '-out', f'{new_cert_name}.crt', '-days', '365',
            '-subj', f'/CN={new_cert_name}/O=FakeOrg'
        ])

        # Read new cert and key
        with open(f'{new_cert_name}.crt', "r") as nc, open(f'{new_cert_name}.key', "r") as nk:
            new_cert = nc.read()
            new_key = nk.read()

        # Store new cert & key in Vault (removing .crt from secret name)
        secret_name = cert_file.replace(".crt", "")
        try:
            client.secrets.kv.v2.create_or_update_secret(
                path=secret_name,  # Correctly structured path
                mount_point=MOUNT_POINT,
                secret={"key": new_key, "cert": new_cert}
            )
            print(f"{Fore.BLUE}🔄 Rotated in Vault: {secret_name}{Style.RESET_ALL}")

        except hvac.exceptions.InvalidPath as e:
            print(f"{Fore.RED}❌ Vault Error: {e}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Unexpected Error: {e}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ Backup and rotation complete!{Style.RESET_ALL}")

def cleanup():
    certs = [f for f in os.listdir() if f.endswith('.crt') or f.endswith('.key')]
    for cert_file in certs:
        os.remove(cert_file)
        print(f"{Fore.RED}🗑️ Deleted: {cert_file}{Style.RESET_ALL}")

    if os.path.exists(BACKUP_DIR):
        for backup_file in os.listdir(BACKUP_DIR):
            os.remove(os.path.join(BACKUP_DIR, backup_file))
            print(f"{Fore.RED}🗑️ Deleted backup: {backup_file}{Style.RESET_ALL}")
        os.rmdir(BACKUP_DIR)
        print(f"{Fore.RED}🗑️ Deleted backup directory: {BACKUP_DIR}{Style.RESET_ALL}")

    if os.path.exists('vault.log'):
        os.remove('vault.log')
        print(f"{Fore.RED}🗑️ Deleted: vault.log{Style.RESET_ALL}")

def main():
    for i in range(100):
        print("Choose an option:\n1. Generate N Fake Certs\n2. Verify Certs\n3. Backup and Rotate Certs\n4. Exit")
        choice = input("Enter your choice: ")
        if choice == '1':
            n = int(input("Number of certs to generate: "))
            generate_certs(n)
        elif choice == '2':
            verify_certs()
        elif choice == '3':
            backup_and_rotate()
        else:
            print("Exiting...")
            break


main()
atexit.register(cleanup)
