from subprocess import *
from requests import *
from colorama import Fore, Style
import asyncio

def loader():
    print(Style.BRIGHT + Fore.RED + "+---------------------------------------------------------------------------------------------+" + Style.RESET_ALL)
    print(Fore.RED + "|                                                                                             |")
    print("|     ██████╗ ███╗   ██╗███████╗    ██████╗ ██████╗ ██╗██╗   ██╗ █████╗ ████████╗███████╗     |")
    print("|     ██╔══██╗████╗  ██║██╔════╝    ██╔══██╗██╔══██╗██║██║   ██║██╔══██╗╚══██╔══╝██╔════╝     |")
    print("|     ██║  ██║██╔██╗ ██║███████╗    ██████╔╝██████╔╝██║██║   ██║███████║   ██║   █████╗       |")
    print("|     ██║  ██║██║╚██╗██║╚════██║    ██╔═══╝ ██╔══██╗██║╚██╗ ██╔╝██╔══██║   ██║   ██╔══╝       |")
    print("|     ██████╔╝██║ ╚████║███████║    ██║     ██║  ██║██║ ╚████╔╝ ██║  ██║   ██║   ███████╗     |")
    print("|     ╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚═╝  ╚═╝   ╚═╝   ╚══════╝     |")
    print("|                                                                                             |")
    print("|"+ Style.BRIGHT + Fore.BLUE +" TelegramID : @iliyadev  " + Fore.RED + "                                                                    |")
    print(Style.BRIGHT + Fore.RED + "+---------------------------------------------------------------------------------------------+")
    print("|" + Fore.GREEN + f" Server Country: {server_country}" + Fore.RED + "                                                                      |")
    print("|" + Fore.GREEN + f" Server IP: {server_ip}" + Fore.RED + "                                                                     |")
    print("|" + Fore.GREEN + f" Server ISP: {server_isp}" + Fore.RED + "                                                                         |")
    print("+---------------------------------------------------------------------------------------------+")
    print("|" + Fore.WHITE + " 1- Install" + Fore.RED + "                                                                                  |")
    print("|" + Fore.WHITE + " 2- Status" + Fore.RED + "                                                                                   |")
    print("|" + Fore.WHITE + " 3- Uninstall" + Fore.RED + "                                                                                |")
    print("|" + Fore.WHITE + " 4- Exit" + Fore.RED + "                                                                                     |")
    print(Style.BRIGHT + Fore.RED + "+---------------------------------------------------------------------------------------------+" + Style.RESET_ALL)

def ipv4_address():
        result = run(["hostname", "-I"], capture_output=True, text=True)
        ip_address = result.stdout.split()[0]
        return ip_address

def country(ip):
        url = f"http://ip-api.com/json/{ip}"
        response = get(url)
        data = response.json()
        if data["status"] == "success":
                return data["country"]
        else:
                return "Error : " + data["message"]

def isp(ip):
        url = f"http://ip-api.com/json/{ip}"
        response = get(url)
        data = response.json()
        if data["status"] == "success":
                return data["isp"]
        else:
                return "Error : " + data["message"]

server_ip = ipv4_address()
server_country = country(server_ip)
server_isp = isp(server_ip)

async def execute_command(command):
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    output = stdout.decode().strip()
    error = stderr.decode().strip()

    if error:
        print(f"Error: {error}")
    if output:
        return output

async def setup_dns(domain):
    await execute_command("sudo apt update && sudo apt upgrade -y")
    await execute_command("sudo apt install bind9 bind9utils bind9-doc -y")
    
    config_options = """
        options {
                directory "/var/cache/bind";

                forwarders {
                8.8.8.8;
                8.8.4.4;
                };

                dnssec-validation auto;

                listen-on-v6 { any; };
        };
    """
    with open("/etc/bind/named.conf.options", "w") as config_file:
        config_file.write(config_options)

    zone_config = f"""
        zone "{domain}" {{
                type master;
                file "/etc/bind/db.{domain}";
        }};
    """
    with open("/etc/bind/named.conf.local", "a") as zone_file:
        zone_file.write(zone_config)

    await execute_command(f"sudo cp /etc/bind/db.local /etc/bind/db.{domain}")
    zone_data = f"""
                $TTL    604800
                @       IN      SOA     ns1.{domain}. admin.{domain}. (
                                        2         ; Serial
                                        604800    ; Refresh
                                        86400     ; Retry
                                        2419200   ; Expire
                                        604800 )  ; Negative Cache TTL
                ;
                @       IN      NS      ns1.{domain}.
                ns1     IN      A       192.168.1.1
                www     IN      A       192.168.1.2
        """
    with open(f"/etc/bind/db.{domain}", "w") as db_file:
        db_file.write(zone_data)

    await execute_command("sudo named-checkconf")
    await execute_command(f"sudo named-checkzone {domain} /etc/bind/db.{domain}")
    await execute_command("sudo systemctl restart bind9")

    print("DNS Server Private setup completed! ✅")
    print(await execute_command(f"nslookup google.com {server_ip}"))

def check_dns_status():
    try:
        result = run("sudo systemctl status bind9", shell=True, check=True, text=True, stdout=PIPE, stderr=PIPE)
        stdout = result.stdout.lower()
        
        if "active" in stdout:
            print("ُStatus : Running✅")
        else:
            print("ُStatus : Inactive❌")
    except CalledProcessError as e:
            if "could not be found" in e.stderr.lower():
                print("ُStatus : Inactive❌")
            else:
                print(f"Error : {e}")

async def remove_dns():
    try:
        await execute_command("sudo systemctl disable bind9")
        await execute_command("sudo apt-get remove --purge bind9 -y")
        await execute_command("sudo rm -rf /etc/bind")
        await execute_command("sudo rm -rf /var/cache/bind")
        await execute_command("sudo rm -rf /var/log/bind")
        await execute_command("sudo apt autoremove -y")

        print("DNS Server Private Successfully Removed ✅")
    except CalledProcessError as e:
        return e

async def main():
    while True:
        try:
            loader()
            number = int(input("Please choose an option: "))

            if number == 1:
                domain = input("Please enter domain or sub domain (example.com) or (sub.example.com): ")
                await setup_dns(domain)
                input("Press enter to countinue...")
                pass
            elif number == 2:
                check_dns_status()
                input("Press enter to countinue...")
                pass
            elif number == 3:
                await remove_dns()
                input("Press enter to countinue...")
                pass
            elif number == 4:
                break
            else:
                print("Number is invalid!")
                input("Press enter to countinue...")
                pass
        except Exception as e:
            print(f'Error : {e}')

if __name__ == "__main__":
     asyncio.run(main())