from django.urls import path

from banking import auth_views, views

urlpatterns = [
    path('auth/login/', auth_views.LoginView.as_view(), name='auth-login'),
    path('auth/logout/', auth_views.LogoutView.as_view(), name='auth-logout'),
    path('auth/me/', auth_views.MeView.as_view(), name='auth-me'),

    path('accounts/', views.AccountListCreateView.as_view(), name='account-list-create'),
    path('accounts/<str:account_id>/', views.AccountDetailView.as_view(), name='account-detail'),

    path('transactions/', views.TransactionListCreateView.as_view(), name='transaction-list-create'),
    path('transactions/<str:transaction_id>/', views.TransactionDetailView.as_view(), name='transaction-detail'),

    path('reviews/', views.HumanReviewListView.as_view(), name='review-list'),
    path('reviews/<int:pk>/', views.HumanReviewDetailView.as_view(), name='review-detail'),
    path('reviews/<int:pk>/add/', views.HumanReviewAddView.as_view(), name='review-add'),
    path('reviews/<int:pk>/remove/', views.HumanReviewRemoveView.as_view(), name='review-remove'),
]
