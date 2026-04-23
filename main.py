import pygame
import math
import numpy as np
from typing import List, Optional

# Global Mapping
dim = 800
onem = 100  # 100px / 1m
PHYSICS_DT = 16  # fixed 16ms physics step
TRACKING_P = 0.1  # small constant P correction for target tracking

def m2px(m_val): return int(m_val * onem)
def px2m(px_val): return px_val / onem

class KinematicsLogger:
    def __init__(self):
        self.data = {
            "time": [],
            "x": [], "y": [], "z": [],
            "vx": [], "vy": [], "vz": [],
            "ax": [], "ay": [], "az": [],
            "jx": [], "jy": [], "jz": []  # Added Jerk arrays
        }
        self.total_time = 0.0

    def log(self, pos: np.ndarray, dt_ms: int):
        dt = dt_ms / 1000.0
        if dt <= 0: return

        # Current Position
        cur_x, cur_y = pos[0, 0], pos[1, 0]
        cur_z = 0.0

        vx, vy, vz = 0.0, 0.0, 0.0
        # in KinematicsLogger, add tracking_error list
        # in main loop, before physics step:
        if self.data["time"]:
            vx = (cur_x - self.data["x"][-1]) / dt
            vy = (cur_y - self.data["y"][-1]) / dt
            vz = (cur_z - self.data["z"][-1]) / dt

        # Calculate Acceleration (a = dv / dt)
        ax, ay, az = 0.0, 0.0, 0.0
        if len(self.data["vx"]) > 0:
            ax = (vx - self.data["vx"][-1]) / dt
            ay = (vy - self.data["vy"][-1]) / dt
            az = (vz - self.data["vz"][-1]) / dt

        # Calculate Jerk (Derivative of Acceleration)
        jx, jy, jz = 0.0, 0.0, 0.0
        if len(self.data["ax"]) > 0:
            jx = (ax - self.data["ax"][-1]) / dt
            jy = (ay - self.data["ay"][-1]) / dt
            jz = (az - self.data["az"][-1]) / dt

        self.total_time += dt
        self.data["time"].append(self.total_time)
        self.data["x"].append(cur_x); self.data["y"].append(cur_y); self.data["z"].append(cur_z)
        self.data["vx"].append(vx); self.data["vy"].append(vy); self.data["vz"].append(vz)
        self.data["ax"].append(ax); self.data["ay"].append(ay); self.data["az"].append(az)
        self.data["jx"].append(jx); self.data["jy"].append(jy); self.data["jz"].append(jz)

    def save_to_csv(self, filename="kinematics_log.csv"):
        import pandas as pd
        df = pd.DataFrame(self.data)
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")

    def plot_data(self):
        import matplotlib.pyplot as plt
        # 4 Subplots to include Jerk
        fig, axs = plt.subplots(4, 1, figsize=(10, 10), sharex=True)
        axs[0].plot(self.data["time"], self.data["x"], label="X Position")
        axs[1].plot(self.data["time"], self.data["vx"], label="X Velocity", color='orange')
        axs[2].plot(self.data["time"], self.data["ax"], label="X Acceleration", color='red')
        axs[3].plot(self.data["time"], self.data["jx"], label="X Jerk", color='purple')
        
        for ax in axs: 
            ax.legend()
            ax.grid(True)
            
        plt.xlabel("Time (s)")
        plt.tight_layout()
        plt.show()


class Obj:
    """Base class for anything with a physical position in the 2D world."""
    def __init__(self, pos_x: float, pos_y: float, x_len: float, y_len: float):
        # Position stored as a 2x1 Numpy Vector
        self._pos = np.array([[float(pos_x)], [float(pos_y)]])
        self.size_real = np.array([[float(x_len)], [float(y_len)]])
        self.children: List['PhysicsObject'] = []
        self.status = "NONE"

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, new_pos):
        self._pos = new_pos
        for child in self.children:
            child.pos = new_pos.copy()

    @property
    def x(self): return self._pos[0, 0]

    @property
    def y(self): return self._pos[1, 0]

    def is_close(self, other: 'Obj', threshold=0.1) -> bool:
        """Euclidean distance check between two Obj instances."""
        self.pos 
        other.pos
        if np.linalg.norm(self.pos - other.pos) < threshold:
            return True
        return False

    def contains(self, other_pos: np.ndarray) -> bool:
        """Checks if a 2x1 position vector is within this object's rectangular bounds."""
        half_size = self.size_real / 2
        low = self.pos - half_size
        high = self.pos + half_size
        if np.all((other_pos >= low) & (other_pos <= high)):
            return True
        return False


class Structure(Obj):
    OUTLINE_THICKNESS = 0.025
    def __init__(self, x_len, y_len, pos_x, pos_y):
        super().__init__(pos_x, pos_y, x_len, y_len)

    def draw(self, screen):
        color = (180, 180, 180)
        t = m2px(self.OUTLINE_THICKNESS)
        w, h = m2px(self.size_real[0, 0]), m2px(self.size_real[1, 0])
        x = m2px(self.x) - w // 2
        y = m2px(self.y) - h // 2
        pygame.draw.rect(screen, color, (x, y, w, h), t)

class PhysicsObject(Obj):
    def __init__(self, x_len, y_len, mass, pos_x=0.0, pos_y=0.0, name="Item", rotate=True):
        if rotate:
            super().__init__(pos_x, pos_y, y_len, x_len)
        else:
            super().__init__(pos_x, pos_y, x_len, y_len)
        self.mass = mass
        self.name = name

    def draw(self, screen):

        for child in self.children:
            child.draw(screen)

        w, h = m2px(self.size_real[0, 0]), m2px(self.size_real[1, 0])
        x, y = m2px(self.x) - w // 2, m2px(self.y) - h // 2
        pygame.draw.rect(screen, (60, 60, 80), (x, y, w, h))

        label = pygame.font.SysFont(None, 16).render(self.name, True, (200, 200, 200))
        screen.blit(label, (x + 2, y + h // 2 - 8))

        second_label = pygame.font.SysFont(None, 16).render(self.status, True, (200, 200, 200))
        screen.blit(second_label, (x + 2, y + h // 2 + 4))

        screen.blit(second_label, (x+2, y + h//2+4))

class MotionProfile:
    def __init__(self, max_v: float, max_a: float):
        self.max_v = max_v
        self.max_a = max_a
        self.stretch_factor = 3  # TUNE THIS: Higher = wider, more gradual S-curve

    def get_approach_velocity(self, pos: np.ndarray, target: np.ndarray) -> np.ndarray:
        error = target - pos
        dist = np.linalg.norm(error)
        
        if dist < 1e-4:
            return np.zeros((2, 1))

        direction = error / dist

        # Stretch the braking zone to give the S-curve more room to breathe
        stopping_dist = ((self.max_v ** 2) / (2 * self.max_a)) * self.stretch_factor

        if dist >= stopping_dist:
            approach_speed = self.max_v
        else:
            t = dist / stopping_dist
            
            # UPGRADE: 5th-Order "Smootherstep" 
            # Guarantees zero Jerk at the start and end of the braking curve
            eased_t = t * t * t * (t * (t * 6.0 - 15.0) + 10.0)
            
            approach_speed = self.max_v * eased_t

        return direction * approach_speed

class EndEffector(Obj):
    def __init__(self, pos_x, pos_y, bound_structure: Structure):
        super().__init__(pos_x, pos_y, 0.1, 0.1)
        self.struct = bound_structure
        self.held_objects: List[PhysicsObject] = []
        
        # Kinematic State for S-Curve
        self.vel = np.array([[0.0], [0.0]])
        self.accel = np.array([[0.0], [0.0]]) # NEW: Track actual acceleration

        self.max_v = 0.5   # m/s  
        self.max_a = 3.0   # m/s² 
        self.max_j = 30.0  # m/s³ (Ideal limit for belt drives)

        self.profile = MotionProfile(self.max_v, self.max_a)

    def update(self, dt: int, target_vec: np.ndarray, ff_vel: Optional[np.ndarray] = None):
        dt_s = dt / 1000.0
        if dt_s <= 0: return

        self.profile.max_v = self.max_v
        self.profile.max_a = self.max_a

        half_limit = self.struct.size_real / 2
        clamped_target = np.clip(target_vec,
                                self.struct.pos - half_limit,
                                self.struct.pos + half_limit)

        v_approach = self.profile.get_approach_velocity(self.pos, clamped_target)
        v_correction = TRACKING_P * (clamped_target - self.pos)
        
        # Ensure we actually use feedforward if it exists!
        v_ff = ff_vel if ff_vel is not None else np.zeros((2, 1))

        # Superposition of all 3 velocities
        desired_vel = v_approach + v_correction + v_ff

        vel_mag = np.linalg.norm(desired_vel)
        absolute_max = self.max_v * 1.5
        if vel_mag > absolute_max:
            desired_vel = (desired_vel / vel_mag) * absolute_max

        # Find ideal acceleration
        desired_accel = (desired_vel - self.vel) / dt_s
        acc_mag = np.linalg.norm(desired_accel)
        if acc_mag > self.max_a:
            desired_accel = (desired_accel / acc_mag) * self.max_a

        # THE SHOCK ABSORBER: Limit Jerk to prevent spikes when targets teleport
        jerk = (desired_accel - self.accel) / dt_s
        jerk_mag = np.linalg.norm(jerk)
        if jerk_mag > self.max_j:
            jerk = (jerk / jerk_mag) * self.max_j

        # Integrate safely
        self.accel += jerk * dt_s
        self.vel += self.accel * dt_s
        self.pos = self.pos + self.vel * dt_s

        # Sync held objects
        for obj in self.held_objects:
            obj.pos = self.pos.copy()

    # ... keep pick/place/draw methods the same ...

    def pick(self, obj: PhysicsObject, line: 'Line'):
        if obj in line.objects:
            line.objects.remove(obj)
            self.held_objects.append(obj)

    def place_inside(self, item: PhysicsObject, container: PhysicsObject):
        if item in self.held_objects:
            self.held_objects.remove(item)
            container.children.append(item)

    def place(self, obj: PhysicsObject, receiver: Optional['Line'] = None):
        if obj in self.held_objects:
            self.held_objects.remove(obj)
            if receiver:
                receiver.add(obj, obj.x)
            else:
                # If no receiver, the object stays exactly where it was placed
                # We return it so the main loop can track it if needed
                return obj
            return None



    def draw(self, screen):
        for obj in self.held_objects: obj.draw(screen)
        pygame.draw.circle(screen, (100, 0, 0), (m2px(self.x), m2px(self.y)), 5)

class Line:
    def __init__(self, pos_y, height, speed=0.30):
        self.pos_y = pos_y
        self.height = height
        self.speed = speed
        self.objects: List[PhysicsObject] = []

    def add(self, obj: PhysicsObject, start_x):
        obj.pos = np.array([[float(start_x)], [float(self.pos_y)]])
        self.objects.append(obj)

    def update(self, dt):
        dt_s = dt / 1000.0
        for obj in self.objects:
            new_pos = obj.pos.copy()
            new_pos[0, 0] += self.speed * dt_s
            obj.pos = new_pos
        self.objects = [o for o in self.objects if o.x < px2m(dim + 100) and o.x > -5.0]



        self.objects = [o for o in self.objects if o.x < px2m(dim + 100) and o.x > -5.0]
    def draw(self, screen):
        py = m2px(self.pos_y)
        ph = m2px(self.height)
        pygame.draw.rect(screen, (40, 120, 40), (0, py - ph // 2, dim, ph))
        for obj in self.objects: obj.draw(screen)


class HUD:
    PARAMS   = ["max_v", "max_a"]
    STEPS    = {"max_v": 0.05, "max_a": 0.25}
    DEFAULTS = {"max_v": 0.5,  "max_a": 3.0}

    def __init__(self, ee: 'EndEffector'):
        self.ee = ee
        self.selected = 0
        self.font = pygame.font.SysFont("Courier New", 16)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self.selected = (self.selected + 1) % len(self.PARAMS)
            param = self.PARAMS[self.selected]
            step = self.STEPS[param]
            if event.key == pygame.K_UP:
                setattr(self.ee, param, round(getattr(self.ee, param) + step, 3))
            elif event.key == pygame.K_DOWN:
                val = round(getattr(self.ee, param) - step, 3)
                setattr(self.ee, param, max(0.0, val))
            elif event.key == pygame.K_r:
                for k, v in self.DEFAULTS.items():
                    setattr(self.ee, k, v)

    def draw(self, screen):
        x, y = 10, 50
        for i, param in enumerate(self.PARAMS):
            val = getattr(self.ee, param)
            selected = (i == self.selected)
            color = (255, 220, 50) if selected else (180, 180, 180)
            prefix = "► " if selected else "  "
            surf = self.font.render(f"{prefix}{param}: {val:.3f}", True, color)
            screen.blit(surf, (x, y + i * 20))
        hint = self.font.render("TAB=select  ↑↓=adjust  R=reset", True, (100, 100, 100))
        screen.blit(hint, (x, y + len(self.PARAMS) * 20 + 8))


def main():
    pygame.init()
    screen = pygame.display.set_mode((dim, dim))
    clock = pygame.time.Clock()


    gantry       = Structure(4.0, 4.0, 4.0, 4.0)
    # CHANGE 1: Moved tape machine to the right (X was 4.0, now 6.0)
    tape_machine = Structure(1.0, 1.0, 4.5, 4.0) 
    pallet       = Structure(1, 1, 5, 2.7)

    ee  = EndEffector(4.0, 4.0, gantry)
    hud = HUD(ee)

    line_speed = 0.03

    item_gap_m = 0.7  
    set_gap_m  = 1.0  
    spawn_x = 1.5
    
    spawn_state = "SPAWN_MW"
    spawn_timer = 0
    
    
    line = Line(pos_y=4.0, height=1.0, speed=line_speed)

    state    = "IDLE"
    running  = True
    home_pos = np.array([[2.5], [4.0]])

    palletized  = []
    current_mw: Optional[PhysicsObject] = None
    current_tc: Optional[PhysicsObject] = None
    current_pkg: Optional[PhysicsObject] = None   
    pallet_pkg:  Optional[PhysicsObject] = None      

    logger     = KinematicsLogger()
    time_scale = 5.0
    accumulated_time = 0.0

    USE_TC = True

    conveyor_vel = np.array([[line.speed], [0.0]])

    # CHANGE 2: Dwell Timer Variables
    PICK_DWELL_MS  = 4000   # time to descend, grip, ascend
    PLACE_DWELL_MS = 3000   # time to descend, release, ascend
    dwell_timer = 0.0
    dwell_target = 0.0
    dwelling = False

    while running:
        real_dt = clock.tick(60)
        sim_dt  = time_scale * real_dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                logger.save_to_csv()
                logger.plot_data()
            hud.handle_event(event)

        # --- SPAWNER ---
        spawn_timer += sim_dt
        item_spawn_delay = (item_gap_m / line.speed) * 1000
        set_spawn_delay  = (set_gap_m / line.speed) * 1000

        spawn_timer += sim_dt
        if spawn_state == "SPAWN_MW":
            line.add(PhysicsObject(0.67, 0.58, 40, name="MW"), spawn_x)  # <-- Changed here
            spawn_state = "WAIT_FOR_BOX"
            spawn_timer = 0

        elif spawn_state == "WAIT_FOR_BOX":
            if spawn_timer >= item_spawn_delay:
                line.add(PhysicsObject(0.67, 0.58, 1, name="Box"), spawn_x)  # <-- Changed here
                spawn_state = "WAIT_FOR_TC" if USE_TC else "WAIT_FOR_NEXT_SET"
                spawn_timer = 0

        elif spawn_state == "WAIT_FOR_TC":
            if spawn_timer >= item_spawn_delay:
                line.add(PhysicsObject(0.67, 0.58, 1, name="TC"), spawn_x)   # <-- Changed here
                spawn_state = "WAIT_FOR_NEXT_SET"
                spawn_timer = 0

        elif spawn_state == "WAIT_FOR_NEXT_SET":
            if spawn_timer >= set_spawn_delay:
                spawn_state = "SPAWN_MW"
                spawn_timer = 0

        # --- STATE MACHINE (WITH DWELL LOGIC) ---
        
        # Update box statuses
        all_boxes_tracked = [o for o in line.objects if o.name == "Box"]
        for b in all_boxes_tracked:
            required_count = 2 if USE_TC else 0
            if len(b.children) >= required_count and b.status == "NONE":
                b.status = "PACKED"
            # If it's packed and hits the tape machine, it's ready
            if b.status == "PACKED" and tape_machine.contains(b.pos):
                b.status = "TAPING"

            if b.status == "TAPING" and not tape_machine.contains(b.pos):
                b.status = "READY"

            print(len(b.children))



        
        # For MW2PKG
        empty_boxes = [b for b in all_boxes if len(b.children) == 0]
        mws_on_belt = [o for o in line.objects if o.name == "MW" and gantry.contains(o.pos) and o.status == "NONE"]



        # For TC2PKG
        tcs_on_belt = [o for o in line.objects if o.name == "TC" and gantry.contains(o.pos) and o.status == "NONE"]
        boxes_needing_tc = [b for b in all_boxes_tracked if len(b.children) == 1]
        ready_to_palletize = [b for b in all_boxes_tracked if b.status in ("TAPING", "READY") and gantry.contains(b.pos)]
        empty_boxes = [b for b in all_boxes_tracked if len(b.children) == 0 and gantry.contains(b.pos)]


        # For palletize
        ready_to_palletize = [b for b in all_boxes if b.status == "READY" and gantry.contains(b.pos)]

        # --- 2. THE STATE MACHINE ---
        if state == "IDLE":
            # Reset dwelling flag just in case
            dwelling = False 
            
            # HIGHEST PRIORITY: Clear the line of finished goods
            if ready_to_palletize:
                pallet_pkg = ready_to_palletize[0]  
                state = "PALLET_PICK"
            
            elif USE_TC and boxes_needing_tc and tcs_on_belt:
                current_pkg = boxes_needing_tc[0]
                current_tc  = tcs_on_belt[0]   
                state = "TC2PKG_PICK"
            
            # THIRD PRIORITY: Start new boxes
            elif mws_on_belt:
                current_mw = mws_on_belt[0]  
                state = "MW2PKG_PICK"

        # PALLET_PICK
        elif state == "PALLET_PICK":
            if not pallet_pkg or pallet_pkg.status not in ("TAPING", "READY"):
                state = "IDLE"
            else:
                if pallet_pkg.status == "READY" and ee.is_close(pallet_pkg):
                    if not dwelling:
                        dwelling = True
                        dwell_timer = 0.0
                        dwell_target = PICK_DWELL_MS
                    else:
                        dwell_timer += sim_dt
                        if dwell_timer >= dwell_target:
                            dwelling = False
                            ee.pick(pallet_pkg, line)
                            state = "PALLET_PLACE"

        # PALLET_PLACE
        elif state == "PALLET_PLACE":
            if ee.is_close(pallet) and pallet_pkg is not None:
                if not dwelling:
                    dwelling = True
                    dwell_timer = 0.0
                    dwell_target = PLACE_DWELL_MS
                else:
                    dwell_timer += sim_dt
                    if dwell_timer >= dwell_target:
                        dwelling = False
                        obj = ee.place(pallet_pkg)
                        if obj: palletized.append(obj)
                        pallet_pkg = None
                        state = "IDLE"

        # MW2PKG_PICK
        elif state == "MW2PKG_PICK":
            current_mw = mws_on_belt[0]
            target = current_mw.pos
            if ee.is_close(current_mw):
                if not dwelling:
                    dwelling = True
                    dwell_timer = 0.0
                    dwell_target = PICK_DWELL_MS
                else:
                    dwell_timer += sim_dt
                    if dwell_timer >= dwell_target:
                        dwelling = False
                        ee.pick(current_mw, line)
                        state = "MW2PKG_PLACE"

        # MW2PKG_PLACE
        elif state == "MW2PKG_PLACE":
            # 1. Drop the box target if it somehow got filled already
            if current_pkg is not None and len(current_pkg.children) > 0:
                current_pkg = None

            # 2. Acquire a new empty box if we don't have one
            if current_pkg is None and empty_boxes:
                current_pkg = empty_boxes[0]

            # 3. Move to target or wait
            if current_pkg is None:
                # No empty boxes available yet, wait at home
                pass 
            else:
                current_pkg = empty_boxes[0]
                target = current_pkg.pos
                if ee.is_close(current_pkg):
                    if not dwelling:
                        dwelling = True
                        dwell_timer = 0.0
                        dwell_target = PLACE_DWELL_MS
                    else:
                        dwell_timer += sim_dt
                        if dwell_timer >= dwell_target:
                            dwelling = False
                            ee.place_inside(current_mw, current_pkg)
                            current_pkg = None  # FIX: Clear memory for next cycle!
                            state = "IDLE"

        # TC2PKG_PICK
        elif state == "TC2PKG_PICK":
            if current_tc is None or current_tc not in line.objects:
                state = "IDLE"
            else:
                current_tc = tcs_on_belt[0]
                target = current_tc.pos
                if ee.is_close(current_tc):
                    if not dwelling:
                        dwelling = True
                        dwell_timer = 0.0
                        dwell_target = PICK_DWELL_MS
                    else:
                        dwell_timer += sim_dt
                        if dwell_timer >= dwell_target:
                            dwelling = False
                            ee.pick(current_tc, line)
                            state = "TC2PKG_PLACE"

        # TC2PKG_PLACE
        elif state == "TC2PKG_PLACE":
            # We must target the specific box identified in IDLE
            target = current_pkg.pos
            if ee.is_close(current_pkg):
                if not dwelling:
                    dwelling = True
                    dwell_timer = 0.0
                    dwell_target = PLACE_DWELL_MS
                else:
                    dwell_timer += sim_dt
                    if dwell_timer >= dwell_target:
                        dwelling = False
                        ee.place_inside(current_tc, current_pkg)
                        current_pkg = None  # FIX: Clear memory for next cycle!
                        state = "IDLE"

        # --- PHYSICS (fixed timestep sub-stepping) ---
        accumulated_time += sim_dt  # Add frame time to the bank
        
        # Only run physics if we have a FULL 16ms chunk in the bank
        while accumulated_time >= PHYSICS_DT:
            
            # Map dynamic targets for FeedForward & Tracking
            active_target_pos = home_pos
            ff_vel = np.zeros((2, 1))
            
            if state == "PALLET_PICK" and pallet_pkg:
                active_target_pos = pallet_pkg.pos
                ff_vel = conveyor_vel
            elif state == "PALLET_PLACE":
                active_target_pos = pallet.pos
            elif state == "MW2PKG_PICK" and current_mw:
                active_target_pos = current_mw.pos
                ff_vel = conveyor_vel
            elif state == "MW2PKG_PLACE" and current_pkg:
                active_target_pos = current_pkg.pos
                ff_vel = conveyor_vel
            elif state == "TC2PKG_PICK" and current_tc:
                active_target_pos = current_tc.pos
                ff_vel = conveyor_vel
            elif state == "TC2PKG_PLACE" and current_pkg:
                active_target_pos = current_pkg.pos
                ff_vel = conveyor_vel

            ee.update(PHYSICS_DT, active_target_pos, ff_vel=ff_vel)
            line.update(PHYSICS_DT)
            logger.log(ee.pos, PHYSICS_DT)
            
            accumulated_time -= PHYSICS_DT # Deduct the 16ms we just used

        # --- RENDERING ---
        screen.fill((50, 20, 70))
        line.draw(screen)
        gantry.draw(screen)
        tape_machine.draw(screen)
        ee.draw(screen)
        pallet.draw(screen)
        hud.draw(screen)

        for obj in palletized:
            obj.draw(screen)

        # Draw states
        img = pygame.font.SysFont('Arial', 24).render(f"STATE: {state}", True, (255, 255, 255))
        screen.blit(img, (20, 20))
        

        ts_img = pygame.font.SysFont('Arial', 18).render(f"Time Scale: {time_scale}x", True, (200, 200, 200))
        screen.blit(ts_img, (dim - 150, 20))
        
        pygame.display.flip()

        logger.log(ee.pos, sim_dt)

if __name__ == "__main__":
    main()
