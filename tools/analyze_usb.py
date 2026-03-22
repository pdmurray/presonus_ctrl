#!/usr/bin/env python3
"""
Presonus IO24 USB Traffic Analyzer

Auto-detection mode: automatically identifies command IDs, channel bytes, and value bytes
from USB traffic variations.

Usage:
    python analyze_usb.py <capture_file.pcap>
    python analyze_usb.py <capture_file.pcap> --save-hexdir DIR
"""

import sys
import os
import argparse
from collections import defaultdict
from pathlib import Path

# Import scapy - handle different versions
try:
    from scapy.all import rdpcap
    try:
        from scapy.layers.usb import USBpcap as USB
    except ImportError:
        from scapy.layers.usb import USB
except ImportError as e:
    print(f"ERROR: scapy import failed: {e}")
    print("Install with: pip install scapy")
    sys.exit(1)


class IO24Analyzer:
    """Analyzer for Presonus IO24 USB traffic."""
    
    VENDOR_ID = 0x194f
    PRODUCT_ID = 0x0422
    INTERFACE_VENDOR_SPECIFIC = 0xff
    INTERFACE_APPLICATION = 0x0e

    def __init__(self, pcap_file: str):
        self.pcap_file = pcap_file
        self.packets = []

    def load_capture(self):
        print(f"Loading: {self.pcap_file}")
        self.packets = rdpcap(self.pcap_file)
        print(f"Loaded {len(self.packets)} packets")

    def get_vendor_packets(self):
        """Filter for vendor-specific or application interface traffic."""
        vendor = []
        for pkt in self.packets:
            # Try USB layer first
            if hasattr(pkt, 'layers'):
                try:
                    usb_layer = pkt.getlayer(USB)
                    if usb_layer:
                        intf_class = getattr(usb_layer, 'bInterfaceClass', None)
                        if intf_class in [self.INTERFACE_VENDOR_SPECIFIC, 
                                        self.INTERFACE_APPLICATION]:
                            vendor.append(pkt)
                        continue
                except:
                    pass
            
            # Fall back to raw packet inspection
            if pkt.haslayer('Raw'):
                raw_data = bytes(pkt.getlayer('Raw').load)
                if len(raw_data) >= 5:
                    vendor.append(pkt)
        
        print(f"Vendor interface packets: {len(vendor)}")
        return vendor

    def get_payload(self, pkt):
        """Extract payload from USB packet."""
        try:
            # Try USB layer
            usb_layer = pkt.getlayer(USB)
            if usb_layer:
                try:
                    data = bytes(usb_layer.data)
                    return {'data': data, 'hex': data.hex(), 
                            'dir': 'IN' if usb_layer.bmRequestType & 0x80 else 'OUT'}
                except:
                    pass
            
            # Fall back to raw data
            if pkt.haslayer('Raw'):
                data = bytes(pkt.getlayer('Raw').load)
                return {'data': data, 'hex': data.hex(), 'dir': 'RAW'}
                
        except Exception as e:
            pass
        return None

    def analyze_commands(self, vendor_packets):
        """Group packets by command type."""
        cmd_types = defaultdict(list)
        for pkt in vendor_packets:
            payload = self.get_payload(pkt)
            if not payload or len(payload['data']) < 2:
                continue
            data = payload['data']
            
            # Multi-byte or single-byte key
            if len(data) >= 4:
                key = f"{data[0]:02x}:{data[1]:02x}"
            else:
                key = f"{data[0]:02x}"
            
            cmd_types[key].append(payload)
        return cmd_types

    def auto_detect_patterns(self, vendor_packets):
        """Auto-detect protocol structure from packet variations."""
        insights = {
            'command_ids': [],
            'channel_byte_positions': [],
            'value_byte_positions': [],
            'fixed_bytes': [],
            'likely_first_command': None
        }
        
        # Collect all valid payloads
        payloads = []
        for pkt in vendor_packets:
            payload = self.get_payload(pkt)
            if payload and len(payload['data']) >= 2:
                payloads.append(payload['data'])
        
        if len(payloads) < 3:
            return insights
        
        # Analyze each byte position
        byte_analysis = {}
        for pos in range(min(12, max(len(p) for p in payloads))):
            vals = set(p[pos] for p in payloads if len(p) > pos)
            byte_analysis[pos] = vals
        
        # Find command ID (2-10 distinct values in first 4 bytes)
        for pos in range(min(4, len(byte_analysis))):
            vals = byte_analysis[pos]
            if 2 <= len(vals) <= 15:
                insights['command_ids'].append((pos, sorted(vals)))
        
        # Find channel byte (values 1-24 only)
        for pos, vals in byte_analysis.items():
            if vals and all(1 <= v <= 24 for v in vals):
                insights['channel_byte_positions'].append((pos, sorted(vals)))
        
        # Find value bytes (3-50 distinct values, not channel bytes)
        for pos, vals in byte_analysis.items():
            if pos in [cp[0] for cp in insights['channel_byte_positions']]:
                continue
            if 3 <= len(vals) <= 60:
                insights['value_byte_positions'].append((pos, sorted(vals)))
        
        # Find fixed bytes (constant value)
        for pos, vals in byte_analysis.items():
            if len(vals) == 1:
                insights['fixed_bytes'].append((pos, list(vals)[0]))
        
        # Likely default command (first observed)
        if insights['command_ids'] and payloads:
            pos = insights['command_ids'][0][0]
            insights['likely_first_command'] = payloads[0][pos]
        
        return insights

    def print_auto_detection(self, vendor_packets):
        """Print auto-detected protocol structure."""
        print("\n" + "=" * 70)
        print("AUTO-DETECTED PROTOCOL STRUCTURE")
        print("=" * 70)
        
        insights = self.auto_detect_patterns(vendor_packets)
        
        if not insights['command_ids']:
            print("Could not detect command IDs automatically.")
            return
        
        print("\nCommand ID Byte Position:")
        for pos, vals in insights['command_ids'][:2]:
            print(f"   Byte {pos}: {vals}")
        
        if insights['channel_byte_positions']:
            print("\nChannel Identifier Byte:")
            for pos, vals in insights['channel_byte_positions']:
                print(f"   Byte {pos}: values {min(vals)}-{max(vals)} (channel 1-24)")
        
        if insights['value_byte_positions']:
            print("\nParameter Value Byte:")
            for pos, vals in insights['value_byte_positions'][:2]:
                print(f"   Byte {pos}: {len(vals)} distinct values")
                if all(-128 <= v <= 127 for v in vals):
                    min_db = min(vals)
                    max_db = max(vals)
                    print(f"   Raw range: {min_db} to {max_db} (could be signed dB)")
        
        if insights['fixed_bytes']:
            print("\nFixed Bytes (protocol signature):")
            for pos, val in insights['fixed_bytes'][:3]:
                print(f"   Byte {pos}: 0x{val:02x} (constant)")
        
        if insights['likely_first_command']:
            print(f"\nDefault Command ID: 0x{insights['likely_first_command']:02x}")

    def print_analysis(self, vendor_packets, cmd_types):
        """Print command analysis."""
        print("\n" + "=" * 70)
        print("COMMAND BREAKDOWN")
        print("=" * 70)
        
        for cmd, pkts in sorted(cmd_types.items()):
            print(f"\nCommand: {cmd} ({len(pkts)} pkts)")
            first = pkts[0]
            data = first['data']
            print(f"  Direction: {first['dir']}, Length: {len(data)} bytes")
            print(f"  Sample: {data[:12].hex()}")
            
            variations = set(p['data'].hex()[:20] for p in pkts[:5])
            if len(variations) > 1:
                print("  Sample variations:")
                for v in sorted(variations)[:3]:
                    print(f"    {v}")
        
        # Auto-detection
        self.print_auto_detection(vendor_packets)
        
        # Next steps with specific byte positions
        print("\n" + "=" * 70)
        print("PROTOCOL IMPLEMENTATION CHECKLIST")
        print("=" * 70)
        insights = self.auto_detect_patterns(vendor_packets)
        
        if insights['command_ids']:
            print("   [ ] Command ID at byte", insights['command_ids'][0][0])
            print("       Values:", [f"0x{v:02x}" for v in insights['command_ids'][0][1][:4]])
        
        if insights['channel_byte_positions']:
            print("   [ ] Channel ID at byte", insights['channel_byte_positions'][0][0])
        
        if insights['value_byte_positions']:
            print("   [ ] Parameter value at byte", insights['value_byte_positions'][0][0])
        
        if insights['fixed_bytes']:
            print("   [ ] Fixed byte 0x{insights['fixed_bytes'][0][1]:02x} at position", insights['fixed_bytes'][0][0])
        
        print("   [ ] CRC/checksum calculation")
        print("   [ ] Command acknowledgment handling")
        print("\nExample Protocol Structure:")
        print("   [CMD_ID][VER][CH_ID][PARAM][CRC]")
        print("    0x01   0x01  0x01   0x80   0xB5")

    def run_analysis(self, save_hexdir=None):
        """Run full analysis."""
        self.load_capture()
        vendor_packets = self.get_vendor_packets()
        
        if not vendor_packets:
            print("No vendor interface packets found!")
            return
        
        cmd_types = self.analyze_commands(vendor_packets)
        self.print_analysis(vendor_packets, cmd_types)
        
        # Save hex dumps
        if save_hexdir:
            Path(save_hexdir).mkdir(parents=True, exist_ok=True)
            for i, pkt in enumerate(vendor_packets[:50]):
                payload = self.get_payload(pkt)
                if payload:
                    (Path(save_hexdir) / f"packet_{i:04d}.hex").write_text(
                        payload['data'].hex() + '\n')
            print(f"\nSaved hex dumps to {save_hexdir}/")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze Presonus IO24 USB traffic from PCAP file')
    parser.add_argument('capture_file', help='PCAP file to analyze')
    parser.add_argument('--save-hexdir', type=str, help='Save hex dumps to directory')
    parser.add_argument('--no-autodetect', action='store_true', 
                       help='Skip auto-detection mode')
    parser.add_argument('--test', action='store_true', 
                       help='Run with example data')

    args = parser.parse_args()
    
    if args.test:
        example_file = Path(__file__).parent / 'example_capture.pcap'
        print(f"Using example capture: {example_file}")
        args.capture_file = str(example_file)
    
    analyzer = IO24Analyzer(args.capture_file)
    analyzer.run_analysis(args.save_hexdir)


if __name__ == '__main__':
    main()
