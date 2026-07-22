"""
courses/views.py

Course Management: add/edit/delete courses and lessons (task spec).
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CourseForm, LessonForm
from .models import Course, Lesson


@login_required
def course_list(request):
    courses = (
        Course.objects.select_related("instructor")
        .annotate(lesson_count=Count("lessons", distinct=True), enrollment_count=Count("enrollments", distinct=True))
        .all()
    )
    return render(request, "courses/course_list.html", {"courses": courses})


@login_required
def course_create(request):
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save()
            messages.success(request, "Course created successfully.")
            return redirect("courses:course_detail", pk=course.pk)
    else:
        form = CourseForm()
    return render(request, "courses/course_form.html", {"form": form, "title": "Add Course"})


@login_required
def course_detail(request, pk):
    """Shows a course with its lessons - the hub for lesson management."""
    course = get_object_or_404(Course.objects.select_related("instructor"), pk=pk)
    lessons = course.lessons.all()
    return render(request, "courses/course_detail.html", {"course": course, "lessons": lessons})


@login_required
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == "POST":
        form = CourseForm(
            request.POST,
            request.FILES,
            instance=course,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated successfully.")
            return redirect("courses:course_detail", pk=course.pk)
    else:
        form = CourseForm(instance=course)
    return render(request, "courses/course_form.html", {"form": form, "title": "Edit Course"})


@login_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == "POST":
        course.delete()
        messages.success(request, "Course deleted.")
        return redirect("courses:course_list")
    return render(request, "courses/course_confirm_delete.html", {"course": course})


@login_required
def lesson_create(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)
    if request.method == "POST":
        form = LessonForm(
            request.POST,
            request.FILES,
        )
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            messages.success(request, "Lesson added.")
            return redirect("courses:course_detail", pk=course.pk)
    else:
        form = LessonForm()
    return render(request, "courses/lesson_form.html", {"form": form, "course": course, "title": "Add Lesson"})


@login_required
def lesson_edit(request, course_pk, pk):
    course = get_object_or_404(Course, pk=course_pk)
    lesson = get_object_or_404(Lesson, pk=pk, course=course)
    if request.method == "POST":
        form = LessonForm(
            request.POST,
            request.FILES,
            instance=lesson,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Lesson updated.")
            return redirect("courses:course_detail", pk=course.pk)
    else:
        form = LessonForm(instance=lesson)
    return render(request, "courses/lesson_form.html", {"form": form, "course": course, "title": "Edit Lesson"})


@login_required
def lesson_delete(request, course_pk, pk):
    course = get_object_or_404(Course, pk=course_pk)
    lesson = get_object_or_404(Lesson, pk=pk, course=course)
    if request.method == "POST":
        lesson.delete()
        messages.success(request, "Lesson deleted.")
        return redirect("courses:course_detail", pk=course.pk)
    return render(request, "courses/lesson_confirm_delete.html", {"lesson": lesson, "course": course})
