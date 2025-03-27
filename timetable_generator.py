from typing import Dict, List, Optional

class Department:
    """Represents a department with classes, staff, and labs"""
    def __init__(self, config: Dict):
        self.days = config['days']
        self.periods_per_day = config['periods_per_day']
        self.period_durations = config['period_durations']
        self.classes = [Class(cls_name, config['subjects'], self.days, self.periods_per_day) for cls_name in config['classes']]
        self.staff = {s['name']: Staff(**s) for s in config['staff']}
        self.labs = {lab['name']: Lab(
            name=lab['name'],
            available_periods=lab['available_periods']
        ) for lab in config['labs']}

class Class:
    """Represents a class with its timetable and subjects"""
    def __init__(self, name: str, subjects: List[Dict], days: List[str], periods_per_day: int):
        self.name = name
        self.subjects = {s['name']: Subject(**s) for s in subjects}
        self.timetable = {day: [None] * Department.periods_per_day for day in Department.days}

class Subject:
    """Represents a subject with scheduling requirements"""
    def __init__(self, name: str, total_hours: int, has_lab: bool):
        self.name = name
        self.total_hours = total_hours * 60  # Convert to minutes
        self.has_lab = has_lab
        self.scheduled = 0

class Staff:
    """Represents a staff member with their availability"""
    def __init__(self, name: str, subjects: List[str]):
        self.name = name
        self.subjects = subjects
        self.schedule = {day: [None] * Department.periods_per_day for day in Department.days}

class Lab:
    """Represents a lab resource with availability tracking"""
    def __init__(self, name: str, available_periods: Dict[str, List[int]]):
        self.name = name
        self.availability = {
            day: [(start, end) for start, end in available_periods.get(day, [])]
            for day in Department.days
        }

class TimetableGenerator:
    """Generates timetable while respecting all constraints"""
    def __init__(self, department: Department):
        self.department = department
        
    def find_continuous_slots(self, day: str, duration: int) -> Optional[int]:
        """Find first available continuous slot of given duration in lab"""
        for lab in self.department.labs.values():
            for start in range(self.department.periods_per_day - duration + 1):
                if all(self._is_lab_available(lab, day, start + i) for i in range(duration)):
                    return start
        return None

    def _is_lab_available(self, lab: Lab, day: str, period: int) -> bool:
        """Check if lab is available at specific time"""
        return any(start <= period < end for start, end in lab.availability[day])

    def allocate_lab(self, cls: Class, subject: Subject) -> bool:
        """Allocate lab sessions for a subject"""
        if not subject.has_lab:
            return False

        lab_duration = 2  # Lab sessions are 2 consecutive periods
        for day in self.department.days:
            start = self.find_continuous_slots(day, lab_duration)
            if start is not None:
                # Allocate the lab session
                for p in range(start, start + lab_duration):
                    cls.timetable[day][p] = {'subject': subject.name, 'type': 'lab'}
                    # Update lab availability
                    lab.availability[day] = [
                        (s, e) for s, e in lab.availability[day]
                        if not (s <= p < e)
                    ]
                subject.scheduled += sum(self.department.period_durations[p] for p in range(start, start + lab_duration))
                return True
        return False

    def allocate_lecture(self, cls: Class, subject: Subject) -> bool:
        """Allocate lecture hours for a subject"""
        for day in self.department.days:
            for period in range(self.department.periods_per_day):
                if cls.timetable[day][period] is None:
                    # Find available staff
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
        """Main generation method"""
        # Allocate labs first
        for cls in self.department.classes:
            for subject in cls.subjects.values():
                required_hours = subject.total_hours
                while subject.scheduled < required_hours:
                    if not self.allocate_lab(cls, subject):
                        break

        # Allocate lectures
        for cls in self.department.classes:
            for subject in cls.subjects.values():
                while subject.scheduled < subject.total_hours:
                    if not self.allocate_lecture(cls, subject):
                        print(f"Warning: Couldn't fully allocate {subject.name} for {cls.name}")
                        break

        return {cls.name: cls.timetable for cls in self.department.classes}

def get_config():
    """Collect user input for configuration"""
    config = {
        'classes': input("Enter class names (space-separated): ").split(),
        'periods_per_day': int(input("Periods per day: ")),
        'period_durations': [int(input(f"Duration for period {i+1} (minutes): ")) for i in range(
            int(input("Number of periods per day: "))
        )],
        'days': ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        'subjects': [],
        'staff': [],
        'labs': []
    }

    # Subjects per class
    config['subjects'] = {}
    for cls_name in config['classes']:
        print(f"\nEnter subjects for {cls_name}:")
        num_subjects = int(input("Number of subjects: "))
        cls_subjects = []
        for _ in range(num_subjects):
            cls_subjects.append({
                'name': input("Subject name: "),
                'total_hours': int(input("Total hours required: ")),
                'has_lab': input("Has lab? (y/n): ").lower() == 'y'
            })
        config['subjects'][cls_name] = cls_subjects

    # Staff
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
        config['labs'].append({
            'name': lab_name,
            'available_periods': {
                day: [(i, i+1) for i in range(config['periods_per_day'])]
                for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            }
        })

    return config

if __name__ == "__main__":
    config = get_config()
    department = Department(config)
    generator = TimetableGenerator(department)
    timetable = generator.generate()
    
    # Print timetable
    for cls_name, schedule in timetable.items():
        print(f"\n{class_name} Timetable:")
        for day, periods in schedule.items():
            print(f"\n{day}:")
            for i, period in enumerate(periods):
                if period:
                    print(f"Period {i+1}: {period['subject']} ({period['type']})" + 
                          (f" - {period['staff']}" if period['type'] == 'lecture' else ""))