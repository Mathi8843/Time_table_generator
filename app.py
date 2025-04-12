from flask import Flask, request, jsonify, render_template
from timetable import Department, TimetableGenerator

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('landing_page.html')

@app.route('/index')
def index_page():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_timetable():
    # Extract form data
    config = {
        'classes': request.form['class-names'].split(),
        'days': ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        'periods_per_day': int(request.form['periods-per-day']),
        'num_breaks': int(request.form['num-breaks']),
        'break_periods': [int(request.form[f'break-period-{i}']) - 1 for i in range(int(request.form['num-breaks']))],
        'lunch_period': int(request.form['lunch-period']) - 1,
        'break_duration': int(request.form['break-duration']),
        'lunch_duration': int(request.form['lunch-duration']),
        'subjects': {},
        'staff': [],
        'special_hours': {}
    }

    # Period durations
    config['period_durations'] = []
    for i in range(config['periods_per_day']):
        if i in config['break_periods']:
            config['period_durations'].append(config['break_duration'])
        elif i == config['lunch_period']:
            config['period_durations'].append(config['lunch_duration'])
        else:
            config['period_durations'].append(int(request.form[f'period-duration-{i}']))

    # Subjects
    for cls_name in config['classes']:
        num_subjects = int(request.form[f'num-subjects-{cls_name}'])
        cls_subjects = []
        for i in range(num_subjects):
            cls_subjects.append({
                'name': request.form[f'subject-name-{cls_name}-{i}'],
                'total_hours': int(request.form[f'subject-hours-{cls_name}-{i}']),
                'has_lab': request.form[f'subject-lab-{cls_name}-{i}'] == 'y'
            })
        config['subjects'][cls_name] = cls_subjects

    # Staff
    num_staff = int(request.form['num-staff'])
    for i in range(num_staff):
        config['staff'].append({
            'name': request.form[f'staff-name-{i}'],
            'subjects_taught': request.form[f'staff-subjects-{i}'].split(','),
            'max_hours_per_day': int(request.form[f'staff-max-hours-{i}'])
        })

    # Special hours
    num_special = int(request.form['num-special'])
    for i in range(num_special):
        config['special_hours'][request.form[f'special-name-{i}']] = int(request.form[f'special-hours-{i}'])

    # Generate timetable
    department = Department(config)
    generator = TimetableGenerator(department)
    timetable = generator.generate()

    # Format class timetable (days as rows, periods as columns)
    formatted_timetable = {'classes': {}, 'staff': {}}
    for cls_name, schedule in timetable.items():
        formatted_schedule = {}
        for day in config['days']:  # Ensure order: Monday to Friday
            formatted_schedule[day] = [None] * config['periods_per_day']
            for i, period in enumerate(schedule[day]):
                if period:
                    if period['type'] == 'lecture':
                        formatted_schedule[day][i] = f"{period['subject']} ({period['type']}) - {period['staff']}"
                    else:
                        formatted_schedule[day][i] = f"{period['subject']} ({period['type']})"
                elif i in config['break_periods']:
                    formatted_schedule[day][i] = "Break"
                elif i == config['lunch_period']:
                    formatted_schedule[day][i] = "Lunch"
        formatted_timetable['classes'][cls_name] = formatted_schedule

    # Generate staff timetable
    for staff_name, staff_obj in department.staff.items():
        staff_schedule = {day: [None] * config['periods_per_day'] for day in config['days']}
        for day in config['days']:
            for i, cls_name in enumerate(staff_obj.schedule[day]):
                if cls_name:
                    staff_schedule[day][i] = f"{cls_name} - {timetable[cls_name][day][i]['subject']} (lecture)"
                elif i in config['break_periods']:
                    staff_schedule[day][i] = "Break"
                elif i == config['lunch_period']:
                    staff_schedule[day][i] = "Lunch"
        formatted_timetable['staff'][staff_name] = staff_schedule

    return jsonify(formatted_timetable)

if __name__ == '__main__':
    app.run(debug=True)