import pandas as pd
import numpy as np

# Constants
GRAVITY_N_PER_KG = 9.81
# PAYLOAD_MASS_KG = 111
PAYLOAD_MASS_KG = 200
PAYLOAD_FORCE_N = PAYLOAD_MASS_KG * GRAVITY_N_PER_KG

FIXED_LENGTH_BETWEEN_RAILS_M = 4
FIXED_LENGTH_BETWEEN_BLOCKS_M = 0.2

FIXED_FORCE_APPLICATION_Z_COORDINATE_M = 0.2

# Load kinematics log
kinematics_log = pd.read_csv('kinematics_log.csv')

# Compute timestep
kinematics_log['dt'] = kinematics_log['time'].diff().fillna(kinematics_log['time'].iloc[0])

# Compute distance travelled per timestep
kinematics_log['dL'] = kinematics_log['vy'].abs() * kinematics_log['dt']

# Compute pad loads at each timestep
kinematics_log['P1'] = (PAYLOAD_FORCE_N/4 ) * (
    1
    + 2 * kinematics_log['y'] / (FIXED_LENGTH_BETWEEN_RAILS_M)
    + 2*kinematics_log['ax'] * FIXED_FORCE_APPLICATION_Z_COORDINATE_M / (GRAVITY_N_PER_KG * FIXED_LENGTH_BETWEEN_RAILS_M)
)

kinematics_log['P2'] = kinematics_log['P1']

kinematics_log['P3'] = (PAYLOAD_FORCE_N /4) * (
    1
    - 2*kinematics_log['y'] / (FIXED_LENGTH_BETWEEN_RAILS_M)
    - 2*kinematics_log['ax'] * FIXED_FORCE_APPLICATION_Z_COORDINATE_M / (GRAVITY_N_PER_KG * FIXED_LENGTH_BETWEEN_RAILS_M)
)

kinematics_log['P4'] = kinematics_log['P3']

# Compute cubic mean load for each pad
L_total = kinematics_log['dL'].sum()

def cubic_mean(P_col, dL_col):
    return np.cbrt((P_col**3 * dL_col).sum() / L_total)

P1_MEAN = cubic_mean(kinematics_log['P1'], kinematics_log['dL'])
P2_MEAN = cubic_mean(kinematics_log['P2'], kinematics_log['dL'])
P3_MEAN = cubic_mean(kinematics_log['P3'], kinematics_log['dL'])
P4_MEAN = cubic_mean(kinematics_log['P4'], kinematics_log['dL'])

# Maximum mean load across all pads
P_AVERAGE_MAX = max(P1_MEAN, P2_MEAN, P3_MEAN, P4_MEAN)

# Basic dynamic load rating (N) - to be filled in
C = 6.37e3  # TODO: fill in from bearing datasheet

# Nominal life (km)
L_NOMINAL_KM = (C / P_AVERAGE_MAX)**3 * 50


WORKDAYS_PER_YEAR = 220
HOURS_PER_DAY = 8
TAKT_TIME_SEC_PER_UNIT = 30
UNITS_PER_HOUR = 3600 / TAKT_TIME_SEC_PER_UNIT
CYCLES_PER_DAY = HOURS_PER_DAY * UNITS_PER_HOUR
TRAVEL_PER_CYCLE_M = 20
TRAVEL_PER_DAY_M = CYCLES_PER_DAY * TRAVEL_PER_CYCLE_M
TRAVEL_PER_YEAR_M = TRAVEL_PER_DAY_M * WORKDAYS_PER_YEAR

YEARS_LIFE = (L_NOMINAL_KM * 1000) / TRAVEL_PER_YEAR_M



print(f"P1_MEAN: {P1_MEAN:.2f} N")
print(f"P2_MEAN: {P2_MEAN:.2f} N")
print(f"P3_MEAN: {P3_MEAN:.2f} N")
print(f"P4_MEAN: {P4_MEAN:.2f} N")
print(f"P_AVERAGE_MAX: {P_AVERAGE_MAX:.2f} N")
print(f"L_NOMINAL_KM: {L_NOMINAL_KM:.2f} km")
print(f"YEARS_LIFE: {YEARS_LIFE:.2f}")
