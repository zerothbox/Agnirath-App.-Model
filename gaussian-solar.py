import math
import csv

# Constants
PEAK_IRRADIANCE_W_M2 = 1073.0
SOLAR_NOON_SECONDS = 12 * 3600
STD_DEV_SECONDS = 11600.0
PANEL_EFFICIENCY = 0.24
SOLAR_AREA_M2 = 6.0


def format_time(seconds: int) -> str:
    """
    Parameters:
        seconds: Seconds from midnight

    Returns:
        The conversion of raw seconds into HH:MM:SS
    """

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds1 = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds1:02d}"


def get_incident_irradiance(time_seconds: int) -> float:
    """
    Parameters:
        time_seconds: Time in seconds

    Returns:
        The sun's irradiance using a Gaussian bell curve.
    """

    numerator = -((time_seconds - SOLAR_NOON_SECONDS) ** 2)
    denominator = 2 * (STD_DEV_SECONDS**2)

    # Gaussian exponent
    exponent = numerator / denominator

    return PEAK_IRRADIANCE_W_M2 * math.exp(exponent)


def get_generated_power(irradiance: float) -> float:
    """
    Parameters:
        irradiance

    Returns:
        The conversion to actual usable power
    """

    return irradiance * SOLAR_AREA_M2 * PANEL_EFFICIENCY


def generate_solar_csv(filename="race_day_solar_data.csv"):
    """
    Parameters:
        filename: Name of the .csv to save to

    Returns:
        Nothing, but saves simulation to CSV
    """

    start_time_sec = 9 * 3600  # 9 AM
    end_time_sec = 17 * 3600  # 5 PM

    total_rows = end_time_sec - start_time_sec + 1

    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow(
            ["Time", "Time_Seconds", "Irradiance_W_m2", "Generated_Power_W"]
        )

        for t_sec in range(start_time_sec, end_time_sec + 1):
            irradiance = get_incident_irradiance(t_sec)
            power = get_generated_power(irradiance)

            time_str = format_time(t_sec)

            writer.writerow([time_str, t_sec, round(irradiance, 4), round(power, 4)])


if __name__ == "__main__":
    generate_solar_csv()
