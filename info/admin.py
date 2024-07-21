from datetime import timedelta, datetime

from import_export.admin import ImportExportModelAdmin
from import_export import resources,widgets

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseRedirect
from django.urls import path

from .models import Dept, Class, Student, Attendance, Course, Teacher, Assign, AssignTime, AttendanceClass
from .models import StudentCourse, Marks, User, AttendanceRange

# Register your models here.

days = {
    'Monday': 1,
    'Tuesday': 2,
    'Wednesday': 3,
    'Thursday': 4,
    'Friday': 5,
    'Saturday': 6,
}


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


class ClassInline(admin.TabularInline):
    model = Class
    extra = 0


class DeptAdmin(admin.ModelAdmin):
    inlines = [ClassInline]
    list_display = ('name', 'id')
    search_fields = ('name', 'id')
    ordering = ['name']


class StudentInline(admin.TabularInline):
    model = Student
    extra = 0


class ClassAdmin(admin.ModelAdmin):
    list_display = ('id', 'dept', 'sem', 'section')
    search_fields = ('id', 'dept__name', 'sem', 'section')
    ordering = ['dept__name', 'sem', 'section']
    inlines = [StudentInline]


class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'dept')
    search_fields = ('id', 'name', 'dept__name')
    ordering = ['dept', 'id']


class AssignTimeInline(admin.TabularInline):
    model = AssignTime
    extra = 0


class AssignAdmin(admin.ModelAdmin):
    inlines = [AssignTimeInline]
    list_display = ('class_id', 'course', 'teacher')
    search_fields = ('class_id__dept__name', 'class_id__id', 'course__name', 'teacher__name', 'course__shortname')
    ordering = ['class_id__dept__name', 'class_id__id', 'course__id']
    raw_id_fields = ['class_id', 'course', 'teacher']


class MarksInline(admin.TabularInline):
    model = Marks
    extra = 0


class StudentCourseAdmin(admin.ModelAdmin):
    inlines = [MarksInline]
    list_display = ('student', 'course',)
    search_fields = ('student__name', 'course__name', 'student__class_id__id', 'student__class_id__dept__name')
    ordering = ('student__class_id__dept__name', 'student__class_id__id', 'student__USN')


class StudentAdmin(admin.ModelAdmin):
    list_display = ('USN', 'name', 'class_id')
    search_fields = ('USN', 'name', 'class_id__id', 'class_id__dept__name')
    ordering = ['class_id__dept__name', 'class_id__id', 'USN']


class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'dept')
    search_fields = ('name', 'dept__name')
    ordering = ['dept__name', 'name']

class AttendanceRangeAdmin(admin.ModelAdmin):
    list_display = ('start_date', 'end_date')
    search_fields = ('start_date', 'end_date')
    ordering = ['start_date', 'end_date']

class AttendanceClassAdmin(admin.ModelAdmin):
    list_display = ('assign', 'date', 'status')
    ordering = ['assign', 'date']
    change_list_template = 'admin/attendance/attendance_change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('reset_attd/', self.reset_attd, name='reset_attd'),
        ]
        return my_urls + urls

    def reset_attd(self, request):

        start_date = datetime.strptime(request.POST['startdate'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.POST['enddate'], '%Y-%m-%d').date()

        try:
            a = AttendanceRange.objects.all()[:1].get()
            a.start_date = start_date
            a.end_date = end_date
            a.save()
        except AttendanceRange.DoesNotExist:
            a = AttendanceRange(start_date=start_date, end_date=end_date)
            a.save()

        Attendance.objects.all().delete()
        AttendanceClass.objects.all().delete()
        for asst in AssignTime.objects.all():
            for single_date in daterange(start_date, end_date):
                if single_date.isoweekday() == days[asst.day]:
                    try:
                        AttendanceClass.objects.get(date=single_date.strftime("%Y-%m-%d"), assign=asst.assign)
                    except AttendanceClass.DoesNotExist:
                        a = AttendanceClass(date=single_date.strftime("%Y-%m-%d"), assign=asst.assign)
                        a.save()

        self.message_user(request, "Attendance Dates reset successfully!")
        return HttpResponseRedirect("../")

# Classes to bulk add users, teachers and students!

class CourseResource(resources.ModelResource):

    class Meta:
        model = Course
        #exclude = ('id',)
        #import_id_fields = ['user']
        fields = ('id', 'dept', 'name', 'shortname',)

class CourseAdminBulk(CourseAdmin,ImportExportModelAdmin,admin.ModelAdmin):
    resource_class = CourseResource

    class Meta:
        model = Course

class ClassResource(resources.ModelResource):

    class Meta:
        model = Class
        #exclude = ('id',)
        #import_id_fields = ['user']
        fields = ('id', 'dept', 'sem', 'section',)

class ClassAdminBulk(ClassAdmin,ImportExportModelAdmin,admin.ModelAdmin):
    resource_class = ClassResource

    class Meta:
        model = Class

class DeptResource(resources.ModelResource):

    class Meta:
        model = Dept
        #exclude = ('id',)
        #import_id_fields = ['user']
        fields = ('id','name',)

class DeptAdminBulk(DeptAdmin,ImportExportModelAdmin,admin.ModelAdmin):
    resource_class = DeptResource

    class Meta:
        model = Dept

class TeacherResource(resources.ModelResource):

    class Meta:
        model = Teacher
        #exclude = ('id',)
        #import_id_fields = ['user']
        fields = ('user','id','dept','name','sex',)

class TeacherAdminBulk(TeacherAdmin,ImportExportModelAdmin,admin.ModelAdmin):
    resource_class = TeacherResource

    class Meta:
        model = Teacher

class StudentResource(resources.ModelResource):

    class Meta:
        model = Student
        exclude = ('id',)
        import_id_fields = ['user']
        fields = ('user','class_id','USN','name','sex',)

class StudentAdminBulk(StudentAdmin,ImportExportModelAdmin,admin.ModelAdmin):
    resource_class = StudentResource

    class Meta:
        model = Student

class UserResource(resources.ModelResource):

    class Meta:
        model = User
        fields = ('id','username','password','first_name', 'last_name', 'email')

    def import_obj(self, obj, data, dry_run):
        plain_text_password = data.get('password')
        hashed_password = make_password(plain_text_password)
        for field in self.get_fields():
            if isinstance(field.widget, widgets.ManyToManyWidget):
                continue
            if field.column_name == 'password':
                data.update({'password': hashed_password})

            self.import_field(field, obj, data)

class UserAdminBulk(UserAdmin,ImportExportModelAdmin,admin.ModelAdmin):
    resource_class = UserResource
    class Meta:
        model = User

admin.site.register(User,UserAdminBulk)
admin.site.register(Dept, DeptAdminBulk)
admin.site.register(Class, ClassAdminBulk)
admin.site.register(Student, StudentAdminBulk)
admin.site.register(Course, CourseAdminBulk)
admin.site.register(Teacher, TeacherAdminBulk)
admin.site.register(Assign, AssignAdmin)
admin.site.register(StudentCourse, StudentCourseAdmin)
admin.site.register(AttendanceClass, AttendanceClassAdmin)
admin.site.register(AttendanceRange, AttendanceRangeAdmin)
