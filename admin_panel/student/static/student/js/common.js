"use strict";

const routes = window.STUDENT_ROUTES || {};

document.addEventListener("DOMContentLoaded", () => {
    bindShell();
    routePage();
});

function pageId() {
    return document.body.dataset.page || "";
}

function isAuthPage() {
    return ["login", "register"].includes(pageId());
}

function routePage() {
    if (!isAuthPage() && !LMS.getAccessToken()) {
        window.location.href = routes.login || "/student/";
        return;
    }

    hydrateShell();
    refreshNotificationBadge();
    connectNotificationSocket();

    const handlers = {
        login: initLogin,
        register: initRegister,
        dashboard: initDashboard,
        courses: initCourses,
        "course-detail": initCourseDetail,
        "my-courses": initMyCourses,
        "lesson-player": initLessonPlayer,
        plans: initPlans,
        subscription: initSubscription,
        payments: initPayments,
        notifications: initNotifications,
        profile: initProfile,
    };

    const handler = handlers[pageId()];
    if (handler) handler();
}

function bindShell() {
    const sidebar = qs("#sidebar");
    const sidebarToggle = qs("#sidebarToggle");
    if (sidebar && sidebarToggle) {
        sidebarToggle.addEventListener("click", (event) => {
            event.stopPropagation();
            sidebar.classList.toggle("open");
        });
    }

    qsa("[data-logout]").forEach((button) => {
        button.addEventListener("click", async () => {
            try {
                if (LMS.getAccessToken()) await LMS.post("/auth/logout/", {});
            } catch {
                // local logout must still complete if token is expired
            }
            LMS.clearSession();
            window.location.href = routes.login || "/student/";
        });
    });
}

function hydrateShell() {
    const user = LMS.getStoredUser();
    const name = user.name || user.email || "Student";
    qsa("[data-student-name]").forEach((node) => (node.textContent = name));
    qsa("[data-first-name]").forEach((node) => (node.textContent = (user.name || "Student").split(" ")[0]));
    qsa("[data-student-avatar]").forEach((node) => {
        if (user.profile_picture) {
            node.innerHTML = `<img src="${escapeHtml(user.profile_picture)}" alt="Profile">`;
        } else {
            node.textContent = name.slice(0, 1).toUpperCase();
        }
    });
}

async function initLogin() {
    if (LMS.getAccessToken()) {
        window.location.href = routes.dashboard || "/student/dashboard/";
        return;
    }
    const form = qs("#loginForm");
    form?.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        const payload = formPayload(form);
        await withButton(qs("#loginSubmit"), "Logging in...", async () => {
            const result = await LMS.post("/auth/login/", payload, false);
            if (result.user?.role !== "student") {
                LMS.clearSession();
                throw new Error("Please login with a student account. Admin and instructor users cannot enter the Student Portal.");
            }
            LMS.setSession(result.access_token, result.user);
            showAlert("Login successful. Opening dashboard...", "success");
            window.location.href = routes.dashboard || "/student/dashboard/";
        });
    });
}

async function initRegister() {
    const form = qs("#registerForm");
    form?.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        const payload = formPayload(form);
        await withButton(qs("#registerSubmit"), "Creating account...", async () => {
            await LMS.post("/auth/register/", payload, false);
            showAlert("Registration successful. Please login.", "success");
            setTimeout(() => (window.location.href = routes.login || "/student/"), 900);
        });
    });
}

async function initDashboard() {
    qs("[data-refresh-page]")?.addEventListener("click", initDashboard);
    const [courses, subscriptions, progress, notifications, activity, plans] = await Promise.all([
        safe(() => LMS.get("/my-courses/"), []),
        safe(() => LMS.get("/subscriptions/me"), []),
        safe(() => LMS.get("/progress/view/"), []),
        safe(() => LMS.get("/notifications/"), []),
        safe(() => LMS.get("/activity/"), []),
        safe(() => LMS.get("/plans/"), []),
    ]);

    const activeSub = subscriptions.find((item) => item.status === "active");
    const avgProgress = progress.length
        ? Math.round(progress.reduce((sum, item) => sum + Number(item.progress_percent || 0), 0) / progress.length)
        : 0;

    setText("#statEnrolled", courses.length);
    setText("#statProgress", `${avgProgress}%`);
    const activePlan = plans.find(plan => Number(plan.id) === Number(activeSub?.plan_id));
    setText("#statPlan", activePlan?.name || "None");
    setText("#statPlanHelp", activeSub ? `Expires ${formatDate(activeSub.end_date)}` : "Choose a plan to unlock premium courses");
    setText("#statNotifications", notifications.filter((item) => !item.is_read).length);

    qs("#continueLearning").innerHTML = courses[0] ? continueCourse(courses[0], progress[0]) : empty("No enrolled course yet", "Browse courses and enroll to start learning.");
    qs("#dashboardCourses").innerHTML = courses.slice(0, 4).map(courseCard).join("") || `<div class="col-12">${empty("No courses", "Your enrolled courses will appear here.")}</div>`;
    qs("#dashboardNotifications").innerHTML = notifications.slice(0, 5).map(notificationMini).join("") || empty("No notifications", "Important updates will appear here.");
    qs("#dashboardActivity").innerHTML = activity.slice(0, 6).map(activityMini).join("") || empty("No activity", "Your learning activity will be tracked here.");
}

async function initCourses() {
    const courses = await LMS.get("/courses/");
    const params = new URLSearchParams(window.location.search);
    const search = qs("#courseSearch");
    const filter = qs("#courseTypeFilter");
    search.value = params.get("q") || "";
    const render = () => {
        const term = search.value.toLowerCase();
        const type = filter.value;
        const filtered = courses.filter((course) => {
            const text = `${course.title} ${course.description} ${course.level}`.toLowerCase();
            const typeOk = type === "all" || (type === "premium" && course.is_premium) || (type === "free" && !course.is_premium);
            return text.includes(term) && typeOk;
        });
        qs("#courseGrid").innerHTML = filtered.map(courseCard).join("") || `<div class="col-12">${empty("No matching courses", "Try another search or filter.")}</div>`;
        bindEnrollButtons();
    };
    search.addEventListener("input", render);
    filter.addEventListener("change", render);
    render();
}

async function initCourseDetail() {
    const course = await LMS.get(`/courses/${window.STUDENT_COURSE_ID}`);
    qs("#courseDetailRoot").innerHTML = `
        <section class="course-hero card mb-4">
            <div class="course-visual">${course.is_premium ? "PRO" : "FREE"}</div>
            <div class="course-hero-body">
                <span class="badge ${course.is_premium ? "bg-warning text-dark" : "bg-success"}">${course.is_premium ? "Premium" : "Free"}</span>
                <h1>${escapeHtml(course.title)}</h1>
                <p>${escapeHtml(course.description || "No description available.")}</p>
                <div class="meta-pills">
                    <span><i class="bi bi-bar-chart"></i> ${escapeHtml(course.level || "Beginner")}</span>
                    <span><i class="bi bi-clock"></i> ${escapeHtml(course.duration || "0 Hours")}</span>
                    <span><i class="bi bi-currency-rupee"></i> ${money(course.price)}</span>
                </div>
                <button class="btn btn-primary mt-3" data-enroll-course="${course.id}"><i class="bi bi-plus-circle me-2"></i>Enroll Now</button>
            </div>
        </section>
        <div class="card"><div class="card-header">Lessons</div><div class="card-body">${lessonList(course)}</div></div>
    `;
    bindEnrollButtons();
}

async function initMyCourses() {
    const courses = await LMS.get("/my-courses/");
    qs("#myCoursesGrid").innerHTML = courses.map((course) => courseCard(course, true)).join("") || `<div class="col-12">${empty("No enrolled courses", "Enroll from the course marketplace.")}</div>`;
}

async function initLessonPlayer() {
    const [course, enrollments] = await Promise.all([
        LMS.get(`/courses/${window.STUDENT_LESSON_CONTEXT_ID}`),
        LMS.get("/enrollments/me")
    ]);
    const lessons = [...(course.lessons || [])].sort((a, b) => (a.order || 0) - (b.order || 0));
    const enrollmentId = enrollments.find((item) => item.course_id === course.id)?.id || LMS.getEnrollmentMap()[String(course.id)];
    qs("#lessonPlayerRoot").innerHTML = `
        <div class="row g-4">
            <div class="col-xl-8">
                <div class="card player-card">
                    <div class="video-stage" id="videoStage">${renderLesson(lessons[0])}</div>
                    <div class="card-body">
                        <h2>${escapeHtml(course.title)}</h2>
                        <p class="text-muted">${escapeHtml(course.description || "")}</p>
                        <form id="progressForm" class="row g-3 align-items-end">
                            <div class="col-md-6">
                                <label class="form-label">Completed lessons</label>
                                <input class="form-control" type="number" name="completed_lessons" min="0" max="${lessons.length}" value="1">
                            </div>
                            <div class="col-md-6"><button class="btn btn-primary w-100" ${enrollmentId ? "" : "disabled"}>Mark Progress</button></div>
                        </form>
                        ${enrollmentId ? "" : `<p class="text-muted mt-2 mb-0">Progress update is available after enrolling from this browser session.</p>`}
                    </div>
                </div>
            </div>
            <div class="col-xl-4">
                <div class="card"><div class="card-header">Course Lessons</div><div class="card-body lesson-buttons">
                    ${lessons.map((lesson, index) => `<button class="lesson-button ${index === 0 ? "active" : ""}" data-lesson-index="${index}"><span>${index + 1}</span><strong>${escapeHtml(lesson.title)}</strong></button>`).join("") || empty("No lessons", "Instructor has not published lessons yet.")}
                </div></div>
            </div>
        </div>
    `;
    qsa("[data-lesson-index]").forEach((button) => button.addEventListener("click", () => {
        qsa("[data-lesson-index]").forEach((item) => item.classList.remove("active"));
        button.classList.add("active");
        qs("#videoStage").innerHTML = renderLesson(lessons[Number(button.dataset.lessonIndex)]);
    }));
    qs("#progressForm")?.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!enrollmentId) return;
        await LMS.post("/progress/update/", {
            enrollment_id: Number(enrollmentId),
            completed_lessons: Number(new FormData(event.currentTarget).get("completed_lessons")),
        });
        showAlert("Progress updated successfully.", "success");
    });
}

async function initPlans() {
    const plans = await LMS.get("/plans/", false);
    qs("#plansGrid").innerHTML = plans.map(planCard).join("") || `<div class="col-12">${empty("No plans", "Plans will appear when admin creates them.")}</div>`;
    qsa("[data-subscribe-plan]").forEach((button) => button.addEventListener("click", async () => {
        await withButton(button, "Subscribing...", async () => {
            await LMS.post("/subscribe/", { plan_id: Number(button.dataset.subscribePlan) });
            showAlert("Subscription request created. Complete payment to activate course access.", "success");
            setTimeout(() => (window.location.href = routes.subscription), 700);
        });
    }));
}

async function initSubscription() {
    const [subscriptions, plans] = await Promise.all([safe(() => LMS.get("/subscriptions/me"), []), safe(() => LMS.get("/plans/", false), [])]);
    const planMap = Object.fromEntries(plans.map((plan) => [plan.id, plan]));
    qs("#subscriptionList").innerHTML = subscriptions.map((sub) => subscriptionCard(sub, planMap[sub.plan_id])).join("") || empty("No subscription", "Choose a plan to activate subscription access.");
    qsa("[data-pay-subscription]").forEach((button) => button.addEventListener("click", async () => {
        await withButton(button, "Processing...", async () => {
            const payment = await LMS.post(`/payments/pay/${button.dataset.paySubscription}?payment_status=success`, {});
            showAlert(`Payment successful. Invoice ${payment.invoice_number || payment.id} generated.`, "success");
            setTimeout(() => (window.location.href = routes.payments), 900);
        });
    }));
    qsa("[data-renew-subscription]").forEach((button) => button.addEventListener("click", async () => {
        await withButton(button, "Renewing...", async () => {
            await LMS.post(`/subscriptions/renew/${button.dataset.renewSubscription}`, {});
            showAlert("Renewal request created. Complete payment to renew access.", "success");
            initSubscription();
        });
    }));
}

async function initPayments() {
    const payments = await LMS.get("/payments/");
    qs("#paymentsTable").innerHTML = payments.map(paymentRow).join("") || `<tr><td colspan="6">${empty("No payments", "Successful and failed payments will appear here.")}</td></tr>`;
    qsa("[data-download-invoice]").forEach((button) => button.addEventListener("click", async () => {
        await withButton(button, "Downloading...", async () => {
            const blob = await LMS.blob(`/payments/${button.dataset.downloadInvoice}/invoice/`);
            downloadBlob(blob, `invoice-${button.dataset.downloadInvoice}.pdf`);
        });
    }));
}

async function initNotifications() {
    const draw = async () => {
        const notifications = await LMS.get("/notifications/");
        qs("#notificationList").innerHTML = notifications.map(notificationCard).join("") || empty("No notifications", "Your notification center is clear.");
        qsa("[data-mark-read]").forEach((button) => button.addEventListener("click", async () => {
            await LMS.post("/notifications/mark-read/", { notification_ids: [Number(button.dataset.markRead)] });
            draw();
            refreshNotificationBadge();
        }));
        qsa("[data-delete-notification]").forEach(button => button.addEventListener("click", async () => {
            if (!confirm("Delete this notification?")) return;
            await LMS.request(`/notifications/item/${button.dataset.deleteNotification}`, {method: "DELETE"});
            showAlert("Notification deleted.", "success"); await draw(); refreshNotificationBadge();
        }));
    };
    qs("#markAllReadBtn")?.addEventListener("click", async () => {
        await LMS.post("/notifications/mark-all-read/", {});
        showAlert("All notifications marked as read.", "success");
        draw();
        refreshNotificationBadge();
    });
    qs("#clearReadBtn")?.addEventListener("click", async () => {
        if (!confirm("Delete all read notifications?")) return;
        await LMS.request("/notifications/actions/clear-read", {method: "DELETE"});
        showAlert("Read notifications cleared.", "success"); await draw(); refreshNotificationBadge();
    });
    draw();
}

async function initProfile() {
    const profile = await LMS.get("/profile/me");
    LMS.setStoredUser(profile);
    hydrateShell();
    renderProfile(profile);

    qs("#profileForm")?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const updated = await LMS.put("/profile/me", formPayload(event.currentTarget));
        LMS.setStoredUser(updated);
        renderProfile(updated);
        hydrateShell();
        showAlert("Profile updated successfully.", "success");
    });

    qs("#passwordForm")?.addEventListener("submit", async (event) => {
        event.preventDefault();
        await LMS.post("/profile/change-password", formPayload(event.currentTarget));
        event.currentTarget.reset();
        showAlert("Password changed successfully.", "success");
    });

    qs("#pictureForm")?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const file = qs("#profilePictureInput").files[0];
        if (!file) return showAlert("Please choose an image first.", "warning");
        const dataUrl = await readFileAsDataUrl(file);
        const updated = await LMS.post("/profile/profile-picture", { profile_picture: dataUrl });
        LMS.setStoredUser(updated);
        renderProfile(updated);
        hydrateShell();
        showAlert("Profile picture updated.", "success");
    });
}

async function refreshNotificationBadge() {
    if (!LMS.getAccessToken() || isAuthPage()) return;
    const notifications = await safe(() => LMS.get("/notifications/"), []);
    const unread = notifications.filter((item) => !item.is_read).length;
    qsa("[data-unread-count]").forEach((node) => {
        node.textContent = unread;
        node.classList.toggle("d-none", unread === 0);
    });
    const menu = qs("#notificationDropdown");
    if (menu) {
        menu.innerHTML = `
            <li><h6 class="dropdown-header">Notifications</h6></li>
            ${notifications.slice(0, 4).map((item) => `<li><a class="dropdown-item small ${item.is_read ? "" : "fw-bold"}" href="${routes.notifications}">${escapeHtml(item.title || item.notification_type)}<br><span class="text-muted">${escapeHtml(item.message || "")}</span></a></li>`).join("") || `<li><span class="dropdown-item-text text-muted">No notifications</span></li>`}
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item text-center" href="${routes.notifications}">View all notifications</a></li>
        `;
    }
}

let notificationSocket = null;
function connectNotificationSocket() {
    if (!LMS.getAccessToken() || isAuthPage() || notificationSocket) return;
    const api = new URL(LMS.apiBaseUrl);
    const protocol = api.protocol === "https:" ? "wss:" : "ws:";
    notificationSocket = new WebSocket(
        protocol + "//" + api.host + "/ws/notifications?token=" + encodeURIComponent(LMS.getAccessToken())
    );
    notificationSocket.onmessage = async (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.event !== "notification") return;
            await refreshNotificationBadge();
            if (pageId() === "chat") return;
            let toast = qs("#instantMessageToast");
            if (!toast) {
                document.body.insertAdjacentHTML("beforeend",
                    '<div id="instantMessageToast" class="position-fixed bottom-0 end-0 m-4 alert alert-primary shadow-lg" style="z-index:1080;max-width:360px"></div>');
                toast = qs("#instantMessageToast");
            }
            toast.innerHTML = '<strong>' + escapeHtml(data.title || "New message") + '</strong><br>' +
                escapeHtml(data.message || "") +
                '<br><a class="alert-link" href="' + (routes.chat || "/student/chat/") + '">Open conversation</a>';
            toast.classList.remove("d-none");
            setTimeout(() => toast?.classList.add("d-none"), 7000);
        } catch (_) {}
    };
    notificationSocket.onclose = () => {
        notificationSocket = null;
        if (LMS.getAccessToken() && !isAuthPage()) setTimeout(connectNotificationSocket, 3000);
    };
}

function renderProfile(profile) {
    setText("#profileName", profile.name);
    setText("#profileEmail", profile.email);
    setText("#profileRole", profile.role);
    qs("#profileNameInput").value = profile.name || "";
    qs("#profileEmailInput").value = profile.email || "";
    const photo = qs("#profilePhoto");
    if (profile.profile_picture) photo.innerHTML = `<img src="${escapeHtml(profile.profile_picture)}" alt="Profile">`;
    else photo.textContent = (profile.name || profile.email || "S").slice(0, 1).toUpperCase();
}

function bindEnrollButtons() {
    qsa("[data-enroll-course]").forEach((button) => button.addEventListener("click", async () => {
        await withButton(button, "Enrolling...", async () => {
            const enrollment = await LMS.post("/enroll/", { course_id: Number(button.dataset.enrollCourse) });
            LMS.saveEnrollment(button.dataset.enrollCourse, enrollment.id);
            showAlert("Enrollment successful. Course added to My Courses.", "success");
        });
    }));
}

function courseCard(course, enrolled = false) {
    return `
        <div class="col-md-6 col-xl-4">
            <article class="course-card card h-100">
                <div class="course-thumb ${course.is_premium ? "premium" : ""}"><span>${course.is_premium ? "PRO" : "FREE"}</span></div>
                <div class="card-body d-flex flex-column">
                    <div class="d-flex justify-content-between gap-2 mb-2">
                        <h5 class="mb-0">${escapeHtml(course.title)}</h5>
                        <span class="badge ${course.is_premium ? "bg-warning text-dark" : "bg-success"}">${course.is_premium ? "Premium" : "Free"}</span>
                    </div>
                    <p class="text-muted flex-grow-1">${escapeHtml(course.description || "No description available.")}</p>
                    <div class="meta-pills mb-3">
                        <span>${escapeHtml(course.level || "Beginner")}</span>
                        <span>${escapeHtml(course.duration || "0 Hours")}</span>
                        <span>${money(course.price)}</span>
                    </div>
                    <div class="d-flex gap-2">
                        <a class="btn btn-outline-primary flex-fill" href="/student/course/${course.id}/">Details</a>
                        ${enrolled ? `<a class="btn btn-primary flex-fill" href="/student/lesson/${course.id}/">Continue</a>` : `<button class="btn btn-primary flex-fill" data-enroll-course="${course.id}">Enroll</button>`}
                    </div>
                </div>
            </article>
        </div>
    `;
}

function continueCourse(course, progress) {
    const percent = Number(progress?.progress_percent || 0);
    return `
        <div class="continue-card">
            <div>
                <h4>${escapeHtml(course.title)}</h4>
                <p class="text-muted mb-2">${escapeHtml(course.description || "")}</p>
                <div class="progress"><div class="progress-bar" style="width:${percent}%"></div></div>
                <small>${percent}% complete</small>
            </div>
            <a class="btn btn-primary" href="/student/lesson/${course.id}/">Continue</a>
        </div>
    `;
}

function lessonList(course) {
    const lessons = [...(course.lessons || [])].sort((a, b) => (a.order || 0) - (b.order || 0));
    return lessons.map((lesson, index) => `
        <div class="lesson-row">
            <span>${String(index + 1).padStart(2, "0")}</span>
            <div><strong>${escapeHtml(lesson.title)}</strong><p>${escapeHtml(lesson.content || "")}</p></div>
        </div>
    `).join("") || empty("No lessons", "Lessons will appear after admin/instructor publishes them.");
}

function toEmbeddableUrl(rawUrl) {
    const url = String(rawUrl || "").trim();
    if (!url) return null;

    let parsed;
    try {
        parsed = new URL(url);
    } catch {
        return null;
    }

    const host = parsed.hostname.replace(/^www\./i, "").toLowerCase();

    // Already an embed-style URL - use as-is.
    if (/^(m\.)?youtube\.com$/i.test(host) && parsed.pathname.startsWith("/embed/")) {
        return url;
    }
    if (/^player\.vimeo\.com$/i.test(host)) {
        return url;
    }

    // youtube.com/watch?v=ID
    if (/^(m\.)?youtube\.com$/i.test(host) && parsed.pathname === "/watch" && parsed.searchParams.get("v")) {
        return `https://www.youtube.com/embed/${encodeURIComponent(parsed.searchParams.get("v"))}`;
    }

    // youtube.com/shorts/ID or /live/ID
    if (/^(m\.)?youtube\.com$/i.test(host)) {
        const match = parsed.pathname.match(/^\/(shorts|live)\/([^/?#]+)/i);
        if (match) return `https://www.youtube.com/embed/${encodeURIComponent(match[2])}`;
    }

    // youtu.be/ID
    if (/^youtu\.be$/i.test(host)) {
        const id = parsed.pathname.replace(/^\//, "").split("/")[0];
        if (id) return `https://www.youtube.com/embed/${encodeURIComponent(id)}`;
    }

    // vimeo.com/ID
    if (/^vimeo\.com$/i.test(host)) {
        const id = parsed.pathname.replace(/^\//, "").split("/")[0];
        if (/^\d+$/.test(id)) return `https://player.vimeo.com/video/${encodeURIComponent(id)}`;
    }

    return null;
}

function renderLesson(lesson) {
    if (!lesson) return empty("No lesson selected", "This course does not have lessons yet.");
    const url = lesson.video_url || "";
    const embedUrl = toEmbeddableUrl(url);
    return `
        <div class="video-inner">
            ${embedUrl ? `<iframe src="${escapeHtml(embedUrl)}" title="${escapeHtml(lesson.title)}" referrerpolicy="strict-origin-when-cross-origin" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>` : `<i class="bi bi-play-btn-fill"></i>`}
            <h3>${escapeHtml(lesson.title)}</h3>
            <p>${escapeHtml(lesson.content || "")}</p>
            ${url && !embedUrl ? `<a class="btn btn-light" href="${escapeHtml(url)}" target="_blank" rel="noopener">Open Video</a>` : ""}
        </div>
    `;
}

function planCard(plan) {
    return `
        <div class="col-md-6 col-xl-4">
            <article class="plan-card card h-100">
                <div class="card-body">
                    <span class="section-kicker">${plan.duration_days} days access</span>
                    <h3>${escapeHtml(plan.name)}</h3>
                    <p class="text-muted">${escapeHtml(plan.description || "Premium learning membership.")}</p>
                    <div class="plan-price">${money(plan.price)}</div>
                    <button class="btn btn-primary w-100 mt-3" data-subscribe-plan="${plan.id}">Subscribe</button>
                </div>
            </article>
        </div>
    `;
}

function subscriptionCard(sub, plan) {
    const isPending = sub.status === "pending";
    const isActive = sub.status === "active";
    return `
        <article class="card subscription-card">
            <div class="card-body d-flex flex-wrap justify-content-between align-items-center gap-3">
                <div>
                    <span class="badge bg-${sub.status === "active" ? "success" : "secondary"}">${escapeHtml(sub.status)}</span>
                    <h4 class="mt-2 mb-1">${escapeHtml(plan?.name || "Subscription plan")}</h4>
                    <p class="text-muted mb-0">${formatDate(sub.start_date)} to ${formatDate(sub.end_date)} ${sub.auto_renew ? "• Auto renew enabled" : ""}</p>
                </div>
                <div class="d-flex gap-2">
                    ${isPending ? `<button class="btn btn-primary" data-pay-subscription="${sub.id}"><i class="bi bi-credit-card me-2"></i>Complete Payment</button>` : ""}
                    ${isActive ? `<button class="btn btn-outline-primary" data-renew-subscription="${sub.id}"><i class="bi bi-arrow-repeat me-2"></i>Renew</button>` : ""}
                </div>
            </div>
        </article>
    `;
}

function paymentRow(payment) {
    const status = String(payment.payment_status || "").toLowerCase();
    return `
        <tr>
            <td><strong>${escapeHtml(payment.invoice_number || `PAY-${payment.id}`)}</strong><br><small class="text-muted">${escapeHtml(payment.transaction_id || "-")}</small></td>
            <td>${money(payment.amount)}</td>
            <td><span class="badge bg-${status === "paid" || status === "success" ? "success" : "danger"}">${escapeHtml(payment.payment_status)}</span></td>
            <td>${escapeHtml(payment.payment_method || "Card")}</td>
            <td>${formatDate(payment.paid_at)}</td>
            <td class="text-end"><button class="btn btn-sm btn-outline-primary" data-download-invoice="${payment.id}"><i class="bi bi-download me-1"></i>Invoice</button></td>
        </tr>
    `;
}

function notificationCard(item) {
    return `
        <article class="card notification-card ${item.is_read ? "" : "unread"}">
            <div class="card-body d-flex gap-3 align-items-start">
                <div class="notification-icon"><i class="bi ${escapeHtml(item.icon || "bi-bell")}"></i></div>
                <div class="flex-grow-1">
                    <h5>${escapeHtml(item.title || item.notification_type)}</h5>
                    <p class="text-muted mb-1">${escapeHtml(item.message || "")}</p>
                    <small>${formatDate(item.created_at)}</small>
                </div>
                <div class="d-flex gap-2"><a class="btn btn-sm btn-outline-primary" href="${escapeHtml(item.link || "#")}">View</a><button class="btn btn-sm btn-outline-danger" data-delete-notification="${item.id}"><i class="bi bi-trash3"></i></button></div>
            </div>
        </article>
    `;
}

function notificationMini(item) {
    return `<div class="mini-row ${item.is_read ? "" : "strong"}"><strong>${escapeHtml(item.title || item.notification_type)}</strong><span>${formatDate(item.created_at)}</span></div>`;
}

function activityMini(item) {
    return `<div class="mini-row"><strong>${escapeHtml(item.action_type)}</strong><span>${escapeHtml(item.action_detail || "")}</span></div>`;
}

function qs(selector, root = document) {
    return root.querySelector(selector);
}

function qsa(selector, root = document) {
    return Array.from(root.querySelectorAll(selector));
}

function setText(selector, value) {
    const node = qs(selector);
    if (node) node.textContent = value;
}

function formPayload(form) {
    return Object.fromEntries(new FormData(form).entries());
}

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function money(value) {
    const number = Number(value || 0);
    return `Rs. ${number.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatDate(value) {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "-";
    return date.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

function empty(title, text) {
    return `<div class="empty-state"><strong>${escapeHtml(title)}</strong><span>${escapeHtml(text)}</span></div>`;
}

async function safe(fn, fallback) {
    try {
        return await fn();
    } catch {
        return fallback;
    }
}

async function withButton(button, label, task) {
    const old = button?.innerHTML;
    try {
        if (button) {
            button.disabled = true;
            button.textContent = label;
        }
        await task();
    } catch (error) {
        showAlert(error.message || "Request failed", "danger");
    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = old;
        }
    }
}

function showAlert(message, type = "info") {
    const alert = qs("#pageAlert");
    if (!alert) return window.alert(message);
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    alert.classList.remove("d-none");
    setTimeout(() => alert.classList.add("d-none"), 2500);
}

function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
}

function readFileAsDataUrl(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}
