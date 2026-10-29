from django.contrib import admin

from .models import Choice, Course, Instructor, Learner, Lesson, Question, Submission


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ("question_text", "course", "grade", "order")


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("question_text", "course", "grade", "lesson", "order")
    list_filter = ("course",)
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
admin.site.register(Instructor)
admin.site.register(Learner)
admin.site.register(Submission)
