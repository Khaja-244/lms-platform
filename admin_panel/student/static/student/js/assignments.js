"use strict";
(async () => {
  const list = document.getElementById("assignmentList");
  const alertBox = document.getElementById("assignmentAlert");
  const user = LMS.getStoredUser();
  const instructor = ["instructor", "admin"].includes(user.role);
  if (instructor) document.getElementById("instructorAssignmentPanel").classList.remove("d-none");
  const message = (text, type = "danger") => { alertBox.textContent = text; alertBox.className = `alert alert-${type}`; };

  async function load() {
    try {
      const [assignments, submissions] = await Promise.all([LMS.get("/assignments/"), LMS.get("/assignments/submissions/")]);
      const byAssignment = Object.fromEntries(submissions.map(item => [item.assignment_id, item]));
      list.innerHTML = assignments.length ? assignments.map(item => {
        const submission = byAssignment[item.id];
        const deadline = new Date(item.deadline);
        return `<div class="col-md-6 col-xl-4"><article class="card h-100 border-0 shadow-sm"><div class="card-body">
          <span class="badge text-bg-light mb-2">Course #${item.course_id}</span><h2 class="h5">${item.title}</h2>
          <p class="text-muted">${item.description || "No description provided."}</p><p class="small"><i class="bi bi-clock me-1"></i>${deadline.toLocaleString()}</p>
          ${submission ? `<div class="alert alert-success py-2">Submitted: ${submission.original_filename}${submission.grade !== null ? `<br>Grade: <strong>${submission.grade}/100</strong>` : ""}</div>` : (!instructor ? `<form class="submit-form" data-id="${item.id}"><input class="form-control form-control-sm mb-2" name="file" type="file" required><button class="btn btn-sm btn-primary" ${deadline < new Date() ? "disabled" : ""}>Submit work</button></form>` : "")}
        </div></article></div>`;
      }).join("") : '<div class="col-12"><div class="alert alert-info">No assignments available.</div></div>';
      document.querySelectorAll(".submit-form").forEach(form => form.addEventListener("submit", async event => {
        event.preventDefault(); const data = new FormData(form); data.append("assignment_id", form.dataset.id);
        try { await LMS.request("/assignments/submit", {method: "POST", body: data}); message("Assignment submitted successfully.", "success"); await load(); } catch (error) { message(error.message); }
      }));
      if (instructor) {
        const panel = document.getElementById("gradingPanel"), target = document.getElementById("submissionList"); panel.classList.remove("d-none");
        target.innerHTML = submissions.length ? `<table class="table align-middle"><thead><tr><th>Assignment</th><th>Student</th><th>File</th><th>Grade</th><th>Action</th></tr></thead><tbody>${submissions.map(item => `<tr><td>${item.assignment_title}</td><td><strong>${item.student_name}</strong><br><small>${item.student_email}</small></td><td><a href="${LMS.apiBaseUrl}${item.file_url}" target="_blank" rel="noopener">${item.original_filename}</a></td><td><input class="form-control form-control-sm grade-value" data-id="${item.id}" type="number" min="0" max="100" value="${item.grade ?? ""}" style="width:90px"></td><td><button class="btn btn-sm btn-outline-primary grade-button" data-id="${item.id}">Save grade</button></td></tr>`).join("")}</tbody></table>` : '<div class="text-muted">No submissions yet.</div>';
        document.querySelectorAll(".grade-button").forEach(button => button.addEventListener("click", async () => { const input = document.querySelector(`.grade-value[data-id="${button.dataset.id}"]`); try { await LMS.put("/assignments/grade", {submission_id: Number(button.dataset.id), grade: Number(input.value), remarks: "Graded from instructor portal"}); message("Grade saved and student notified.", "success"); await load(); } catch (error) { message(error.message); } }));
      }
    } catch (error) { list.innerHTML = `<div class="col-12"><div class="alert alert-danger">${error.message}</div></div>`; }
  }
  document.getElementById("createAssignmentForm")?.addEventListener("submit", async event => {
    event.preventDefault(); const data = new FormData(event.target); data.set("deadline", new Date(data.get("deadline")).toISOString());
    if (!data.get("file")?.name) data.delete("file");
    try { await LMS.request("/assignments/create", {method: "POST", body: data}); event.target.reset(); message("Assignment created and students notified.", "success"); await load(); } catch (error) { message(error.message); }
  });
  await load();
})();
