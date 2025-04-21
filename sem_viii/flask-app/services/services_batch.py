import re


def get_from_table_rows(header_line, value_line):
    positions = []
    last_pos = 0

    for match in re.finditer(r'\s+', header_line):
        positions.append((last_pos, match.start()))
        last_pos = match.end()
    positions.append((last_pos, len(header_line)))

    headers = [header_line[start:end].strip() for start, end in positions]
    next_start = [start for start, _ in positions[1:]] + [len(value_line)]
    values  = [value_line[start:n_start].strip() for (start, _), n_start in zip(positions, next_start)]

    return {header : value for header, value in zip(headers, values) if header != "" and value != ""}


def parse_info(text_lines):
    if len(text_lines) < 3:
        return {}
    
    header_line = text_lines[0]
    value_line = text_lines[2]
    return get_from_table_rows(header_line, value_line)


def parse_multi_info(multi_text_lines):
    if len(multi_text_lines) < 3:
        return []

    multi_entries = []
    header_line = multi_text_lines[0]

    for line in multi_text_lines[2:]:
        value_line = line
        multi_entries.append(get_from_table_rows(header_line, value_line))

    return multi_entries


def parse_system_report(file_path):
    system_info = {
        "CPU": None,
        "GPU": "Not Detected",
        "Memory": [],
        "Disks": [],
        "OS": None,
        "BIOS": None,
        "Performance": {
            "Date/Time": None,
            "CPU Usage (%)": None,
            "Available Memory (MB)": None,
            "Uptime (seconds)": None,
            "CPU Temperature (°C)": None
        },
        "MemoryStatus": {},
        "VirtualMemory": {}
    }

    with open(file_path, 'r') as file:
        content = file.read()
        sections = re.split(r'={10,}', content)
        sections = [section.strip() for section in sections if section.strip()]
        sections = [section for section in sections if len(section.split('\n')) > 1]

    perf_text = sections[3]

    # Extract each value using regex safely
    date_match = re.search(r'Date/Time:\s*(.*)', perf_text)
    system_info["Performance"]["Date/Time"] = date_match.group(1) if date_match else "Not Found"

    cpu_usage_match = re.search(r'CPU Usage:\s*(.*)', perf_text)
    system_info["Performance"]["CPU Usage (%)"] = cpu_usage_match.group(1) if cpu_usage_match else "Not Found"

    memory_match = re.search(r'Available Memory:\s*(.*)', perf_text)
    system_info["Performance"]["Available Memory (MB)"] = memory_match.group(1) if memory_match else "Not Found"

    uptime_match = re.search(r'System Uptime \(seconds\):\s*(.*)', perf_text)
    system_info["Performance"]["Uptime (seconds)"] = uptime_match.group(1) if uptime_match else "Not Found"

    temp_match = re.search(r'CPU Temperature:\s*(.*)', perf_text)
    system_info["Performance"]["CPU Temperature (°C)"] = temp_match.group(1) if temp_match else "Not Found"

    # CPU
    cpu_section = re.search(r'CPU:\s*\n\n(.*?)(?:\n\n|$)', content, re.DOTALL)
    if cpu_section:
        system_info["CPU"] = parse_info(cpu_section.group(1).splitlines())

    # Memory
    mem_section = re.search(r'Memory:\s*\n\n(.*?)(?:\n\n|$)', content, re.DOTALL)
    if mem_section:
        system_info["Memory"] = parse_multi_info(mem_section.group(1).split('\n'))

    # Disk Drives
    disk_section = re.search(r'Disk Drives:\s*\n\n(.*?)(?:\n\n|$)', content, re.DOTALL)
    if disk_section:
        system_info["Disks"] = parse_multi_info(disk_section.group(1).split('\n'))

    # BIOS
    bios_section = re.search(r'BIOS:\s*\n\n(.*?)(?:\n\n|$)', content, re.DOTALL)
    if bios_section:
        system_info["BIOS"] = parse_info(bios_section.group(1).splitlines())

    # OS
    os_section = re.search(r'\bOS:\s*\n\n(.*?)(?:\n\n|$)', content, re.DOTALL)
    if os_section:
        system_info["OS"] = parse_info(os_section.group(1).splitlines())

    # GPU
    gpu_section = re.search(r'GPU:\s*\n\n(.*?)(?:\n\n|$)', content, re.DOTALL)
    if gpu_section:
        system_info["GPU"] = parse_info(gpu_section.group(1).splitlines())

    # Memory Info
    mem_info_section = re.search(r'Memory Info:\s*\n\n(.*?)(?:\n\n|$)', content, re.DOTALL)
    if mem_info_section:
        system_info["MemoryInfo"] = parse_multi_info(mem_info_section.group(1).split('\n'))

    # System Memory Status
    mem_status_section = re.search(r'System Memory Status:\s*\n(.*?)(?:\n\n|$)', content, re.DOTALL)
    if mem_status_section:
        status_text = mem_status_section.group(1)
        system_info["MemoryStatus"]["Total Physical Memory"] = re.search(r'Total Physical Memory:\s*(.*)', status_text).group(1)
        system_info["MemoryStatus"]["Available Physical Memory"] = re.search(r'Available Physical Memory:\s*(.*)', status_text).group(1)

    # Virtual Memory Details
    virt_mem_section = re.search(r'Virtual Memory Details:\s*\n(.*?)(?:\n\n|$)', content, re.DOTALL)
    if virt_mem_section:
        virt_text = virt_mem_section.group(1)
        system_info["VirtualMemory"]["Max Size"] = re.search(r'Virtual Memory: Max Size:\s*(.*)', virt_text).group(1)
        system_info["VirtualMemory"]["Available"] = re.search(r'Virtual Memory: Available:\s*(.*)', virt_text).group(1)
        system_info["VirtualMemory"]["In Use"] = re.search(r'Virtual Memory: In Use:\s*(.*)', virt_text).group(1)

    print(system_info)
    return system_info


def get_driver_links(system_info):
    driver_links = {
        "CPU Driver": "https://www.intel.com/content/www/us/en/download-center/home.html",  # default Intel link
        "GPU Driver": "https://www.nvidia.com/Download/index.aspx",  # default NVIDIA link
        "BIOS Update": "https://www.amd.com/en/support/chipsets/amd-socket-am4/x570"  # example link, could vary
    }

    # CPU driver link
    cpu_info = system_info['CPU'].get("Name", "").lower()
    if "intel" in cpu_info:
        driver_links["CPU Driver"] = "https://www.intel.com/content/www/us/en/download-center/home.html"
    elif "amd" in cpu_info:
        driver_links["CPU Driver"] = "https://www.amd.com/en/support"
    else:
        driver_links["CPU Driver"] = "https://www.cpuid.com/softwares/cpu-z.html"  # generic

    # GPU driver link
    gpu_info = system_info['GPU'].get("Caption", "").lower()
    if "nvidia" in gpu_info:
        driver_links["GPU Driver"] = "https://www.nvidia.com/Download/index.aspx"
    elif "amd" in gpu_info:
        driver_links["GPU Driver"] = "https://www.amd.com/en/support"
    elif "intel" in gpu_info:
        driver_links["GPU Driver"] = "https://www.intel.com/content/www/us/en/download-center/home.html"
    else:
        driver_links["GPU Driver"] = "https://www.techpowerup.com/download/techpowerup-gpu-z/"  # generic GPU tool

    # BIOS link suggestion based on detected BIOS vendor
    bios_info = system_info["BIOS"].get("Manufacturer", "").lower()
    if "american megatrends" in bios_info:
        driver_links["BIOS Update"] = "https://www.ami.com/en/support/"
    elif "phoenix" in bios_info:
        driver_links["BIOS Update"] = "https://www.phoenix.com/products/"
    elif "dell" in bios_info:
        driver_links["BIOS Update"] = "https://www.dell.com/support/home"
    elif "hp" in bios_info:
        driver_links["BIOS Update"] = "https://support.hp.com/us-en/drivers"
    else:
        driver_links["BIOS Update"] = "https://www.techpowerup.com/download/ami-rufus-bios-update-usb/"  # generic BIOS tool

    # OS Update link
    driver_links["Windows Update"] = "ms-settings:windowsupdate"  # opens Windows Update settings when clicked locally

    return driver_links
