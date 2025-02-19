from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from .views import FileViewSet, AnnotationViewSet, LoginView

# 创建路由器
router = DefaultRouter()
router.register(r'files', FileViewSet)
router.register(r'annotations', AnnotationViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),  # API 路由
    path('api/auth/login/', LoginView.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # 媒体文件服务 