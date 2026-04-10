from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.SignUpView.as_view()),
    path('verify/', views.CodeVerifyView.as_view()),
    path('verify/new-code/', views.GetNewCodeView.as_view()),
    path('change-info/', views.UserChangeInfoView.as_view()),
    path('change-photo/', views.UserPhotoChangeView.as_view()),
    path('login/', views.LoginView.as_view()),
    path('logout/', views.LogoutView.as_view()),
    path('login/refresh/', views.LoginRefreshView.as_view()),
    path('profile/', views.ProfileView.as_view()),
    path('profile/update/', views.UpdatePofileView.as_view()),
    path('profile/change-password/', views.ChangePasswordView.as_view()),
    path('password/reset/', views.ResetPasswordRequestView.as_view()),
    path('password/reset/confirm/', views.ResetPasswordConfirmView.as_view()),
    path('cards/', views.CardListCreateView.as_view()),
    path('cards/<int:pk>/', views.CardDetailView.as_view()),
    path('premium/buy/', views.BuyPremiumView.as_view()),
    path('premium/history/', views.PremiumTransactionListView.as_view()),
]