from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from .models import Election, Position, Candidate, VoterProfile, Vote


class PositionInline(admin.TabularInline):
    model = Position
    extra = 1


class CandidateInline(admin.TabularInline):
    model = Candidate
    extra = 1


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'starts_at', 'ends_at', 'published', 'position_count']
    list_filter = ['published']
    search_fields = ['name']
    inlines = [PositionInline]

    def position_count(self, obj):
        return obj.positions.count()
    position_count.short_description = 'Positions'


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['title', 'election', 'order', 'candidate_count']
    list_filter = ['election']
    inlines = [CandidateInline]

    def candidate_count(self, obj):
        return obj.candidates.count()
    candidate_count.short_description = 'Candidates'


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'vote_count']
    list_filter = ['position__election']
    search_fields = ['name']


class VoterProfileInline(admin.StackedInline):
    model = VoterProfile
    can_delete = False
    verbose_name_plural = 'Voter profile'


class CustomUserAdmin(UserAdmin):
    inlines = [VoterProfileInline]
    list_display = UserAdmin.list_display + ('student_id',)

    def student_id(self, obj):
        profile = getattr(obj, 'voter_profile', None)
        return profile.student_id if profile else '-'
    student_id.short_description = 'Student ID'


@admin.register(VoterProfile)
class VoterProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'student_id', 'department', 'gender', 'year_of_study', 'session', 'is_verified']
    list_filter = ['is_verified', 'department']
    search_fields = ['user__username', 'student_id']


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['voter', 'position', 'candidate', 'cast_at']
    list_filter = ['position__election', 'position']
    search_fields = ['voter__username']
    readonly_fields = ['cast_at']


# Replace the default User admin with our extended one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
