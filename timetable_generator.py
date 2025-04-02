from typing import Dict, List, Optional
import random

class Subject:
    def __init__(self, name: str, total_hours: int, has_lab: bool):
        self.name = name
        self.total_hours = total_hours * 60  # Convert to minutes
        self.has_lab = has_lab
        self.scheduled = 0
        self.lab_scheduled = False  # Track if lab is scheduled for the week

class Class:
    def __init__(self, name: str, subjects: list[dict], days: list[str], periods_per_day: int):
        self.name = name
        self.days = days
        self.periods_per_day = periods_per_day
        self.subjects = {s['name']: Subject(**s) for s in subjects}
        self.timetable = {day: [None] * self.periods_per_day for day in self.days}
        self.daily_labs = {day: 0 for day in days}  # Track labs per day

class Staff:
    def __init__(self, name: str, subjects_taught: list[str], days: list[str], periods_per_day: int, 
                 max_hours_per_day: int):
        self.name = name
        self.subjects_taught = subjects_taught
        self.days = days
        self.periods_per_day = periods_per_day
        self.schedule = {day: [None] * self.periods_per_day for day in self.days}
        self.max_hours_per_day = max_hours_per_day * 60  # Convert to minutes
        self.daily_hours = {day: 0 for day in days}

class Department:
    def __init__(self, config: dict):
        self.days = config['days']
        self.periods_per_day = config['periods_per_day']
        self.period_durations = config['period_durations']
        self.break_periods = config['break_periods']
        self.lunch_period = config['lunch_period']
        self.classes = [Class(cls_name, config['subjects'][cls_name], self.days, self.periods_per_day) 
                       for cls_name in config['classes']]
        self.staff = {s['name']: Staff(s['name'], s['subjects_taught'], self.days, self.periods_per_day,
                                     s['max_hours_per_day']) 
                     for s in config['staff']}
        self.special_hours = config['special_hours']

class TimetableGenerator:
    def __init__(self, department: Department):
        self.department = department

    def is_valid_previous_period(self, cls: Class, day: str, period: int, subject_name: str) -> bool:
        if period == 0:
            return True
        prev_slot = cls.timetable[day][period - 1]
        return prev_slot is None or prev_slot['subject'] != subject_name

    def find_lab_slot(self, day: str, cls: Class) -> Optional[int]:
        if cls.daily_labs[day] >= 1:  # Max 1 lab per day
            return None
        for start in range(self.department.periods_per_day - 1):
            if (all(cls.timetable[day][start + i] is None for i in range(2)) and
                start not in self.department.break_periods and
                start != self.department.lunch_period and
                self.is_valid_previous_period(cls, day, start, cls.subjects[list(cls.subjects.keys())[0]].name)):
                return start
        return None

    def allocate_lab(self, cls: Class, subject: Subject) -> bool:
        if not subject.has_lab or subject.lab_scheduled:
            return False
        for day in self.department.days:
            start = self.find_lab_slot(day, cls)
            if start is not None:
                for p in range(start, start + 2):  # 1 consecutive hour (2 periods)
                    cls.timetable[day][p] = {
                        'subject': subject.name, 
                        'type': 'lab'
                    }
                subject.scheduled += sum(self.department.period_durations[p] for p in range(start, start + 2))
                subject.lab_scheduled = True
                cls.daily_labs[day] += 1
                return True
        return False

    def allocate_lecture(self, cls: Class, subject: Subject) -> bool:
        slots = [(day, period) for day in self.department.days 
                for period in range(self.department.periods_per_day)
                if period not in self.department.break_periods and period != self.department.lunch_period]
        random.shuffle(slots)
        
        for day, period in slots:
            if (cls.timetable[day][period] is not None or 
                not self.is_valid_previous_period(cls, day, period, subject.name)):
                continue
                
            for staff in self.department.staff.values():
                if (subject.name not in staff.subjects_taught or 
                    staff.schedule[day][period] is not None or
                    staff.daily_hours[day] + self.department.period_durations[period] > staff.max_hours_per_day):
                    continue
                    
                cls.timetable[day][period] = {
                    'subject': subject.name,
                    'type': 'lecture',
                    'staff': staff.name
                }
                staff.schedule[day][period] = cls.name
                staff.daily_hours[day] += self.department.period_durations[period]
                subject.scheduled += self.department.period_durations[period]
                return True
        return False

    def allocate_special_hours(self, cls: Class, special_name: str, hours: int) -> bool:
        minutes_needed = hours * 60
        scheduled = 0
        slots = [(day, period) for day in self.department.days 
                for period in range(self.department.periods_per_day)
                if period not in self.department.break_periods and period != self.department.lunch_period]
        random.shuffle(slots)
        
        for day, period in slots:
            if cls.timetable[day][period] is not None:
                continue
            cls.timetable[day][period] = {
                'subject': special_name,
                'type': 'special'
            }
            scheduled += self.department.period_durations[period]
            if scheduled >= minutes_needed:
                return True
        return scheduled >= minutes_needed

    def generate(self) -> dict:
        # Allocate labs first
        for cls in self.department.classes:
            for subject in cls.subjects.values():
                if subject.has_lab:
                    if not self.allocate_lab(cls, subject):
                        print(f"Warning: Couldn't allocate lab for {subject.name} in {cls.name}")

        # Allocate special hours
        for cls in self.department.classes:
            for special_name, hours in self.department.special_hours.items():
                if not self.allocate_special_hours(cls, special_name, hours):
                    print(f"Warning: Couldn't fully allocate {special_name} for {cls.name}")

        # Allocate lectures
        for cls in self.department.classes:
            for subject in cls.subjects.values():
                while subject.scheduled < subject.total_hours:
                    if not self.allocate_lecture(cls, subject):
                        print(f"Warning: Couldn't fully allocate {subject.name} for {cls.name}")
                        break

        return {cls.name: cls.timetable for cls in self.department.classes}

def get_valid_int(prompt: str, min_val: int = 1) -> int:
    while True:
        try:
            value = int(input(prompt))
            if value < min_val:
                print(f"Error: Please enter a number >= {min_val}")
                continue
            return value
        except ValueError:
            print("Error: Please enter a valid integer")

def get_config() -> dict:
    config = {
        'classes': input("Enter class names (space-separated): ").split(),
        'days': ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        'subjects': {},
        'staff': [],
        'special_hours': {}
    }
    
    config['periods_per_day'] = get_valid_int("Number of hours per day (including breaks and lunch): ")
    num_breaks = get_valid_int("Number of breaks: ")
    config['break_periods'] = [get_valid_int(f"Enter break {i+1} period number (1-based): ") - 1 
                              for i in range(num_breaks)]
    config['lunch_period'] = get_valid_int("Enter lunch period number (1-based): ") - 1
    
    break_duration = get_valid_int("Duration for each break (minutes): ")
    lunch_duration = get_valid_int("Duration for lunch (minutes): ")
    config['period_durations'] = []
    for i in range(config['periods_per_day']):
        if i in config['break_periods']:
            config['period_durations'].append(break_duration)
        elif i == config['lunch_period']:
            config['period_durations'].append(lunch_duration)
        else:
            config['period_durations'].append(get_valid_int(f"Duration for period {i+1} (minutes): "))

    for cls_name in config['classes']:
        num_subjects = get_valid_int(f"Number of subjects for {cls_name}: ")
        cls_subjects = []
        for _ in range(num_subjects):
            cls_subjects.append({
                'name': input("Subject name: "),
                'total_hours': get_valid_int("Total hours required: "),
                'has_lab': input("Has lab? (y/n): ").lower() == 'y'
            })
        config['subjects'][cls_name] = cls_subjects

    num_staff = get_valid_int("Number of staff members: ")
    for _ in range(num_staff):
        name = input("Staff name: ")
        config['staff'].append({
            'name': name,
            'subjects_taught': input("Subjects taught (comma-separated): ").split(','),
            'max_hours_per_day': get_valid_int(f"Max teaching hours per day for {name}: ")
        })

    num_special = get_valid_int("Number of special hours (e.g., library): ")
    for _ in range(num_special):
        name = input("Special hour name: ")
        hours = get_valid_int(f"Number of hours required for {name}: ")
        config['special_hours'][name] = hours

    return config

if __name__ == "__main__":
    config = get_config()
    department = Department(config)
    generator = TimetableGenerator(department)
    timetable = generator.generate()
    
    for cls_name, schedule in timetable.items():
        print(f"\n{cls_name} Timetable:")
        for day, periods in schedule.items():
            print(f"\n{day}:")
            for i, period in enumerate(periods):
                if period:
                    print(f"Period {i+1}: {period['subject']} ({period['type']})" + 
                          (f" - {period['staff']}" if period['type'] == 'lecture' else ""))