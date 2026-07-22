# Deep Production Audit — Issues and Implementation Checklist

Date: 22 July 2026

This checklist records the issues found before the final implementation and verification pass. Working invoice and migration fixes are intentionally preserved.

## Critical blockers

- [ ] Instructor features are mixed into the student portal; create a separate instructor portal and enforce role-based routing.
- [ ] Demo accounts use non-public `.local` addresses, which fail FastAPI `EmailStr` validation; replace them with realistic Gmail demo accounts.
- [ ] Public registration accepts a client-supplied instructor role; public registration must always create students.
- [ ] Subscription is activated before payment succeeds; use a pending state and activate access only after successful payment.
- [ ] Subscription, payment, registration, login, and chat events do not consistently notify both the affected user and administrators.
- [ ] Seed lessons use placeholder `example.com` video URLs; use valid demo videos and verify YouTube URL conversion/player behavior.

## Authentication and authorization

- [ ] Require normalized `@gmail.com` addresses for login, registration, and profile email changes.
- [ ] Return clear validation messages instead of the generic “Validation failed”.
- [ ] Prevent students from entering instructor pages and instructors/admins from entering student pages.
- [ ] Add separate admin, instructor, and student dashboard entry points.
- [ ] Add login activity/notification records without exposing passwords or tokens.
- [ ] Ensure disabled users cannot authenticate.

## Student workflows

- [ ] Verify registration, login, logout, profile update, and password change.
- [ ] Verify course catalogue, enrolment, premium access, lesson playback, and progress.
- [ ] Verify plans, pending subscription, successful/failed payment, activation, history, and PDF invoice.
- [ ] Verify attendance, assignment submission, grading visibility, chat, and notifications.
- [ ] Ensure responsive empty, loading, validation, unauthorized, and server-error states.

## Instructor workflows

- [ ] Add instructor login and dashboard.
- [ ] Add own-course visibility and lesson/video management.
- [ ] Add enrolled-student visibility.
- [ ] Add assignment creation, submission review, grading, and notifications.
- [ ] Add attendance marking/reporting with ownership and enrolment validation.
- [ ] Add instructor chat and notification pages.

## Notifications and messaging

- [ ] Notify administrators of new registration, login, subscription request, successful/failed payment, and relevant chat activity.
- [ ] Notify students of subscription/payment, attendance, assignment, grade, login/security, and messages.
- [ ] Avoid duplicate notifications and use portal-correct links.
- [ ] Verify real-time chat delivery and notification refresh behavior.
- [ ] Validate chat membership and uploaded file type/size securely.

## Data and demo quality

- [ ] Replace synthetic local-domain identities with realistic names and Gmail addresses.
- [ ] Keep seed operation idempotent and ensure known demo passwords are refreshed.
- [ ] Include realistic courses, lessons, plans, subscriptions, payments, attendance, assignments, and chat data.
- [ ] Document exact demo credentials and record counts.

## Production and delivery quality

- [ ] Remove fixed Docker container names to prevent conflicts between copies.
- [ ] Keep secrets configurable through environment variables and exclude real secrets from the ZIP.
- [ ] Add Docker ignore rules for caches, local environments, uploads, and generated files.
- [ ] Verify Django checks, migrations, FastAPI startup/OpenAPI, tests, and Docker health.
- [ ] Execute browser-based role and workflow smoke tests.
- [ ] Update README, requirement checklist, Postman collections, and final audit report.
- [ ] Build a clean final ZIP and verify its contents and checksum.

