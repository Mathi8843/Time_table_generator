from typing import Dict, List, Optional

class Subject:
    """Represents a subject with scheduling requirements"""
    def __init__(self, name: str, total_hours: int, has_lab: bool):
        self.name = name
        self.total_hours = total_hours * 60  # Convert to minutes
        self.has_lab = has_lab
        self.scheduled = 0

class Class:
    """Represents a class with its timetable and subjects"""
    def __init__(self, name: str, subjects: List[Dict], department: 'Department'):
        self.name = name
        self.department = department
        self.subjects = {s['name']: Subject(**s) for s in subjects}  # Unique subjects per class
        self.timetable = {day: [None] * department.periods_per_day for day in department.days}

class Staff:
    """Represents a staff member with their availability"""
    def __init__(self, name: str, subjects: List[str], department: 'Department'):
        self.name = name
        self.department = department
        self.subjects = subjects  # Teacher can teach multiple subjects
        self.schedule = {day: [None] * department.periods_per_day for day in department.days}

class Lab:
    """Represents a lab resource with availability tracking"""
    def __init__(self, name: str, available_periods: Dict[str, List[tuple]], days: List[str]):
        self.name = name
        self.availability = {
            day: [(start, end) for start, end in available_periods.get(day, [])]
            for day in days
        }

class Department:
    """Represents a department with classes, staff, and labs"""
    def __init__(self, config: Dict):
        self.days = config['days']
        self.periods_per_day = config['periods_per_day']
        self.period_durations = config['period_durations']  # Varying durations (e.g., [50, 60, ...])
        self.classes = [Class(cls_name, config['classes_subjects'][cls_name], self) 
                       for cls_name in config['classes']]  # Subjects per class
        self.staff = {s['name']: Staff(s['name'], s['subjects'], department=self) 
                     for s in config['staff']}
        self.labs = {lab['name']: Lab(
            name=lab['name'],
            available_periods=lab['available_periods'],
            days=self.days
        ) for lab in config['labs']}

class TimetableGenerator:
    """Generates timetable while respecting all constraints"""
    def __init__(self, department: Department):
        self.department = department
        
    def _is_lab_available(self, lab: Lab, day: str, period: int) -> bool:
        return any(start <= period < end for start, end in lab.availability[day])

    def allocate_lab(self, cls: Class, subject: Subject) -> bool:
        if not subject.has_lab:
            return False
        lab_duration = 2  # Lab takes 2 consecutive periods
        for day in self.department.days:
            for lab in self.department.labs.values():
                for start in range(self.department.periods_per_day - lab_duration + 1):
                    if all(self._is_lab_available(lab, day, start + i) for i in range(lab_duration)):
                        if all(cls.timetable[day][p] is None for p in range(start, start + lab_duration)):
                            for p in range(start, start + lab_duration):
                                cls.timetable[day][p] = {'subject': subject.name, 'type': 'lab'}
                                lab.availability[day] = [
                                    (s, e) for s, e in lab.availability[day]
                                    if e <= start or s >= start + lab_duration
                                ] + [(start, start + lab_duration)]
                            subject.scheduled += sum(self.department.period_durations[p] 
                                                   for p in range(start, start + lab_duration))
                            return True
        return False

    def allocate_lecture(self, cls: Class, subject: Subject) -> bool:
        for day in self.department.days:
            for period in range(self.department.periods_per_day):
                if cls.timetable[day][period] is None:
                    for staff in self.department.staff.values():
                        if subject.name in staff.subjects and staff.schedule[day][period] is None:
                            cls.timetable[day][period] = {
                                'subject': subject.name,
                                'type': 'lecture',
                                'staff': staff.name
                            }
                            staff.schedule[day][period] = cls.name
                            subject.scheduled += self.department.period_durations[period]
                            return True
        return False

    def generate(self) -> Dict:
        for cls in self.department.classes:
            for subject in cls.subjects.values():
                while subject.scheduled < subject.total_hours:
                    if subject.has_lab and self.allocate_lab(cls, subject):
                        continue
                    elif self.allocate_lecture(cls, subject):
                        continue
                    else:
                        print(f"Warning: Could not fully schedule {subject.name} for {cls.name}")
                        break
        return {cls.name: cls.timetable for cls in self.department.classes}

def get_config():
    """Collect user input for configuration"""
    config = {
        'classes': input("Enter class names (space-separated): ").split(),
        'periods_per_day': int(input("Periods per day: ")),
        'days': ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        'classes_subjects': {},  # Dictionary to store subjects per class
        'staff': [],
        'labs': []
    }
    
    # Period durations with varying lengths
    num_periods = int(input("Number of periods per day: "))
    config['period_durations'] = [int(input(f"Duration for period {i+1} (minutes): ")) 
                                 for i in range(num_periods)]

    # Subjects per class
    for cls_name in config['classes']:
        print(f"\nEnter subjects for {cls_name}:")
        num_subjects = int(input("Number of subjects: "))
        config['classes_subjects'][cls_name] = []
        for _ in range(num_subjects):
            config['classes_subjects'][cls_name].append({
                'name': input("Subject name: "),
                'total_hours': int(input("Total hours required: ")),
                'has_lab': input("Has lab? (y/n): ").lower() == 'y'
            })

    # Staff (can teach multiple subjects)
    num_staff = int(input("Number of staff members: "))
    for _ in range(num_staff):
        config['staff'].append({
            'name': input("Staff name: "),
            'subjects': input("Subjects taught (comma-separated): ").split(',')
        })

    # Labs
    num_labs = int(input("Number of labs: "))
    for _ in range(num_labs):
        lab_name = input("Lab name: ")
        periods = input("Enter period pairs (e.g., '0,2,3,5' for 0-2, 3-5): ")
        periods_list = list(map(int, periods.split(','))) if periods else []
        available_periods = {day: [] for day in config['days']}
        for i in range(0, len(periods_list), 2):
            start, end = periods_list[i], periods_list[i+1]
            if 0 <= start < end < config['periods_per_day']:
                available_periods[config['days'][i//2 % len(config['days'])]] = [(start, end)]
        config['labs'].append({'name': lab_name, 'available_periods': available_periods})

    return config

if __name__ == "__main__":
    config = get_config()
    department = Department(config)
    generator = TimetableGenerator(department)
    timetable = generator.generate()
    
    # Print timetable
    for cls_name, schedule in timetable.items():
        print(f"\n{cls_name} Timetable:")
        for day, periods in schedule.items():
            print(f"\n{day}:")
            for i, period in enumerate(periods):
                if period:
                    duration = department.period_durations[i]
                    print(f"Period {i+1} ({duration} min): {period['subject']} ({period['type']})" + 
                          (f" - {period['staff']}" if 'staff' in period else ""))