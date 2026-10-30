from django.urls import path
from . import views

urlpatterns = [
    # Dashboard & Auth
    path("", views.dashboard_view, name="dashboard"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Projects CRUD
    path("projects/", views.project_list_view, name="project_list"),
    path("projects/create/", views.project_create_view, name="project_create"),
    path("projects/<int:pk>/", views.project_detail_view, name="project_detail"),
    path("projects/<int:pk>/edit/", views.project_update_view, name="project_update"),
    path("projects/<int:pk>/delete/", views.project_delete_view, name="project_delete"),

    # Tasks CRUD
    path("projects/<int:project_pk>/tasks/create/", views.task_create_view, name="task_create"),
    path("tasks/", views.task_list_view, name="task_list"),
    path("tasks/<int:pk>/", views.task_detail_view, name="task_detail"),
    path("tasks/<int:pk>/edit/", views.task_update_view, name="task_update"),
    path("tasks/<int:pk>/delete/", views.task_delete_view, name="task_delete"),
    path("tasks/<int:pk>/status/", views.task_update_status_quick_view, name="task_quick_status"),
    path("tasks/<int:pk>/timelog/", views.task_add_timelog_view, name="task_add_timelog"),
]