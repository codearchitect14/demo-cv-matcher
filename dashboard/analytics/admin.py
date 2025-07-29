from django.contrib import admin
from django.db.models import Count, Q
from .models import Candidate, Job, Application, InteractionLog

# --- Custom Filters ---

class ZeroApplicantsFilter(admin.SimpleListFilter):
    title = 'Zero Applicants'
    parameter_name = 'zero_applicants'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Jobs with zero applicants'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.annotate(applicant_count=Count('application')).filter(applicant_count=0)
        return queryset

class ZeroVisibilityFilter(admin.SimpleListFilter):
    title = 'Zero Visibility'
    parameter_name = 'zero_visibility'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Candidates with zero visibility'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.annotate(vis_count=Count('interactionlog')).filter(vis_count=0)
        return queryset

# --- Job Admin ---

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'company', 'location', 'domain', 'applicant_count', 'view_count')
    search_fields = ('title', 'company', 'location', 'domain')
    list_filter = (ZeroApplicantsFilter,)

    def applicant_count(self, obj):
        return Application.objects.filter(job=obj).count()
    applicant_count.short_description = 'Applicants'

    def view_count(self, obj):
        return InteractionLog.objects.filter(job=obj, interaction_type='viewed').count()
    view_count.short_description = 'Views'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(applicant_count=Count('application'))

# --- Candidate Admin ---

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'location', 'domain', 'visibility_count')
    search_fields = ('name', 'location', 'domain')
    list_filter = (ZeroVisibilityFilter,)

    def visibility_count(self, obj):
        return InteractionLog.objects.filter(user=obj).count()
    visibility_count.short_description = 'Visibility Events'

# --- Application Admin ---

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'candidate', 'status')
    list_filter = ('status',)
    search_fields = ('job__title', 'candidate__name')

# --- InteractionLog Admin ---

@admin.register(InteractionLog)
class InteractionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'job', 'interaction_type', 'timestamp')
    list_filter = ('interaction_type',)
    search_fields = ('user__name', 'job__title')

# --- Custom Admin Actions/Reports ---

# Top viewed jobs with low applications
@admin.action(description='Show top viewed jobs with low applications')
def top_viewed_low_applications(modeladmin, request, queryset):
    jobs = queryset.annotate(
        views=Count('interactionlog', filter=Q(interactionlog__interaction_type='viewed')),
        applications=Count('application')
    ).filter(views__gt=10, applications__lt=3)
    # You can export or display jobs as needed
    for job in jobs:
        print(f"{job.title}: {job.views} views, {job.applications} applications")

JobAdmin.actions = [top_viewed_low_applications]

# --- Skill Demand vs Availability (for manual export or further charting) ---

def skill_demand_vs_supply():
    from .models import JobMandatorySkill, CandidateExperience
    demand = JobMandatorySkill.objects.values('skill').annotate(demand=Count('id')).order_by('-demand')
    supply = CandidateExperience.objects.values('skill').annotate(supply=Count('id')).order_by('-supply')
    # Combine and return as needed for charting
    return list(demand), list(supply)