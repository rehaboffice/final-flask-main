# from flask import request, jsonify, session
# from flask_login import login_user, logout_user, login_required, current_user
# from datetime import datetime
# from functools import wraps

# from models import db, User, EmployeeProfile, Department, LeaveRequest, Attendance
# from werkzeug.security import check_password_hash

# import csv
# from io import StringIO, BytesIO
# from flask import Response, send_file
# from reportlab.lib.pagesizes import letter
# from reportlab.pdfgen import canvas

# # Custom decorator for admin access
# def admin_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if not current_user.is_authenticated or current_user.role != 'admin':
#             return jsonify({"error": "Admin access required"}), 403
#         return f(*args, **kwargs)
#     return decorated_function

# # Custom decorator for manager access
# def manager_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if not current_user.is_authenticated or current_user.role != 'manager':
#             return jsonify({"error": "Manager access required"}), 403
#         return f(*args, **kwargs)
#     return decorated_function

# # Authentication routes
# def login():
#     data = request.get_json()
    
#     if not data or not data.get('email') or not data.get('password'):
#         return jsonify({"error": "Missing email or password"}), 400
    
#     user = User.query.filter_by(email=data['email']).first()
    
#     if not user or not check_password_hash(user.password_hash, data['password']):
#         return jsonify({"error": "Invalid credentials"}), 401
    
#     login_user(user)
#     session.permanent = True  # Use the permanent session lifetime
    
#     return jsonify({
#         "message": "Login successful",
#         "user": {
#             "id": user.id,
#             "emp_id": user.emp_id,
#             "email": user.email,
#             "role": user.role
#         }
#     }), 200

# @login_required
# def logout():
#     logout_user()
#     return jsonify({"message": "Logout successful"}), 200

# Admin Routes
# @login_required
# @admin_required
# def get_all_employees():
#     employees = User.query.all()
#     employee_list = []
#     current_year = datetime.utcnow().year
    
#     for employee in employees:
#         profile = employee.profile
#         leave_balance = employee.leave_balance(year=current_year)
#         employee_data = {
#             "id": employee.id,
#             "emp_id": employee.emp_id,
#             "email": employee.email,
#             "role": employee.role,
#             "department_id": employee.department_id,
#             "leave_balance": leave_balance,
#             "profile": None
#         }
        
#         if profile:
#             employee_data["profile"] = {
#                 "full_name": profile.full_name,
#                 "salary": profile.salary,
#                 "contact_email": profile.contact_email,
#                 "phone": profile.phone
#             }
        
#         employee_list.append(employee_data)
    
#     return jsonify({"employees": employee_list}), 200

# @login_required
# @admin_required
# def add_employee():
#     data = request.get_json()
    
#     # Validate required fields
#     required_fields = ['emp_id', 'email', 'password', 'role', 'department_id', 'full_name']
#     for field in required_fields:
#         if field not in data:
#             return jsonify({"error": f"Missing required field: {field}"}), 400
    
#     # Check if employee already exists
#     if User.query.filter_by(emp_id=data['emp_id']).first() or User.query.filter_by(email=data['email']).first():
#         return jsonify({"error": "Employee with this ID or email already exists"}), 409
    
#     # Create new user
#     new_user = User(
#         emp_id=data['emp_id'],
#         email=data['email'],
#         role=data['role'],
#         department_id=data['department_id']
#     )
#     new_user.set_password(data['password'])
    
#     # Create employee profile
#     new_profile = EmployeeProfile(
#         full_name=data['full_name'],
#         salary=data.get('salary', 0),
#         contact_email=data.get('contact_email', data['email']),
#         phone=data.get('phone', '')
#     )
    
#     # Save to database
#     try:
#         db.session.add(new_user)
#         db.session.flush()  # To get the user ID
        
#         new_profile.user_id = new_user.id
#         db.session.add(new_profile)
#         db.session.commit()
        
#         return jsonify({"message": "Employee added successfully", "emp_id": new_user.emp_id}), 201
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"error": str(e)}), 500

# @login_required
# @admin_required
# def update_employee(emp_id):
#     data = request.get_json()
#     user = User.query.filter_by(emp_id=emp_id).first()
    
#     if not user:
#         return jsonify({"error": "Employee not found"}), 404
    
#     try:
#         # Update user data
#         if 'email' in data:
#             user.email = data['email']
#         if 'role' in data:
#             user.role = data['role']
#         if 'department_id' in data:
#             user.department_id = data['department_id']
#         if 'password' in data:
#             user.set_password(data['password'])
        
#         # Update profile data
#         profile = user.profile
#         if profile:
#             if 'full_name' in data:
#                 profile.full_name = data['full_name']
#             if 'salary' in data:
#                 profile.salary = data['salary']
#             if 'contact_email' in data:
#                 profile.contact_email = data['contact_email']
#             if 'phone' in data:
#                 profile.phone = data['phone']
        
#         db.session.commit()
#         return jsonify({"message": "Employee updated successfully"}), 200
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"error": str(e)}), 500

# @login_required
# @admin_required
# def get_all_departments():
#     departments = Department.query.all()
#     department_list = []
    
#     for dept in departments:
#         employees = User.query.filter_by(department_id=dept.id).count()
#         department_list.append({
#             "id": dept.id,
#             "name": dept.name,
#             "employee_count": employees
#         })
    
#     return jsonify({"departments": department_list}), 200

# @login_required
# @admin_required
# def add_department():
#     data = request.get_json()
    
#     if not data or not data.get('name'):
#         return jsonify({"error": "Department name is required"}), 400
    
#     # Check if department already exists
#     if Department.query.filter_by(name=data['name']).first():
#         return jsonify({"error": "Department with this name already exists"}), 409
    
#     new_department = Department(name=data['name'])
    
#     try:
#         db.session.add(new_department)
#         db.session.commit()
#         return jsonify({
#             "message": "Department added successfully",
#             "id": new_department.id,
#             "name": new_department.name
#         }), 201
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"error": str(e)}), 500

# @login_required
# @admin_required
# def get_all_leave_requests():
#     leave_requests = LeaveRequest.query.all()
#     request_list = []
#     current_year = datetime.utcnow().year
    
#     for leave in leave_requests:
#         employee = User.query.get(leave.employee_id)
#         profile = employee.profile if employee else None
#         leave_balance = employee.leave_balance(year=current_year) if employee else None
        
#         request_list.append({
#             "id": leave.id,
#             "employee_id": leave.employee_id,
#             "employee_name": profile.full_name if profile else "Unknown",
#             "start_date": leave.start_date.strftime('%Y-%m-%d'),
#             "end_date": leave.end_date.strftime('%Y-%m-%d'),
#             "status": leave.status,
#             "reason": leave.reason,
#             "leave_balance": leave_balance
#         })
    
#     return jsonify({"leave_requests": request_list}), 200

# @login_required
# @admin_required
# def update_leave_request(request_id):
#     data = request.get_json()
#     leave_request = LeaveRequest.query.get(request_id)
    
#     if not leave_request:
#         return jsonify({"error": "Leave request not found"}), 404
    
#     if 'status' not in data:
#         return jsonify({"error": "Status is required"}), 400
    
#     valid_statuses = ['pending_manager', 'pending_admin', 'approved', 'rejected']
#     if data['status'] not in valid_statuses:
#         return jsonify({"error": "Invalid status value"}), 400
    
#     try:
#         leave_request.status = data['status']
#         db.session.commit()
#         return jsonify({"message": "Leave request updated successfully"}), 200
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"error": str(e)}), 500

# # Employee Routes
# @login_required
# def get_profile():
#     profile = current_user.profile
    
#     if not profile:
#         return jsonify({"error": "Profile not found"}), 404
    
#     department = Department.query.get(current_user.department_id)
#     current_year = datetime.utcnow().year
#     leave_balance = current_user.leave_balance(year=current_year)
    
#     return jsonify({
#         "employee": {
#             "id": current_user.id,
#             "emp_id": current_user.emp_id,
#             "email": current_user.email,
#             "department": department.name if department else None,
#             "leave_balance": leave_balance,
#             "profile": {
#                 "full_name": profile.full_name,
#                 "contact_email": profile.contact_email,
#                 "phone": profile.phone
#             }
#         }
#     }), 200

# @login_required
# def update_contact_info():
#     data = request.get_json()
#     profile = current_user.profile
    
#     if not profile:
#         return jsonify({"error": "Profile not found"}), 404
    
#     try:
#         if 'contact_email' in data:
#             profile.contact_email = data['contact_email']
#         if 'phone' in data:
#             profile.phone = data['phone']
        
#         db.session.commit()
#         return jsonify({"message": "Contact information updated successfully"}), 200
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"error": str(e)}), 500

# @login_required
# def submit_leave_request():
#     data = request.get_json()
    
#     # Validate required fields
#     required_fields = ['start_date', 'end_date', 'reason']
#     for field in required_fields:
#         if field not in data:
#             return jsonify({"error": f"Missing required field: {field}"}), 400
    
#     try:
#         start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
#         end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
#         if start_date > end_date:
#             return jsonify({"error": "Start date cannot be after end date"}), 400
        
#         leave_request = LeaveRequest(
#             employee_id=current_user.id,
#             start_date=start_date,
#             end_date=end_date,
#             reason=data['reason'],
#             status='pending'
#         )
        
#         db.session.add(leave_request)
#         db.session.commit()
        
#         return jsonify({
#             "message": "Leave request submitted successfully",
#             "id": leave_request.id,
#             "status": leave_request.status
#         }), 201
#     except ValueError:
#         return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"error": str(e)}), 500

# @login_required
# def get_leave_requests():
#     leave_requests = LeaveRequest.query.filter_by(employee_id=current_user.id).all()
#     request_list = []
    
#     for leave in leave_requests:
#         request_list.append({
#             "id": leave.id,
#             "start_date": leave.start_date.strftime('%Y-%m-%d'),
#             "end_date": leave.end_date.strftime('%Y-%m-%d'),
#             "reason": leave.reason,
#             "status": leave.status
#         })
    
#     return jsonify({"leave_requests": request_list}), 200

# @login_required
# @manager_required
# def manager_update_leave_request(request_id):
#     leave_request = LeaveRequest.query.get(request_id)
#     if not leave_request:
#         return jsonify({"error": "Leave request not found"}), 404

#     # Only allow update if status is pending_manager
#     if leave_request.status != 'pending_manager':
#         return jsonify({"error": "Leave request is not pending manager approval"}), 400

#     try:
#         leave_request.status = 'pending_admin'
#         db.session.commit()
#         return jsonify({"message": "Leave request forwarded to admin"}), 200
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"error": str(e)}), 500
    
# @login_required
# @admin_required
# def get_employee_attendance(emp_id):
#     user = User.query.filter_by(emp_id=emp_id).first()
#     if not user:
#         return jsonify({"error": "Employee not found"}), 404

#     attendance_records = Attendance.query.filter_by(user_id=user.id).all()
#     records = [{
#         "date": record.date.strftime('%Y-%m-%d'),
#         "status": record.status,
#         "check_in_time": record.check_in_time.strftime('%H:%M:%S') if record.check_in_time else None,
#         "check_out_time": record.check_out_time.strftime('%H:%M:%S') if record.check_out_time else None
#     } for record in attendance_records]

#     return jsonify({
#         "emp_id": user.emp_id,
#         "attendance": records
#     }), 200

# @login_required
# def get_self_attendance():
#     attendance_records = Attendance.query.filter_by(user_id=current_user.id).all()
#     records = [{
#         "date": record.date.strftime('%Y-%m-%d'),
#         "status": record.status,
#         "check_in_time": record.check_in_time.strftime('%H:%M:%S') if record.check_in_time else None,
#         "check_out_time": record.check_out_time.strftime('%H:%M:%S') if record.check_out_time else None
#     } for record in attendance_records]

#     return jsonify({
#         "emp_id": current_user.emp_id,
#         "attendance": records
#     }), 200

# @login_required
# @admin_required
# def get_all_attendance():
#     users = User.query.all()
#     all_attendance = []
#     for user in users:
#         attendance_records = Attendance.query.filter_by(user_id=user.id).all()
#         records = [{
#             "date": record.date.strftime('%Y-%m-%d'),
#             "status": record.status,
#             "check_in_time": record.check_in_time.strftime('%H:%M:%S') if record.check_in_time else None,
#             "check_out_time": record.check_out_time.strftime('%H:%M:%S') if record.check_out_time else None
#         } for record in attendance_records]
#         all_attendance.append({
#             "emp_id": user.emp_id,
#             "attendance": records
#         })
#     return jsonify({"all_attendance": all_attendance}), 200

# @login_required
# def mark_attendance():
#     data = request.get_json()
#     today = datetime.utcnow().date()
#     status = data.get('status', 'present')  # default to 'present'
#     check_in_time = data.get('check_in_time')
#     check_out_time = data.get('check_out_time')

#     # Check if already marked for today
#     attendance = Attendance.query.filter_by(user_id=current_user.id, date=today).first()
#     if attendance:
#         return jsonify({"error": "Attendance already marked for today"}), 400

#     attendance = Attendance(
#         user_id=current_user.id,
#         date=today,
#         status=status,
#         check_in_time=check_in_time,
#         check_out_time=check_out_time
#     )
#     db.session.add(attendance)
#     db.session.commit()
#     return jsonify({"message": "Attendance marked"}), 201

# @login_required
# @admin_required
# def get_employee_leave_balance(emp_id):
#     user = User.query.filter_by(emp_id=emp_id).first()
#     if not user:
#         return jsonify({"error": "Employee not found"}), 404
#     current_year = datetime.utcnow().year
#     leave_balance = user.leave_balance(year=current_year)
#     return jsonify({
#         "emp_id": user.emp_id,
#         "leave_balance": leave_balance
#     }), 200

# @login_required
# def get_self_leave_balance():
#     current_year = datetime.utcnow().year
#     leave_balance = current_user.leave_balance(year=current_year)
#     return jsonify({
#         "emp_id": current_user.emp_id,
#         "leave_balance": leave_balance
#     }), 200

# @login_required
# @admin_required
# def get_all_leave_balances():
#     users = User.query.all()
#     current_year = datetime.utcnow().year
#     balances = []
#     for user in users:
#         balances.append({
#             "emp_id": user.emp_id,
#             "leave_balance": user.leave_balance(year=current_year)
#         })
#     return jsonify({"leave_balances": balances}), 200

# def generate_employee_csv(user):
#     output = StringIO()
#     writer = csv.writer(output)
#     profile = user.profile

#     writer.writerow(['Employee Details'])
#     writer.writerow(['emp_id', 'full_name', 'email', 'role', 'department', 'leave_balance'])
#     writer.writerow([
#         user.emp_id,
#         profile.full_name if profile else '',
#         user.email,
#         user.role,
#         user.department.name if user.department else '',
#         user.leave_balance(datetime.utcnow().year)
#     ])
#     writer.writerow([])

#     writer.writerow(['Attendance'])
#     writer.writerow(['date', 'status', 'check_in_time', 'check_out_time'])
#     for record in user.attendance:
#         writer.writerow([
#             record.date.strftime('%Y-%m-%d'),
#             record.status,
#             record.check_in_time.strftime('%H:%M:%S') if record.check_in_time else '',
#             record.check_out_time.strftime('%H:%M:%S') if record.check_out_time else ''
#         ])
#     writer.writerow([])

#     writer.writerow(['Leave Requests'])
#     writer.writerow(['start_date', 'end_date', 'reason', 'status'])
#     for leave in user.leave_requests:
#         writer.writerow([
#             leave.start_date.strftime('%Y-%m-%d'),
#             leave.end_date.strftime('%Y-%m-%d'),
#             leave.reason,
#             leave.status
#         ])
#     return output.getvalue()

# def generate_employee_pdf(user):
#     buffer = BytesIO()
#     p = canvas.Canvas(buffer, pagesize=letter)
#     width, height = letter
#     y = height - 40
#     profile = user.profile

#     p.setFont("Helvetica-Bold", 14)
#     p.drawString(40, y, "Employee Details")
#     y -= 20
#     p.setFont("Helvetica", 12)
#     p.drawString(40, y, f"ID: {user.emp_id}")
#     y -= 15
#     p.drawString(40, y, f"Name: {profile.full_name if profile else ''}")
#     y -= 15
#     p.drawString(40, y, f"Email: {user.email}")
#     y -= 15
#     p.drawString(40, y, f"Role: {user.role}")
#     y -= 15
#     p.drawString(40, y, f"Department: {user.department.name if user.department else ''}")
#     y -= 15
#     p.drawString(40, y, f"Leave Balance: {user.leave_balance(datetime.utcnow().year)}")
#     y -= 30

#     p.setFont("Helvetica-Bold", 14)
#     p.drawString(40, y, "Attendance")
#     y -= 20
#     p.setFont("Helvetica", 10)
#     for record in user.attendance:
#         p.drawString(40, y, f"{record.date.strftime('%Y-%m-%d')}, {record.status}, {record.check_in_time or ''}, {record.check_out_time or ''}")
#         y -= 12
#         if y < 60:
#             p.showPage()
#             y = height - 40

#     y -= 20
#     p.setFont("Helvetica-Bold", 14)
#     p.drawString(40, y, "Leave Requests")
#     y -= 20
#     p.setFont("Helvetica", 10)
#     for leave in user.leave_requests:
#         p.drawString(40, y, f"{leave.start_date.strftime('%Y-%m-%d')} to {leave.end_date.strftime('%Y-%m-%d')}, {leave.reason}, {leave.status}")
#         y -= 12
#         if y < 60:
#             p.showPage()
#             y = height - 40

#     p.save()
#     buffer.seek(0)
#     return buffer

# @login_required
# @admin_required
# def export_employee_data_csv():
#     emp_id = request.args.get('emp_id')
#     output = StringIO()
#     if emp_id:
#         user = User.query.filter_by(emp_id=emp_id).first()
#         if not user:
#             return jsonify({"error": "Employee not found"}), 404
#         csv_data = generate_employee_csv(user)
#         output.write(csv_data)
#     else:
#         users = User.query.all()
#         for user in users:
#             output.write(generate_employee_csv(user))
#             output.write('\n\n')
#     output.seek(0)
#     return Response(
#         output,
#         mimetype='text/csv',
#         headers={"Content-Disposition": "attachment;filename=employee_data.csv"}
#     )

# @login_required
# def export_self_data_csv():
#     csv_data = generate_employee_csv(current_user)
#     output = StringIO(csv_data)
#     return Response(
#         output,
#         mimetype='text/csv',
#         headers={"Content-Disposition": "attachment;filename=employee_data.csv"}
#     )

# @login_required
# @admin_required
# def export_employee_data_pdf():
#     emp_id = request.args.get('emp_id')
#     if emp_id:
#         user = User.query.filter_by(emp_id=emp_id).first()
#         if not user:
#             return jsonify({"error": "Employee not found"}), 404
#         pdf_buffer = generate_employee_pdf(user)
#         return send_file(pdf_buffer, as_attachment=True, download_name='employee_data.pdf', mimetype='application/pdf')
#     else:
#         return jsonify({"error": "PDF export for all users not implemented"}), 400

# @login_required
# def export_self_data_pdf():
#     pdf_buffer = generate_employee_pdf(current_user)
#     return send_file(pdf_buffer, as_attachment=True, download_name='employee_data.pdf', mimetype='application/pdf')

# Blueprint registration function
# def register_routes(app):
    # Authentication routes
    # app.route('/api/login', methods=['POST'])(login)
    # app.route('/api/logout', methods=['POST'])(logout)
    
    # Admin routes
    # app.route('/api/admin/employees', methods=['GET'])(get_all_employees)
    # app.route('/api/admin/employees', methods=['POST'])(add_employee)
    # app.route('/api/admin/employees/<emp_id>', methods=['PUT'])(update_employee)
    # app.route('/api/admin/departments', methods=['GET'])(get_all_departments)
    # app.route('/api/admin/departments', methods=['POST'])(add_department)
    # app.route('/api/admin/leave-requests', methods=['GET'])(get_all_leave_requests)
    #  app.route('/api/admin/leave-requests/<int:request_id>', methods=['PUT'])(update_leave_request)
    # app.route('/api/admin/attendance/<emp_id>', methods=['GET'])(get_employee_attendance)
    # app.route('/api/admin/attendance', methods=['GET'])(get_all_attendance)
    #  app.route('/api/admin/leave-balance/<emp_id>', methods=['GET'])(get_employee_leave_balance)
    # app.route('/api/admin/leave-balances', methods=['GET'])(get_all_leave_balances)
    # app.route('/api/admin/export-employee', methods=['GET'])(export_employee_data_csv)
    #  app.route('/api/admin/export-employee-pdf', methods=['GET'])(export_employee_data_pdf)
    
    # Employee routes
    # app.route('/api/profile', methods=['GET'])(get_profile)
    # app.route('/api/profile/contact', methods=['PATCH'])(update_contact_info)
    # app.route('/api/leave', methods=['POST'])(submit_leave_request)
    # app.route('/api/leave', methods=['GET'])(get_leave_requests)
    # app.route('/api/attendance', methods=['GET'])(get_self_attendance)
    # app.route('/api/attendance', methods=['POST'])(mark_attendance)
    # app.route('/api/leave-balance', methods=['GET'])(get_self_leave_balance)
    # app.route('/api/export-self', methods=['GET'])(export_self_data_csv)
    # app.route('/api/export-self-pdf', methods=['GET'])(export_self_data_pdf)

    # Manager routes
    # app.route('/api/manager/leave-requests/<int:request_id>', methods=['PUT'])(manager_update_leave_request)