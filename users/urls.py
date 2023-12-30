from django.urls import re_path, path
from users import views

urlpatterns = [
    #------Auth------
    re_path('login', views.login),
    re_path('signup', views.signup),
    path('mailconfirm/<str:uidb64>/<str:token>/', views.mailconfirm, name='mailconfirm'),
    path('resetpass/<str:uidb64>/<str:token>/', views.resetpassword, name='resetpass'),
    re_path('wannaresetpass/', views.wannaresetpass),
    #------Transactions------
    re_path('get_transaction', views.get_transaction),
    re_path('post_transaction', views.post_transaction),
    re_path('sort_by_category', views.sort_by_category),
    re_path('procent_of_categories', views.procent_of_categories),
    re_path('month_transaction_info', views.month_transaction_info),
    re_path('forecast_transaction', views.forecast_transaction),
    re_path('delete_transaction', views.delete_transaction),
    #------To-Do-List------
    re_path('post_task', views.post_task),
    re_path('update_task', views.update_task),
    re_path('get_task', views.get_task),
    re_path('delete_task', views.delete_task),
    #-----PhoneFriendList------
    re_path('create_phonefriend',views.post_friendphone),
    re_path('get_phonefriend',views.get_friendlist),
    re_path('update_phonefriend',views.update_phonefriend),
    re_path('delete_phonefriend',views.delete_phonefriend),
    #-----B-Objects------------
    re_path('create_bobject',views.post_BObject),
    re_path('get_bobject',views.get_BObject),
    re_path('update_bobject',views.update_BObject),
    re_path('delete_bobject',views.delete_BObject)
    
]