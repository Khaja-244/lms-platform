"use strict";
const attendanceUser = LMS.getStoredUser();
if (["instructor", "admin"].includes(attendanceUser.role)) { document.getElementById("markAttendancePanel")?.classList.remove("d-none"); document.getElementById("attendanceStudentField")?.classList.remove("d-none"); document.getElementById("attendanceStudentId").required = true; }
document.getElementById("markAttendanceForm")?.addEventListener("submit", async event => {
  event.preventDefault(); const form = new FormData(event.target); const target = document.getElementById("markAttendanceResult");
  try {
    const records = String(form.get("records")).split(",").map(pair => { const [student, status] = pair.split(":").map(value => value.trim()); if (!student || !["Present", "Absent", "Late"].includes(status)) throw new Error("Use the format 3:Present, 4:Absent, 5:Late"); return {student_id: Number(student), status}; });
    const data = await LMS.post("/attendance/mark", {course_id: Number(form.get("course_id")), date: form.get("date"), records});
    target.innerHTML = `<div class="alert alert-success">Marked ${data.length} attendance records and notified students.</div>`; event.target.reset();
  } catch (error) { target.innerHTML = `<div class="alert alert-danger">${error.message}</div>`; }
});
document.getElementById("attendanceForm")?.addEventListener("submit", async event => {
  event.preventDefault();
  const user = LMS.getStoredUser(); const courseId = document.getElementById("attendanceCourseId").value;
  const summary = document.getElementById("attendanceSummary"); const table = document.getElementById("attendanceTable");
  if (!user.id) { summary.innerHTML = '<div class="alert alert-warning">Please sign in again.</div>'; return; }
  try {
    const studentId = ["instructor", "admin"].includes(user.role) ? document.getElementById("attendanceStudentId").value : user.id;
    const data = await LMS.get(`/attendance/student/${studentId}/?course_id=${courseId}`);
    summary.innerHTML = `<div class="row g-3"><div class="col"><div class="p-3 bg-light rounded"><strong>${data.percentage}%</strong><br><span class="text-muted">Attendance</span></div></div><div class="col"><div class="p-3 bg-light rounded"><strong>${data.present}</strong><br><span class="text-muted">Present</span></div></div><div class="col"><div class="p-3 bg-light rounded"><strong>${data.absent}</strong><br><span class="text-muted">Absent</span></div></div><div class="col"><div class="p-3 bg-light rounded"><strong>${data.late||0}</strong><br><span class="text-muted">Late</span></div></div></div>`;
    table.innerHTML = data.records.length ? `<table class="table align-middle"><thead><tr><th>Date</th><th>Status</th></tr></thead><tbody>${data.records.map(row => `<tr><td>${row.date}</td><td><span class="badge ${row.status === "Present" ? "text-bg-success" : "text-bg-danger"}">${row.status}</span></td></tr>`).join("")}</tbody></table>` : '<div class="alert alert-info">No attendance has been marked for this course.</div>';
  } catch (error) { summary.innerHTML = `<div class="alert alert-danger">${error.message}</div>`; table.innerHTML = ""; }
});
