#!/usr/bin/env python3
"""Compare water flow data from myUplink CSV with Domoticz API.

This script compares:
1. Raw myUplink data (from uplink_waterflow.cvs)
2. Domoticz API data (from demo_water_flow_history.py)

Purpose: Identify discrepancies in flow rate calculations.
"""

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from myuplink2mqtt.utils.domoticz_json_util import create_domoticz_client


def read_uplink_csv(csv_file):
    """Read myUplink CSV file and extract flow data."""
    print("\n" + "=" * 80)
    print("READING MYUPLINK CSV DATA")
    print("=" * 80)

    uplink_data = []

    try:
        with open(csv_file, "r") as f:
            reader = csv.reader(f, delimiter=";")
            header = next(reader)
            print(f"Header: {header}")

            for i, row in enumerate(reader, 1):
                if len(row) >= 2:
                    timestamp_str = row[0]
                    try:
                        flow_value = float(row[1])
                    except (ValueError, IndexError):
                        print(f"  ⚠️  Row {i}: Could not parse flow value: {row[1]}")
                        continue

                    uplink_data.append({
                        "timestamp": timestamp_str,
                        "flow": flow_value,
                        "source": "myUplink",
                    })

        print(f"\n✓ Successfully read {len(uplink_data)} data points from myUplink CSV")
        return uplink_data

    except FileNotFoundError:
        print(f"✗ File not found: {csv_file}")
        return []
    except Exception as e:
        print(f"✗ Error reading CSV: {e}")
        return []


def get_domoticz_data(device_id=9185):
    """Fetch water flow data from Domoticz API."""
    print("\n" + "=" * 80)
    print("FETCHING DOMOTICZ DATA")
    print("=" * 80)

    try:
        client = create_domoticz_client(host="10.0.0.2", port=80)
        print(f"✓ Connected to Domoticz at {client.base_url}")

        # Fetch day range
        endpoint = f"/json.htm?type=command&param=graph&sensor=Percentage&idx={device_id}&range=day&method=1"
        response = client._make_request(endpoint)

        if not response or response.get("status") != "OK":
            print(f"✗ Failed to fetch data: {response}")
            return []

        data_points = response.get("result", [])
        print(f"✓ Successfully fetched {len(data_points)} data points from Domoticz")

        domoticz_data = []
        for point in data_points:
            try:
                flow_value = float(point.get("v", 0))
                domoticz_data.append({
                    "datetime": point.get("d"),
                    "flow": flow_value,
                    "source": "Domoticz",
                })
            except (ValueError, TypeError):
                pass

        return domoticz_data

    except Exception as e:
        print(f"✗ Error fetching Domoticz data: {e}")
        return []


def normalize_timestamp(ts_str):
    """Convert timestamp string to comparable format (YYYY-MM-DD HH:MM)."""
    try:
        # Try ISO format first
        if "T" in ts_str:
            if "Z" in ts_str:
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(ts_str)
            # Return in HH:MM format (5-minute interval)
            return dt.strftime("%Y-%m-%d %H:%M")
        else:
            # Try standard format
            dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%Y-%m-%d %H:%M")
    except Exception as e:
        print(f"Could not parse timestamp: {ts_str} - {e}")
        return None


def compare_data(uplink_data, domoticz_data):
    """Compare myUplink and Domoticz data."""
    print("\n" + "=" * 80)
    print("DATA COMPARISON")
    print("=" * 80)

    # Create lookup dictionaries
    uplink_by_time = {}
    for point in uplink_data:
        normalized_time = normalize_timestamp(point["timestamp"])
        if normalized_time:
            if normalized_time not in uplink_by_time:
                uplink_by_time[normalized_time] = []
            uplink_by_time[normalized_time].append(point["flow"])

    domoticz_by_time = {}
    for point in domoticz_data:
        time_key = point["datetime"]  # Already in YYYY-MM-DD HH:MM format
        if time_key not in domoticz_by_time:
            domoticz_by_time[time_key] = []
        domoticz_by_time[time_key].append(point["flow"])

    print(f"\nMyUplink unique time slots: {len(uplink_by_time)}")
    print(f"Domoticz unique time slots: {len(domoticz_by_time)}")

    # Analyze overlaps
    matching_times = set(uplink_by_time.keys()) & set(domoticz_by_time.keys())
    uplink_only = set(uplink_by_time.keys()) - set(domoticz_by_time.keys())
    domoticz_only = set(domoticz_by_time.keys()) - set(uplink_by_time.keys())

    print(f"\n✓ Matching time slots: {len(matching_times)}")
    print(f"⚠️  myUplink only: {len(uplink_only)}")
    print(f"⚠️  Domoticz only: {len(domoticz_only)}")

    # Compare values at matching times
    print("\n" + "-" * 80)
    print("DETAILED COMPARISON AT MATCHING TIME SLOTS")
    print("-" * 80)

    discrepancies = []
    matches = []

    for time_slot in sorted(matching_times):
        uplink_vals = uplink_by_time[time_slot]
        domoticz_vals = domoticz_by_time[time_slot]

        # Average values if multiple readings
        uplink_avg = sum(uplink_vals) / len(uplink_vals) if uplink_vals else 0
        domoticz_avg = sum(domoticz_vals) / len(domoticz_vals) if domoticz_vals else 0

        difference = abs(uplink_avg - domoticz_avg)
        pct_diff = (difference / max(uplink_avg, domoticz_avg, 1)) * 100

        if difference > 0.01:  # More than 0.01 l/min difference
            discrepancies.append({
                "time": time_slot,
                "uplink": uplink_avg,
                "domoticz": domoticz_avg,
                "diff": difference,
                "pct_diff": pct_diff,
            })
        else:
            matches.append({
                "time": time_slot,
                "uplink": uplink_avg,
                "domoticz": domoticz_avg,
            })

    # Show matches first
    if matches:
        print(f"\n✓ {len(matches)} time slots with MATCHING values (within 0.01 l/min):")
        print("\n  Time              myUplink    Domoticz    Diff")
        print("  " + "-" * 50)
        for match in matches[:5]:  # Show first 5
            print(f"  {match['time']}    {match['uplink']:6.2f}      {match['domoticz']:6.2f}      ✓")
        if len(matches) > 5:
            print(f"  ... and {len(matches) - 5} more matching slots")

    # Show discrepancies
    if discrepancies:
        print(f"\n⚠️  {len(discrepancies)} time slots with DISCREPANCIES (> 0.01 l/min):")
        print("\n  Time              myUplink    Domoticz    Diff    %Diff")
        print("  " + "-" * 60)
        for disc in sorted(discrepancies, key=lambda x: x["diff"], reverse=True)[:10]:
            print(
                f"  {disc['time']}    {disc['uplink']:6.2f}      {disc['domoticz']:6.2f}      {disc['diff']:6.2f}   {disc['pct_diff']:6.1f}%"
            )
        if len(discrepancies) > 10:
            print(f"  ... and {len(discrepancies) - 10} more discrepancies")

    return {
        "matching_times": len(matching_times),
        "uplink_only": len(uplink_only),
        "domoticz_only": len(domoticz_only),
        "matches": len(matches),
        "discrepancies": len(discrepancies),
        "discrepancy_list": discrepancies,
    }


def calculate_totals(uplink_data, domoticz_data):
    """Calculate total water flow from both sources."""
    print("\n" + "=" * 80)
    print("TOTAL WATER FLOW CALCULATION")
    print("=" * 80)

    if not uplink_data or not domoticz_data:
        print("✗ Insufficient data for comparison")
        return

    # Calculate totals
    uplink_total = sum(p["flow"] for p in uplink_data)
    domoticz_total = sum(p["flow"] for p in domoticz_data)

    print(f"\nmyUplink total flow:  {uplink_total:10.2f} l/min")
    print(f"Domoticz total flow:  {domoticz_total:10.2f} l/min")
    print(f"Difference:           {abs(uplink_total - domoticz_total):10.2f} l/min")
    print(f"Ratio (Domoticz/myUplink): {domoticz_total / max(uplink_total, 1):.4f}x")

    # Calculate averages
    uplink_avg = uplink_total / len(uplink_data) if uplink_data else 0
    domoticz_avg = domoticz_total / len(domoticz_data) if domoticz_data else 0

    print(f"\nmyUplink average:     {uplink_avg:10.4f} l/min")
    print(f"Domoticz average:     {domoticz_avg:10.4f} l/min")

    # Count non-zero readings
    uplink_active = len([p for p in uplink_data if p["flow"] > 0])
    domoticz_active = len([p for p in domoticz_data if p["flow"] > 0])

    print(f"\nmyUplink active readings: {uplink_active} ({uplink_active/len(uplink_data)*100:.1f}%)")
    print(f"Domoticz active readings: {domoticz_active} ({domoticz_active/len(domoticz_data)*100:.1f}%)")

    # Statistics
    uplink_flows = [p["flow"] for p in uplink_data if p["flow"] > 0]
    domoticz_flows = [p["flow"] for p in domoticz_data if p["flow"] > 0]

    if uplink_flows and domoticz_flows:
        print(f"\nmyUplink when active:")
        print(f"  Min:  {min(uplink_flows):6.2f} l/min")
        print(f"  Max:  {max(uplink_flows):6.2f} l/min")
        print(f"  Avg:  {sum(uplink_flows)/len(uplink_flows):6.2f} l/min")

        print(f"\nDomoticz when active:")
        print(f"  Min:  {min(domoticz_flows):6.2f} l/min")
        print(f"  Max:  {max(domoticz_flows):6.2f} l/min")
        print(f"  Avg:  {sum(domoticz_flows)/len(domoticz_flows):6.2f} l/min")


def main():
    """Main comparison function."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "WATER FLOW DATA COMPARISON ANALYSIS" + " " * 24 + "║")
    print("║" + " " * 15 + "myUplink CSV vs Domoticz API" + " " * 35 + "║")
    print("╚" + "=" * 78 + "╝")

    # Read myUplink data
    csv_file = Path(__file__).parent.parent / "uplink_waterflow.cvs"
    uplink_data = read_uplink_csv(csv_file)

    if not uplink_data:
        print("✗ Failed to read myUplink data")
        return

    # Fetch Domoticz data
    domoticz_data = get_domoticz_data()

    if not domoticz_data:
        print("✗ Failed to fetch Domoticz data")
        return

    # Compare data
    comparison = compare_data(uplink_data, domoticz_data)

    # Calculate totals
    calculate_totals(uplink_data, domoticz_data)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(f"\nmyUplink data points:   {len(uplink_data)}")
    print(f"Domoticz data points:   {len(domoticz_data)}")
    print(f"\nMatching time slots:    {comparison['matching_times']}")
    print(f"  - Values match:       {comparison['matches']}")
    print(f"  - Values differ:      {comparison['discrepancies']}")
    print(f"\nData in myUplink only:  {comparison['uplink_only']}")
    print(f"Data in Domoticz only:  {comparison['domoticz_only']}")

    if comparison['discrepancies'] > 0:
        print(f"\n⚠️  ALERT: Found {comparison['discrepancies']} discrepancies!")
        print("\nThis suggests:")
        print("  1. Different data sources or aggregation methods")
        print("  2. Time zone or timestamp conversion issues")
        print("  3. Data transformation or filtering in myUplink")
        print("  4. Possible calculation error in Domoticz")
    else:
        print("\n✓ All matching time slots have consistent values!")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
