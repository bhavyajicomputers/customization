import frappe

def execute():
    today = frappe.utils.nowdate()
    cutoff_time = frappe.utils.get_time("09:30:00")
    late_employees = []

    employees = frappe.get_all("Employee",
        filters={"status": "Active", "department": "Service - KIPL"},
        fields=["name", "employee_name", "holiday_list"]
    )

    for emp in employees:
        if emp.holiday_list and frappe.db.exists("Holiday", {"parent": emp.holiday_list, "holiday_date": today}):
            continue

        checkin = frappe.db.get_list("Employee Checkin",
            filters={"employee": emp.name, "time": ["between", [f"{today} 00:00:00", f"{today} 23:59:59"]]},
            fields=["time"],
            order_by="time asc",
            limit=1
        )

        if not checkin or frappe.utils.get_time(checkin[0].time) > cutoff_time:
            late_employees.append({
                "employee": emp.name,
                "employee_name": emp.employee_name,
                "checkin_time": checkin[0].time if checkin else "Not Checked In"
            })

    if late_employees:
        rows = ""
        for emp in late_employees:
            time_str = frappe.utils.format_time(emp["checkin_time"]) if isinstance(emp["checkin_time"], str) == False else emp["checkin_time"]
            rows += f"<tr><td>{emp['employee']}</td><td>{emp['employee_name']}</td><td>{time_str}</td></tr>"

        report_html = f"""
        <h3>Late Check-in Report - {frappe.utils.formatdate(today)}</h3>
        <p><b>Department:</b> Service - KIPL</p>
        <table border="1" cellpadding="5" cellspacing="0">
            <tr><th>Employee ID</th><th>Employee Name</th><th>Check-in Time</th></tr>
            {rows}
        </table>
        """

        pdf_file = frappe.utils.pdf.get_pdf(report_html)
        file_name = f"Late_Checkin_Report_{today}.pdf"
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": file_name,
            "is_private": 0,
            "content": pdf_file
        })
        file_doc.insert(ignore_permissions=True)

        frappe.sendmail(
            recipients=["hr@example.com"],
            subject=f"Late Check-in Report - {frappe.utils.formatdate(today)}",
            message="Please find attached the late check-in report.",
            attachments=[{
                "file_url": file_doc.file_url,
                "filename": file_name
            }]
        )
