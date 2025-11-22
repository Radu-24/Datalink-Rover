import subprocess


def run_netsh(args: list[str]) -> None:
    """
    Run a netsh command as a subprocess.
    Raises RuntimeError on failure.
    """
    completed = subprocess.run(
        ["netsh"] + args,
        capture_output=True,
        text=True,
        shell=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"netsh failed: {' '.join(args)}\n"
            f"stdout: {completed.stdout}\n"
            f"stderr: {completed.stderr}"
        )


def get_network_interfaces() -> list[str]:
    """
    Returns ALL network interface names from Windows.
    Uses: netsh interface show interface
    """
    result = subprocess.run(
        ["netsh", "interface", "show", "interface"],
        capture_output=True,
        text=True,
    )

    interfaces: list[str] = []

    for line in result.stdout.splitlines():
        # Example:
        # Enabled    Connected    Dedicated    Ethernet
        if ("Enabled" in line or "Disabled" in line) and "Interface Name" not in line:
            parts = line.split()
            if len(parts) >= 4:
                name = " ".join(parts[3:])
                interfaces.append(name)

    return interfaces


def get_ethernet_adapter() -> str | None:
    """
    Pick the real Ethernet adapter.
    Prefer the one literally called 'Ethernet', ignore vEthernet / VMware.
    """
    interfaces = get_network_interfaces()

    for nic in interfaces:
        if nic.lower() == "ethernet":
            return nic

    for nic in interfaces:
        lname = nic.lower()
        if (
            "ethernet" in lname
            and "vethernet" not in lname
            and "vmware" not in lname
        ):
            return nic

    return None


def enable_rover_link():
    """
    Set static IP 10.0.0.10/24, gateway 10.0.0.1 and metric 50
    on the detected Ethernet adapter.
    """
    nic = get_ethernet_adapter()
    if nic is None:
        raise RuntimeError(
            "No Ethernet adapter detected.\n"
            "Plug in your Ethernet / Thunderbolt adapter and try again."
        )

    run_netsh([
        "interface", "ipv4", "set", "address",
        f"name={nic}",
        "static", "10.0.0.10", "255.255.255.0", "10.0.0.1"
    ])

    run_netsh([
        "interface", "ipv4", "set", "interface",
        nic,
        "metric=50"
    ])


def disable_rover_link():
    """
    Return Ethernet adapter to normal (DHCP IP/DNS, automatic metric).
    """
    nic = get_ethernet_adapter()
    if nic is None:
        raise RuntimeError(
            "No Ethernet adapter detected.\n"
            "Plug in the Ethernet adapter to restore automatic settings."
        )

    run_netsh([
        "interface", "ipv4", "set", "address",
        f"name={nic}",
        "dhcp"
    ])

    run_netsh([
        "interface", "ipv4", "set", "dns",
        f"name={nic}",
        "dhcp"
    ])

    run_netsh([
        "interface", "ipv4", "set", "interface",
        nic,
        "metric=0"
    ])
