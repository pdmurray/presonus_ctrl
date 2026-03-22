#!/usr/bin/env python3
"""
Presonus IO24 USB Traffic Capture Helper

This script provides a simple workflow for capturing and analyzing USB traffic.
It's designed for use on Windows where you'll run actions in the Presonus Control app.

Usage on Windows:
    1. Run this script: python capture_and_analyze.py
    2. It will guide you through starting/stopping capture
    3. Automatically saves to capture.pcap
    4. Optionally analyzes if scapy is available

This is a helper that works with Wireshark's command-line tool (tshark).
"""

import subprocess
import sys
import os
import time
import argparse
from pathlib import Path


def check_tshark():
    """Check if tshark (Wireshark CLI) is available."""
    try:
        result = subprocess.run(['tshark', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return True, result.stdout.split('\n')[0]
    except:
        pass
    return False, None


def get_usb_interfaces():
    """List available USB capture interfaces."""
    result = subprocess.run(
        ['tshark', '-L', '-e', 'interface'],
        capture_output=True, text=True, timeout=10
    )
    interfaces = []
    for line in result.stdout.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('Number') or line.startswith('Name'):
            continue
        # tshark -L -e interface gives: Name, Description, Type
        parts = line.split('|')
        if len(parts) >= 2:
            name = parts[0].strip()
            desc = parts[1].strip() if len(parts) > 1 else ''
            if 'USB' in desc or 'USBPcap' in desc or 'Wi-Fi' in desc or 'Ethernet' in desc:
                interfaces.append((name, desc))
    return interfaces


def start_capture(interface, output_file):
    """Start tshark USB capture."""
    print(f"\n📡 Starting capture on interface: {interface}")
    print("   → Now switch to Presonus Control app and perform actions")
    print("   → Watch for USB packets appearing in Wireshark GUI")
    print("   → Press Ctrl+C when done\n")
    
    cmd = [
        'tshark', '-i', interface,
        '-Y', 'usb.capdata',  # Filter for USB data packets
        '-w', output_file,
        '--color', 'never'
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n✅ Capture stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Capture failed: {e}")
        sys.exit(1)
    
    return True


def print_capture_instructions():
    """Print instructions for capturing USB traffic."""
    print("""
📋 CAPTURE INSTRUCTIONS
========================

OPTION 1: Using tshark (command-line, automated)
-------------------------------------------------
1. Find USB interface: tshark -L -e interface
2. Start capture: python capture_and_analyze.py -i USBPcap0 -o capture.pcap
3. In Presonus Control app, do actions while capture is running
4. Press Ctrl+C when done

OPTION 2: Using Wireshark GUI
-----------------------------
1. Open Wireshark
2. Select USBPcap0 or USBPcap1 interface
3. Apply filter: usb.capdata
4. Start capture (blue shark fin)
5. Do actions in Presonus Control app
6. Stop capture (red square), save as capture.pcap

Actions to perform:
-------------------
• Click on channels 1, 10, 24 (to change channel byte)
• Drag fader to min (-60dB), nominal (-6dB), max (0dB)
• Load different presets (to trigger different command IDs)

The analysis tool will automatically detect which bytes change!
""")


def run_analysis(pcap_file):
    """Run the USB analysis tool on capture."""
    if not Path(pcap_file).exists():
        print(f"❌ Capture file not found: {pcap_file}")
        return False
    
    # Try to import scapy
    try:
        from tools.analyze_usb import IO24Analyzer
        analyzer = IO24Analyzer(pcap_file)
        analyzer.load_capture()
        
        vendor = analyzer.get_vendor_packets()
        cmd_types = analyzer.analyze_commands(vendor)
        analyzer.print_analysis(vendor, cmd_types)
        return True
    except ImportError:
        print("⚠️  Scapy not installed for analysis.")
        print("   Install with: pip install scapy")
        print(f"   Or run from project root: python -m tools.analyze_usb {pcap_file}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Presonus IO24 USB Capture Helper'
    )
    parser.add_argument('-i', '--interface', 
                        help='USB interface to capture on (e.g., USBPcap0)')
    parser.add_argument('-o', '--output', default='capture.pcap',
                        help='Output PCAP file name')
    parser.add_argument('-a', '--analyze', action='store_true',
                        help='Automatically analyze capture after saving')
    parser.add_argument('-l', '--list', action='store_true',
                        help='List available interfaces and exit')
    parser.add_argument('-s', '--show-instructions', action='store_true',
                        help='Show capture instructions and exit')
    
    args = parser.parse_args()
    
    # Show instructions
    if args.show_instructions:
        print_capture_instructions()
        return
    
    # List interfaces
    if args.list:
        interfaces = get_usb_interfaces()
        if interfaces:
            print("\nAvailable USB interfaces:")
            print("-" * 50)
            for name, desc in interfaces:
                print(f"  {name} → {desc}")
        else:
            print("\nNo USB interfaces found!")
            print("Make sure Wireshark/USBPcap is installed.")
        return
    
    # Check for tshark
    has_tshark, version = check_tshark()
    if not has_tshark:
        print("❌ tshark (Wireshark CLI) not found.")
        print("   Install Wireshark: https://www.wireshark.org/download.html")
        print("   Then run with: python capture_and_analyze.py -s")
        return
    
    print(f"✅ tshark found: {version}")
    
    # Start capture
    if args.interface:
        start_capture(args.interface, args.output)
        
        if args.analyze:
            print("\n🔬 Running analysis...")
            run_analysis(args.output)
    else:
        # Interactive mode
        interfaces = get_usb_interfaces()
        if interfaces:
            print("\nAvailable USB interfaces:")
            for i, (name, desc) in enumerate(interfaces, 1):
                print(f"  {i}. {name} → {desc}")
            
            try:
                choice = input("\nSelect interface number (or enter name): ").strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(interfaces):
                        interface = interfaces[idx][0]
                    else:
                        print("❌ Invalid selection")
                        return
                else:
                    interface = choice
            except EOFError:
                print("No interface selected")
                return
        else:
            interface = input("Enter USB interface name: ").strip()
        
        if interface:
            start_capture(interface, args.output)
            
            if args.analyze or input("\nAnalyze capture now? (y/n): ").lower() == 'y':
                run_analysis(args.output)


if __name__ == '__main__':
    main()
