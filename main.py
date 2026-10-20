import asyncio
from typing import Optional

from pywizlight import wizlight, PilotBuilder, discovery
from pywizlight.exceptions import WizLightError

BULB_IP = "192.168.1.38"  # last known IP; set to None to always discover
BULB_MAC = "d8a011c12251"  # identifies the bulb if the router hands out a new IP
BROADCAST = "192.168.1.255"
CHECK_TIMEOUT = 3


def normalize_mac(mac: Optional[str]) -> str:
    return (mac or "").replace(":", "").replace("-", "").lower()


async def is_our_bulb(ip: str) -> bool:
    """Return True if the device at `ip` answers and has our bulb's MAC."""
    bulb = wizlight(ip)
    try:
        mac = await asyncio.wait_for(bulb.getMac(), CHECK_TIMEOUT)
        return normalize_mac(mac) == normalize_mac(BULB_MAC)
    except (WizLightError, asyncio.TimeoutError, OSError):
        return False
    finally:
        await bulb.async_close()


async def discover_bulb_ip() -> Optional[str]:
    """Broadcast on the network and return the IP of the bulb with BULB_MAC."""
    print("Discovering WiZ bulbs...")
    bulbs = await discovery.discover_lights(broadcast_space=BROADCAST)
    for b in bulbs:
        print(f"Found bulb at {b.ip} (MAC {b.mac})")
    for b in bulbs:
        if normalize_mac(b.mac) == normalize_mac(BULB_MAC):
            return b.ip
    return None


async def find_bulb_ip() -> Optional[str]:
    """Use BULB_IP if it's still our bulb, otherwise rediscover it by MAC."""
    if BULB_IP and await is_our_bulb(BULB_IP):
        return BULB_IP

    if BULB_IP:
        print(f"Bulb not reachable at {BULB_IP}, it may have a new IP.")
    ip = await discover_bulb_ip()
    if ip and ip != BULB_IP:
        print(f"Bulb is now at {ip}. Update BULB_IP in main.py to skip discovery next time.")
    return ip


async def main():
    ip = await find_bulb_ip()
    if ip is None:
        print("Bulb not found. Make sure you're on the same Wi-Fi network as the bulb.")
        return

    bulb = wizlight(ip)
    try:
        print(f"Turning on the WiZ bulb at {ip}...")
        await bulb.turn_on(PilotBuilder(rgb=(255, 0, 0), brightness=100))
        print("Success!")
    finally:
        await bulb.async_close()


if __name__ == "__main__":
    asyncio.run(main())
