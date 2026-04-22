import numpy as np

# TODO: Based on kinematics.csv, calculate this LB equation over time



# ==============================
# INPUT PARAMETERS
# ==============================

# Masses
m1 = 300      # kg (moving mass)
m2 = 50      # kg (payload)

# Gravity
g = 9.81

# Acceleration
a1 = 3.2
a3 = 3.2

# Geometry (mm)
l0 = 500
l1 = 4000
l2 = 500
l3 = 500
l4 = 50
l5 = 100

# Stroke segments (mm)
S1 = 100
S2 = 2800
S3 = 100

ls = S1 + S2 + S3
cycle_length = 2 * ls

# LM Guide ratings
C = 11380       # N (dynamic load rating)
C0 = 16970      # N (static load rating)

# Load factor
fw = 1.5
alpha = 1/fw



# ==============================
# HELPER FUNCTIONS
# ==============================

def cube_mean(values, distances):
    """Calculate cubic mean load."""
    total = sum((p**3) * s for p, s in zip(values, distances))
    return (total / cycle_length) ** (1/3)


def positive(x):
    """THK groove rule"""
    return max(x, 0)


# ==============================
# STEP 1 — RADIAL LOAD (uniform motion)
# ==============================

P1 = (m1*g)/4 - (m1*g*l2)/(2*l0) + (m1*g*l5)/(2*l1) + (m2*g)/4
P2 = (m1*g)/4 + (m1*g*l2)/(2*l0) + (m1*g*l5)/(2*l1) + (m2*g)/4
P3 = (m1*g)/4 + (m1*g*l2)/(2*l0) - (m1*g*l5)/(2*l1) + (m2*g)/4
P4 = (m1*g)/4 - (m1*g*l2)/(2*l0) - (m1*g*l5)/(2*l1) + (m2*g)/4

print("Uniform radial loads:")
print(P1, P2, P3, P4)


# ==============================
# STEP 2 — ACCELERATION TERMS
# ==============================

radial_acc = (m1*a1*l5)/(2*l0) + (m2*a1*l4)/(2*l0)
lateral_acc = (m1*a1*l3)/(2*l0)


# ==============================
# STEP 3 — LEFTWARD ACCELERATION
# ==============================

Pla = [
    P1 - radial_acc,
    P2 + radial_acc,
    P3 + radial_acc,
    P4 - radial_acc
]

Ptla = [
    -lateral_acc,
    lateral_acc,
    lateral_acc,
    -lateral_acc
]


# ==============================
# STEP 4 — LEFTWARD DECELERATION
# ==============================

Pld = [
    P1 + radial_acc,
    P2 - radial_acc,
    P3 - radial_acc,
    P4 + radial_acc
]

Ptld = [
    lateral_acc,
    -lateral_acc,
    -lateral_acc,
    lateral_acc
]


# ==============================
# STEP 5 — RIGHTWARD ACCELERATION
# ==============================

Pra = [
    P1 + radial_acc,
    P2 - radial_acc,
    P3 - radial_acc,
    P4 + radial_acc
]

Ptra = [
    lateral_acc,
    -lateral_acc,
    -lateral_acc,
    lateral_acc
]


# ==============================
# STEP 6 — RIGHTWARD DECELERATION
# ==============================

Prd = [
    P1 - radial_acc,
    P2 + radial_acc,
    P3 + radial_acc,
    P4 - radial_acc
]

Ptrd = [
    -lateral_acc,
    lateral_acc,
    lateral_acc,
    -lateral_acc
]


# ==============================
# STEP 7 — COMBINED LOADS
# ==============================

def combined(P, Pt):
    return [positive(p) + positive(pt) for p, pt in zip(P, Pt)]

Pe_la = combined(Pla, Ptla)
Pe_ld = combined(Pld, Ptld)
Pe_ra = combined(Pra, Ptra)
Pe_rd = combined(Prd, Ptrd)

Pe_uniform = [positive(P1), positive(P2), positive(P3), positive(P4)]


# ==============================
# STEP 8 — AVERAGE LOADS
# ==============================

Pm = []

for i in range(4):

    loads = [
        Pe_la[i], Pe_uniform[i], Pe_ld[i],
        Pe_ra[i], Pe_uniform[i], Pe_rd[i]
    ]

    distances = [S1, S2, S3, S1, S2, S3]

    Pm.append(cube_mean(loads, distances))


print("\nAverage loads Pm:")
for i, p in enumerate(Pm):
    print(f"Block {i+1}: {p:.2f} N")


# ==============================
# STEP 9 — NOMINAL LIFE
# ==============================

L10 = []

for p in Pm:
    life = alpha * 50 * (C/p)**3
    L10.append(life)

print("\nNominal life (km):")
for i, life in enumerate(L10):
    print(f"Block {i+1}: {life:.0f} km")


# ==============================
# STEP 10 — SYSTEM LIFE
# ==============================

system_life = min(L10)
critical_block = np.argmin(L10) + 1

print("\nSystem Life:")
print(f"Critical block: {critical_block}")
print(f"Life: {system_life:.0f} km")
