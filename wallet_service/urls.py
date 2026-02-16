
from django.urls import path, include

urlpatterns = [
        path('wallet_service/authentication/', include('src.apis.authentication.urls')), 
        path('wallet_service/', include('src.apis.wallet.urls')), 
]
