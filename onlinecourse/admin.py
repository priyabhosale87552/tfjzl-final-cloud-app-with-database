from django.contrib import admin

from .models import Choice, Course, Enrollment, Instructor, Lesson, Question, Submission


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("prompt", "lesson", "order")
    list_filter = ("lesson__course",)
    inlines = (ChoiceInline,)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)
    inlines = (QuestionInline,)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


admin.site.register(Choice)
admin.site.register(Enrollment)
admin.site.register(Instructor)
admin.site.register(Submission)
