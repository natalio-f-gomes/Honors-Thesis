# UserInterface/urls.py

from django.urls import path, re_path
from django.views.generic import TemplateView
from . import views
from UserAuth import views as UserAuthViews
from Scanner import views as ScannerViews
from Evaluator import views as EvaluatorViews

urlpatterns = [

    path('', views.index, name='home'),
    path('about-us', views.about_us, name='about'),
    path('feedback_page', views.feedback_page, name='feedback_page'),
    path('feedback/<int:user_id>/', views.feedback, name='feedback'),
    path('terms_and_conditions', views.terms_and_conditions, name='terms_and_conditions'),
    path('contact_page', views.contact_page, name='contact_page'),
    path('contact_function', views.contact_function, name='contact_function'),
    path('page-not-found/', views.custom_error_404, name='page_not_found'),


    # AUTHENTICATION & USER ACCOUNT MANAGEMENT (UserAuth App)
    path('login', views.login_page, name='login'),
    path('register', views.register_page, name='register'),
    path('register_user/', UserAuthViews.register_user, name='register_user'),
    path('sign_in/', UserAuthViews.sign_in_user, name='sign_in_user'),
    path('logout/', UserAuthViews.sign_out_user, name='logout'),

    # User Account Pages
    path('user-account/<int:user_id>', views.user_account, name='user-account'),
    path('update_account_page<str:username>', UserAuthViews.update_account_page, name='update_account_page'),
    path('update_account_info/<int:user_id>', UserAuthViews.update_account_info, name='update_account_info'),

    # Password Reset (for authenticated uses with current password)
    path('reset-password-page/<int:user_id>', views.reset_password_page, name='reset_password_page'),
    path('reset_password/<int:user_id>', UserAuthViews.reset_password, name='reset_password'),


    path(
        'forgot-password/',
        UserAuthViews.PasswordResetRequestView.as_view(),
        name='password_reset_request'
    ),
    re_path(
        r'^reset-password-confirm/(?P<token>[A-Za-z0-9_\-=]+)/$',
        UserAuthViews.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),

    # Account Deletion
    path('confirm_delete_account/', UserAuthViews.confirm_delete_account, name='confirm_delete_account'),

    # Legacy URLs for backward compatibility
    path('delete_account/<int:user_id>', UserAuthViews.delete_account_legacy, name='delete_account'),
    path('confirm_deletion/<str:username>', UserAuthViews.confirm_deletion_legacy, name='confirm_deletion'),

    path('resume_upload/<str:username>/', ScannerViews.resume_upload_page, name='resume_upload_page'),
    path('resume_file_upload/<str:username>', ScannerViews.resume_file_upload, name='resume_file_upload'),
    path('resume_detail/<str:username>/<int:resume_id>', ScannerViews.resume_detail_page, name='resume_detail_page'),


    path(
        'jobs_matched_from_resume_file_page/<str:username>/<int:resume_id>',
        EvaluatorViews.jobs_matched_page_from_resume_file,
        name='jobs_matched_from_resume_file'
    ),
    path(
        'recommendation/<str:username>/<int:resume_id>',
        EvaluatorViews.recommendation_skills_page,
        name='recommendation_skills'
    ),
    
    path('password-reset/', UserAuthViews.PasswordResetRequestView.as_view()),
    path('password-recovery/', UserAuthViews.PasswordResetRequestView.as_view()),
    path('password/reset/', UserAuthViews.PasswordResetRequestView.as_view()),
]

