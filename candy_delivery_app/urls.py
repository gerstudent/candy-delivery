from django.contrib import admin
from django.urls import path, include
from apis import views
from apis.routers import CourierRouter, OrdersRouter



courier_router = CourierRouter()
courier_router.register(r'couriers', views.CourierView)

order_router = OrdersRouter()
order_router.register(r'orders', views.OrderView)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(order_router.urls)),
    path('', include(courier_router.urls)),
]
