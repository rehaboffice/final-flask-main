from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, User, EmployeeProfile, Department, LeaveRequest, Attendance
from datetime import datetime

import csv
from io import StringIO, BytesIO
from flask import Response, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/api/profile', methods=['GET'])
@login_required
def get_profile():
    profile = current_user.profile
    
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    department = Department.query.get(current_user.department_id)
    current_year = datetime.utcnow().year
    leave_balance = current_user.leave_balance(year=current_year)
    
    return jsonify({
        "employee": {
            "id": current_user.id,
            "emp_id": current_user.emp_id,
            "email": current_user.email,
            "department": department.name if department else None,
            "leave_balance": leave_balance,
            "profile": {
                "full_name": profile.full_name,
                "contact_email": profile.contact_email,
                "phone": profile.phone
            }
        }
    }), 200

@employee_bp.route('/api/profile/contact', methods=['PATCH'])
@login_required
def update_contact_info():
    data = request.get_json()
    profile = current_user.profile
    
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    try:
        if 'contact_email' in data:
            profile.contact_email = data['contact_email']
        if 'phone' in data:
            profile.phone = data['phone']
        
        db.session.commit()
        return jsonify({"message": "Contact information updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@employee_bp.route('/api/leave', methods=['POST'])
@login_required
def submit_leave_request():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['start_date', 'end_date', 'reason']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    try:
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        if start_date > end_date:
            return jsonify({"error": "Start date cannot be after end date"}), 400
        
        leave_request = LeaveRequest(
            employee_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            reason=data['reason'],
            status='pending_manager'
        )
        
        db.session.add(leave_request)
        db.session.commit()
        
        return jsonify({
            "message": "Leave request submitted successfully",
            "id": leave_request.id,
            "status": leave_request.status
        }), 201
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@employee_bp.route('/api/leave', methods=['GET'])
@login_required
def get_leave_requests():
    leave_requests = LeaveRequest.query.filter_by(employee_id=current_user.id).all()
    request_list = []
    
    for leave in leave_requests:
        request_list.append({
            "id": leave.id,
            "start_date": leave.start_date.strftime('%Y-%m-%d'),
            "end_date": leave.end_date.strftime('%Y-%m-%d'),
            "reason": leave.reason,
            "status": leave.status
        })
    
    return jsonify({"leave_requests": request_list}), 200

@employee_bp.route('/api/attendance', methods=['GET'])
@login_required
def get_self_attendance():
    attendance_records = Attendance.query.filter_by(user_id=current_user.id).all()
    records = [{
        "date": record.date.strftime('%Y-%m-%d'),
        "status": record.status,
        "check_in_time": record.check_in_time.strftime('%H:%M:%S') if record.check_in_time else None,
        "check_out_time": record.check_out_time.strftime('%H:%M:%S') if record.check_out_time else None
    } for record in attendance_records]

    return jsonify({
        "emp_id": current_user.emp_id,
        "attendance": records
    }), 200

@employee_bp.route('/api/attendance', methods=['POST'])
@login_required
def mark_attendance():
    data = request.get_json()
    today = datetime.utcnow().date()
    status = data.get('status', 'present')  # default to 'present'
    check_in_time = data.get('check_in_time')
    check_out_time = data.get('check_out_time')

    # Check if already marked for today
    attendance = Attendance.query.filter_by(user_id=current_user.id, date=today).first()
    if attendance:
        return jsonify({"error": "Attendance already marked for today"}), 400

    attendance = Attendance(
        user_id=current_user.id,
        date=today,
        status=status,
        check_in_time=check_in_time,
        check_out_time=check_out_time
    )
    db.session.add(attendance)
    db.session.commit()
    return jsonify({"message": "Attendance marked"}), 201

@employee_bp.route('/api/leave-balance', methods=['GET'])
@login_required
def get_self_leave_balance():
    current_year = datetime.utcnow().year
    leave_balance = current_user.leave_balance(year=current_year)
    return jsonify({
        "emp_id": current_user.emp_id,
        "leave_balance": leave_balance
    }), 200

def generate_employee_csv(user):
    output = StringIO()
    writer = csv.writer(output)
    profile = user.profile

    writer.writerow(['Employee Details'])
    writer.writerow(['emp_id', 'full_name', 'email', 'role', 'department', 'leave_balance'])
    writer.writerow([
        user.emp_id,
        profile.full_name if profile else '',
        user.email,
        user.role,
        user.department.name if user.department else '',
        user.leave_balance(datetime.utcnow().year)
    ])
    writer.writerow([])

    writer.writerow(['Attendance'])
    writer.writerow(['date', 'status', 'check_in_time', 'check_out_time'])
    for record in user.attendance:
        writer.writerow([
            record.date.strftime('%Y-%m-%d'),
            record.status,
            record.check_in_time.strftime('%H:%M:%S') if record.check_in_time else '',
            record.check_out_time.strftime('%H:%M:%S') if record.check_out_time else ''
        ])
    writer.writerow([])

    writer.writerow(['Leave Requests'])
    writer.writerow(['start_date', 'end_date', 'reason', 'status'])
    for leave in user.leave_requests:
        writer.writerow([
            leave.start_date.strftime('%Y-%m-%d'),
            leave.end_date.strftime('%Y-%m-%d'),
            leave.reason,
            leave.status
        ])
    return output.getvalue()

@employee_bp.route('/api/export-self', methods=['GET'])
@login_required
def export_self_data_csv():
    csv_data = generate_employee_csv(current_user)
    output = StringIO(csv_data)
    return Response(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=employee_data.csv"}
    )

def generate_employee_pdf(user):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40
    profile = user.profile

    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, y, "Employee Details")
    y -= 20
    p.setFont("Helvetica", 12)
    p.drawString(40, y, f"ID: {user.emp_id}")
    y -= 15
    p.drawString(40, y, f"Name: {profile.full_name if profile else ''}")
    y -= 15
    p.drawString(40, y, f"Email: {user.email}")
    y -= 15
    p.drawString(40, y, f"Role: {user.role}")
    y -= 15
    p.drawString(40, y, f"Department: {user.department.name if user.department else ''}")
    y -= 15
    p.drawString(40, y, f"Leave Balance: {user.leave_balance(datetime.utcnow().year)}")
    y -= 30

    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, y, "Attendance")
    y -= 20
    p.setFont("Helvetica", 10)
    for record in user.attendance:
        p.drawString(40, y, f"{record.date.strftime('%Y-%m-%d')}, {record.status}, {record.check_in_time or ''}, {record.check_out_time or ''}")
        y -= 12
        if y < 60:
            p.showPage()
            y = height - 40

    y -= 20
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, y, "Leave Requests")
    y -= 20
    p.setFont("Helvetica", 10)
    for leave in user.leave_requests:
        p.drawString(40, y, f"{leave.start_date.strftime('%Y-%m-%d')} to {leave.end_date.strftime('%Y-%m-%d')}, {leave.reason}, {leave.status}")
        y -= 12
        if y < 60:
            p.showPage()
            y = height - 40

    p.save()
    buffer.seek(0)
    return buffer

@employee_bp.route('/api/export-self-pdf', methods=['GET'])
@login_required
def export_self_data_pdf():
    pdf_buffer = generate_employee_pdf(current_user)
    return send_file(pdf_buffer, as_attachment=True, download_name='employee_data.pdf', mimetype='application/pdf')