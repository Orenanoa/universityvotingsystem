from django.contrib import admin
from django.urls import path

from voting import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Public / voter
    path('', views.home, name='home'),
    path('elections/', views.elections_list, name='elections'),
    path('elections/<int:pk>/', views.election_detail, name='election_detail'),
    path('elections/<int:pk>/ballot/', views.ballot, name='ballot'),
    path('elections/<int:pk>/results/', views.results, name='results'),

    # Auth
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),

    # Staff CRUD: elections
    path('manage/elections/', views.manage_elections, name='manage_elections'),
    path('manage/elections/new/', views.election_create, name='election_create'),
    path('manage/elections/<int:pk>/edit/', views.election_update, name='election_update'),
    path('manage/elections/<int:pk>/delete/', views.election_delete, name='election_delete'),
    path('manage/elections/<int:election_pk>/positions/', views.manage_positions, name='manage_positions'),
    path('manage/elections/<int:election_pk>/positions/new/', views.position_create, name='position_create'),

    # Staff CRUD: positions
    path('manage/positions/<int:pk>/edit/', views.position_update, name='position_update'),
    path('manage/positions/<int:pk>/delete/', views.position_delete, name='position_delete'),

    # Staff CRUD: candidates
    path('manage/positions/<int:position_pk>/candidates/new/', views.candidate_create, name='candidate_create'),
    path('manage/candidates/<int:pk>/edit/', views.candidate_update, name='candidate_update'),
    path('manage/candidates/<int:pk>/delete/', views.candidate_delete, name='candidate_delete'),

    # Staff CRUD: voters
    path('manage/voters/', views.manage_voters, name='manage_voters'),
    path('manage/voters/new/', views.voter_create, name='voter_create'),
    path('manage/voters/<int:pk>/edit/', views.voter_update, name='voter_update'),
    path('manage/voters/<int:pk>/delete/', views.voter_delete, name='voter_delete'),
    path('manage/voters/<int:pk>/toggle-verify/', views.voter_toggle_verify, name='voter_toggle_verify'),
]
