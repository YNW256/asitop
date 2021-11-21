
import time
import glob
import argparse
from collections import deque
from dashing import VSplit, Text
from .utils import *


parser = argparse.ArgumentParser(
    description='asitop: Performance monitoring CLI tool for Apple Silicon')
parser.add_argument('--interval', type=int, default=1,
                    help='Display interval and sampling interval for powermetrics (seconds)')
parser.add_argument('--color', type=int, default=7,
                    help='Choose display color (0~8)')
parser.add_argument('--avg', type=int, default=30,
                    help='Interval for averaged values (seconds)')
args = parser.parse_args()


def main():
    print("\n[1/3] Loading ASITOP\n")

    textt =Text(text="NULL",color=args.color,)

    print("\n[2/3] Starting powermetrics process\n")

    timecode = str(int(time.time()))
    powermetrics_process = run_powermetrics_process(timecode,
                                                    interval=args.interval*1000)

    print("\n[3/3] Waiting for first reading...\n")

    def get_reading(wait=0.1):
        ready = parse_powermetrics(timecode=timecode)
        while not ready:
            time.sleep(wait)
            ready = parse_powermetrics(timecode=timecode)
        return ready

    ready = get_reading()
    last_timestamp = ready[-1]

    clear_console()

    try:
        while True:
            ready = parse_powermetrics(timecode=timecode)
            if ready:
                cpu_metrics_dict, gpu_metrics_dict, thermal_pressure, bandwidth_metrics, timestamp = ready

                if timestamp > last_timestamp:
                    last_timestamp = timestamp

                    if thermal_pressure == "Nominal":
                        thermal_throttle = "no"
                    else:
                        thermal_throttle = "yes"


                    #内存相关
                    ram_metrics_dict = get_ram_metrics_dict()
                    ecpu_read_GB = bandwidth_metrics["ECPU DCS RD"]
                    ecpu_write_GB = bandwidth_metrics["ECPU DCS WR"]
                    total_bw_GB = bandwidth_metrics["DCS RD"] + bandwidth_metrics["DCS WR"]
                    
                    #功耗相关
                    package_power_W = cpu_metrics_dict["package_W"]
                    cpu_power_W = cpu_metrics_dict["cpu_W"]
                    gpu_power_W = cpu_metrics_dict["gpu_W"]

                    net_workr = get_networkr()
                    net_works = get_networks()


                    #主输出部分
                    textt.text = "".join([
                        "E-CPU: ",
                        str(cpu_metrics_dict["E-Cluster_active"]),
                        "% @ ",
                        str(cpu_metrics_dict["E-Cluster_freq_Mhz"]),
                        " MHz",
                        "\nP-CPU: ",
                        str(cpu_metrics_dict["P-Cluster_active"]),
                        "% @ ",
                        str(cpu_metrics_dict["P-Cluster_freq_Mhz"]),
                        " MHz",
                        "\nGPU: ",
                        str(gpu_metrics_dict["active"]),
                        "% @ ",
                        str(gpu_metrics_dict["freq_MHz"]),
                        " MHz",

                        "\n\nRAM Usage: ",
                        str(ram_metrics_dict["used_GB"]),
                        "/",
                        str(ram_metrics_dict["total_GB"]),
                        "GB",
                        "\nswap: ",
                        str(ram_metrics_dict["swap_used_GB"]),
                        "/",
                        str(ram_metrics_dict["swap_total_GB"]),
                        "GB",
                        "\nBandwidth: ",
                        '{0:.2f}'.format(total_bw_GB),
                        " GB/s \n(R:",
                        '{0:.2f}'.format(bandwidth_metrics["DCS RD"]),
                        " GB/s W:",
                        '{0:.2f}'.format(bandwidth_metrics["DCS WR"]),
                        " GB/s)",

                        "\n\nPackage Power: ",
                        '{0:.2f}'.format(package_power_W),
                        " W",
                        "\nCPU: ",
                        '{0:.2f}'.format(cpu_power_W),
                        " W",
                        "\nGPU: ",
                        '{0:.2f}'.format(gpu_power_W),
                        " W\n",

                        "\nUpload speed: ",str(net_workr),
                        "\nDownload speed: ",str(net_works),


                    ])

                    textt.display()

            time.sleep(args.interval)

    except KeyboardInterrupt:
        pass

    return powermetrics_process


if __name__ == "__main__":
    powermetrics_process = main()
    for tmpf in glob.glob("/tmp/asitop_powermetrics*"):
        os.remove(tmpf)
    powermetrics_process.terminate()
    print("Successfully terminated powermetrics process")
