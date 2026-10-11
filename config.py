WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FPS = 60

BG_COLOR = (24, 28, 36)
ROAD_COLOR = (45, 52, 65)
ROAD_MARKING_COLOR = (220, 220, 220)
ROAD_BORDER_COLOR = (80, 90, 110)
SIDEWALK_COLOR = (34, 40, 50)
GRASS_COLOR = (28, 36, 43)

RED_COLOR = (239, 68, 68)
YELLOW_COLOR = (245, 158, 11)
GREEN_COLOR = (16, 185, 129)
LIGHT_HOUSING_COLOR = (15, 23, 42)
LIGHT_OFF_COLOR = (55, 65, 81)

PANEL_BG = (17, 24, 39, 230)
PANEL_BORDER = (59, 130, 246)
TEXT_WHITE = (243, 244, 246)
TEXT_MUTED = (156, 163, 175)
TEXT_ACCENT = (96, 165, 250)
TEXT_SUCCESS = (52, 211, 153)
TEXT_WARNING = (251, 191, 36)
BUTTON_BG = (37, 99, 235)
BUTTON_HOVER = (29, 78, 216)
BUTTON_ACTIVE = (16, 185, 129)

ROAD_WIDTH = 160           
LANE_WIDTH = 40            
CENTER_X = 460             
CENTER_Y = WINDOW_HEIGHT // 2

VEHICLE_TYPES = {
    'car': {
        'length': 34,
        'width': 18,
        'max_speed': 3.5,
        'accel': 0.08,
        'decel': 0.15,
        'colors': [
            (59, 130, 246),   
            (239, 68, 68),    
            (234, 179, 8),    
            (168, 85, 247),   
            (243, 244, 246),  
            (14, 165, 233),   
        ]
    },
    'bus': {
        'length': 58,
        'width': 22,
        'max_speed': 2.4,
        'accel': 0.04,
        'decel': 0.12,
        'colors': [
            (245, 158, 11),  
            (16, 185, 129),   
        ]
    },
    'bike': {
        'length': 20,
        'width': 10,
        'max_speed': 4.0,
        'accel': 0.12,
        'decel': 0.20,
        'colors': [
            (236, 72, 153),  
            (34, 197, 94),  
        ]
    }
}

SAFE_DISTANCE = 14         
STOP_LINE_OFFSET = ROAD_WIDTH // 2 + 10 

FIXED_GREEN_TIME = 8.0
FIXED_YELLOW_TIME = 2.5
ALL_RED_CLEARANCE = 1.0

MIN_SMART_GREEN = 4.0
MAX_SMART_GREEN = 16.0
SMART_QUEUE_WEIGHT = 1.2
SMART_WAIT_WEIGHT = 0.5
